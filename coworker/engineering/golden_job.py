"""E6 Golden Job: one controlled RC-column engineering path.

This is an orchestration fixture, not a second workflow engine. AI-Engineering-OS owns
Project/Job lifecycle; specialist repositories own engineering computation and artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .digital_thread import DigitalThread, RelationKind, design_forge_artifact_ref, os_job_ref


class JobControlPlane(Protocol):
    def readiness(self) -> Any: ...
    def create_job(self, **kwargs: Any) -> dict[str, Any]: ...


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
    digital_thread: dict[str, Any]


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
        forge_health = self.design_forge.health()
        if forge_health.get("status") != "ready":
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
        job_ref = os_job_ref(job)

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
        thread.add(job_ref)
        for artifact_payload in artifacts:
            if not isinstance(artifact_payload, Mapping):
                raise RuntimeError("Design Forge artifact must be an object")
            artifact = thread.add(design_forge_artifact_ref(artifact_payload))
            thread.link(artifact, RelationKind.BELONGS_TO_JOB, job_ref)

        return GoldenJobResult(job=job, design_result=response, digital_thread=thread.to_dict())
