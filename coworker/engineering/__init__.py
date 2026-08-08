"""Engineering extension layer for OpenWorker.

This package is intentionally thin: OpenWorker owns orchestration, permissions, sessions,
and connectors; domain repositories own engineering logic. Integrations should be added
through adapters instead of embedding domain implementations into the core runtime.
"""

from .adapters import EngineeringAdapter, EngineeringAdapterRegistry, EngineeringCapability
from .contracts import AdapterDescriptor, ApprovalPolicy, HealthReport, HealthStatus
from .engineering_os import (
    EngineeringOSClient,
    EngineeringOSConfig,
    EngineeringOSContractError,
    EngineeringOSError,
    EngineeringOSHTTPError,
    EngineeringOSTimeoutError,
    EngineeringOSTransport,
    EngineeringOSTransportError,
    TransportResponse,
    UrllibEngineeringOSTransport,
)
from .specialists import (
    BIMForgeAdapter,
    CommandResult,
    DesignForgeAdapter,
    EngSketchAdapter,
    KnowGraphAdapter,
    SubprocessCommandRunner,
    core_specialist_adapters,
)
from .tools import engineering_os_tools

__all__ = [
    "AdapterDescriptor",
    "ApprovalPolicy",
    "BIMForgeAdapter",
    "CommandResult",
    "DesignForgeAdapter",
    "EngineeringAdapter",
    "EngineeringAdapterRegistry",
    "EngineeringCapability",
    "EngineeringOSClient",
    "EngineeringOSConfig",
    "EngineeringOSContractError",
    "EngineeringOSError",
    "EngineeringOSHTTPError",
    "EngineeringOSTimeoutError",
    "EngineeringOSTransport",
    "EngineeringOSTransportError",
    "EngSketchAdapter",
    "HealthReport",
    "HealthStatus",
    "KnowGraphAdapter",
    "SubprocessCommandRunner",
    "TransportResponse",
    "UrllibEngineeringOSTransport",
    "core_specialist_adapters",
    "engineering_os_tools",
]
