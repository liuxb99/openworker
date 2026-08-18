from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coworker.case_worklist import CaseStep, CaseWorklist, CaseWorklistError, CaseWorklistStore, StepStatus
from coworker.case_worklist_runtime import CaseWorklistRuntime
from scripts.case0002_apply_openmaic_receipt import apply_receipt, validate_receipt


def _write_artifacts(workspace: Path, rel: str = "presentation/storyboard.pptx", *, slides: int = 4):
    pptx = workspace / rel
    pptx.parent.mkdir(parents=True, exist_ok=True)
    pptx.write_bytes(b"physical-openmaic-pptx")
    sha = hashlib.sha256(pptx.read_bytes()).hexdigest()
    manifest = pptx.with_suffix(".manifest.json")
    manifest.write_text(
        json.dumps({"status": "succeeded", "artifact": {"path": rel, "sha256": sha, "slide_count": slides}}),
        encoding="utf-8",
    )
    return pptx, manifest, sha


def _receipt(workspace: Path, *, media: int = 0, rel: str = "presentation/storyboard.pptx", slides: int = 4):
    pptx, manifest, sha = _write_artifacts(workspace, rel, slides=slides)
    return {
        "tool": "presentation.openmaic",
        "status": "succeeded",
        "artifact": {
            "path": str(pptx),
            "size_bytes": pptx.stat().st_size,
            "slide_count": slides,
            "sha256": sha,
            "media_count": media,
        },
        "manifest": str(manifest),
        "runner": {"computer_name": "DESKTOP-ODAQN0D"},
    }


def _text_worklist(workspace: Path) -> CaseWorklist:
    return CaseWorklist(
        case_id="0002",
        workspace_root=str(workspace),
        assigned_host="DESKTOP-ODAQN0D",
        steps=[
            CaseStep("0002-020", "storyboard request", status=StepStatus.PASSED),
            CaseStep(
                "0002-025",
                "text storyboard",
                dependencies=["0002-020"],
                allowed_actions=["presentation.openmaic"],
                acceptance=[
                    "storyboard_pptx",
                    "storyboard_manifest",
                    "storyboard_pptx_sha256",
                    "slide_count",
                    "reopen_receipt",
                    "image_count",
                ],
            ),
            CaseStep(
                "0002-027",
                "user approval",
                kind="approval",
                dependencies=["0002-025"],
                allowed_actions=["openworker.user.approval"],
                acceptance=["approval_decision"],
            ),
        ],
    )


def test_text_only_receipt_passes_025_and_stops_at_user_approval(tmp_path: Path):
    workspace = tmp_path.resolve()
    CaseWorklistStore(workspace).save(_text_worklist(workspace))
    runtime = CaseWorklistRuntime(workspace)
    runtime.start_action("0002-025", "presentation.openmaic", execution_id="presentation.openmaic:42")

    result = apply_receipt(
        workspace,
        "0002-025",
        "presentation.openmaic:42",
        _receipt(workspace, media=0),
    )
    data = result.as_dict()
    step = result.step("0002-025")
    assert step.status == StepStatus.PASSED
    assert step.evidence["image_count"] == 0
    assert step.evidence["slide_count"] == 4
    assert data["canonical_next_step_id"] == "0002-027"
    assert result.step("0002-027").status == StepStatus.READY


def test_text_only_receipt_rejects_embedded_media(tmp_path: Path):
    workspace = tmp_path.resolve()
    receipt = _receipt(workspace, media=1)
    with pytest.raises(CaseWorklistError, match="media_count == 0"):
        validate_receipt(workspace, "DESKTOP-ODAQN0D", "0002-025", receipt)


def test_receipt_rejects_physical_sha_mismatch(tmp_path: Path):
    workspace = tmp_path.resolve()
    receipt = _receipt(workspace, media=0)
    pptx = Path(receipt["artifact"]["path"])
    pptx.write_bytes(b"tampered-after-receipt")
    with pytest.raises(CaseWorklistError, match="physical PPTX sha256 mismatch"):
        validate_receipt(workspace, "DESKTOP-ODAQN0D", "0002-025", receipt)


def test_illustrated_receipt_requires_media_and_maps_bound_count(tmp_path: Path):
    workspace = tmp_path.resolve()
    rel = "presentation/storyboard-illustrated.pptx"
    with pytest.raises(CaseWorklistError, match="requires media_count > 0"):
        validate_receipt(workspace, "DESKTOP-ODAQN0D", "0002-055", _receipt(workspace, media=0, rel=rel))

    evidence = validate_receipt(
        workspace,
        "DESKTOP-ODAQN0D",
        "0002-055",
        _receipt(workspace, media=4, rel=rel),
    )
    assert evidence["bound_image_count"] == 4
    assert evidence["illustrated_storyboard_sha256"]
