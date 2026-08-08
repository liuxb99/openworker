import pytest

from coworker.engineering.contracts import HealthReport, HealthStatus
from coworker.engineering.golden_job import RCColumnGoldenJob


COLUMN = {
    "semantic_id": "column-C1",
    "width_mm": 600,
    "depth_mm": 600,
    "clear_height_mm": 3500,
    "concrete_grade": "C35",
    "steel_grade": "HRB400",
    "axial_force_kn": 1800,
    "moment_x_knm": 220,
}


class FakeOS:
    def __init__(self, ready=True):
        self.ready = ready
        self.created = []

    def readiness(self):
        return HealthReport(status=HealthStatus.READY if self.ready else HealthStatus.UNAVAILABLE)

    def create_job(self, **kwargs):
        self.created.append(kwargs)
        return {"id": "job_001", "project_id": kwargs["project_id"], "code": kwargs["code"], "status": "draft", "revision": 1}


class FakeForge:
    def __init__(self, ready=True, response=None):
        self.ready = ready
        self.calls = []
        self.response = response or {
            "request_id": "golden-rc-column:prj_001:column-C1",
            "tool_id": "forge.rc-column",
            "protocol_version": "tool-protocol/1.0.0",
            "tool_version": "1.0.0",
            "status": "succeeded",
            "data": {"semantic_id": "column-C1", "design_ok": True, "calculation": {}},
            "artifacts": [{
                "artifact_id": "calculation:rc-column:column-C1",
                "artifact_type": "calculation_trace",
                "path": "artifacts/rc-column/column-C1.json",
                "sha256": "a" * 64,
                "media_type": "application/json",
                "schema_version": "artifact/1.0.0",
                "semantic_id": "column-C1",
            }],
        }

    def health(self):
        return {"status": "ready" if self.ready else "unavailable"}

    def invoke(self, operation, payload):
        self.calls.append((operation, payload))
        return self.response


def test_golden_job_creates_control_plane_job_then_executes_authoritative_tool():
    os_client, forge = FakeOS(), FakeForge()
    result = RCColumnGoldenJob(os_client, forge).run(project_id="prj_001", column=COLUMN)
    assert os_client.created[0]["metadata"]["golden_job"] == "rc-column/v1"
    operation, payload = forge.calls[0]
    assert operation == "execute"
    assert payload["request"]["tool_id"] == "forge.rc-column"
    assert payload["request"]["arguments"]["input"]["project_id"] == "prj_001"
    assert result.design_result["data"]["design_ok"] is True
    assert len(result.digital_thread["evidence"]) == 2
    assert result.digital_thread["links"][0]["relation"] == "belongs_to_job"


def test_golden_job_fail_closed_before_side_effect_when_dependency_not_ready():
    os_client = FakeOS(ready=False)
    forge = FakeForge()
    with pytest.raises(RuntimeError, match="not ready"):
        RCColumnGoldenJob(os_client, forge).run(project_id="prj_001", column=COLUMN)
    assert os_client.created == []
    assert forge.calls == []


def test_golden_job_rejects_incomplete_or_conflicting_identity_before_job_creation():
    os_client, forge = FakeOS(), FakeForge()
    broken = dict(COLUMN)
    broken.pop("steel_grade")
    with pytest.raises(ValueError, match="steel_grade"):
        RCColumnGoldenJob(os_client, forge).run(project_id="prj_001", column=broken)
    conflict = dict(COLUMN, project_id="other")
    with pytest.raises(ValueError, match="conflicts"):
        RCColumnGoldenJob(os_client, forge).run(project_id="prj_001", column=conflict)
    assert os_client.created == []


def test_golden_job_rejects_failed_or_identity_inconsistent_forge_result():
    failed = FakeForge(response={"status": "failed", "data": {}, "artifacts": []})
    with pytest.raises(RuntimeError, match="did not succeed"):
        RCColumnGoldenJob(FakeOS(), failed).run(project_id="prj_001", column=COLUMN)
    mismatch = FakeForge(response={"status": "succeeded", "data": {"semantic_id": "C2"}, "artifacts": []})
    with pytest.raises(RuntimeError, match="inconsistent semantic identity"):
        RCColumnGoldenJob(FakeOS(), mismatch).run(project_id="prj_001", column=COLUMN)


def test_golden_job_requires_authoritative_hashed_artifact():
    forge = FakeForge(response={"status": "succeeded", "data": {"semantic_id": "column-C1"}, "artifacts": [{"artifact_id": "x"}]})
    with pytest.raises(ValueError):
        RCColumnGoldenJob(FakeOS(), forge).run(project_id="prj_001", column=COLUMN)
