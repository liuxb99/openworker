"""Canonical Case 0005 controller gated by REAL local-supervisor verification.

This wrapper is intentionally small: the true-local four-slot fanout logic lives
in case0005_true_local_controller.py, while this layer prevents bootstrap or
business dispatch unless go-tool :8848 has a fresh REAL_VERIFIED receipt.
There is no GitHub Actions fallback.
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .case0005_true_local_controller import TrueLocalCase0005Controller
from .case_worklist import CaseWorklistError

_VERIFY_URL = "http://127.0.0.1:8848/api/execution/local-supervisor/verification"


class VerifiedLocalCase0005Controller(TrueLocalCase0005Controller):
    def _require_verified_local_supervisor(self, operation: str) -> dict:
        try:
            request = Request(_VERIFY_URL, method="GET")
            with urlopen(request, timeout=8) as response:
                payload = response.read(2 * 1024 * 1024)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            self._append_ledger(
                "local_supervisor_verification_failed",
                operation=operation,
                verification_url=_VERIFY_URL,
                reason=f"verification endpoint unavailable: {exc}",
                execution_route="blocked",
                github_action_fallback_allowed=False,
            )
            raise CaseWorklistError(f"true local supervisor verification endpoint unavailable: {exc}") from exc
        try:
            value = json.loads(payload.decode("utf-8"))
        except Exception as exc:
            self._append_ledger(
                "local_supervisor_verification_failed",
                operation=operation,
                verification_url=_VERIFY_URL,
                reason=f"invalid verification JSON: {exc}",
                execution_route="blocked",
                github_action_fallback_allowed=False,
            )
            raise CaseWorklistError("true local supervisor verification returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise CaseWorklistError("true local supervisor verification response must be an object")
        status = str(value.get("status", "")).strip()
        receipt = value.get("receipt")
        if status != "REAL_VERIFIED" or not isinstance(receipt, dict):
            self._append_ledger(
                "local_supervisor_verification_failed",
                operation=operation,
                verification_url=_VERIFY_URL,
                verification_status=status or "UNKNOWN",
                verification=value,
                execution_route="blocked",
                github_action_fallback_allowed=False,
            )
            raise CaseWorklistError(
                f"true local supervisor is not REAL_VERIFIED (status={status or 'UNKNOWN'}); "
                "business dispatch is blocked and GitHub Actions fallback is forbidden"
            )
        if str(receipt.get("route_label", "")).strip() != "LOCAL_SUPERVISOR":
            raise CaseWorklistError("verification receipt route_label is not LOCAL_SUPERVISOR")
        if bool(receipt.get("github_action_used_for_business_execution")):
            raise CaseWorklistError("verification receipt reports GitHub business execution")
        if int(receipt.get("distinct_claim_worker_count", 0) or 0) < 4:
            raise CaseWorklistError("verification receipt proves fewer than four claim workers")
        if int(receipt.get("distinct_executor_slot_count", 0) or 0) < 4:
            raise CaseWorklistError("verification receipt proves fewer than four executor slots")
        self._append_ledger(
            "local_supervisor_verification_passed",
            operation=operation,
            verification_url=_VERIFY_URL,
            verification_status=status,
            verification_receipt_path=str(value.get("receipt_path", "")),
            max_parallel_actions=int(receipt.get("max_parallel_actions", 0) or 0),
            distinct_claim_worker_count=int(receipt.get("distinct_claim_worker_count", 0) or 0),
            distinct_executor_slot_count=int(receipt.get("distinct_executor_slot_count", 0) or 0),
            execution_route="local_supervisor",
            github_action_used_for_business_execution=False,
        )
        return value

    def bootstrap(self, manifest_path, spec_path):
        self._require_verified_local_supervisor("bootstrap")
        return super().bootstrap(manifest_path, spec_path)

    def dispatch_ready(self):
        self._require_verified_local_supervisor("dispatch")
        return super().dispatch_ready()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Case 0005 REAL-verified local controller")
    parser.add_argument("--node-url", default="http://127.0.0.1:8787")
    sub = parser.add_subparsers(dest="command", required=True)
    bootstrap = sub.add_parser("bootstrap")
    bootstrap.add_argument("--workspace", required=True)
    bootstrap.add_argument("--manifest", required=True)
    bootstrap.add_argument("--spec", required=True)
    dispatch = sub.add_parser("dispatch")
    dispatch.add_argument("--workspace", required=True)
    dispatch.add_argument("--spec")
    run = sub.add_parser("run-step")
    run.add_argument("--workspace", required=True)
    run.add_argument("--spec")
    run.add_argument("--step-id", required=True)
    run.add_argument("--action-id", required=True)
    run.add_argument("--execution-id", required=True)
    run.add_argument("--claim", required=True)
    image = sub.add_parser("run-image-asset")
    image.add_argument("--workspace", required=True)
    image.add_argument("--step-id", required=True)
    image.add_argument("--group-execution-id", required=True)
    image.add_argument("--child-job-id", required=True)
    image.add_argument("--asset-id", required=True)
    image.add_argument("--role", required=True)
    image.add_argument("--claim", required=True)
    image.add_argument("--fanout-manifest", required=True)
    video = sub.add_parser("run-video-shot")
    video.add_argument("--workspace", required=True)
    video.add_argument("--spec")
    video.add_argument("--group-execution-id", required=True)
    video.add_argument("--child-job-id", required=True)
    video.add_argument("--shot-id", required=True)
    video.add_argument("--claim", required=True)
    video.add_argument("--fanout-manifest", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    controller = VerifiedLocalCase0005Controller(args.workspace, node_url=args.node_url, spec_path=getattr(args, "spec", None))
    try:
        if args.command == "bootstrap":
            result = controller.bootstrap(args.manifest, args.spec)
        elif args.command == "dispatch":
            result = controller.dispatch_ready()
        elif args.command == "run-step":
            result = controller.run_step(
                step_id=args.step_id,
                action_id=args.action_id,
                execution_id=args.execution_id,
                claim_path=args.claim,
            )
        elif args.command == "run-image-asset":
            result = controller.run_image_asset(
                step_id=args.step_id,
                group_execution_id=args.group_execution_id,
                child_job_id=args.child_job_id,
                asset_id=args.asset_id,
                role=args.role,
                claim_path=args.claim,
                fanout_manifest=args.fanout_manifest,
            )
        else:
            result = controller.run_video_shot(
                group_execution_id=args.group_execution_id,
                child_job_id=args.child_job_id,
                shot_id=args.shot_id,
                claim_path=args.claim,
                fanout_manifest=args.fanout_manifest,
            )
    except Exception as exc:
        try:
            controller._append_ledger("controller_command_failed", command=args.command, error=str(exc))
        except Exception:
            pass
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.command not in {"run-step", "run-image-asset", "run-video-shot"}:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
