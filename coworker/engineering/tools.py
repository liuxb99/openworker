"""OpenWorker tool facade for the AI-Engineering-OS control plane.

These tools intentionally expose a small, stable task-oriented surface to the model.
Read operations are low-risk and do not require approval. Creating a Job mutates the
engineering control plane and therefore always uses OpenWorker's standard approval gate.
"""

from __future__ import annotations

import json
from typing import Any

import aisuite as ai

from .engineering_os import EngineeringOSClient


def _set_tool_contract(
    func: Any,
    *,
    schema: dict[str, Any],
    risk_level: str,
    capabilities: list[str],
    requires_approval: bool,
) -> Any:
    func.__coworker_schema__ = schema
    func.__aisuite_tool_metadata__ = ai.ToolMetadata(
        name=func.__name__,
        category="engineering",
        risk_level=risk_level,
        capabilities=capabilities,
        requires_approval=requires_approval,
        description=schema["function"]["description"],
    )
    return func


def _schema(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
                "additionalProperties": False,
            },
        },
    }


def engineering_os_tools(client: EngineeringOSClient | None = None) -> list[Any]:
    """Build the Engineering Coworker's control-plane tools.

    ``client`` is injectable so permanent tests can exercise the facade without network
    access. Production callers use the E2 client's localhost default configuration.
    """

    api = client or EngineeringOSClient()

    def engineering_system_readiness() -> dict[str, Any]:
        """Inspect AI-Engineering-OS health, readiness, schema version, and capabilities."""
        health = api.health()
        readiness = api.readiness()
        result: dict[str, Any] = {
            "health": health.to_dict(),
            "readiness": readiness.to_dict(),
            "ready": health.ready and readiness.ready,
        }
        if result["ready"]:
            result["schema_version"] = api.schema_version()
            result["capabilities"] = sorted(cap.value for cap in api.capabilities())
        else:
            result["schema_version"] = None
            result["capabilities"] = []
        return result

    _set_tool_contract(
        engineering_system_readiness,
        schema=_schema(
            "engineering_system_readiness",
            "Check whether AI-Engineering-OS is healthy and ready, and list its configured engineering capabilities. Use this before starting engineering work when availability is uncertain.",
            {},
        ),
        risk_level="low",
        capabilities=["read", "engineering"],
        requires_approval=False,
    )

    def engineering_list_projects() -> dict[str, Any]:
        """List engineering projects from the authoritative control plane."""
        items = api.list_projects()
        return {"items": items, "count": len(items)}

    _set_tool_contract(
        engineering_list_projects,
        schema=_schema(
            "engineering_list_projects",
            "List Projects registered in AI-Engineering-OS. Project data remains authoritative in AI-Engineering-OS.",
            {},
        ),
        risk_level="low",
        capabilities=["read", "engineering", "project"],
        requires_approval=False,
    )

    def engineering_get_project(project_id: str) -> dict[str, Any]:
        """Get one engineering project by stable Project ID."""
        return api.get_project(project_id)

    _set_tool_contract(
        engineering_get_project,
        schema=_schema(
            "engineering_get_project",
            "Get one AI-Engineering-OS Project by its stable project_id.",
            {"project_id": {"type": "string", "description": "Stable AI-Engineering-OS Project ID."}},
            ["project_id"],
        ),
        risk_level="low",
        capabilities=["read", "engineering", "project"],
        requires_approval=False,
    )

    def engineering_list_jobs(project_id: str = "") -> dict[str, Any]:
        """List all engineering Jobs, or only Jobs belonging to a Project."""
        items = api.list_jobs(project_id=project_id.strip() or None)
        return {"items": items, "count": len(items), "project_id": project_id.strip() or None}

    _set_tool_contract(
        engineering_list_jobs,
        schema=_schema(
            "engineering_list_jobs",
            "List AI-Engineering-OS Jobs. Optionally filter by project_id.",
            {"project_id": {"type": "string", "description": "Optional stable Project ID. Omit to list all Jobs."}},
        ),
        risk_level="low",
        capabilities=["read", "engineering", "job"],
        requires_approval=False,
    )

    def engineering_get_job(job_id: str) -> dict[str, Any]:
        """Get one engineering Job by stable Job ID."""
        return api.get_job(job_id)

    _set_tool_contract(
        engineering_get_job,
        schema=_schema(
            "engineering_get_job",
            "Get one AI-Engineering-OS Job by its stable job_id, including status, progress, revisions, and delivery paths when available.",
            {"job_id": {"type": "string", "description": "Stable AI-Engineering-OS Job ID."}},
            ["job_id"],
        ),
        risk_level="low",
        capabilities=["read", "engineering", "job"],
        requires_approval=False,
    )

    def engineering_create_job(
        project_id: str,
        code: str,
        name: str,
        user_request: str,
        expected_deliverables: list[str] | None = None,
        priority: str = "normal",
        metadata_json: str = "",
    ) -> dict[str, Any]:
        """Create a new engineering Job after the standard OpenWorker approval gate."""
        metadata: dict[str, Any] | None = None
        if metadata_json.strip():
            try:
                decoded = json.loads(metadata_json)
            except json.JSONDecodeError as exc:
                raise ValueError("metadata_json must be valid JSON") from exc
            if not isinstance(decoded, dict):
                raise ValueError("metadata_json must encode a JSON object")
            metadata = decoded
        return api.create_job(
            project_id=project_id,
            code=code,
            name=name,
            user_request=user_request,
            expected_deliverables=expected_deliverables,
            priority=priority,
            metadata=metadata,
        )

    _set_tool_contract(
        engineering_create_job,
        schema=_schema(
            "engineering_create_job",
            "Create a new AI-Engineering-OS Job. This changes authoritative engineering project state and must pass OpenWorker approval before execution.",
            {
                "project_id": {"type": "string", "description": "Stable target Project ID."},
                "code": {"type": "string", "description": "Unique human-readable Job code."},
                "name": {"type": "string", "description": "Job title."},
                "user_request": {"type": "string", "description": "The engineering work request in the user's own terms."},
                "expected_deliverables": {"type": "array", "items": {"type": "string"}, "description": "Optional expected deliverables."},
                "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"], "description": "AI-Engineering-OS Job priority."},
                "metadata_json": {"type": "string", "description": "Optional JSON object encoded as a string for trace/context metadata."},
            },
            ["project_id", "code", "name", "user_request"],
        ),
        risk_level="medium",
        capabilities=["write", "engineering", "job"],
        requires_approval=True,
    )

    return [
        engineering_system_readiness,
        engineering_list_projects,
        engineering_get_project,
        engineering_list_jobs,
        engineering_get_job,
        engineering_create_job,
    ]
