import json

import pytest

from coworker.engineering import (
    EngineeringCapability,
    EngineeringOSClient,
    EngineeringOSConfig,
    EngineeringOSContractError,
    EngineeringOSHTTPError,
    HealthStatus,
    TransportResponse,
)


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, *, body, headers, timeout):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "body": body,
                "headers": dict(headers),
                "timeout": timeout,
            }
        )
        if not self.responses:
            raise AssertionError("unexpected transport call")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def response(status, payload):
    return TransportResponse(status=status, body=json.dumps(payload).encode("utf-8"))


def client(*responses):
    transport = FakeTransport(responses)
    return (
        EngineeringOSClient(
            EngineeringOSConfig("http://127.0.0.1:8080/", timeout_seconds=3.5),
            transport=transport,
        ),
        transport,
    )


def test_config_normalizes_base_url_and_rejects_invalid_values():
    config = EngineeringOSConfig("http://127.0.0.1:8080///", timeout_seconds=1)
    assert config.base_url == "http://127.0.0.1:8080"

    with pytest.raises(ValueError, match="http"):
        EngineeringOSConfig("127.0.0.1:8080")
    with pytest.raises(ValueError, match="greater than zero"):
        EngineeringOSConfig(timeout_seconds=0)


def test_health_and_readiness_use_authoritative_endpoints():
    bridge, transport = client(
        response(200, {"status": "ok", "started_at": "2026-08-08T00:00:00Z"}),
        response(200, {"status": "ready"}),
    )

    health = bridge.health()
    readiness = bridge.readiness()

    assert health.status is HealthStatus.READY
    assert readiness.status is HealthStatus.READY
    assert [call["url"] for call in transport.calls] == [
        "http://127.0.0.1:8080/healthz",
        "http://127.0.0.1:8080/readyz",
    ]
    assert all(call["timeout"] == 3.5 for call in transport.calls)


def test_readiness_503_is_reported_as_unavailable_not_raised():
    bridge, _ = client(response(503, {"status": "not_ready"}))

    report = bridge.readiness()

    assert report.status is HealthStatus.UNAVAILABLE


def test_unexpected_health_payload_is_degraded():
    bridge, _ = client(response(200, {"status": "mystery"}))

    report = bridge.health()

    assert report.status is HealthStatus.DEGRADED
    assert "mystery" in report.message


def test_system_modules_exposes_schema_version_and_engine_capabilities():
    bridge, _ = client(
        response(
            200,
            {
                "schema_version": "1.0.0",
                "modules": [
                    {"id": "design-engine", "required": True},
                    {"id": "drawing-engine", "required": True},
                    {"id": "bim-engine", "required": True},
                    {"id": "quantity-engine", "required": False},
                    {"id": "budget-engine", "required": False},
                    {"id": "schedule-engine", "required": False},
                    {"id": "knowledge-engine", "required": True},
                    {"id": "visual-workbench", "required": True},
                ],
            },
        ),
        response(
            200,
            {
                "schema_version": "1.0.0",
                "modules": [
                    {"id": "design-engine"},
                    {"id": "drawing-engine"},
                    {"id": "bim-engine"},
                    {"id": "quantity-engine"},
                    {"id": "budget-engine"},
                    {"id": "schedule-engine"},
                    {"id": "knowledge-engine"},
                    {"id": "visual-workbench"},
                ],
            },
        ),
    )

    assert bridge.schema_version() == "1.0.0"
    assert bridge.capabilities() == {
        EngineeringCapability.STRUCTURAL,
        EngineeringCapability.REPORTING,
        EngineeringCapability.DRAWING,
        EngineeringCapability.BIM_IFC,
        EngineeringCapability.QUANTITY,
        EngineeringCapability.COST,
        EngineeringCapability.SCHEDULING,
        EngineeringCapability.KNOWLEDGE_GRAPH,
        EngineeringCapability.VISUALIZATION,
    }


def test_unknown_modules_do_not_invent_capabilities():
    bridge, _ = client(
        response(200, {"schema_version": "1.0.0", "modules": [{"id": "future-engine"}]})
    )

    assert bridge.capabilities() == set()


