from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

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
    for key in ("assigned_host", "expected_size", "expected_sha256", "expected_header", "candidate_paths"):
        if key not in data:
            raise RuntimeError(f"missing source locator field: {key}")
    if not isinstance(data["candidate_paths"], list) or not data["candidate_paths"]:
        raise RuntimeError("candidate_paths must be a non-empty array")
    if len(data["candidate_paths"]) > 64:
        raise RuntimeError("candidate_paths exceeds 64 bounded candidates")
    data["expected_size"] = int(data["expected_size"])
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


def inspect(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    digest = sha256_file(path)
    with path.open("rb") as handle:
        header = handle.read(32).decode("ascii", errors="replace").rstrip("\x00")
    return {"path": str(path), "size": size, "sha256": digest, "header": header}


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
    for candidate in request["candidate_paths"]:
        for path in expand_candidates(str(candidate)):
            key = os.path.normcase(str(path))
            if key in seen:
                continue
            seen.add(key)
            item = inspect(path)
            item["size_match"] = item["size"] == expected_size
            item["sha256_match"] = item["sha256"] == expected_sha
            item["header_match"] = (not expected_header) or str(item["header"]).startswith(expected_header)
            checked.append(item)
            if item["size_match"] and item["sha256_match"] and item["header_match"]:
                matches.append(item)

    if len(matches) > 1:
        unique_paths = {os.path.normcase(item["path"]) for item in matches}
        if len(unique_paths) > 1:
            raise RuntimeError(f"ambiguous exact source: {len(matches)} matching files")
    result = {
        "schema_version": "openworker.source-locator-evidence.v1",
        "assigned_host": assigned,
        "actual_host": host,
        "expected_size": expected_size,
        "expected_sha256": expected_sha,
        "expected_header": expected_header,
        "candidate_count": len(request["candidate_paths"]),
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
