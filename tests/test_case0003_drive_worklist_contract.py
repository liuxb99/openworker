from __future__ import annotations

import json
from pathlib import Path

from coworker.case_worklist import CaseWorklist


ROOT = Path(__file__).resolve().parents[1]


def test_case0003_remaining_worklist_starts_at_drive_publish() -> None:
    payload = json.loads((ROOT / "case-worklists" / "0003.json").read_text(encoding="utf-8"))
    worklist = CaseWorklist.from_dict(payload)

    assert worklist.case_id == "0003"
    assert worklist.assigned_host == "DESKTOP-UL7V2VV"
    assert Path(worklist.workspace_root) == Path(r"D:\AI-Work\jobs\0003-YUJING-BRIDGE")
    assert worklist.next_step() is not None
    assert worklist.next_step().step_id == "0003-160"
    assert worklist.next_step().allowed_actions == ["openworker.review.publish_drive"]


def test_case0003_drive_workflow_is_worklist_gated_and_ul7_only() -> None:
    workflow = (ROOT / ".github" / "workflows" / "case-0003-drive-api-publish-ul7.yml").read_text(
        encoding="utf-8"
    )

    assert "runs-on: [self-hosted, Windows, X64, UL7]" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "case-worklists/0003.json" in workflow
    assert "coworker/case_worklist_runtime.py" in workflow
    assert "case_worklist_action.py ensure" in workflow
    assert "case_worklist_action.py start" in workflow
    assert "--step-id '0003-160'" in workflow
    assert "--action-id 'openworker.review.publish_drive'" in workflow
    assert "--execution-id $env:GITHUB_RUN_ID" in workflow
    assert "case_worklist_action.py block-active" in workflow
    assert "python $script complete-action" in workflow
    assert "CASE0003_WORKLIST_PASS step=0003-160 next=0003-170" in workflow
