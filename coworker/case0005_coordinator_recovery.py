"""Recovery for Case 0005 queue-owned fanout coordinators.

The durable business queue is go-tool :8848. A missing/failed OpenWorker
coordinator must never cause the business children to be submitted again.
This mixin repairs only the lightweight coordinator process.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .case_worklist import StepStatus


class Case0005CoordinatorRecoveryMixin:
    def _resume_queue_owned_coordinators(self) -> list[dict[str, Any]]:
        worklist = self.runtime.load()
        fanout_root = self.workspace / ".openworker" / "fanout"
        if not fanout_root.is_dir():
            return []
        recovered: list[dict[str, Any]] = []
        for manifest_path in sorted(fanout_root.glob("*/fanout-manifest.json")):
            try:
                manifest = self._load_json(manifest_path)
            except Exception as exc:
                self._append_ledger("queue_coordinator_manifest_invalid", manifest_path=str(manifest_path), error=str(exc))
                continue
            if not isinstance(manifest, Mapping) or not bool(manifest.get("queue_owns_all_children")):
                continue
            step_id = str(manifest.get("step_id", "")).strip()
            group_id = str(manifest.get("group_execution_id", "")).strip()
            if not step_id or not group_id:
                continue
            try:
                step = worklist.step(step_id)
            except Exception:
                continue
            if step.status != StepStatus.RUNNING:
                continue
            active = str(step.evidence.get("__openworker_active_execution", "") or "").strip()
            if active != group_id:
                continue
            action = str(manifest.get("action_id", "")).strip()
            kind = "video" if action == "comfyx.production.video.real" else "image"
            timeout = 14400 if kind == "video" else 5400
            coordinator_id = f"{group_id}--queue-coordinator"
            state: dict[str, Any] | None = None
            try:
                state = self.node.job_status(coordinator_id)
            except Exception:
                state = None
            status = str((state or {}).get("status", "")).strip().lower()
            if state is None:
                payload = self._coordinator_payload(
                    worklist,
                    group_id=group_id,
                    kind=kind,
                    manifest_path=Path(manifest_path),
                    timeout_sec=timeout,
                )
                ack = self.node.submit(payload)
                if bool(ack.get("accepted")):
                    entry = {"step_id":step_id,"group_execution_id":group_id,"coordinator_id":coordinator_id,"action":"submitted_missing","ack":ack}
                    recovered.append(entry)
                    self._append_ledger("queue_coordinator_recovered", **entry, queue_authority="go-tool-runtime:8848", business_children_resubmitted=False)
                continue
            if status in {"failed", "cancelled", "canceled"}:
                result = self.node.retry(coordinator_id)
                entry = {"step_id":step_id,"group_execution_id":group_id,"coordinator_id":coordinator_id,"action":"retried_terminal","previous_status":status,"result":result}
                recovered.append(entry)
                self._append_ledger("queue_coordinator_recovered", **entry, queue_authority="go-tool-runtime:8848", business_children_resubmitted=False)
                continue
            self._append_ledger(
                "queue_coordinator_observed",
                step_id=step_id,
                group_execution_id=group_id,
                coordinator_id=coordinator_id,
                coordinator_status=status or "unknown",
                queue_authority="go-tool-runtime:8848",
                business_children_resubmitted=False,
            )
        return recovered
