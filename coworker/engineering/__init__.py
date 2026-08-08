"""Engineering extension layer for OpenWorker.

This package is intentionally thin: OpenWorker owns orchestration, permissions, sessions,
and connectors; domain repositories own engineering logic. Integrations should be added
through adapters instead of embedding domain implementations into the core runtime.
"""

from .adapters import EngineeringAdapter, EngineeringAdapterRegistry, EngineeringCapability
from .contracts import AdapterDescriptor, ApprovalPolicy, HealthReport, HealthStatus
from .digital_thread import (
    DigitalThread,
    EvidenceKind,
    EvidenceRef,
    ProvenanceLink,
    RelationKind,
    add_all,
    bim_forge_artifact_ref,
    design_forge_artifact_ref,
    engsketch_version_refs,
    os_artifact_ref,
    os_job_ref,
)
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
    "DigitalThread",
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
    "EvidenceKind",
    "EvidenceRef",
    "HealthReport",
    "HealthStatus",
    "KnowGraphAdapter",
    "ProvenanceLink",
    "RelationKind",
    "SubprocessCommandRunner",
    "TransportResponse",
    "UrllibEngineeringOSTransport",
    "add_all",
    "bim_forge_artifact_ref",
    "core_specialist_adapters",
    "design_forge_artifact_ref",
    "engineering_os_tools",
    "engsketch_version_refs",
    "os_artifact_ref",
    "os_job_ref",
]
