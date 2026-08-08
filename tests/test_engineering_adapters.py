from coworker.engineering import (
    AdapterDescriptor,
    ApprovalPolicy,
    EngineeringAdapterRegistry,
    EngineeringCapability,
    HealthStatus,
)


class FakeAdapter:
    name = "fake-structural"
    capabilities = {EngineeringCapability.STRUCTURAL, EngineeringCapability.REPORTING}

    def health(self):
        return {"ok": True}

    def invoke(self, operation, payload):
        return {"operation": operation, "payload": payload}


class ExplicitDescriptorAdapter(FakeAdapter):
    name = "design-core"
    capabilities = {EngineeringCapability.STRUCTURAL}
    descriptor = AdapterDescriptor(
        name="design-core",
        capabilities=frozenset({EngineeringCapability.STRUCTURAL.value}),
        transport="http",
        version="1.2.3",
        approval_policy=ApprovalPolicy.MUTATING,
        operations=("health", "calculate"),
        metadata={"authority": "AI-CivilDesign-Forge"},
    )

    def health(self):
        return {"status": "ready", "message": "ok", "latency_ms": 12}


class FailingHealthAdapter(FakeAdapter):
    name = "broken-engine"
    capabilities = {EngineeringCapability.COST}

    def health(self):
        raise RuntimeError("connection refused")


class DegradedAdapter(FakeAdapter):
    name = "degraded-engine"
    capabilities = {EngineeringCapability.STRUCTURAL}

    def health(self):
        return {"status": "degraded", "message": "read-only"}


def test_registry_register_and_resolve_by_capability():
    registry = EngineeringAdapterRegistry()
    adapter = FakeAdapter()

    registry.register(adapter)

    assert registry.names() == ["fake-structural"]
    assert registry.get("fake-structural") is adapter
    assert registry.for_capability(EngineeringCapability.STRUCTURAL) == [adapter]
    assert registry.for_capability(EngineeringCapability.COST) == []


def test_registry_rejects_duplicate_names():
    registry = EngineeringAdapterRegistry()
    registry.register(FakeAdapter())

    try:
        registry.register(FakeAdapter())
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("duplicate adapter name must be rejected")


def test_registry_unregister_is_idempotent():
    registry = EngineeringAdapterRegistry()
    registry.register(FakeAdapter())

    registry.unregister("fake-structural")
    registry.unregister("fake-structural")

    assert registry.names() == []


def test_legacy_adapter_gets_conservative_descriptor_and_ready_health():
    registry = EngineeringAdapterRegistry()
    registry.register(FakeAdapter())

    descriptor = registry.descriptor("fake-structural")
    health = registry.health_report("fake-structural")

    assert descriptor.name == "fake-structural"
    assert descriptor.transport == "unspecified"
    assert descriptor.version is None
    assert descriptor.approval_policy is ApprovalPolicy.MUTATING
    assert descriptor.capabilities == frozenset({"structural", "reporting"})
    assert health.status is HealthStatus.READY
    assert health.ready is True


def test_explicit_descriptor_is_preserved_in_deterministic_inventory():
    registry = EngineeringAdapterRegistry()
    registry.register(FakeAdapter())
    registry.register(ExplicitDescriptorAdapter())

    inventory = registry.inventory()

    assert [item["name"] for item in inventory] == ["design-core", "fake-structural"]
    assert inventory[0]["transport"] == "http"
    assert inventory[0]["version"] == "1.2.3"
    assert inventory[0]["capabilities"] == ["structural"]
    assert inventory[0]["operations"] == ["calculate", "health"]
    assert inventory[0]["health"]["status"] == "ready"
    assert inventory[0]["health"]["details"]["latency_ms"] == 12


def test_health_probe_failure_is_contained_and_marked_unavailable():
    registry = EngineeringAdapterRegistry()
    registry.register(FailingHealthAdapter())

    report = registry.health_report("broken-engine")

    assert report.status is HealthStatus.UNAVAILABLE
    assert report.ready is False
    assert "connection refused" in report.message
    assert report.details["exception_type"] == "RuntimeError"


def test_ready_adapters_filters_degraded_and_by_capability():
    registry = EngineeringAdapterRegistry()
    ready = FakeAdapter()
    degraded = DegradedAdapter()
    registry.register(ready)
    registry.register(degraded)

    assert registry.ready_adapters() == [ready]
    assert registry.ready_adapters(EngineeringCapability.STRUCTURAL) == [ready]
    assert registry.ready_adapters(EngineeringCapability.COST) == []


def test_register_rejects_descriptor_capability_mismatch():
    class BadDescriptorAdapter(FakeAdapter):
        descriptor = AdapterDescriptor(
            name="fake-structural",
            capabilities=frozenset({EngineeringCapability.COST.value}),
        )

    registry = EngineeringAdapterRegistry()

    try:
        registry.register(BadDescriptorAdapter())
    except ValueError as exc:
        assert "capabilities do not match" in str(exc)
    else:
        raise AssertionError("descriptor capability mismatch must be rejected")


def test_descriptor_rejects_invalid_operations():
    try:
        AdapterDescriptor(
            name="invalid",
            capabilities=frozenset({"structural"}),
            operations=("health", "health"),
        )
    except ValueError as exc:
        assert "must be unique" in str(exc)
    else:
        raise AssertionError("duplicate operation names must be rejected")
