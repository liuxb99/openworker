"""OpenWorker permission bridge for DeepSeek Harness ACP requests.

Official ACP rc.5 permission requests expose only sessionId + toolCallId. They do
not carry the tool name or arguments needed by PermissionEngine. H4 therefore
requires an OpenWorker-owned resolver that maps the Harness call id back to the
canonical tool context. Missing context fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from ..engine import ApprovalOutcome, Approver, PermissionRequest
from ..permissions import PermissionEngine


@dataclass(frozen=True)
class HarnessToolContext:
    """Canonical OpenWorker context associated with one Harness tool call."""

    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]
    metadata: Any = None


ToolContextResolver = Callable[[str], Optional[HarnessToolContext]]


class HarnessPermissionBridge:
    """Translate ACP one-shot permission requests into OpenWorker policy decisions.

    The bridge never trusts ACP request payloads to describe the operation. A
    tool_call_id must resolve through an OpenWorker-owned context resolver first.
    """

    def __init__(
        self,
        *,
        permissions: PermissionEngine,
        approver: Approver,
        resolve_context: ToolContextResolver,
    ) -> None:
        self.permissions = permissions
        self.approver = approver
        self.resolve_context = resolve_context

    async def __call__(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_call = params.get("toolCall")
        call_id = tool_call.get("toolCallId") if isinstance(tool_call, dict) else None
        if not isinstance(call_id, str) or not call_id:
            return self._cancelled()

        context = self.resolve_context(call_id)
        if context is None or context.tool_call_id != call_id:
            return self._cancelled()

        decision = self.permissions.evaluate(
            context.tool_name,
            context.arguments,
            context.metadata,
        )
        if decision.allowed:
            return self._allow_once()
        if not decision.needs_user:
            return self._reject_once()

        outcome = await self.approver(
            PermissionRequest(
                tool_name=context.tool_name,
                arguments=context.arguments,
                metadata=context.metadata,
                reason=decision.reason,
                tool_call_id=context.tool_call_id,
            )
        )
        if outcome is ApprovalOutcome.ONCE:
            return self._allow_once()
        if outcome is ApprovalOutcome.ALWAYS_TOOL:
            self.permissions.allow_tool_for_session(context.tool_name)
            return self._allow_once()
        if outcome is ApprovalOutcome.ALWAYS_COMMAND:
            command = str(context.arguments.get("command", ""))
            self.permissions.allow_command_for_session(command)
            return self._allow_once()
        return self._reject_once()

    @staticmethod
    def _allow_once() -> dict[str, Any]:
        return {"outcome": {"outcome": "selected", "optionId": "allow-once"}}

    @staticmethod
    def _reject_once() -> dict[str, Any]:
        return {"outcome": {"outcome": "selected", "optionId": "reject-once"}}

    @staticmethod
    def _cancelled() -> dict[str, Any]:
        return {"outcome": {"outcome": "cancelled"}}


__all__ = [
    "HarnessPermissionBridge",
    "HarnessToolContext",
    "ToolContextResolver",
]