def test_modules_contract_requires_module_list_and_objects():
    bridge, _ = client(response(200, {"schema_version": "1.0.0"}))
    with pytest.raises(EngineeringOSContractError, match="modules list"):
        bridge.system_modules()

    bridge, _ = client(response(200, {"modules": ["bad"]}))
    with pytest.raises(EngineeringOSContractError, match="non-object"):
        bridge.capabilities()


def test_project_and_job_queries_follow_existing_os_routes():
    bridge, transport = client(
        response(200, {"items": [{"id": "project-1", "code": "P001"}]}),
        response(200, {"id": "project-1", "code": "P001", "name": "Bridge"}),
        response(200, {"items": [{"id": "job-1", "project_id": "project-1"}]}),
        response(200, {"items": [{"id": "job-1", "project_id": "project-1"}]}),
        response(200, {"id": "job-1", "project_id": "project-1"}),
    )

    assert bridge.list_projects()[0]["id"] == "project-1"
    assert bridge.get_project("project-1")["name"] == "Bridge"
    assert bridge.list_jobs()[0]["id"] == "job-1"
    assert bridge.list_jobs(project_id="project-1")[0]["id"] == "job-1"
    assert bridge.get_job("job-1")["id"] == "job-1"

    assert [call["url"] for call in transport.calls] == [
        "http://127.0.0.1:8080/api/v1/projects",
        "http://127.0.0.1:8080/api/v1/projects/project-1",
        "http://127.0.0.1:8080/api/v1/jobs",
        "http://127.0.0.1:8080/api/v1/projects/project-1/jobs",
        "http://127.0.0.1:8080/api/v1/jobs/job-1",
    ]


def test_create_job_matches_ai_engineering_os_create_input_contract():
    bridge, transport = client(
        response(
            201,
            {
                "id": "job-1",
                "project_id": "project-1",
                "code": "J001",
                "name": "RC Column Design",
                "user_request": "Design an RC column",
                "status": "draft",
                "priority": "high",
                "revision": 1,
            },
        )
    )

    job = bridge.create_job(
        project_id="project-1",
        code="J001",
        name="RC Column Design",
        user_request="Design an RC column",
        expected_deliverables=["calculation", "drawing", "ifc"],
        priority="high",
        metadata={"source": "openworker"},
    )

    assert job["status"] == "draft"
    call = transport.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/api/v1/jobs")
    assert call["headers"]["Content-Type"] == "application/json"
    assert json.loads(call["body"]) == {
        "project_id": "project-1",
        "code": "J001",
        "name": "RC Column Design",
        "user_request": "Design an RC column",
        "expected_deliverables": ["calculation", "drawing", "ifc"],
        "priority": "high",
        "metadata": {"source": "openworker"},
    }


def test_remote_domain_error_preserves_status_code_and_message():
    bridge, _ = client(
        response(409, {"error": "code_conflict", "message": "工作單代碼已存在"})
    )

    with pytest.raises(EngineeringOSHTTPError) as captured:
        bridge.create_job(
            project_id="project-1",
            code="J001",
            name="Duplicate",
            user_request="Duplicate job",
        )

    assert captured.value.status == 409
    assert captured.value.code == "code_conflict"
    assert captured.value.remote_message == "工作單代碼已存在"


def test_invalid_json_and_invalid_collection_shapes_fail_closed():
    bridge, _ = client(TransportResponse(status=200, body=b"not-json"))
    with pytest.raises(EngineeringOSContractError, match="invalid JSON"):
        bridge.list_projects()

    bridge, _ = client(response(200, {"items": {"id": "project-1"}}))
    with pytest.raises(EngineeringOSContractError, match="items list"):
        bridge.list_projects()

    bridge, _ = client(response(200, {"items": ["bad"]}))
    with pytest.raises(EngineeringOSContractError, match="non-object"):
        bridge.list_jobs()


def test_ids_reject_path_injection_and_required_create_fields_are_trimmed():
    bridge, _ = client()

    with pytest.raises(ValueError, match="path characters"):
        bridge.get_project("../../healthz")
    with pytest.raises(ValueError, match="must not be empty"):
        bridge.create_job(project_id=" ", code="J1", name="x", user_request="x")
