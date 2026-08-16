"""Typed contracts for engineering capability discovery and readiness.

These contracts are intentionally transport-neutral. Specialist engineering systems may be
reached through HTTP, MCP, CLI, or an in-process package while exposing the same metadata to
OpenWorker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class HealthStatus(str, Enum):
    """Normalized health state used by orchestration and UI layers."""

    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class ApprovalPolicy(str, Enum):
    """Default human-approval posture for an engineering adapter."""

    NEVER = "never"
    MUTATING = "mutating"
    ALWAYS = "always"


@dataclass(frozen=True)
class AdapterDescriptor:
    """Stable, serializable metadata for one engineering adapter."""

    name: str
    capabilities: frozenset[str]
    transport: str = "unspecified"
    version: str | None = None
    approval_policy: ApprovalPolicy = ApprovalPolicy.MUTATING
    operations: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        name = self.name.strip()
        transport = self.transport.strip()
        if not name:
            raise ValueError("engineering adapter descriptor name must not be empty")
        if not transport:
            raise ValueError("engineering adapter transport must not be empty")

        normalized_capabilities = frozenset(
            capability.strip() for capability in self.capabilities if capability.strip()
        )
        if not normalized_capabilities:
            raise ValueError("engineering adapter must expose at least one capability")

        normalized_operations = tuple(operation.strip() for operation in self.operations)
        if any(not operation for operation in normalized_operations):
            raise ValueError("engineering adapter operation names must not be empty")
        if len(set(normalized_operations)) != len(normalized_operations):
            raise ValueError("engineering adapter operation names must be unique")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "transport", transport)
        object.__setattr__(self, "capabilities", normalized_capabilities)
        object.__setattr__(self, "operations", tuple(sorted(normalized_operations)))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": sorted(self.capabilities),
            "transport": self.transport,
            "version": self.version,
            "approval_policy": self.approval_policy.value,
            "operations": list(self.operations),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class HealthReport:
    """Normalized adapter health result.

    Legacy adapters may still return ``{"ok": bool}``; ``from_raw`` converts those payloads
    to this contract so the registry can evolve without breaking the initial adapter protocol.
    """

    status: HealthStatus
    message: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return self.status is HealthStatus.READY

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "ready": self.ready,
            "message": self.message,
            "details": dict(self.details),
        }

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "HealthReport":
        raw_status = raw.get("status")
        if isinstance(raw_status, HealthStatus):
            status = raw_status
        elif isinstance(raw_status, str):
            try:
                status = HealthStatus(raw_status.strip().lower())
            except ValueError:
                status = HealthStatus.UNKNOWN
        elif raw.get("ok") is True:
            status = HealthStatus.READY
        elif raw.get("ok") is False:
            status = HealthStatus.UNAVAILABLE
        else:
            status = HealthStatus.UNKNOWN

        message = raw.get("message")
        return cls(
            status=status,
            message=str(message) if message is not None else None,
            details={key: value for key, value in raw.items() if key not in {"status", "message"}},
        )
