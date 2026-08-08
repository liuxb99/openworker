import json
import pytest

from coworker.engineering import EngineeringOSClient, EngineeringOSConfig, TransportResponse


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, *, body, headers, timeout):
        self.calls.append({"method": method, "url": url, "body": body})
        if not self.responses:
            raise AssertionError("unexpected transport call")
        return self.responses.pop(0)


def resp(status, payload):
    return TransportResponse(status=status, body=json.dumps(payload).encode())


def make_client(*responses):
    transport = FakeTransport(responses)
    return EngineeringOSClient(EngineeringOSConfig("http://127.0.0.1:8080"), transport=transport), transport


def test_transition_job_matches_authoritative_route_and_revision_contract():
    client, transport = make_client(resp(200, {"id": "job_1", "status": "queued", "revision": 2}))
    result = client.transition_job(job_id="job_1", target="queued", expected_revision=1)
    assert result["revision"] == 2
    call = transport.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/api/v1/jobs/job_1/transitions")
    assert json.loads(call["body"]) == {"target": "queued", "expected_revision": 1}


def test_register_artifact_matches_authoritative_project_route_and_payload():
    client, transport = make_client(resp(201, {
        "id": "art_1", "project_id": "prj_1", "job_id": "job_1", "component_id": "column-C1",
        "kind": "calculation_trace", "revision": 1, "uri": "artifacts/c1.json",
        "media_type": "application/json", "checksum": "abc", "source_run_id": "run_1",
    }))
    result = client.register_artifact(
        project_id="prj_1", job_id="job_1", component_id="column-C1",
        kind="calculation_trace", uri="artifacts/c1.json", media_type="application/json",
        checksum="abc", source_run_id="run_1",
    )
    assert result["id"] == "art_1"
    call = transport.calls[0]
    assert call["url"].endswith("/api/v1/projects/prj_1/artifacts")
    assert json.loads(call["body"]) == {
        "job_id": "job_1", "component_id": "column-C1", "kind": "calculation_trace",
        "uri": "artifacts/c1.json", "media_type": "application/json", "checksum": "abc",
        "source_run_id": "run_1",
    }


def test_job_artifact_queries_follow_existing_routes():
    client, transport = make_client(
        resp(200, {"items": [{"id": "art_1"}]}),
        resp(200, {"id": "art_1"}),
    )
    assert client.list_job_artifacts("job_1")[0]["id"] == "art_1"
    assert client.get_artifact("art_1")["id"] == "art_1"
    assert [call["url"] for call in transport.calls] == [
        "http://127.0.0.1:8080/api/v1/jobs/job_1/artifacts",
        "http://127.0.0.1:8080/api/v1/artifacts/art_1",
    ]


def test_lifecycle_inputs_fail_closed_before_transport():
    client, transport = make_client()
    with pytest.raises(ValueError):
        client.transition_job(job_id="job_1", target="review", expected_revision=0)
    with pytest.raises(ValueError):
        client.register_artifact(project_id="../x", job_id="job_1", component_id="C1",
                                 kind="x", uri="x", media_type="x", checksum="x")
    with pytest.raises(ValueError):
        client.register_artifact(project_id="prj_1", job_id="job_1", component_id="C1",
                                 kind=" ", uri="x", media_type="x", checksum="x")
    assert transport.calls == []
