"""Append-only project work knowledge for durable OpenWorker continuity."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ProjectWorkEvent:
    event_type: str
    summary: str
    project_id: str = ""
    job_id: str = ""
    stage: str = ""
    status: str = ""
    owner: str = ""
    blocker: str = ""
    next_action: str = ""
    execution_id: str = ""
    prompt_id: str = ""
    runtime: str = ""
    runtime_job_id: str = ""
    session_id: str = ""
    artifact_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)
    event_id: str = ""
    timestamp: str = ""

    def normalized(self) -> "ProjectWorkEvent":
        return ProjectWorkEvent(
            **{
                **asdict(self),
                "event_id": self.event_id or str(uuid.uuid4()),
                "timestamp": self.timestamp or datetime.now(timezone.utc).isoformat(),
                "artifact_refs": tuple(self.artifact_refs),
                "evidence_refs": tuple(self.evidence_refs),
            }
        )


@dataclass(frozen=True)
class ProjectSnapshot:
    project_id: str = ""
    job_id: str = ""
    assigned_host: str = ""
    workspace: str = ""
    current_stage: str = ""
    current_status: str = ""
    latest_summary: str = ""
    active_blocker: str = ""
    next_action: str = ""
    latest_execution_id: str = ""
    latest_prompt_id: str = ""
    latest_runtime_job_id: str = ""
    latest_session_id: str = ""
    accepted_artifacts: tuple[str, ...] = ()
    rejected_artifacts: tuple[str, ...] = ()
    latest_event_id: str = ""
    updated_at: str = ""


class ProjectKnowledgeStore:
    """Workspace-local append-only ledger; snapshot is always derived."""

    def __init__(self, workspace: str | os.PathLike[str]) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.root = self.workspace / ".openworker"
        self.events_path = self.root / "project-events.jsonl"
        self.snapshot_path = self.root / "project-snapshot.json"

    def append(self, event: ProjectWorkEvent) -> ProjectWorkEvent:
        value = event.normalized()
        self.root.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(asdict(value), ensure_ascii=False, separators=(",", ":")) + "\n")
        self._write_snapshot(self.rebuild())
        return value

    def events(self) -> list[ProjectWorkEvent]:
        if not self.events_path.is_file():
            return []
        result: list[ProjectWorkEvent] = []
        for number, raw in enumerate(self.events_path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
                payload["artifact_refs"] = tuple(payload.get("artifact_refs") or ())
                payload["evidence_refs"] = tuple(payload.get("evidence_refs") or ())
                result.append(ProjectWorkEvent(**payload))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid project ledger line {number}: {exc}") from exc
        return result

    def rebuild(self) -> ProjectSnapshot:
        state: dict[str, Any] = {
            "workspace": str(self.workspace), "accepted_artifacts": [], "rejected_artifacts": []
        }
        for event in self.events():
            for key in ("project_id", "job_id", "stage", "status", "summary", "blocker", "next_action",
                        "execution_id", "prompt_id", "runtime_job_id", "session_id"):
                value = getattr(event, key)
                if value:
                    target = {"stage":"current_stage", "status":"current_status", "summary":"latest_summary",
                              "blocker":"active_blocker", "execution_id":"latest_execution_id",
                              "prompt_id":"latest_prompt_id", "runtime_job_id":"latest_runtime_job_id",
                              "session_id":"latest_session_id"}.get(key, key)
                    state[target] = value
            host = str(event.details.get("assigned_host") or "")
            if host: state["assigned_host"] = host
            disposition = str(event.details.get("artifact_disposition") or "").lower()
            bucket = "accepted_artifacts" if disposition == "accepted" else "rejected_artifacts" if disposition == "rejected" else ""
            if bucket:
                for ref in event.artifact_refs:
                    if ref not in state[bucket]: state[bucket].append(ref)
            if event.event_type in {"accepted", "repaired", "retry", "progress"} and not event.blocker:
                state["active_blocker"] = ""
            state["latest_event_id"] = event.event_id
            state["updated_at"] = event.timestamp
        state["accepted_artifacts"] = tuple(state["accepted_artifacts"])
        state["rejected_artifacts"] = tuple(state["rejected_artifacts"])
        return ProjectSnapshot(**state)

    def snapshot(self) -> ProjectSnapshot:
        return self.rebuild()

    def query(self, question: str) -> dict[str, Any]:
        q = str(question or "").strip().lower()
        s = self.snapshot()
        if not self.events():
            return {"answer":"尚無 OpenWorker 專案工作事件。", "snapshot":asdict(s), "evidence_event_ids":[]}
        if "prompt" in q:
            answer = f"最新 prompt_id：{s.latest_prompt_id or '尚無'}。"
        elif "卡" in q or "block" in q or "fail" in q:
            answer = f"目前 blocker：{s.active_blocker or '無已記錄 blocker'}。下一步：{s.next_action or '尚未記錄'}。"
        elif "下一" in q or "next" in q:
            answer = f"下一步：{s.next_action or '尚未記錄'}。"
        elif "harness" in q or "runtime" in q:
            answer = f"最新 Harness session={s.latest_session_id or '尚無'}，runtime_job_id={s.latest_runtime_job_id or '尚無'}。"
        else:
            answer = (f"目前階段 {s.current_stage or '未知'}，狀態 {s.current_status or '未知'}。"
                      f"{s.latest_summary} blocker={s.active_blocker or '無'}；下一步={s.next_action or '尚未記錄'}。")
        ids = [e.event_id for e in self.events()[-5:]]
        return {"answer":answer, "snapshot":asdict(s), "evidence_event_ids":ids}

    def _write_snapshot(self, snapshot: ProjectSnapshot) -> None:
        tmp = self.snapshot_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(snapshot), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.snapshot_path)


__all__ = ["ProjectKnowledgeStore", "ProjectSnapshot", "ProjectWorkEvent"]