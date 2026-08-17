"""Classify LLM review findings into tuning versus real tool gaps.

A tool gap is not a parameter tweak. It must enter the owning-repository repair
loop and preserve the diagnosis in the WorkLedger review receipt/rework event.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from .review_cycle import ReviewCycle, ReviewCycleError
from .work_ledger import WorkLedger


class ReviewGapError(ReviewCycleError):
    pass


def _normalize_pass_coverage(cycle: ReviewCycle, revision_id: str, finding: Mapping[str, Any]) -> dict[str, Any]:
    """Require PASS to cover every immutable artifact in the review request.

    The model may identify reviewed artifacts by logical_name only. OpenWorker
    enriches each entry with the authoritative SHA from review-request.json so
    the durable receipt records exactly which bytes were accepted.
    """
    request_path = cycle.review_dir / revision_id / "review-request.json"
    if not request_path.is_file():
        raise ReviewGapError(f"review request unavailable for PASS: {request_path}")
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReviewGapError(f"invalid review request for PASS: {exc}") from exc
    requested_items = request.get("artifacts") or []
    requested: dict[str, dict[str, Any]] = {}
    for item in requested_items:
        if not isinstance(item, Mapping):
            raise ReviewGapError("review request contains invalid artifact entry")
        name = str(item.get("logical_name") or "").strip()
        sha = str(item.get("sha256") or "").strip().lower()
        if not name or len(sha) != 64:
            raise ReviewGapError("review request artifact missing logical_name/sha256")
        if name in requested:
            raise ReviewGapError(f"duplicate artifact in review request: {name}")
        requested[name] = dict(item)
    if not requested:
        raise ReviewGapError("PASS requires at least one requested review artifact")

    reviewed_items = finding.get("reviewed_artifacts") or []
    if not isinstance(reviewed_items, list) or not reviewed_items:
        raise ReviewGapError("PASS requires reviewed_artifacts covering the entire review bundle")
    reviewed_names: list[str] = []
    for item in reviewed_items:
        if isinstance(item, Mapping):
            name = str(item.get("logical_name") or "").strip()
        else:
            name = str(item).strip()
        if not name:
            raise ReviewGapError("PASS reviewed_artifacts contains an empty logical_name")
        if name not in requested:
            raise ReviewGapError(f"PASS references artifact outside review request: {name}")
        reviewed_names.append(name)
    if len(reviewed_names) != len(set(reviewed_names)):
        raise ReviewGapError("PASS reviewed_artifacts contains duplicates")
    missing = sorted(set(requested) - set(reviewed_names))
    extra = sorted(set(reviewed_names) - set(requested))
    if missing or extra:
        raise ReviewGapError(f"PASS does not cover complete review bundle: missing={missing} extra={extra}")

    normalized = dict(finding)
    normalized["reviewed_artifacts"] = [
        {
            "logical_name": name,
            "sha256": requested[name]["sha256"],
            "size_bytes": requested[name].get("size_bytes"),
        }
        for name in sorted(requested)
    ]
    return normalized


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

    PASS must cover every immutable artifact in the review request. TOOL_GAP
    requires an owning repository, affected capability and a concrete
    verification plan. It is normalized to the ReviewCycle FAIL path so the
    authoritative WorkLedger enters REWORK_REQUIRED rather than pretending a
    parameter-only rerun can repair missing capability.
    """
    verdict = str(finding.get("verdict") or "").strip().upper()
    if verdict == "PASS":
        finding = _normalize_pass_coverage(cycle, revision_id, finding)
        return cycle.apply_receipt(
            ledger,
            revision_id,
            finding,
            allowed_parameter_keys=allowed_parameter_keys,
            current_parameters=current_parameters,
        )
    if verdict in {"TUNE", "FAIL"}:
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
