"""Bind every fixed OpenWorker job to the Git-like WorkLedger.

The bridge keeps lifecycle ownership in OpenWorker: creating a JobBinding creates
its durable mini-Git ledger automatically. Higher-level runtimes attach physical
artifacts, verification failures and rework without case-specific bookkeeping.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from ..work_ledger import WorkLedger, WorkLedgerError
from .job_binding import JobBinding

_FAILURE_KINDS = {"failed", "failure", "rework_required", "rework-required"}
_FAILURE_STATUSES = {"failed", "failure", "rework_required", "rework-required"}
_REPAIR_KINDS = {"repaired", "repair", "progress", "executing", "retry"}


class WorkLedgerBridge:
    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.path = self.workspace / ".openworker" / "work-ledger.sqlite"

    def ensure(self, binding: JobBinding, *, goal: str = "") -> dict[str, Any]:
        ledger = WorkLedger(self.path)
        try:
            try:
                return ledger.get_work_by_code(binding.job_code)
            except WorkLedgerError:
                return ledger.create_work(
                    code=binding.job_code,
                    title=f"{binding.project_code} / {binding.job_code}",
                    workspace=str(self.workspace),
                    goal=goal,
                    plan={
                        "project_id": binding.project_id,
                        "project_code": binding.project_code,
                        "job_id": binding.job_id,
                        "assigned_host": binding.assigned_host,
                    },
                )
        finally:
            ledger.close()

    def snapshot(self, binding: JobBinding) -> dict[str, Any]:
        ledger = WorkLedger(self.path)
        try:
            work = ledger.get_work_by_code(binding.job_code)
            return ledger.snapshot(work["work_id"])
        finally:
            ledger.close()

    def sync_project_event(self, binding: JobBinding, event: Any) -> dict[str, Any]:
        """Project a ProjectKnowledge event into the authoritative revision chain.

        This deliberately does not auto-accept a revision. Completion/accepted
        natural-language events may move a mutable revision to verifying, but only
        the WorkLedger required-check gate may move the protected accepted pointer.
        """
        ledger = WorkLedger(self.path)
        try:
            try:
                work = ledger.get_work_by_code(binding.job_code)
            except WorkLedgerError:
                work = ledger.create_work(
                    code=binding.job_code,
                    title=f"{binding.project_code} / {binding.job_code}",
                    workspace=str(self.workspace),
                )

            head_id = str(work["head_revision_id"] or "")
            if not head_id:
                raise WorkLedgerError("work has no HEAD revision")
            head = ledger.get_revision(head_id)
            kind = str(getattr(event, "kind", "") or "").strip().lower()
            status = str(getattr(event, "status", "") or "").strip().lower()
            summary = str(getattr(event, "summary", "") or "").strip()
            details = dict(getattr(event, "details", {}) or {})

            # A new progress/repair event after a recorded failure must create a
            # child revision first. The failed revision is never mutated in place.
            if head["status"] == "rework_required" and kind in _REPAIR_KINDS:
                head = ledger.open_rework(
                    head_id,
                    goal=summary,
                    plan={"source_event_id": str(getattr(event, "event_id", "") or "")},
                    reason=head.get("reason", ""),
                    gap_owner_repo=head.get("gap_owner_repo", ""),
                )
                head_id = head["revision_id"]

            # Materialize physical artifact refs into the current revision. Only
            # paths that actually exist as non-empty files are authoritative.
            for index, ref in enumerate(tuple(getattr(event, "artifact_refs", ()) or ())):
                candidate = Path(str(ref)).expanduser()
                if not candidate.is_absolute():
                    candidate = self.workspace / candidate
                if not candidate.is_file() or candidate.stat().st_size <= 0:
                    continue
                logical_name = candidate.name or f"artifact-{index + 1}"
                try:
                    ledger.add_file_artifact(
                        head_id,
                        logical_name=logical_name,
                        path=candidate,
                        provenance={
                            "source": "ProjectKnowledgeStore",
                            "event_id": str(getattr(event, "event_id", "") or ""),
                            "capability_id": str(getattr(event, "capability_id", "") or ""),
                            "runtime_job_id": str(getattr(event, "runtime_job_id", "") or ""),
                        },
                        verification_status="passed",
                    )
                except WorkLedgerError as exc:
                    # Re-recording exactly the same logical artifact in one
                    # revision is not a new tree; any real replacement still
                    # requires a child revision and remains fail-closed elsewhere.
                    if "already exists in revision" not in str(exc):
                        raise

            if kind in _FAILURE_KINDS or status in _FAILURE_STATUSES:
                current = ledger.get_revision(head_id)
                if current["status"] != "rework_required":
                    reason = summary or "project knowledge verification failure"
                    gap_owner_repo = str(details.get("gap_owner_repo") or details.get("owner_repo") or "").strip()
                    changed_contracts = tuple(str(v) for v in details.get("changed_contracts", ()) if str(v).strip())
                    verification_plan = tuple(str(v) for v in details.get("verification_plan", ()) if str(v).strip())
                    ledger.request_rework(
                        head_id,
                        reason=reason,
                        gap_owner_repo=gap_owner_repo,
                        changed_contracts=changed_contracts,
                        verification_plan=verification_plan,
                    )
            elif status in {"executing", "in_progress", "in-progress", "running"}:
                current = ledger.get_revision(head_id)
                if current["status"] in {"open", "blocked", "verifying"}:
                    ledger.set_revision_status(head_id, "executing", reason=summary)
            elif kind in {"completed", "accepted"} or status in {"completed", "accepted", "success", "succeeded"}:
                current = ledger.get_revision(head_id)
                if current["status"] in {"open", "executing", "blocked"}:
                    ledger.set_revision_status(head_id, "verifying", reason=summary)

            return ledger.snapshot(work["work_id"])
        finally:
            ledger.close()

    def add_file_artifact(
        self,
        binding: JobBinding,
        *,
        logical_name: str,
        path: str | Path,
        provenance: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        ledger = WorkLedger(self.path)
        try:
            work = ledger.get_work_by_code(binding.job_code)
            revision_id = str(work["head_revision_id"] or "")
            if not revision_id:
                raise WorkLedgerError("work has no HEAD revision")
            return ledger.add_file_artifact(
                revision_id,
                logical_name=logical_name,
                path=path,
                provenance=provenance,
                verification_status="passed",
            )
        finally:
            ledger.close()

    def require_rework(
        self,
        binding: JobBinding,
        *,
        reason: str,
        gap_owner_repo: str = "",
        changed_contracts: Sequence[str] = (),
        verification_plan: Sequence[str] = (),
    ) -> dict[str, Any]:
        ledger = WorkLedger(self.path)
        try:
            work = ledger.get_work_by_code(binding.job_code)
            revision_id = str(work["head_revision_id"] or "")
            if not revision_id:
                raise WorkLedgerError("work has no HEAD revision")
            return ledger.request_rework(
                revision_id,
                reason=reason,
                gap_owner_repo=gap_owner_repo,
                changed_contracts=changed_contracts,
                verification_plan=verification_plan,
            )
        finally:
            ledger.close()

    def open_rework(
        self,
        binding: JobBinding,
        *,
        goal: str = "",
        plan: Mapping[str, Any] | None = None,
        reason: str = "",
        gap_owner_repo: str = "",
    ) -> dict[str, Any]:
        ledger = WorkLedger(self.path)
        try:
            work = ledger.get_work_by_code(binding.job_code)
            revision_id = str(work["head_revision_id"] or "")
            if not revision_id:
                raise WorkLedgerError("work has no HEAD revision")
            return ledger.open_rework(
                revision_id,
                goal=goal,
                plan=plan,
                reason=reason,
                gap_owner_repo=gap_owner_repo,
            )
        finally:
            ledger.close()


__all__ = ["WorkLedgerBridge"]
