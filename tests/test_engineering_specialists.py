import types

import pytest

from coworker.engineering import (
    BIMForgeAdapter,
    CommandResult,
    DesignForgeAdapter,
    EngSketchAdapter,
    EngineeringAdapterRegistry,
    EngineeringCapability,
    KnowGraphAdapter,
)


class FakeRunner:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def run(self, argv, *, timeout):
        self.calls.append((list(argv), timeout))
        if not self.responses:
            raise AssertionError("unexpected command")
        return self.responses.pop(0)


def test_design_forge_health_and_capabilities():
    runner = FakeRunner([CommandResult(0, '[{"id":"forge.rc-column"}]', "")])
    adapter = DesignForgeAdapter(runner=runner)
    assert adapter.health()["status"] == "ready"
    assert runner.calls[0][0] == ["civilforge-tool", "capabilities"]
    assert adapter.descriptor.version == "tool-protocol/1.0.0"


def test_design_forge_execute_uses_request_file_and_parses_json():
    runner = FakeRunner([CommandResult(0, '{"status":"succeeded","data":{"design_ok":true}}', "")])
    adapter = DesignForgeAdapter(runner=runner)
    result = adapter.invoke("execute", {"request": {"request_id": "req-1", "tool_id": "forge.rc-column"}})
    argv = runner.calls[0][0]
    assert argv[:2] == ["civilforge-tool", "execute"]
    assert argv[2].endswith("request.json")
    assert result["status"] == "succeeded"


def test_design_forge_rejects_arbitrary_operation():
    with pytest.raises(ValueError):
        DesignForgeAdapter(runner=FakeRunner([])).invoke("shell", {})


def test_engsketch_only_exposes_vetted_operations():
    runner = FakeRunner([CommandResult(0, "v001\n", "")])
    adapter = EngSketchAdapter(runner=runner)
    result = adapter.invoke("versions", {"project": "bridge-A"})
    assert runner.calls[0][0] == ["draftforge-cli", "versions", "--project", "bridge-A"]
    assert "v001" in result["stdout"]
    with pytest.raises(ValueError):
        adapter.invoke("patch_apply", {"project": "bridge-A"})


def test_knowgraph_requires_dsn_and_uses_json_node_list():
    assert KnowGraphAdapter(dsn="").health()["status"] == "unavailable"
    runner = FakeRunner([CommandResult(0, '[{"id":"n1"}]', "")])
    adapter = KnowGraphAdapter(dsn="graph.db", runner=runner)
    result = adapter.invoke("node_list", {"namespace": "engineering"})
    assert runner.calls[0][0] == [
        "knowgraph", "node", "list", "--ns", "engineering", "--dsn", "graph.db", "--json"
    ]
    assert result["items"][0]["id"] == "n1"


def test_bim_forge_health_and_invoke_use_canonical_api(monkeypatch):
    module = types.SimpleNamespace(
        build_ifc_model=lambda **kwargs: {"model": kwargs},
        build_and_write_ifc=lambda **kwargs: {"path": kwargs.get("path")},
        reopen_and_audit=lambda **kwargs: {"audit": True},
        get_element_quantities=lambda **kwargs: {"quantity": 1},
    )
    monkeypatch.setattr("coworker.engineering.specialists.importlib.import_module", lambda name: module)
    adapter = BIMForgeAdapter()
    assert adapter.health()["status"] == "ready"
    result = adapter.invoke("get_element_quantities", {"kwargs": {"element_id": "C1"}})
    assert result["result"] == {"quantity": 1}


def test_registry_accepts_four_specialist_contracts(monkeypatch):
    module = types.SimpleNamespace(
        build_ifc_model=lambda **kwargs: None,
        build_and_write_ifc=lambda **kwargs: None,
        reopen_and_audit=lambda **kwargs: None,
        get_element_quantities=lambda **kwargs: None,
    )
    monkeypatch.setattr("coworker.engineering.specialists.importlib.import_module", lambda name: module)
    registry = EngineeringAdapterRegistry()
    registry.register(DesignForgeAdapter(runner=FakeRunner([CommandResult(0, '[]', '')])))
    registry.register(EngSketchAdapter(runner=FakeRunner([CommandResult(0, 'themes', '')])))
    registry.register(KnowGraphAdapter(dsn="graph.db", runner=FakeRunner([CommandResult(0, '', '')])))
    registry.register(BIMForgeAdapter())
    assert registry.names() == ["ai-bim-forge", "ai-civildesign-forge", "ai-engsketch", "knowgraphgo"]
    assert len(registry.for_capability(EngineeringCapability.BIM_IFC)) == 1
