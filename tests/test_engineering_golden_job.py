import pytest

from coworker.engineering.contracts import HealthReport, HealthStatus
from coworker.engineering.golden_job import RCColumnGoldenJob

COLUMN = {
    "semantic_id": "column-C1", "width_mm": 600, "depth_mm": 600,
    "clear_height_mm": 3500, "concrete_grade": "C35", "steel_grade": "HRB400",
    "axial_force_kn": 1800, "moment_x_knm": 220,
}


class FakeOS:
    def __init__(self, ready=True):
        self.ready = ready
        self.created = []
        self.transitions = []
        self.artifacts = []
        self.revision = 1

    def readiness(self):
        return HealthReport(status=HealthStatus.READY if self.ready else HealthStatus.UNAVAILABLE)

    def create_job(self, **kwargs):
        self.created.append(kwargs)
        self.revision = 1
        return {"id": "job_001", "project_id": kwargs["project_id"], "code": kwargs["code"], "status": "draft", "revision": 1}

    def transition_job(self, *, job_id, target, expected_revision):
        assert expected_revision == self.revision
        self.transitions.append((job_id, target, expected_revision))
        self.revision += 1
        return {"id": job_id, "project_id": "prj_001", "code": "RC-COLUMN-column-C1", "status": target, "revision": self.revision}

    def register_artifact(self, **kwargs):
        self.artifacts.append(kwargs)
        return {
            "id": f"art_{len(self.artifacts)}", "project_id": kwargs["project_id"],
            "job_id": kwargs["job_id"], "component_id": kwargs["component_id"],
            "kind": kwargs["kind"], "revision": 1, "uri": kwargs["uri"],
            "media_type": kwargs["media_type"], "checksum": kwargs["checksum"],
            "source_run_id": kwargs.get("source_run_id"),
        }


class FakeForge:
    def __init__(self, ready=True, response=None):
        self.ready = ready
        self.calls = []
        self.response = response or {
            "request_id": "golden-rc-column:prj_001:column-C1",
            "tool_id": "forge.rc-column", "protocol_version": "tool-protocol/1.0.0",
            "tool_version": "1.0.0", "status": "succeeded",
            "data": {"semantic_id": "column-C1", "design_ok": True, "calculation": {}},
            "artifacts": [{
                "artifact_id": "calculation:rc-column:column-C1",
                "artifact_type": "calculation_trace",
                "path": "artifacts/rc-column/column-C1.json", "sha256": "a" * 64,
                "media_type": "application/json", "schema_version": "artifact/1.0.0",
                "semantic_id": "column-C1", "calculation_run_id": "run_001",
            }],
        }

    def health(self): return {"status": "ready" if self.ready else "unavailable"}
    def invoke(self, operation, payload):
        self.calls.append((operation, payload))
        return self.response


def test_golden_job_closes_authoritative_lifecycle_to_review_and_registers_artifact():
    os_client, forge = FakeOS(), FakeForge()
    result = RCColumnGoldenJob(os_client, forge).run(project_id="prj_001", column=COLUMN)
    assert [target for _, target, _ in os_client.transitions] == ["queued", "running", "review"]
    assert os_client.artifacts[0] == {
        "project_id": "prj_001", "job_id": "job_001", "component_id": "column-C1",
        "kind": "calculation_trace", "uri": "artifacts/rc-column/column-C1.json",
        "media_type": "application/json", "checksum": "a" * 64, "source_run_id": "run_001",
    }
    assert result.job["status"] == "review"
    assert len(result.registered_artifacts) == 1
    relations = {item["relation"] for item in result.digital_thread["links"]}
    assert relations == {"belongs_to_job", "derived_from"}
    assert len(result.digital_thread["evidence"]) == 3


def test_dependency_failure_happens_before_job_side_effect():
    os_client = FakeOS(ready=False)
    with pytest.raises(RuntimeError, match="not ready"):
        RCColumnGoldenJob(os_client, FakeForge()).run(project_id="prj_001", column=COLUMN)
    assert os_client.created == []


def test_design_failure_after_running_is_compensated_to_cancelled():
    os_client = FakeOS()
    forge = FakeForge(response={"status": "failed", "data": {}, "artifacts": []})
    with pytest.raises(RuntimeError, match="did not succeed"):
        RCColumnGoldenJob(os_client, forge).run(project_id="prj_001", column=COLUMN)
    assert [target for _, target, _ in os_client.transitions] == ["queued", "running", "cancelled"]


def test_identity_and_required_input_fail_closed_before_job_creation():
    os_client = FakeOS()
    broken = dict(COLUMN); broken.pop("steel_grade")
    with pytest.raises(ValueError, match="steel_grade"):
        RCColumnGoldenJob(os_client, FakeForge()).run(project_id="prj_001", column=broken)
    with pytest.raises(ValueError, match="conflicts"):
        RCColumnGoldenJob(os_client, FakeForge()).run(project_id="prj_001", column=dict(COLUMN, project_id="other"))
    assert os_client.created == []


def test_invalid_source_artifact_cancels_job_and_is_not_registered():
    os_client = FakeOS()
    forge = FakeForge(response={
        "status": "succeeded", "data": {"semantic_id": "column-C1"},
        "artifacts": [{"artifact_id": "x", "artifact_type": "calculation_trace"}],
    })
    with pytest.raises(ValueError):
        RCColumnGoldenJob(os_client, forge).run(project_id="prj_001", column=COLUMN)
    assert os_client.artifacts == []
    assert os_client.transitions[-1][1] == "cancelled"
