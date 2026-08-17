"""Classify LLM review findings into tuning versus real tool gaps.

A tool gap is not a parameter tweak. It must enter the owning-repository repair
loop and preserve the diagnosis in the WorkLedger review receipt/rework event.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .review_cycle import ReviewCycle, ReviewCycleError
from .work_ledger import WorkLedger


class ReviewGapError(ReviewCycleError):
    pass


def apply_review_finding(
    cycle: ReviewCycle,
    ledger: WorkLedger,
    revision_id: str,
    finding: Mapping[str, Any],
    *,
    allowed_parameter_keys: Sequence[str],
    current_parameters: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply PASS/TUNE/TOOL_GAP with a strict semantic boundary.

    TOOL_GAP requires an owning repository, affected capability and a concrete
    verification plan. It is normalized to the ReviewCycle FAIL path so the
    authoritative WorkLedger enters REWORK_REQUIRED rather than pretending a
    parameter-only rerun can repair missing capability.
    """
    verdict = str(finding.get("verdict") or "").strip().upper()
    if verdict in {"PASS", "TUNE", "FAIL"}:
        return cycle.apply_receipt(
            ledger,
            revision_id,
            finding,
            allowed_parameter_keys=allowed_parameter_keys,
            current_parameters=current_parameters,
        )
    if verdict != "TOOL_GAP":
        raise ReviewGapError(f"unsupported review finding verdict: {verdict!r}")

    owner = str(finding.get("owning_repo") or "").strip()
    capability = str(finding.get("gap_capability") or "").strip()
    description = str(finding.get("gap_description") or finding.get("summary") or "").strip()
    verification_plan = [str(v).strip() for v in finding.get("verification_plan", []) if str(v).strip()]
    if not owner:
        raise ReviewGapError("TOOL_GAP requires owning_repo")
    if not capability:
        raise ReviewGapError("TOOL_GAP requires gap_capability")
    if not description:
        raise ReviewGapError("TOOL_GAP requires gap_description")
    if not verification_plan:
        raise ReviewGapError("TOOL_GAP requires verification_plan")

    normalized = dict(finding)
    normalized.update(
        {
            "verdict": "FAIL",
            "finding_type": "TOOL_GAP",
            "summary": description,
            "owning_repo": owner,
            "gap_capability": capability,
            "gap_description": description,
            "verification_plan": verification_plan,
            "parameter_changes": [],
        }
    )
    result = cycle.apply_receipt(
        ledger,
        revision_id,
        normalized,
        allowed_parameter_keys=allowed_parameter_keys,
        current_parameters=current_parameters,
    )
    result["finding_type"] = "TOOL_GAP"
    result["gap_capability"] = capability
    result["owning_repo"] = owner
    result["verification_plan"] = verification_plan
    return result


__all__ = ["ReviewGapError", "apply_review_finding"]
