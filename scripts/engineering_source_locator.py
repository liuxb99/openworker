from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "openworker.source-locator-request.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_request(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA:
        raise RuntimeError("unsupported source locator request schema")
    for key in ("assigned_host", "expected_size", "expected_sha256", "expected_header"):
        if key not in data:
            raise RuntimeError(f"missing source locator field: {key}")
    candidate_paths = data.get("candidate_paths", [])
    search_roots = data.get("search_roots", [])
    name_patterns = data.get("name_patterns", [])
    if candidate_paths is None:
        candidate_paths = []
    if search_roots is None:
        search_roots = []
    if name_patterns is None:
        name_patterns = []
    if not isinstance(candidate_paths, list) or len(candidate_paths) > 64:
        raise RuntimeError("candidate_paths must be an array with at most 64 entries")
    if not isinstance(search_roots, list) or len(search_roots) > 16:
        raise RuntimeError("search_roots must be an array with at most 16 entries")
    if not isinstance(name_patterns, list) or len(name_patterns) > 16:
        raise RuntimeError("name_patterns must be an array with at most 16 entries")
    if not candidate_paths and not search_roots:
        raise RuntimeError("candidate_paths or search_roots is required")
    if search_roots and not name_patterns:
        raise RuntimeError("name_patterns is required when search_roots is used")
    data["candidate_paths"] = [str(v) for v in candidate_paths if str(v).strip()]
    data["search_roots"] = [str(v) for v in search_roots if str(v).strip()]
    data["name_patterns"] = [str(v) for v in name_patterns if str(v).strip()]
    data["max_depth"] = int(data.get("max_depth", 8))
    data["max_name_matches"] = int(data.get("max_name_matches", 256))
    if data["max_depth"] < 0 or data["max_depth"] > 20:
        raise RuntimeError("max_depth must be between 0 and 20")
    if data["max_name_matches"] <= 0 or data["max_name_matches"] > 4096:
        raise RuntimeError("max_name_matches must be between 1 and 4096")
    data["expected_size"] = int(data["expected_size"])
    if data["expected_size"] <= 0:
        raise RuntimeError("expected_size must be positive")
    digest = str(data["expected_sha256"]).strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise RuntimeError("expected_sha256 must be 64 hexadecimal characters")
    data["expected_sha256"] = digest
    return data


def current_host() -> str:
    for key in ("COMPUTERNAME", "HOSTNAME"):
        value = str(os.environ.get(key, "") or "").strip()
        if value:
            return value
    return ""


def expand_candidates(raw: str) -> list[Path]:
    text = os.path.expandvars(str(raw or "").strip())
    if not text:
        return []
    path = Path(text)
    if any(ch in text for ch in "*?["):
        parent = path.parent
        pattern = path.name
        if not parent.is_dir():
            return []
        return sorted(p.resolve() for p in parent.glob(pattern) if p.is_file())
    return [path.resolve()] if path.is_file() else []


def bounded_recursive_candidates(
    roots: Iterable[str],
    patterns: list[str],
    *,
    max_depth: int,
    max_name_matches: int,
) -> tuple[list[Path], list[dict[str, Any]]]:
    found: list[Path] = []
    roots_evidence: list[dict[str, Any]] = []
    for raw_root in roots:
        root = Path(os.path.expandvars(str(raw_root))).expanduser()
        root_entry: dict[str, Any] = {
            "root": str(root),
            "exists": root.is_dir(),
            "name_match_count": 0,
            "truncated": False,
        }
        roots_evidence.append(root_entry)
        if not root.is_dir():
            continue
        root = root.resolve()
        root_parts = len(root.parts)
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            depth = len(current_path.parts) - root_parts
            if depth >= max_depth:
                dirs[:] = []
            # Avoid runner / VCS internals and other high-churn trees if a broad root is used.
            dirs[:] = [
                d for d in dirs
                if d.casefold() not in {".git", "node_modules", ".venv", "venv", "__pycache__", "_work"}
            ]
            for name in files:
                if not any(fnmatch.fnmatch(name.casefold(), pattern.casefold()) for pattern in patterns):
                    continue
                root_entry["name_match_count"] += 1
                found.append((current_path / name).resolve())
                if len(found) >= max_name_matches:
                    root_entry["truncated"] = True
                    return found, roots_evidence
    return found, roots_evidence


