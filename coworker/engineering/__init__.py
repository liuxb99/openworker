"""Engineering extension layer for OpenWorker.

This package is intentionally thin: OpenWorker owns orchestration, permissions, sessions,
and connectors; domain repositories own engineering logic. Integrations should be added
through adapters instead of embedding domain implementations into the core runtime.
"""

from .adapters import EngineeringAdapter, EngineeringAdapterRegistry, EngineeringCapability

__all__ = [
    "EngineeringAdapter",
    "EngineeringAdapterRegistry",
    "EngineeringCapability",
]
