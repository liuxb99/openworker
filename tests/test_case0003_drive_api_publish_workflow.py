from __future__ import annotations

from pathlib import Path


def test_case0003_drive_api_publish_is_fixed_to_ul7_and_cloud_identity_complete():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "case-0003-drive-api-publish-ul7.yml").read_text(encoding="utf-8")

    assert "CASE0003_ASSIGNED_HOST: DESKTOP-UL7V2VV" in workflow
    assert "CASE0003_WORKSPACE: 'D:\\\\AI-Work\\\\jobs\\\\0003-YUJING-BRIDGE'" in workflow
    assert "publish_review_bundle_to_drive.py" in workflow
    assert "OPENWORKER_GOOGLE_DRIVE_ACCESS_TOKEN" in workflow
    assert "openworker-review-publish-receipt/v1" in workflow
    assert "google-drive-api" in workflow
    assert "drive_revision_folder_id" in workflow
    assert "drive_file_id" in workflow
    assert "Google Drive Review Publication" in workflow
    assert "accepted pointer moved before LLM review" in workflow
    assert "delivered pointer moved before LLM review" in workflow


def test_case0003_drive_api_publish_does_not_regenerate_physical_results():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "case-0003-drive-api-publish-ul7.yml").read_text(encoding="utf-8")

    assert "case0003_final_acceptance.py" not in workflow
    assert "build_region_pack_from_terrain_grid.py" not in workflow
    assert "workspace_region_pack_browse.gd" not in workflow
    assert "case0003_review_handoff.py" not in workflow
