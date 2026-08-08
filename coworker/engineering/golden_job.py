"""E6 Golden Job: controlled RC-column path with explicit review/publish closure."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .digital_thread import (
    DigitalThread, RelationKind, design_forge_artifact_ref, os_artifact_ref, os_job_ref,
)


class JobControlPlane(Protocol):
    def readiness(self) -> Any: ...
    def create_job(self, **kwargs: Any) -> dict[str, Any]: ...
    def transition_job(self, **kwargs: Any) -> dict[str, Any]: ...
    def register_artifact(self, **kwargs: Any) -> dict[str, Any]: ...
    def submit_artifact_review(self, **kwargs: Any) -> dict[str, Any]: ...
    def approval_status(self, job_id: str) -> dict[str, Any]: ...
    def publish_job(self, **kwargs: Any) -> dict[str, Any]: ...
    def get_job(self, job_id: str) -> dict[str, Any]: ...


class Specialist(Protocol):
    def health(self) -> dict[str, Any]: ...
    def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]: ...


_REQUIRED_COLUMN_FIELDS = (
    "semantic_id", "width_mm", "depth_mm", "clear_height_mm", "concrete_grade",
    "steel_grade", "axial_force_kn", "moment_x_knm",
)


@dataclass(frozen=True)
class GoldenJobResult:
    job: dict[str, Any]
    design_result: dict[str, Any]
    registered_artifacts: tuple[dict[str, Any], ...]
    digital_thread: dict[str, Any]


@dataclass(frozen=True)
class GoldenJobReviewResult:
    reviews: tuple[dict[str, Any], ...]
    approval_status: dict[str, Any]
    job: dict[str, Any]


@dataclass
class RCColumnGoldenJob:
    os_client: JobControlPlane
    design_forge: Specialist

    def run(self, *, project_id: str, column: Mapping[str, Any]) -> GoldenJobResult:
        project_id = str(project_id).strip()
        if not project_id:
            raise ValueError("project_id must not be empty")
        inputs = dict(column)
        missing = [name for name in _REQUIRED_COLUMN_FIELDS if inputs.get(name) in (None, "")]
        if missing:
            raise ValueError(f"RC column golden job missing fields: {', '.join(missing)}")
        if inputs.get("project_id") not in (None, project_id):
            raise ValueError("RC column project_id conflicts with golden job project_id")
        inputs["project_id"] = project_id

        ready = self.os_client.readiness()
        status = getattr(getattr(ready, "status", None), "value", getattr(ready, "status", None))
        if status != "ready":
            raise RuntimeError("AI-Engineering-OS is not ready")
        if self.design_forge.health().get("status") != "ready":
            raise RuntimeError("AI-CivilDesign-Forge is not ready")

        semantic_id = str(inputs["semantic_id"]).strip()
        request_id = f"golden-rc-column:{project_id}:{semantic_id}"
        job = self.os_client.create_job(
            project_id=project_id,
            code=f"RC-COLUMN-{semantic_id}",
            name=f"RC 柱設計 {semantic_id}",
            user_request=f"執行 RC 柱 {semantic_id} Golden Job 設計與追溯驗證",
            expected_deliverables=["calculation_trace"],
            metadata={"golden_job": "rc-column/v1", "semantic_id": semantic_id},
        )
        job_id = _required_result_text(job, "id", "created Job")
        revision = _required_revision(job, "created Job")
        job = self.os_client.transition_job(job_id=job_id, target="queued", expected_revision=revision)
        revision = _required_revision(job, "queued Job")
        job = self.os_client.transition_job(job_id=job_id, target="running", expected_revision=revision)
        revision = _required_revision(job, "running Job")

        try:
            response = self.design_forge.invoke(
                "execute",
                {"request": {
                    "request_id": request_id,
                    "tool_id": "forge.rc-column",
                    "version": "1.0.0",
                    "arguments": {"input": inputs},
                }},
            )
            if response.get("status") != "succeeded":
                raise RuntimeError("Design Forge RC-column execution did not succeed")
            data = response.get("data")
            if not isinstance(data, dict) or data.get("semantic_id") != semantic_id:
                raise RuntimeError("Design Forge returned inconsistent semantic identity")
            artifacts = response.get("artifacts")
            if not isinstance(artifacts, list) or not artifacts:
                raise RuntimeError("Design Forge returned no authoritative artifacts")

            thread = DigitalThread()
            registered: list[dict[str, Any]] = []
            source_refs = []
            for artifact_payload in artifacts:
                if not isinstance(artifact_payload, Mapping):
                    raise RuntimeError("Design Forge artifact must be an object")
                source_ref = design_forge_artifact_ref(artifact_payload)
                source_refs.append(source_ref)
                os_artifact = self.os_client.register_artifact(
                    project_id=project_id,
                    job_id=job_id,
                    component_id=semantic_id,
                    kind=_required_result_text(artifact_payload, "artifact_type", "Design Forge Artifact"),
                    uri=_required_result_text(artifact_payload, "path", "Design Forge Artifact"),
                    media_type=_required_result_text(artifact_payload, "media_type", "Design Forge Artifact"),
                    checksum=_required_result_text(artifact_payload, "sha256", "Design Forge Artifact"),
                    source_run_id=_optional_text(artifact_payload.get("calculation_run_id")),
                )
                registered.append(os_artifact)

            job = self.os_client.transition_job(job_id=job_id, target="review", expected_revision=revision)
            job_ref = thread.add(os_job_ref(job))
            for source_ref, registered_payload in zip(source_refs, registered, strict=True):
                source = thread.add(source_ref)
                registered_ref = thread.add(os_artifact_ref(registered_payload))
                thread.link(registered_ref, RelationKind.BELONGS_TO_JOB, job_ref)
                thread.link(registered_ref, RelationKind.DERIVED_FROM, source)

            return GoldenJobResult(
                job=job,
                design_result=response,
                registered_artifacts=tuple(registered),
                digital_thread=thread.to_dict(),
            )
        except Exception:
            try:
                self.os_client.transition_job(job_id=job_id, target="cancelled", expected_revision=revision)
            except Exception:
                pass
            raise

    def approve_for_delivery(self, result: GoldenJobResult, *, reviewer: str,
                             comment: str = "") -> GoldenJobReviewResult:
        """Explicitly approve every current Golden Job artifact; never called by run()."""
        job_id = _required_result_text(result.job, "id", "Golden Job")
        if result.job.get("status") != "review":
            raise RuntimeError("Golden Job must be in review status before approval")
        reviews: list[dict[str, Any]] = []
        for artifact in result.registered_artifacts:
            artifact_id = _required_result_text(artifact, "id", "registered Artifact")
            reviews.append(self.os_client.submit_artifact_review(
                job_id=job_id,
                artifact_id=artifact_id,
                reviewer=reviewer,
                decision="approved",
                comment=comment,
            ))
        status = self.os_client.approval_status(job_id)
        if status.get("approved") is not True:
            raise RuntimeError("AI-Engineering-OS did not approve all current artifact revisions")
        job = self.os_client.get_job(job_id)
        if job.get("status") != "completed":
            raise RuntimeError("approved Golden Job must transition to completed in AI-Engineering-OS")
        return GoldenJobReviewResult(tuple(reviews), status, job)

    def publish(self, review: GoldenJobReviewResult, *, publisher: str,
                note: str = "") -> dict[str, Any]:
        """Publish only after the authoritative approval gate reports approved."""
        job_id = _required_result_text(review.job, "id", "approved Golden Job")
        if review.approval_status.get("approved") is not True:
            raise RuntimeError("Golden Job is not approved for delivery")
        if review.job.get("status") != "completed":
            raise RuntimeError("Golden Job must be completed before delivery publish")
        return self.os_client.publish_job(job_id=job_id, publisher=publisher, note=note)


def _required_result_text(payload: Mapping[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{context} missing required field: {key}")
    return value.strip()


def _required_revision(payload: Mapping[str, Any], context: str) -> int:
    value = payload.get("revision")
    if not isinstance(value, int) or value < 1:
        raise RuntimeError(f"{context} missing valid revision")
    return value


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
