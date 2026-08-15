from pathlib import Path
from coworker.project_knowledge import ProjectKnowledgeStore, ProjectWorkEvent


def test_project_knowledge_rebuild_and_query(tmp_path: Path) -> None:
    store = ProjectKnowledgeStore(tmp_path)
    start = store.append(ProjectWorkEvent(
        event_type="dispatch", summary="Harness started Case 0002", project_id="p2", job_id="j2",
        stage="shot-generation", status="running", runtime="engineering-harness",
        session_id="acp-1", runtime_job_id="runtime-1", next_action="wait H3",
        details={"assigned_host":"DESKTOP-ODAQN0D"}, evidence_refs=("run:1",),
    ))
    store.append(ProjectWorkEvent(
        event_type="failure", summary="stale artifact rejected", blocker="artifact provenance mismatch",
        prompt_id="old-prompt", artifact_refs=("MiniMax_H3_00005_.mp4",),
        details={"artifact_disposition":"rejected"},
    ))
    accepted = store.append(ProjectWorkEvent(
        event_type="accepted", summary="current prompt artifact accepted", status="running",
        prompt_id="new-prompt", execution_id="exec-2", artifact_refs=("MiniMax_H3_00006_.mp4",),
        details={"artifact_disposition":"accepted"}, next_action="generate remaining shots",
    ))
    snap = store.snapshot()
    assert snap.assigned_host == "DESKTOP-ODAQN0D"
    assert snap.latest_runtime_job_id == "runtime-1"
    assert snap.latest_session_id == "acp-1"
    assert snap.latest_prompt_id == "new-prompt"
    assert snap.active_blocker == ""
    assert snap.accepted_artifacts == ("MiniMax_H3_00006_.mp4",)
    assert snap.rejected_artifacts == ("MiniMax_H3_00005_.mp4",)
    assert start.event_id and accepted.event_id and start.event_id != accepted.event_id
    assert "new-prompt" in store.query("最新 prompt_id 是什麼？")["answer"]
    assert "generate remaining shots" in store.query("下一步是什麼？")["answer"]
    assert "runtime-1" in store.query("Harness runtime 到哪了？")["answer"]


def test_ledger_is_append_only(tmp_path: Path) -> None:
    store = ProjectKnowledgeStore(tmp_path)
    store.append(ProjectWorkEvent(event_type="plan", summary="one"))
    first = store.events_path.read_text(encoding="utf-8")
    store.append(ProjectWorkEvent(event_type="progress", summary="two"))
    second = store.events_path.read_text(encoding="utf-8")
    assert second.startswith(first)
    assert len(store.events()) == 2