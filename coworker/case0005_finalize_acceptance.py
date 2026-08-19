"""Case 0005 finalization acceptance including the physical review contact sheet."""
from __future__ import annotations

from typing import Any, Mapping

from .case_worklist import CaseWorklistError


class Case0005FinalizeAcceptanceMixin:
    def _acceptance_evidence(self, step, local_result: Mapping[str, Any]) -> dict[str, Any]:
        action = str(local_result.get("capability_id", "")).strip()
        if action != "comfyx-studio.finalize":
            return super()._acceptance_evidence(step, local_result)
        if str(local_result.get("status", "")).strip().lower() != "completed":
            raise CaseWorklistError("finalize result did not report completed")
        evidence = local_result.get("evidence")
        if not isinstance(evidence, Mapping):
            raise CaseWorklistError("finalize result missing evidence")
        mapped = {
            "final_mp4": evidence.get("final_mp4"),
            "final_mp4_sha256": evidence.get("final_mp4_sha256"),
            "resolution": evidence.get("resolution") or "physical_qc",
            "duration": evidence.get("duration") or "physical_qc",
            "subtitle_receipt": evidence.get("subtitle_receipt") or "see finalize receipt",
            "physical_qc": evidence.get("physical_qc"),
            "review_contact_sheet": evidence.get("review_contact_sheet"),
            "review_contact_sheet_sha256": evidence.get("review_contact_sheet_sha256"),
        }
        return self._require_keys(mapped, step.acceptance)
