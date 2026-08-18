from pathlib import Path

from coworker.case_worklist import CaseStep, CaseWorklist, StepStatus


def make_worklist(tmp_path: Path) -> CaseWorklist:
    return CaseWorklist(
        case_id="0005",
        workspace_root=str(tmp_path),
        assigned_host="DESKTOP-ODAQN0D",
        steps=[
            CaseStep("010", "root", allowed_actions=["a.root"], acceptance=["ok"]),
            CaseStep("030", "characters", dependencies=["010"], allowed_actions=["a.image"], acceptance=["ok"]),
            CaseStep("040", "scenes", dependencies=["010"], allowed_actions=["a.image"], acceptance=["ok"]),
            CaseStep("050", "join", dependencies=["030", "040"], allowed_actions=["a.join"], acceptance=["ok"]),
        ],
    )


def pass_with_evidence(worklist: CaseWorklist, step_id: str, action: str) -> None:
    worklist.start(step_id, action)
    worklist.record_evidence(step_id, "ok", True)
    worklist.pass_step(step_id)


def test_parallel_frontier_allows_two_independent_running_steps(tmp_path: Path) -> None:
    worklist = make_worklist(tmp_path)
    pass_with_evidence(worklist, "010", "a.root")
    assert [step.step_id for step in worklist.ready_steps()] == ["030", "040"]

    worklist.start("030", "a.image")
    worklist.start("040", "a.image")
    assert [step.step_id for step in worklist.running_steps()] == ["030", "040"]


def test_join_waits_for_both_parallel_parents(tmp_path: Path) -> None:
    worklist = make_worklist(tmp_path)
    pass_with_evidence(worklist, "010", "a.root")
    pass_with_evidence(worklist, "030", "a.image")
    assert [step.step_id for step in worklist.ready_steps()] == ["040"]
    pass_with_evidence(worklist, "040", "a.image")
    assert [step.step_id for step in worklist.ready_steps()] == ["050"]


def test_legacy_next_step_remains_compatible_with_parallel_running(tmp_path: Path) -> None:
    worklist = make_worklist(tmp_path)
    pass_with_evidence(worklist, "010", "a.root")
    worklist.start("030", "a.image")
    worklist.start("040", "a.image")
    assert worklist.next_step().step_id == "030"
    payload = worklist.as_dict()
    assert payload["running_step_ids"] == ["030", "040"]
