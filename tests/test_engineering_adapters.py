from coworker.engineering import (
    EngineeringAdapterRegistry,
    EngineeringCapability,
)


class FakeAdapter:
    name = "fake-structural"
    capabilities = {EngineeringCapability.STRUCTURAL, EngineeringCapability.REPORTING}

    def health(self):
        return {"ok": True}

    def invoke(self, operation, payload):
        return {"operation": operation, "payload": payload}


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
