"""Durable OpenWorker project/job knowledge for model-facing status questions.

This is deliberately separate from go-tool-runtime.  go-tool-runtime remains the
information authority for *tool* discovery/usage/readiness.  OpenWorker owns the
continuity of *work*: what this project/job is, what was done, current stage,
blockers, decisions, evidence, and next actions.

The store is workspace-local and append-only.  It can be updated after each
meaningful work step and queried later by any model without replaying GitHub
Actions logs or guessing from repository state.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .job_binding import JobBindingStore
from .mission_guard import MissionStore


class ProjectKnowledgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProjectKnowledgeEvent:
    schema_version: str
    sequence: int
    timestamp: str
    project_id: str
    job_id: str
    kind: str
    stage: str
    summary: str
    status: str = ""
    owner: str = ""
    capability_id: str = ""
    evidence: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    decisions: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectKnowledgeSnapshot:
    schema_version: str
    project_id: str
    project_code: str
    job_id: str
    job_code: str
    assigned_host: str
    workspace_root: str
    mission_id: str = ""
    user_goal: str = ""
    current_stage: str = ""
    current_status: str = ""
    current_owner: str = ""
    current_capability: str = ""
    latest_summary: str = ""
    blockers: tuple[str, ...] = ()
    decisions: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    event_count: int = 0


@dataclass(frozen=True)
class ProjectKnowledgeAnswer:
    question: str
    answer: str
    snapshot: ProjectKnowledgeSnapshot
    matched_events: tuple[ProjectKnowledgeEvent, ...] = ()


class ProjectKnowledgeStore:
    """Append-only project continuity journal under `.openworker`."""

    def __init__(self, workspace: str | os.PathLike[str]) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.root = self.workspace / ".openworker"
        self.events_path = self.root / "project-knowledge.jsonl"

    def _binding(self):
        binding = JobBindingStore(self.workspace).load()
        if binding is None:
            raise ProjectKnowledgeError("fixed OpenWorker job binding is required")
        return binding

    def _read_events(self) -> list[ProjectKnowledgeEvent]:
        if not self.events_path.exists():
            return []
        result: list[ProjectKnowledgeEvent] = []
        try:
            lines = self.events_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ProjectKnowledgeError(f"cannot read project knowledge: {exc}") from exc
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                raw["evidence"] = tuple(raw.get("evidence", ()))
                raw["blockers"] = tuple(raw.get("blockers", ()))
                raw["decisions"] = tuple(raw.get("decisions", ()))
                raw["next_actions"] = tuple(raw.get("next_actions", ()))
                event = ProjectKnowledgeEvent(**raw)
            except (ValueError, TypeError) as exc:
                raise ProjectKnowledgeError(f"invalid project knowledge event at line {number}: {exc}") from exc
            if event.schema_version != "openworker.project-knowledge-event.v1":
                raise ProjectKnowledgeError(f"unsupported project knowledge schema: {event.schema_version}")
            result.append(event)
        return result

    def record(
        self,
        *,
        kind: str,
        stage: str,
        summary: str,
        status: str = "",
        owner: str = "",
        capability_id: str = "",
        evidence: Iterable[str] = (),
        blockers: Iterable[str] = (),
        decisions: Iterable[str] = (),
        next_actions: Iterable[str] = (),
        details: dict[str, Any] | None = None,
    ) -> ProjectKnowledgeEvent:
        binding = self._binding()
        normalized_summary = str(summary or "").strip()
        if not normalized_summary:
            raise ProjectKnowledgeError("summary is required")
        events = self._read_events()
        event = ProjectKnowledgeEvent(
            schema_version="openworker.project-knowledge-event.v1",
            sequence=len(events) + 1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            project_id=binding.project_id,
            job_id=binding.job_id,
            kind=str(kind or "progress").strip() or "progress",
            stage=str(stage or "").strip(),
            summary=normalized_summary,
            status=str(status or "").strip(),
            owner=str(owner or "").strip(),
            capability_id=str(capability_id or "").strip(),
            evidence=tuple(str(v).strip() for v in evidence if str(v).strip()),
            blockers=tuple(str(v).strip() for v in blockers if str(v).strip()),
            decisions=tuple(str(v).strip() for v in decisions if str(v).strip()),
            next_actions=tuple(str(v).strip() for v in next_actions if str(v).strip()),
            details=dict(details or {}),
        )
        self.root.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")
        return event

    def snapshot(self) -> ProjectKnowledgeSnapshot:
        binding = self._binding()
        events = self._read_events()
        mission = MissionStore(self.workspace).load_contract()
        checkpoint = MissionStore(self.workspace).load_checkpoint()
        latest = events[-1] if events else None

        def latest_nonempty(attr: str) -> tuple[str, ...]:
            for event in reversed(events):
                value = getattr(event, attr)
                if value:
                    return value
            return ()

        return ProjectKnowledgeSnapshot(
            schema_version="openworker.project-knowledge-snapshot.v1",
            project_id=binding.project_id,
            project_code=binding.project_code,
            job_id=binding.job_id,
            job_code=binding.job_code,
            assigned_host=binding.assigned_host,
            workspace_root=binding.workspace_root,
            mission_id=mission.mission_id if mission else "",
            user_goal=mission.user_goal if mission else "",
            current_stage=(checkpoint.stage if checkpoint else (latest.stage if latest else "")),
            current_status=(latest.status if latest else ""),
            current_owner=(checkpoint.current_owner if checkpoint else (latest.owner if latest else "")),
            current_capability=(checkpoint.current_capability if checkpoint else (latest.capability_id if latest else "")),
            latest_summary=(latest.summary if latest else ""),
            blockers=(checkpoint.unresolved_blockers if checkpoint and checkpoint.unresolved_blockers else latest_nonempty("blockers")),
            decisions=latest_nonempty("decisions"),
            next_actions=(
                (checkpoint.next_intended_action,)
                if checkpoint and checkpoint.next_intended_action
                else latest_nonempty("next_actions")
            ),
            evidence=latest_nonempty("evidence"),
            event_count=len(events),
        )

    @staticmethod
    def _terms(question: str) -> set[str]:
        text = str(question or "").casefold()
        separators = "，。！？；：、,.!?;:()[]{}<>/\\|\n\r\t"
        for ch in separators:
            text = text.replace(ch, " ")
        return {term for term in text.split() if len(term) >= 2}

    def query(self, question: str, *, limit: int = 8) -> ProjectKnowledgeAnswer:
        normalized = str(question or "").strip()
        if not normalized:
            raise ProjectKnowledgeError("question is required")
        snapshot = self.snapshot()
        events = self._read_events()
        terms = self._terms(normalized)

        def score(event: ProjectKnowledgeEvent) -> int:
            haystack = " ".join(
                [
                    event.kind,
                    event.stage,
                    event.summary,
                    event.status,
                    event.owner,
                    event.capability_id,
                    *event.evidence,
                    *event.blockers,
                    *event.decisions,
                    *event.next_actions,
                    json.dumps(event.details, ensure_ascii=False, sort_keys=True),
                ]
            ).casefold()
            return sum(1 for term in terms if term in haystack)

        ranked = sorted(enumerate(events), key=lambda pair: (score(pair[1]), pair[0]), reverse=True)
        matched = tuple(event for _, event in ranked if score(event) > 0)[: max(1, limit)]
        if not matched:
            matched = tuple(events[-max(1, limit) :][::-1])

        q = normalized.casefold()
        if any(token in q for token in ("做到哪", "進度", "进度", "目前", "現在", "现在", "status")):
            answer = self._status_answer(snapshot)
        elif any(token in q for token in ("卡", "問題", "问题", "失敗", "失败", "blocker", "error")):
            answer = self._blocker_answer(snapshot, matched)
        elif any(token in q for token in ("下一步", "接下來", "接下来", "next")):
            answer = self._next_answer(snapshot)
        elif any(token in q for token in ("做了什麼", "做了什么", "完成", "history", "歷史", "历史")):
            answer = self._history_answer(snapshot, matched)
        else:
            answer = self._detail_answer(snapshot, matched)
        return ProjectKnowledgeAnswer(normalized, answer, snapshot, matched)

    @staticmethod
    def _status_answer(snapshot: ProjectKnowledgeSnapshot) -> str:
        parts = [
            f"project={snapshot.project_code} ({snapshot.project_id})",
            f"job={snapshot.job_code} ({snapshot.job_id})",
            f"stage={snapshot.current_stage or 'unknown'}",
            f"status={snapshot.current_status or 'unknown'}",
        ]
        if snapshot.latest_summary:
            parts.append(f"latest={snapshot.latest_summary}")
        if snapshot.blockers:
            parts.append("blockers=" + " | ".join(snapshot.blockers))
        if snapshot.next_actions:
            parts.append("next=" + " | ".join(snapshot.next_actions))
        return "; ".join(parts)

    @staticmethod
    def _blocker_answer(snapshot: ProjectKnowledgeSnapshot, events: tuple[ProjectKnowledgeEvent, ...]) -> str:
        blockers = list(snapshot.blockers)
        for event in events:
            for blocker in event.blockers:
                if blocker not in blockers:
                    blockers.append(blocker)
        return "目前沒有已記錄 blocker。" if not blockers else "目前 blocker：" + "；".join(blockers)

    @staticmethod
    def _next_answer(snapshot: ProjectKnowledgeSnapshot) -> str:
        return "目前沒有已記錄下一步。" if not snapshot.next_actions else "下一步：" + "；".join(snapshot.next_actions)

    @staticmethod
    def _history_answer(snapshot: ProjectKnowledgeSnapshot, events: tuple[ProjectKnowledgeEvent, ...]) -> str:
        if not events:
            return "目前沒有已記錄的工作歷史。"
        return "；".join(f"#{event.sequence} {event.stage}: {event.summary}" for event in reversed(events))

    @staticmethod
    def _detail_answer(snapshot: ProjectKnowledgeSnapshot, events: tuple[ProjectKnowledgeEvent, ...]) -> str:
        if not events:
            return ProjectKnowledgeStore._status_answer(snapshot)
        details = "；".join(f"#{event.sequence} {event.summary}" for event in events)
        return ProjectKnowledgeStore._status_answer(snapshot) + "；相關記錄：" + details


__all__ = [
    "ProjectKnowledgeAnswer",
    "ProjectKnowledgeError",
    "ProjectKnowledgeEvent",
    "ProjectKnowledgeSnapshot",
    "ProjectKnowledgeStore",
]
