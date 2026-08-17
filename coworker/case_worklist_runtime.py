"""Cross-process mutation guard for :mod:`coworker.case_worklist`.

The JSON worklist is durable authority, while this module serializes mutations
from separate GitHub Actions / local processes that share one workspace.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import time
from typing import Iterable, Iterator

from .case_worklist import CaseWorklist, CaseWorklistError, CaseWorklistStore, StepStatus


_LOCK_NAME = "case-worklist.lock"
_ACTIVE_ACTION_KEY = "__openworker_active_action"
_ACTIVE_EXECUTION_KEY = "__openworker_active_execution"


class CaseWorklistRuntime:
    """Serialize worklist mutations and enforce one active action per case step."""

    def __init__(self, workspace_root: str | Path, *, lock_timeout: float = 30.0, stale_after: float = 180.0) -> None:
        self.store = CaseWorklistStore(workspace_root)
        self.lock_path = self.store.path.parent / _LOCK_NAME
        self.lock_timeout = float(lock_timeout)
        self.stale_after = float(stale_after)

    @contextmanager
    def lock(self) -> Iterator[None]:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.lock_timeout
        while True:
            try:
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                self._remove_stale_lock_if_safe()
                if time.monotonic() >= deadline:
                    raise CaseWorklistError(f"case worklist mutation lock timeout: {self.lock_path}")
                time.sleep(0.05)
                continue
            try:
                payload = {
                    "pid": os.getpid(),
                    "created_unix": time.time(),
                }
                os.write(fd, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))
            finally:
                os.close(fd)
            break
        try:
            yield
        finally:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass

    def _remove_stale_lock_if_safe(self) -> None:
        try:
            age = time.time() - self.lock_path.stat().st_mtime
        except FileNotFoundError:
            return
        if age <= self.stale_after:
            return
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass

    def load(self) -> CaseWorklist:
        return self.store.load()

    def ensure(self, manifest: CaseWorklist | None = None) -> CaseWorklist:
        with self.lock():
            if self.store.path.is_file():
                return self.store.load()
            if manifest is None:
                raise CaseWorklistError("manifest is required when creating a worklist")
            self.store.save(manifest)
            return manifest

    def add_repair(
        self,
        *,
        parent_step_id: str,
        step_id: str,
        title: str,
        allowed_actions: Iterable[str],
        acceptance: Iterable[str] = (),
    ) -> CaseWorklist:
        """Insert one repair step while holding the cross-process mutation lock."""
        with self.lock():
            worklist = self.store.load()
            worklist.add_repair(
                parent_step_id=parent_step_id,
                step_id=step_id,
                title=title,
                allowed_actions=allowed_actions,
                acceptance=acceptance,
            )
            self.store.save(worklist)
            return worklist

    def start_action(self, step_id: str, action_id: str, *, execution_id: str) -> CaseWorklist:
        execution = execution_id.strip()
        if not execution:
            raise CaseWorklistError("execution_id is required for worklist action start")
        with self.lock():
            worklist = self.store.load()
            step = worklist.assert_action_allowed(step_id, action_id)
            active_action = str(step.evidence.get(_ACTIVE_ACTION_KEY, "") or "").strip()
            active_execution = str(step.evidence.get(_ACTIVE_EXECUTION_KEY, "") or "").strip()
            if active_action:
                if active_action == action_id and active_execution == execution:
                    return worklist
                raise CaseWorklistError(
                    f"case action concurrency blocked: step {step.step_id!r} already runs "
                    f"action {active_action!r} execution {active_execution!r}"
                )
            worklist.start(step_id, action_id)
            step.evidence[_ACTIVE_ACTION_KEY] = action_id
            step.evidence[_ACTIVE_EXECUTION_KEY] = execution
            worklist.revision += 1
            self.store.save(worklist)
            return worklist

    def complete_action(self, step_id: str, action_id: str, *, execution_id: str) -> CaseWorklist:
        with self.lock():
            worklist = self.store.load()
            step = worklist.step(step_id)
            self._assert_active(step, action_id, execution_id)
            step.evidence.pop(_ACTIVE_ACTION_KEY, None)
            step.evidence.pop(_ACTIVE_EXECUTION_KEY, None)
            worklist.revision += 1
            self.store.save(worklist)
            return worklist

    def record(self, step_id: str, key: str, value: object) -> CaseWorklist:
        with self.lock():
            worklist = self.store.load()
            worklist.record_evidence(step_id, key, value)
            self.store.save(worklist)
            return worklist

    def pass_step(self, step_id: str) -> CaseWorklist:
        with self.lock():
            worklist = self.store.load()
            step = worklist.step(step_id)
            if step.evidence.get(_ACTIVE_ACTION_KEY):
                raise CaseWorklistError(
                    f"step {step.step_id!r} cannot pass while action {step.evidence[_ACTIVE_ACTION_KEY]!r} is active"
                )
            worklist.pass_step(step_id)
            self.store.save(worklist)
            return worklist

    def block_active(self, step_id: str, reason: str) -> CaseWorklist:
        with self.lock():
            worklist = self.store.load()
            step = worklist.step(step_id)
            step.evidence.pop(_ACTIVE_ACTION_KEY, None)
            step.evidence.pop(_ACTIVE_EXECUTION_KEY, None)
            if step.status in {StepStatus.RUNNING, StepStatus.READY}:
                worklist.block(step_id, reason)
            elif step.status != StepStatus.BLOCKED:
                return worklist
            self.store.save(worklist)
            return worklist

    @staticmethod
    def _assert_active(step, action_id: str, execution_id: str) -> None:
        action = str(step.evidence.get(_ACTIVE_ACTION_KEY, "") or "").strip()
        execution = str(step.evidence.get(_ACTIVE_EXECUTION_KEY, "") or "").strip()
        if action != action_id.strip() or execution != execution_id.strip():
            raise CaseWorklistError(
                f"active action ownership mismatch for step {step.step_id!r}: "
                f"expected action={action!r} execution={execution!r}"
            )
