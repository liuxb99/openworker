import json

import pytest

from coworker.engineering import EngineeringOSClient, EngineeringOSConfig, EngineeringOSContractError, TransportResponse


class FakeTransport:
    def __init__(self, responses):
        self.responses=list(responses); self.calls=[]
    def request(self, method, url, *, body, headers, timeout):
        self.calls.append({"method":method,"url":url,"body":body,"headers":dict(headers)})
        return self.responses.pop(0)


def response(status, payload):
    return TransportResponse(status=status, body=json.dumps(payload).encode())


def client(*responses):
    t=FakeTransport(responses)
    return EngineeringOSClient(EngineeringOSConfig("http://127.0.0.1:8080"),transport=t),t


def test_review_and_approval_routes_match_authoritative_os_contract():
    api,t=client(
        response(201,{"id":"revw-1","job_id":"job-1","artifact_id":"art-1","artifact_revision":1,"reviewer":"eng","decision":"approved"}),
        response(200,{"job_id":"job-1","approved":True,"total":1,"approved_count":1,"pending_artifact_ids":[],"latest_reviews":{}}),
        response(200,{"items":[{"id":"revw-1","artifact_id":"art-1"}]}),
    )
    review=api.submit_artifact_review(job_id="job-1",artifact_id="art-1",reviewer="eng",decision="approved")
    status=api.approval_status("job-1")
    reviews=api.list_job_reviews("job-1")
    assert review["decision"]=="approved"
    assert status["approved"] is True
    assert reviews[0]["id"]=="revw-1"
    assert t.calls[0]["url"].endswith("/api/v1/artifacts/art-1/reviews")
    assert json.loads(t.calls[0]["body"])=={"job_id":"job-1","reviewer":"eng","decision":"approved","comment":""}


def test_review_validation_fails_closed_before_transport():
    api,t=client()
    with pytest.raises(ValueError,match="decision"):
        api.submit_artifact_review(job_id="job-1",artifact_id="art-1",reviewer="eng",decision="maybe")
    with pytest.raises(ValueError,match="comment"):
        api.submit_artifact_review(job_id="job-1",artifact_id="art-1",reviewer="eng",decision="rework")
    assert t.calls==[]


def test_approval_status_requires_boolean_contract():
    api,_=client(response(200,{"job_id":"job-1","approved":"yes"}))
    with pytest.raises(EngineeringOSContractError,match="approved boolean"):
        api.approval_status("job-1")


def test_publish_route_and_response_contract():
    api,t=client(response(201,{"delivery":{"id":"del-1","job_id":"job-1","status":"published"},"website":{"status":"ready"}}))
    result=api.publish_job(job_id="job-1",publisher="chief",note="release")
    assert result["delivery"]["id"]=="del-1"
    assert t.calls[0]["url"].endswith("/api/v1/jobs/job-1/publish")
    assert json.loads(t.calls[0]["body"])=={"publisher":"chief","note":"release"}


def test_publish_requires_delivery_and_website_objects():
    api,_=client(response(201,{"delivery":{"id":"del-1"}}))
    with pytest.raises(EngineeringOSContractError,match="delivery and website"):
        api.publish_job(job_id="job-1",publisher="chief")


def test_delivery_read_routes_are_stable():
    api,t=client(
        response(200,{"items":[{"id":"del-1","revision":1}]}),
        response(200,{"id":"del-1","revision":1}),
    )
    assert api.list_deliveries("job-1")[0]["id"]=="del-1"
    assert api.latest_delivery("job-1")["revision"]==1
    assert [c["url"] for c in t.calls]==[
        "http://127.0.0.1:8080/api/v1/jobs/job-1/deliveries",
        "http://127.0.0.1:8080/api/v1/jobs/job-1/deliveries/latest",
    ]
