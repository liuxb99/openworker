from __future__ import annotations

import json
from pathlib import Path

import pytest

from coworker.runtimes.engineering_scope import EngineeringScope
from coworker.runtimes.job_binding import JobBindingError, JobBindingStore


def test_job_binding_persists_host_workspace_and_scope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPUTERNAME", "DESKTOP-A")
    scope = EngineeringScope("prj-1", "CASE-0002", "job-1", "0002-ALADDIN")
    store = JobBindingStore(tmp_path)

    created = store.create(scope)
    loaded = store.load()

    assert loaded == created
    assert loaded is not None
    assert loaded.assigned_host == "DESKTOP-A"
    assert Path(loaded.workspace_root) == tmp_path.resolve()
    assert loaded.scope() == scope
    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "openworker.job-binding.v1"


def test_job_binding_fails_closed_on_other_host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPUTERNAME", "DESKTOP-A")
    store = JobBindingStore(tmp_path)
    store.create(EngineeringScope("prj-1", "P", "job-1", "J"))

    monkeypatch.setenv("COMPUTERNAME", "DESKTOP-B")
    with pytest.raises(JobBindingError, match="assigned to host DESKTOP-A"):
        store.load()
