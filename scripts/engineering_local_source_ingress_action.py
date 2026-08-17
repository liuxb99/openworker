from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from coworker.engineering.source_ingress import EngineeringSourceIngress, SourceIngressError
from coworker.runtimes.job_binding import JobBindingStore

try:
    from scripts.engineering_source_ingress_action import start_isolated_os, write_github_outputs
    from scripts.engineering_source_locator import bounded_recursive_candidates, expand_candidates, inspect, load_request
except ModuleNotFoundError:
    from engineering_source_ingress_action import start_isolated_os, write_github_outputs
    from engineering_source_locator import bounded_recursive_candidates, expand_candidates, inspect, load_request


def _resolve_exact_source(request: dict) -> Path:
    actual = JobBindingStore.current_host().strip()
    assigned = str(request["assigned_host"]).strip()
    if not actual or actual.casefold() != assigned.casefold():
        raise SourceIngressError(f"wrong self-hosted machine: expected {assigned}, got {actual or '<unknown>'}")

    paths: list[Path] = []
    for candidate in request["candidate_paths"]:
        paths.extend(expand_candidates(candidate))
    discovered, _ = bounded_recursive_candidates(
        request["search_roots"],
        request["name_patterns"],
        expected_size=int(request["expected_size"]),
        max_depth=int(request["max_depth"]),
        max_size_matches=int(request["max_size_matches"]),
    )
    paths.extend(discovered)

    matches: list[Path] = []
    seen: set[str] = set()
    expected_sha = str(request["expected_sha256"]).lower()
    expected_header = str(request.get("expected_header", "") or "")
    for path in paths:
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        try:
            item = inspect(path, int(request["expected_size"]))
        except (OSError, PermissionError):
            continue
        if not item.get("size_match"):
            continue
        if str(item.get("sha256", "")).lower() != expected_sha:
            continue
        if expected_header and not str(item.get("header", "")).startswith(expected_header):
            continue
        matches.append(path)
    if not matches:
        raise SourceIngressError("exact local source was not found on the assigned host")
    unique = {os.path.normcase(str(path.resolve())): path.resolve() for path in matches}
    if len(unique) != 1:
        raise SourceIngressError(f"ambiguous exact local source: {len(unique)} matching paths")
    return next(iter(unique.values()))


def _stop_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--os-root", required=True)
    parser.add_argument("--os-port", type=int, default=18084)
    args = parser.parse_args()

    request_path = Path(args.request).expanduser().resolve()
    request = load_request(request_path)
    workspace_raw = str(request.get("workspace_root", "") or "").strip()
    if not workspace_raw:
        raise SourceIngressError("source locator request has no workspace_root")
    workspace = Path(workspace_raw).expanduser().resolve()
    source_path = _resolve_exact_source(request)

    original_name = str(request.get("original_name", "") or source_path.name).strip() or source_path.name
    canonical_name = str(request.get("canonical_name", "") or "source.dwg").strip() or "source.dwg"
    media_type = str(request.get("media_type", "") or "application/octet-stream").strip()
    user_request = str(request.get("user_request", "") or f"Ingest {original_name}").strip()
    assigned_host = str(request["assigned_host"]).strip()

    process: subprocess.Popen[bytes] | None = None
    ingress: EngineeringSourceIngress | None = None
    try:
        process, os_url, stdout_path, stderr_path = start_isolated_os(
            Path(args.os_root).expanduser().resolve(), workspace, args.os_port
        )
        ingress = EngineeringSourceIngress(
            os_url=os_url,
            workspace=workspace,
            assigned_host=assigned_host,
            user_request=user_request,
        )
        result = ingress.ingest(
            source_path,
            canonical_name=canonical_name,
            original_name=original_name,
            media_type=media_type,
            expected_sha256=str(request["expected_sha256"]),
            expected_size=int(request["expected_size"]),
            expected_header=str(request.get("expected_header", "") or ""),
            source_run_id=os.environ.get("GITHUB_RUN_ID", ""),
            producer_repository=os.environ.get("GITHUB_REPOSITORY", ""),
            producer_commit_sha=os.environ.get("GITHUB_SHA", ""),
        )
    finally:
        if ingress is not None:
            ingress.close()
        _stop_process(process)

    output = result.as_dict()
    output.update(
        {
            "schema_version": "openworker.local-source-ingress-result.v2",
            "case_id": str(request.get("case_id", "") or ""),
            "source_path": str(source_path),
            "runner_name": os.environ.get("RUNNER_NAME", ""),
            "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "os_stdout": str(stdout_path),
            "os_stderr": str(stderr_path),
        }
    )
    evidence_root = workspace / "evidence" / "source-ingress"
    evidence_root.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_root / f"local-run-{os.environ.get('GITHUB_RUN_ID', 'local')}.json"
    temp = evidence_path.with_suffix(".tmp")
    temp.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, evidence_path)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    print(
        f"LOCAL_SOURCE_INGRESS_REAL_PASS host={output['assigned_host']} "
        f"job_id={output['job_id']} sha256={output['sha256']} canonical={output['canonical_path']}"
    )
    write_github_outputs(output, evidence_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"LOCAL_SOURCE_INGRESS_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
