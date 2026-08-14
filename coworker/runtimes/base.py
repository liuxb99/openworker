"""Agent runtime contract for OpenWorker.

The product layer talks in terms of an agent runtime, not a specific loop
implementation.  The current implementation remains :class:`TurnEngine`; the
contract is deliberately small so a sidecar-backed runtime (for example
DeepSeek Harness) can implement it without inheriting TurnEngine internals.

H1 only introduces the seam.  Session persistence, approvals, tools and all
user-visible behaviour continue to be owned by the existing native runtime.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Optional, Protocol

from ..events import Event


class AgentRuntime(Protocol):
    """Minimum lifecycle surface a session driver needs from an agent runtime.

    This protocol intentionally describes controls/events rather than native
    implementation details such as ``ProviderClient`` or ``ToolRegistry``.
    Future runtimes may live in another process and still satisfy this seam.
    """

    runtime_name: str

    def run(
        self,
        user_input: str | list,
        *,
        source: Optional[dict[str, Any]] = None,
        display: Optional[str] = None,
    ) -> AsyncIterator[Event]:
        """Start one user turn and stream normalized OpenWorker events."""
        ...

    def retry(self) -> AsyncIterator[Event]:
        """Retry a retriable failed turn without appending a new user message."""
        ...

    def resume(self) -> AsyncIterator[Event]:
        """Resume durable unfinished work for the current session."""
        ...

    def request_interrupt(self) -> None:
        """Request cancellation of the active turn and its interruptible work."""
        ...

    def queue_steering(
        self, text: str, source: Optional[dict[str, Any]] = None
    ) -> None:
        """Queue a steering message for the active runtime."""
        ...

    def switch_model(self, model: str) -> Optional[str]:
        """Switch the model used by this runtime, returning any user notice."""
        ...