def inspect(path: Path, expected_size: int) -> dict[str, Any]:
    size = path.stat().st_size
    item: dict[str, Any] = {
        "path": str(path),
        "size": size,
        "size_match": size == expected_size,
        "sha256": "",
        "header": "",
    }
    # Avoid hashing every same-name historical file when size already proves it is not the source.
    if size != expected_size:
        item["sha256_match"] = False
        item["header_match"] = False
        return item
    item["sha256"] = sha256_file(path)
    with path.open("rb") as handle:
        item["header"] = handle.read(32).decode("ascii", errors="replace").rstrip("\x00")
    return item


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    request = load_request(Path(args.request).resolve())
    host = current_host()
    assigned = str(request["assigned_host"]).strip()
    if not host or host.casefold() != assigned.casefold():
        raise RuntimeError(f"wrong self-hosted machine: expected {assigned}, got {host or '<unknown>'}")

    expected_size = int(request["expected_size"])
    expected_sha = request["expected_sha256"]
    expected_header = str(request.get("expected_header", "") or "").strip()
    checked: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()

    discovered, roots_evidence = bounded_recursive_candidates(
        request["search_roots"],
        request["name_patterns"],
        max_depth=request["max_depth"],
        max_name_matches=request["max_name_matches"],
    )
    paths: list[Path] = []
    for candidate in request["candidate_paths"]:
        paths.extend(expand_candidates(str(candidate)))
    paths.extend(discovered)

    for path in paths:
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        try:
            item = inspect(path, expected_size)
        except (OSError, PermissionError) as exc:
            checked.append({"path": str(path), "error": str(exc)})
            continue
        if item["size_match"]:
            item["sha256_match"] = item["sha256"] == expected_sha
            item["header_match"] = (not expected_header) or str(item["header"]).startswith(expected_header)
        checked.append(item)
        if item.get("size_match") and item.get("sha256_match") and item.get("header_match"):
            matches.append(item)

    if len(matches) > 1:
        unique_paths = {os.path.normcase(item["path"]) for item in matches}
        if len(unique_paths) > 1:
            raise RuntimeError(f"ambiguous exact source: {len(matches)} matching files")
    result = {
        "schema_version": "openworker.source-locator-evidence.v2",
        "assigned_host": assigned,
        "actual_host": host,
        "expected_size": expected_size,
        "expected_sha256": expected_sha,
        "expected_header": expected_header,
        "candidate_count": len(request["candidate_paths"]),
        "search_root_count": len(request["search_roots"]),
        "name_patterns": request["name_patterns"],
        "search_roots": roots_evidence,
        "physical_checked_count": len(checked),
        "checked": checked,
        "matched": bool(matches),
        "source_path": matches[0]["path"] if matches else "",
    }
    evidence = Path(args.evidence).resolve()
    evidence.parent.mkdir(parents=True, exist_ok=True)
    temp = evidence.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, evidence)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if matches:
        print(f"SOURCE_LOCATOR_EXACT_MATCH path={matches[0]['path']} sha256={expected_sha}")
        output = os.environ.get("GITHUB_OUTPUT", "").strip()
        if output:
            with open(output, "a", encoding="utf-8") as handle:
                handle.write(f"source_path={matches[0]['path']}\n")
                handle.write(f"evidence_path={evidence}\n")
        return 0
    print("SOURCE_LOCATOR_NO_MATCH", file=sys.stderr)
    return 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SOURCE_LOCATOR_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
