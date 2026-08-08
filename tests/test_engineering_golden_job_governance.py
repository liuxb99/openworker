import pytest

from coworker.engineering.golden_job import GoldenJobResult, RCColumnGoldenJob


class FakeOS:
    def __init__(self):
        self.reviews=[]; self.publishes=[]; self.job={"id":"job-1","status":"completed","revision":5}
    def submit_artifact_review(self, **kwargs):
        self.reviews.append(kwargs); return {"id":f"rev-{len(self.reviews)}",**kwargs,"artifact_revision":1}
    def approval_status(self, job_id):
        return {"job_id":job_id,"approved":True,"total":2,"approved_count":2,"pending_artifact_ids":[],"latest_reviews":{}}
    def get_job(self, job_id): return dict(self.job)
    def publish_job(self, **kwargs):
        self.publishes.append(kwargs); return {"delivery":{"id":"del-1","job_id":kwargs["job_id"],"status":"published"},"website":{"status":"ready"}}


class DummyForge: pass


def golden_result(status="review"):
    return GoldenJobResult(
        job={"id":"job-1","status":status,"revision":4},
        design_result={"status":"succeeded"},
        registered_artifacts=(
            {"id":"art-1","revision":1},
            {"id":"art-2","revision":1},
        ),
        digital_thread={"schema_version":"openworker-digital-thread/1.0.0","evidence":[],"links":[]},
    )


def test_approval_is_explicit_and_reviews_every_registered_artifact():
    api=FakeOS(); flow=RCColumnGoldenJob(api,DummyForge())
    reviewed=flow.approve_for_delivery(golden_result(),reviewer="engineer-a",comment="checked")
    assert [r["artifact_id"] for r in api.reviews]==["art-1","art-2"]
    assert all(r["decision"]=="approved" for r in api.reviews)
    assert reviewed.approval_status["approved"] is True
    assert reviewed.job["status"]=="completed"


def test_approval_does_not_run_outside_review_state():
    api=FakeOS(); flow=RCColumnGoldenJob(api,DummyForge())
    with pytest.raises(RuntimeError,match="review status"):
        flow.approve_for_delivery(golden_result(status="running"),reviewer="engineer-a")
    assert api.reviews==[]


def test_publish_requires_authoritative_approved_completed_review_result():
    api=FakeOS(); flow=RCColumnGoldenJob(api,DummyForge())
    reviewed=flow.approve_for_delivery(golden_result(),reviewer="engineer-a")
    published=flow.publish(reviewed,publisher="chief-engineer",note="issued")
    assert published["delivery"]["status"]=="published"
    assert api.publishes==[{"job_id":"job-1","publisher":"chief-engineer","note":"issued"}]


def test_approval_fails_if_os_does_not_report_completed():
    api=FakeOS(); api.job["status"]="review"; flow=RCColumnGoldenJob(api,DummyForge())
    with pytest.raises(RuntimeError,match="transition to completed"):
        flow.approve_for_delivery(golden_result(),reviewer="engineer-a")
