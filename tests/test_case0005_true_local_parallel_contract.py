from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_activation_uses_canonical_operational_supervisor() -> None:
    text = (ROOT / "scripts" / "activate-case0005-local-supervisor.ps1").read_text(encoding="utf-8")
    assert "coworker.case0005_verified_local_controller" in text
    assert "install-and-verify-true-local-supervisor.ps1" in text
    assert "/api/execution/local-supervisor/status" in text
    assert "fresh_claim_slot_count" in text
    assert "fresh_executor_slot_count" in text
    assert "OPERATIONAL" in text
    assert "verify-gtr-local-supervisor.ps1" not in text
    assert "controllerModule = 'coworker.case0005_local_supervisor'" not in text


def test_activation_cannot_skip_real_verification_or_reuse_unknown_old_binaries() -> None:
    text = (ROOT / "scripts" / "activate-case0005-local-supervisor.ps1").read_text(encoding="utf-8")
    assert "SkipParallelVerification" not in text
    assert "binaries_reinstalled_from_current_checkout = $true" in text
    assert "install-and-verify-true-local-supervisor.ps1" in text
    assert "REAL_VERIFIED" in text
    assert "registered_capabilities" in text
    assert "required_case_capabilities" in text
    assert "capability_coverage_complete = $true" in text
    for capability in (
        "comfyx-studio.director.preproduction",
        "comfyx-studio.storyboard.plan",
        "presentation.openmaic",
        "image.comfyx.storyboard-real",
        "comfyx-studio.storyboard.real-bind",
        "comfyx.production.video.real",
        "comfyx-studio.finalize",
        "openworker.case.publish-artifacts",
        "drive.review.publish",
    ):
        assert capability in text


def test_case0005_worklist_requires_live_four_plus_four_and_queue_owned_fanout() -> None:
    worklist = json.loads((ROOT / "case-worklists" / "0005.json").read_text(encoding="utf-8"))
    policy = worklist["parallel_policy"]
    assert policy["canonical_controller_module"] == "coworker.case0005_verified_local_controller"
    assert policy["required_supervisor_status"] == "OPERATIONAL"
    assert policy["required_verification_status"] == "REAL_VERIFIED"
    assert policy["required_fresh_claim_slots"] == 4
    assert policy["required_fresh_executor_slots"] == 4
    assert policy["max_local_slots"] == 4
    assert policy["fanout_queue_owner"] == "go-tool-runtime:8848"
    assert policy["openworker_business_child_jobs_allowed"] is False
    assert policy["github_actions_business_execution_allowed"] is False
    assert policy["github_actions_fallback_allowed"] is False


def test_approval_pptx_must_publish_locally_before_user_gate() -> None:
    worklist = json.loads((ROOT / "case-worklists" / "0005.json").read_text(encoding="utf-8"))
    steps = {step["step_id"]: step for step in worklist["steps"]}
    assert steps["0005-026"]["dependencies"] == ["0005-025"]
    assert steps["0005-026"]["allowed_actions"] == ["openworker.case.publish-artifacts"]
    assert steps["0005-027"]["dependencies"] == ["0005-026"]
    assert steps["0005-056"]["dependencies"] == ["0005-055"]
    assert steps["0005-056"]["allowed_actions"] == ["openworker.case.publish-artifacts"]
    assert steps["0005-057"]["dependencies"] == ["0005-056"]
    for step_id in ("0005-026", "0005-056"):
        acceptance = set(steps[step_id]["acceptance"])
        assert "published_artifact_sha256" in acceptance
        assert "artifact_transport" in acceptance
        assert "github_action_used_for_artifact_transport" in acceptance


def test_artifact_acceptance_mapper_is_wired_into_canonical_controller() -> None:
    text = (ROOT / "coworker" / "case0005_verified_local_controller.py").read_text(encoding="utf-8")
    assert "Case0005ArtifactPublishAcceptanceMixin" in text
    mapper = (ROOT / "coworker" / "case0005_artifact_publish_acceptance.py").read_text(encoding="utf-8")
    assert 'google-drive-api' in mapper
    assert 'github_action_used_for_artifact_transport' in mapper
    assert 'presentation/storyboard-text-only.pptx' in mapper
    assert 'presentation/storyboard-illustrated.pptx' in mapper
