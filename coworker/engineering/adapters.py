"""Contracts and registry for engineering-domain integrations.

Adapters provide a stable boundary between OpenWorker and specialist engineering
repositories or MCP/services. The core runtime must not import those repositories or
reproduce their domain algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from .contracts import AdapterDescriptor, ApprovalPolicy, HealthReport, HealthStatus


class EngineeringCapability(str, Enum):
    KNOWLEDGE_GRAPH = "knowledge_graph"
    DRAWING = "drawing"
    DWG_DXF = "dwg_dxf"
    BIM_IFC = "bim_ifc"
    QUANTITY = "quantity"
    COST = "cost"
    STRUCTURAL = "structural"
    SCHEDULING = "scheduling"
    REPORTING = "reporting"
    VISUALIZATION = "visualization"


class EngineeringAdapter(Protocol):
    """Minimal protocol implemented by each specialist integration.

    ``descriptor`` is intentionally optional at runtime for compatibility with the first
    adapter contract. The registry synthesizes a conservative descriptor for legacy adapters.
    """

    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> set[EngineeringCapability]: ...

    def health(self) -> dict[str, Any]: ...

    def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class EngineeringAdapterRegistry:
    """In-process registry for configured engineering adapters.

    The registry is transport-neutral and produces deterministic inventory/readiness data for
    tool, orchestration, and UI layers. Health exceptions are contained and normalized instead
    of escaping into the caller that is merely asking whether an engine is available.
    """

    _adapters: dict[str, EngineeringAdapter] = field(default_factory=dict)

    def register(self, adapter: EngineeringAdapter) -> None:
        name = adapter.name.strip()
        if not name:
            raise ValueError("engineering adapter name must not be empty")
        if name in self._adapters:
            raise ValueError(f"engineering adapter already registered: {name}")

        descriptor = self._descriptor_from_adapter(adapter)
        if descriptor.name != name:
            raise ValueError(
                "engineering adapter descriptor name must match adapter name: "
                f"{descriptor.name!r} != {name!r}"
            )
        adapter_capabilities = {capability.value for capability in adapter.capabilities}
        if descriptor.capabilities != frozenset(adapter_capabilities):
            raise ValueError(
                f"engineering adapter descriptor capabilities do not match adapter: {name}"
            )
        self._adapters[name] = adapter

    def unregister(self, name: str) -> None:
        self._adapters.pop(name, None)

    def get(self, name: str) -> EngineeringAdapter:
        try:
            return self._adapters[name]
        except KeyError as exc:
            raise KeyError(f"engineering adapter not registered: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._adapters)

    def descriptor(self, name: str) -> AdapterDescriptor:
        return self._descriptor_from_adapter(self.get(name))

    def for_capability(self, capability: EngineeringCapability) -> list[EngineeringAdapter]:
        return [
            self._adapters[name]
            for name in self.names()
            if capability in self._adapters[name].capabilities
        ]

    def health_report(self, name: str) -> HealthReport:
        adapter = self.get(name)
        try:
            raw = adapter.health()
        except Exception as exc:  # health probes must not break capability discovery
            return HealthReport(
                status=HealthStatus.UNAVAILABLE,
                message=f"health probe failed: {exc}",
                details={"exception_type": type(exc).__name__},
            )
        if not isinstance(raw, dict):
            return HealthReport(
                status=HealthStatus.UNKNOWN,
                message="adapter health() returned a non-dict payload",
                details={"payload_type": type(raw).__name__},
            )
        return HealthReport.from_raw(raw)

    def ready_adapters(
        self, capability: EngineeringCapability | None = None
    ) -> list[EngineeringAdapter]:
        candidates = self.for_capability(capability) if capability is not None else [
            self._adapters[name] for name in self.names()
        ]
        return [adapter for adapter in candidates if self.health_report(adapter.name).ready]

    def inventory(self) -> list[dict[str, Any]]:
        """Return deterministic capability inventory suitable for APIs and tools."""

        inventory: list[dict[str, Any]] = []
        for name in self.names():
            descriptor = self.descriptor(name)
            health = self.health_report(name)
            inventory.append({**descriptor.to_dict(), "health": health.to_dict()})
        return inventory

    @staticmethod
    def _descriptor_from_adapter(adapter: EngineeringAdapter) -> AdapterDescriptor:
        explicit = getattr(adapter, "descriptor", None)
        if callable(explicit):
            explicit = explicit()
        if explicit is not None:
            if not isinstance(explicit, AdapterDescriptor):
                raise ValueError("engineering adapter descriptor must be an AdapterDescriptor")
            return explicit

        return AdapterDescriptor(
            name=adapter.name,
            capabilities=frozenset(capability.value for capability in adapter.capabilities),
            transport="unspecified",
            approval_policy=ApprovalPolicy.MUTATING,
        )
