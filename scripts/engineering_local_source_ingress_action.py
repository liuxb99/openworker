from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from coworker.engineering.source_ingress import EngineeringSourceIngress, SourceIngressError
from coworker.runtimes.job_binding import JobBindingStore
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
        if (
            item.get("size_match")
            and item.get("sha256") == expected_sha
            and ((not expected_header) or str(item.get("header", "")).startswith(expected_header))
        ):
            matches.append(path)

    unique = {os.path.normcase(str(path)): path for path in matches}
    if not unique:
        raise SourceIngressError("no exact local source matched size/SHA256/header")
    if len(unique) != 1:
        raise SourceIngressError(f"ambiguous exact local source: {len(unique)} matching paths")
    return next(iter(unique.values()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixed-host local engineering source ingress")
    parser.add_argument("--request", required=True)
    parser.add_argument("--os-root", required=True)
    parser.add_argument("--port", type=int, default=18084)
    args = parser.parse_args()

    request = load_request(Path(args.request).resolve())
    workspace_root = str(request.get("workspace_root", "") or "").strip()
    user_request = str(request.get("user_request", "") or "").strip()
    if not workspace_root:
        raise SourceIngressError("workspace_root is required for local source ingress")
    if not user_request:
        raise SourceIngressError("user_request is required for local source ingress")

    source = _resolve_exact_source(request)
    workspace = Path(workspace_root).expanduser().resolve()
    process = None
    try:
        process, os_url, stdout_path, stderr_path = start_isolated_os(Path(args.os_root), workspace, args.port)
        ingress = EngineeringSourceIngress(
            os_url=os_url,
            workspace=workspace,
            assigned_host=str(request["assigned_host"]),
            user_request=user_request,
        )
        try:
            result = ingress.ingest(
                source,
                canonical_name=str(request.get("canonical_name", "source.dwg") or "source.dwg"),
                original_name=str(request.get("original_name", source.name) or source.name),
                media_type=str(request.get("media_type", "application/acad") or "application/acad"),
                expected_size=int(request["expected_size"]),
                expected_sha256=str(request["expected_sha256"]),
                expected_header=str(request.get("expected_header", "") or ""),
                source_run_id=os.environ.get("GITHUB_RUN_ID", ""),
                producer_repository=os.environ.get("GITHUB_REPOSITORY", ""),
                producer_commit_sha=os.environ.get("GITHUB_SHA", ""),
            )
        finally:
            ingress.close()

        payload = result.as_dict()
        payload.update(
            source_local_path=str(source),
            runner_name=os.environ.get("RUNNER_NAME", ""),
            github_run_id=os.environ.get("GITHUB_RUN_ID", ""),
            os_stdout=str(stdout_path),
            os_stderr=str(stderr_path),
        )
        evidence_root = workspace / "evidence" / "source-ingress"
        evidence_root.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_root / f"local-run-{os.environ.get('GITHUB_RUN_ID', 'local')}.json"
        tmp = evidence_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, evidence_path)
        write_github_outputs(payload, evidence_path)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print(
            "LOCAL_SOURCE_INGRESS_REAL_PASS "
            f"host={payload['assigned_host']} source={source} project={payload['project_id']} "
            f"job={payload['job_id']} path={payload['canonical_path']} sha256={payload['sha256']}"
        )
        return 0
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except Exception:
                process.kill()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SourceIngressError, RuntimeError) as exc:
        print(f"LOCAL_SOURCE_INGRESS_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
