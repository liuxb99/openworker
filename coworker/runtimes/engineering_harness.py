"""Engineering Harness runtime composed from existing OpenWorker seams.

H6 owns AI-Engineering-OS tool discovery/invocation. H7 adds only the missing
information ingress: the first Harness turn is prefixed with the authoritative
prompt returned by go-tool-runtime for the current Project Workspace.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from ..events import Event, EventType
from .harness import DeepSeekHarnessRuntime, HarnessProcessConfig, PermissionHandler
from .tool_runtime_bootstrap import (
    ToolRuntimeBootstrap,
    ToolRuntimeBootstrapClient,
    ToolRuntimeBootstrapError,
)


class EngineeringHarnessRuntime(DeepSeekHarnessRuntime):
    """DeepSeek Harness with one authoritative Project Workspace bootstrap."""

    def __init__(
        self,
        *,
        process_config: HarnessProcessConfig | None = None,
        workspace: str | os.PathLike[str] | None = None,
        bootstrap_client: ToolRuntimeBootstrapClient | None = None,
        bootstrap_project: str = "",
        permission_handler: PermissionHandler | None = None,
    ) -> None:
        super().__init__(
            process_config=process_config,
            workspace=workspace,
            permission_handler=permission_handler,
        )
        self._bootstrap_client = bootstrap_client or ToolRuntimeBootstrapClient.from_env()
        self._owns_bootstrap_client = bootstrap_client is None
        self._bootstrap_project = str(bootstrap_project or "").strip()
        self._bootstrap: ToolRuntimeBootstrap | None = None
        self._bootstrap_lock = asyncio.Lock()
        self._last_result = "success"
        self._last_summary = "OpenWorker engineering Harness session closed"

    @property
    def bootstrap(self) -> ToolRuntimeBootstrap | None:
        return self._bootstrap

    async def _bootstrap_prompt(self, user_input: str) -> str:
        if self._bootstrap is None:
            async with self._bootstrap_lock:
                if self._bootstrap is None:
                    self._bootstrap = await asyncio.to_thread(
                        self._bootstrap_client.start,
                        self.workspace,
                        user_input,
                        task="Execute the current Project Workspace task using dynamically discovered engineering tools.",
                        project=self._bootstrap_project,
                        agent="openworker-harness",
                    )
        assert self._bootstrap is not None
        return (
            self._bootstrap.prompt.rstrip()
            + "\n\n<CurrentUserRequest>\n"
            + user_input
            + "\n</CurrentUserRequest>"
        )

    async def run(
        self,
        user_input: str | list,
        *,
        source: Optional[dict[str, Any]] = None,
        display: Optional[str] = None,
    ) -> AsyncIterator[Event]:
        if not isinstance(user_input, str):
            async for event in super().run(user_input, source=source, display=display):
                yield event
            return
        try:
            prompt = await self._bootstrap_prompt(user_input) if self._bootstrap is None else user_input
        except ToolRuntimeBootstrapError as exc:
            self._last_result = "failed"
            self._last_summary = f"go-tool-runtime bootstrap failed: {exc}"
            yield Event(EventType.TURN_START, {"runtime": "harness", "source": source, "display": display})
            yield Event(EventType.ERROR, {"runtime": "harness", "error": str(exc), "authority": "go-tool-runtime"})
            yield Event(EventType.TURN_END, {"runtime": "harness", "stop_reason": "bootstrap_error"})
            return

        saw_error = False
        stop_reason = ""
        async for event in super().run(prompt, source=source, display=display):
            if event.type is EventType.ERROR:
                saw_error = True
                self._last_result = "failed"
                self._last_summary = str(event.data.get("error") or "Harness runtime error")
            elif event.type is EventType.TURN_END:
                stop_reason = str(event.data.get("stop_reason") or "")
            yield event
        if not saw_error:
            self._last_result = "success"
            self._last_summary = f"Harness turn completed: {stop_reason or 'end_turn'}"

    async def health(self) -> dict[str, Any]:
        base = await super().health()
        capabilities = dict(base.get("capabilities") or {})
        capabilities["tool_runtime_bootstrap"] = True
        base["capabilities"] = capabilities
        base["information_authority"] = "go-tool-runtime"
        base["execution_authority"] = "AI-Engineering-OS"
        base["bootstrap_session_created"] = self._bootstrap is not None
        return base

    async def aclose(self) -> None:
        try:
            if self._bootstrap is not None:
                try:
                    await asyncio.to_thread(
                        self._bootstrap_client.finish,
                        self._bootstrap.session_id,
                        summary=self._last_summary,
                        result=self._last_result,
                    )
                except ToolRuntimeBootstrapError:
                    # Runtime shutdown must still release the Harness process. The
                    # information-authority finish failure cannot justify leaking it.
                    pass
        finally:
            await super().aclose()
            if self._owns_bootstrap_client:
                self._bootstrap_client.close()


__all__ = ["EngineeringHarnessRuntime"]
