"""Bind every fixed OpenWorker job to the Git-like WorkLedger.

The bridge keeps lifecycle ownership in OpenWorker: creating a JobBinding creates
its durable mini-Git ledger automatically. Higher-level runtimes can then attach
physical artifacts, verification failures, rework and acceptance without case-
specific bookkeeping.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from ..work_ledger import WorkLedger, WorkLedgerError
from .job_binding import JobBinding


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
