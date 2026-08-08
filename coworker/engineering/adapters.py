"""Contracts for engineering-domain integrations.

Adapters provide a stable boundary between OpenWorker and specialist engineering
repositories or MCP/services. The core runtime should not import those repositories
or reproduce their domain algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


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
    """Minimal protocol implemented by each specialist integration."""

    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> set[EngineeringCapability]: ...

    def health(self) -> dict[str, Any]: ...

    def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class EngineeringAdapterRegistry:
    """In-process registry for configured engineering adapters.

    This deliberately contains no transport assumptions. A later adapter may call MCP,
    HTTP, a local CLI, or a Python package while exposing the same coordinator contract.
    """

    _adapters: dict[str, EngineeringAdapter] = field(default_factory=dict)

    def register(self, adapter: EngineeringAdapter) -> None:
        name = adapter.name.strip()
        if not name:
            raise ValueError("engineering adapter name must not be empty")
        if name in self._adapters:
            raise ValueError(f"engineering adapter already registered: {name}")
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

    def for_capability(self, capability: EngineeringCapability) -> list[EngineeringAdapter]:
        return [
            adapter
            for adapter in self._adapters.values()
            if capability in adapter.capabilities
        ]
