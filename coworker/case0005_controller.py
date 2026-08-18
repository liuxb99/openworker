"""Case 0005 Snow White local-first controller extensions.

The generic LocalCaseController remains reusable. This module only adds the
Case 0005 business mappings that depend on the REAL storyboard visual plan.
OpenWorker Go remains the durable scheduler; ComfyX remains the IMAGE execution
authority and knowledge-graph owner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from .case_controller import LocalCaseController
from .case_worklist import CaseStep, CaseWorklist, CaseWorklistError


class Case0005Controller(LocalCaseController):
    def _claim_inputs(
        self,
        worklist: CaseWorklist,
        step: CaseStep,
        action: str,
        spec: Mapping[str, Any],
    ) -> dict[str, Any]:
        common = {"workspace_root": str(self.workspace), "assigned_host": worklist.assigned_host}
        if action == "image.comfyx.storyboard-real":
            if step.step_id == "0005-030":
                return {**common, "role": "character_master", "requirements_relpath": "visual-assets/requirements.json"}
            if step.step_id == "0005-040":
                return {**common, "role": "scene_concept", "requirements_relpath": "visual-assets/requirements.json"}
        if action == "comfyx-studio.storyboard.real-bind" and step.step_id == "0005-050":
            return {
                **common,
                "request_relpath": "presentation/storyboard-request.json",
                "output_relpath": "presentation/storyboard-request.bound.json",
            }
        return super()._claim_inputs(worklist, step, action, spec)

    def _acceptance_evidence(self, step: CaseStep, local_result: Mapping[str, Any]) -> dict[str, Any]:
        action = str(local_result.get("capability_id", ""))
        if action == "comfyx-studio.storyboard.plan" and step.step_id == "0005-020":
            evidence = local_result.get("evidence")
            if not isinstance(evidence, Mapping):
                raise CaseWorklistError("0005-020 storyboard plan missing evidence")
            actual = str(evidence.get("director_plan_sha256", "")).strip().lower()
            parent = self.runtime.load().step("0005-010")
            expected = str(parent.evidence.get("director_plan_sha256", "")).strip().lower()
            if not expected:
                raise CaseWorklistError("0005-020 requires durable 0005-010 director_plan_sha256 evidence")
            if actual != expected:
                raise CaseWorklistError(
                    f"0005-020 Director provenance mismatch expected={expected} actual={actual}"
                )
            return super()._acceptance_evidence(step, local_result)
        if action == "presentation.openmaic" and step.step_id == "0005-025":
            evidence = local_result.get("evidence")
            if not isinstance(evidence, Mapping):
                raise CaseWorklistError("0005-025 OpenMAIC missing evidence")
            request_path = self.workspace / "presentation" / "storyboard-request.json"
            if not request_path.is_file():
                raise CaseWorklistError("0005-025 canonical storyboard request is missing")
            expected_request_sha = self._sha256_file(request_path)
            actual_request_sha = str(evidence.get("request_sha256", "")).strip().lower()
            if actual_request_sha != expected_request_sha:
                raise CaseWorklistError(
                    f"0005-025 request provenance mismatch expected={expected_request_sha} actual={actual_request_sha}"
                )
            return super()._acceptance_evidence(step, local_result)
        if action == "image.comfyx.storyboard-real" and step.step_id in {"0005-030", "0005-040"}:
            if str(local_result.get("status", "")).lower() != "completed":
                raise CaseWorklistError("ComfyX storyboard IMAGE batch did not report completed")
            evidence = local_result.get("evidence")
            if not isinstance(evidence, Mapping):
                raise CaseWorklistError("ComfyX storyboard IMAGE batch missing evidence")
            receipts = evidence.get("receipts")
            images = evidence.get("images")
            hashes = evidence.get("sha256")
            if not isinstance(receipts, list) or not receipts:
                raise CaseWorklistError("ComfyX storyboard IMAGE batch returned no receipts")
            if not isinstance(images, list) or len(images) != len(receipts):
                raise CaseWorklistError("ComfyX storyboard IMAGE batch image count mismatch")
            if not isinstance(hashes, list) or len(hashes) != len(receipts):
                raise CaseWorklistError("ComfyX storyboard IMAGE batch sha256 count mismatch")
            if step.step_id == "0005-030":
                if str(evidence.get("role", "")) != "character_master":
                    raise CaseWorklistError("0005-030 requires character_master role evidence")
                mapped = {
                    "character_receipts": receipts,
                    "character_images": images,
                    "character_sha256": hashes,
                }
            else:
                if str(evidence.get("role", "")) != "scene_concept":
                    raise CaseWorklistError("0005-040 requires scene_concept role evidence")
                mapped = {
                    "scene_receipts": receipts,
                    "scene_images": images,
                    "scene_sha256": hashes,
                }
            return self._require_keys(mapped, step.acceptance)
        if action == "comfyx-studio.storyboard.real-bind" and step.step_id == "0005-050":
            if str(local_result.get("status", "")).lower() != "completed":
                raise CaseWorklistError("shot storyboard REAL bind did not report completed")
            evidence = local_result.get("evidence")
            if not isinstance(evidence, Mapping):
                raise CaseWorklistError("shot storyboard REAL bind missing evidence")
            mapped = {
                "shot_image_receipts": evidence.get("shot_image_receipts"),
                "shot_images": evidence.get("shot_images"),
                "shot_image_sha256": evidence.get("shot_image_sha256"),
                "bound_storyboard_request": evidence.get("bound_request"),
            }
            receipts = mapped["shot_image_receipts"]
            images = mapped["shot_images"]
            hashes = mapped["shot_image_sha256"]
            if not isinstance(receipts, list) or not receipts:
                raise CaseWorklistError("0005-050 returned no shot image receipts")
            if not isinstance(images, list) or len(images) != len(receipts):
                raise CaseWorklistError("0005-050 shot image count mismatch")
            if not isinstance(hashes, list) or len(hashes) != len(receipts):
                raise CaseWorklistError("0005-050 shot sha256 count mismatch")
            return self._require_keys(mapped, step.acceptance)
        return super()._acceptance_evidence(step, local_result)

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _job_payload(
        self,
        worklist: CaseWorklist,
        step: CaseStep,
        action: str,
        execution_id: str,
        claim_path: Path,
    ) -> dict[str, Any]:
        python = sys.executable or "python"
        argv = [
            python,
            "-m",
            "coworker.case0005_controller",
            "run-step",
            "--workspace",
            str(self.workspace),
            "--step-id",
            step.step_id,
            "--action-id",
            action,
            "--execution-id",
            execution_id,
            "--claim",
            str(claim_path),
        ]
        return {
            "job_id": execution_id,
            "dispatch_id": "local-controller-" + execution_id,
            "machine": worklist.assigned_host,
            "priority": 100 if step.kind in {"fanout", "join"} else 80,
            "command": subprocess.list2cmdline(argv),
            "cwd": str(self.openworker_root),
            "workspace_root": str(self.workspace),
            "env": self._localexec_env(),
            "timeout_sec": 3600,
            "locks": [f"case:{worklist.case_id}:step:{step.step_id}"],
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Case 0005 Snow White local-first controller")
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
    return parser


def main() -> int:
    args = _parser().parse_args()
    controller = Case0005Controller(args.workspace, node_url=args.node_url, spec_path=getattr(args, "spec", None))
    try:
        if args.command == "bootstrap":
            result = controller.bootstrap(args.manifest, args.spec)
        elif args.command == "dispatch":
            result = controller.dispatch_ready()
        else:
            result = controller.run_step(
                step_id=args.step_id,
                action_id=args.action_id,
                execution_id=args.execution_id,
                claim_path=args.claim,
            )
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.command != "run-step":
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
