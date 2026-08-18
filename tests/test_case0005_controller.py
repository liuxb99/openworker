from pathlib import Path

from coworker.case0005_controller import Case0005Controller
from coworker.case_worklist import CaseStep, CaseWorklist


def _worklist(tmp_path: Path) -> CaseWorklist:
    return CaseWorklist(
        case_id="0005",
        workspace_root=str(tmp_path),
        assigned_host="DESKTOP-ODAQN0D",
        steps=[],
    )


def test_role_claims_for_parallel_character_and_scene_branches(tmp_path: Path):
    controller = Case0005Controller(tmp_path)
    worklist = _worklist(tmp_path)
    character = CaseStep(
        step_id="0005-030",
        title="characters",
        kind="fanout",
        allowed_actions=["image.comfyx.storyboard-real"],
        acceptance=["character_receipts", "character_images", "character_sha256"],
    )
    scene = CaseStep(
        step_id="0005-040",
        title="scenes",
        kind="fanout",
        allowed_actions=["image.comfyx.storyboard-real"],
        acceptance=["scene_receipts", "scene_images", "scene_sha256"],
    )

    assert controller._claim_inputs(worklist, character, "image.comfyx.storyboard-real", {}) == {
        "workspace_root": str(tmp_path.resolve()),
        "assigned_host": "DESKTOP-ODAQN0D",
        "role": "character_master",
        "requirements_relpath": "visual-assets/requirements.json",
    }
    assert controller._claim_inputs(worklist, scene, "image.comfyx.storyboard-real", {})["role"] == "scene_concept"


def test_character_batch_acceptance_maps_real_receipts(tmp_path: Path):
    controller = Case0005Controller(tmp_path)
    step = CaseStep(
        step_id="0005-030",
        title="characters",
        kind="fanout",
        allowed_actions=["image.comfyx.storyboard-real"],
        acceptance=["character_receipts", "character_images", "character_sha256"],
    )
    result = {
        "status": "completed",
        "capability_id": "image.comfyx.storyboard-real",
        "evidence": {
            "role": "character_master",
            "receipts": [{"status": "succeeded"}, {"status": "succeeded"}],
            "images": [r"D:\AI-Work\jobs\0005-SNOW-WHITE\visual-assets\characters\snow-white\master.png", r"D:\AI-Work\jobs\0005-SNOW-WHITE\visual-assets\characters\queen\master.png"],
            "sha256": ["a" * 64, "b" * 64],
        },
    }
    evidence = controller._acceptance_evidence(step, result)
    assert len(evidence["character_receipts"]) == 2
    assert len(evidence["character_images"]) == 2
    assert evidence["character_sha256"] == ["a" * 64, "b" * 64]


def test_scene_batch_acceptance_requires_matching_arrays(tmp_path: Path):
    controller = Case0005Controller(tmp_path)
    step = CaseStep(
        step_id="0005-040",
        title="scenes",
        kind="fanout",
        allowed_actions=["image.comfyx.storyboard-real"],
        acceptance=["scene_receipts", "scene_images", "scene_sha256"],
    )
    result = {
        "status": "completed",
        "capability_id": "image.comfyx.storyboard-real",
        "evidence": {
            "role": "scene_concept",
            "receipts": [{"status": "succeeded"}],
            "images": [r"D:\AI-Work\jobs\0005-SNOW-WHITE\visual-assets\scene-bibles\forest\concept.png"],
            "sha256": ["c" * 64],
        },
    }
    evidence = controller._acceptance_evidence(step, result)
    assert evidence["scene_sha256"] == ["c" * 64]


def test_child_job_keeps_case0005_controller(tmp_path: Path):
    controller = Case0005Controller(tmp_path)
    worklist = _worklist(tmp_path)
    step = CaseStep(
        step_id="0005-030",
        title="characters",
        kind="fanout",
        allowed_actions=["image.comfyx.storyboard-real"],
        acceptance=["character_receipts"],
    )
    claim = tmp_path / "claim.json"
    payload = controller._job_payload(worklist, step, "image.comfyx.storyboard-real", "case0005-test", claim)
    assert "coworker.case0005_controller" in payload["command"]
    assert "github" not in payload["command"].lower()
