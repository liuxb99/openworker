"""Typed bridge from OpenWorker to the AI-Engineering-OS control plane.

The bridge deliberately owns only transport and API-contract concerns. Project/Job
business rules remain authoritative in AI-Engineering-OS.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import socket
from typing import Any, Mapping, Protocol
from urllib import error as urlerror
from urllib import request as urlrequest

from .contracts import EngineeringCapability, HealthReport, HealthStatus


class EngineeringOSError(RuntimeError):
    """Base error raised by the AI-Engineering-OS bridge."""


class EngineeringOSTransportError(EngineeringOSError):
    pass


class EngineeringOSTimeoutError(EngineeringOSTransportError):
    pass


class EngineeringOSHTTPError(EngineeringOSError):
    def __init__(self, status: int, code: str | None = None, message: str | None = None):
        self.status = status
        self.code = code
        self.remote_message = message
        detail = f"AI-Engineering-OS HTTP {status}"
        if code:
            detail += f" ({code})"
        if message:
            detail += f": {message}"
        super().__init__(detail)


class EngineeringOSContractError(EngineeringOSError):
    pass


@dataclass(frozen=True)
class TransportResponse:
    status: int
    body: bytes


class EngineeringOSTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        body: bytes | None,
        headers: Mapping[str, str],
        timeout: float,
    ) -> TransportResponse: ...


class UrllibEngineeringOSTransport:
    """Small stdlib transport so the bridge adds no third-party HTTP dependency."""

    def request(
        self,
        method: str,
        url: str,
        *,
        body: bytes | None,
        headers: Mapping[str, str],
        timeout: float,
    ) -> TransportResponse:
        req = urlrequest.Request(url, data=body, headers=dict(headers), method=method)
        try:
            with urlrequest.urlopen(req, timeout=timeout) as response:
                return TransportResponse(status=response.status, body=response.read())
        except urlerror.HTTPError as exc:
            return TransportResponse(status=exc.code, body=exc.read())
        except (TimeoutError, socket.timeout) as exc:
            raise EngineeringOSTimeoutError(f"AI-Engineering-OS request timed out: {url}") from exc
        except urlerror.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise EngineeringOSTimeoutError(
                    f"AI-Engineering-OS request timed out: {url}"
                ) from exc
            raise EngineeringOSTransportError(
                f"AI-Engineering-OS transport failed: {url}: {exc.reason}"
            ) from exc
        except OSError as exc:
            raise EngineeringOSTransportError(
                f"AI-Engineering-OS transport failed: {url}: {exc}"
            ) from exc


@dataclass(frozen=True)
class EngineeringOSConfig:
    base_url: str = "http://127.0.0.1:8080"
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        base_url = self.base_url.strip().rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("AI-Engineering-OS base_url must use http:// or https://")
        if self.timeout_seconds <= 0:
            raise ValueError("AI-Engineering-OS timeout_seconds must be greater than zero")
        object.__setattr__(self, "base_url", base_url)


_MODULE_CAPABILITIES: dict[str, set[EngineeringCapability]] = {
    "design-engine": {EngineeringCapability.STRUCTURAL, EngineeringCapability.REPORTING},
    "drawing-engine": {EngineeringCapability.DRAWING, EngineeringCapability.REPORTING},
    "bim-engine": {EngineeringCapability.BIM_IFC},
    "quantity-engine": {EngineeringCapability.QUANTITY},
    "budget-engine": {EngineeringCapability.COST},
    "schedule-engine": {EngineeringCapability.SCHEDULING},
    "knowledge-engine": {EngineeringCapability.KNOWLEDGE_GRAPH},
    "visual-workbench": {EngineeringCapability.VISUALIZATION},
    "media-engine": {EngineeringCapability.VISUALIZATION},
}


class EngineeringOSClient:
    """Client for the stable control-plane subset consumed by OpenWorker."""

    def __init__(
        self,
        config: EngineeringOSConfig | None = None,
        *,
        transport: EngineeringOSTransport | None = None,
    ) -> None:
        self.config = config or EngineeringOSConfig()
        self.transport = transport or UrllibEngineeringOSTransport()

    def health(self) -> HealthReport:
        try:
            payload = self._request_json("GET", "/healthz")
        except EngineeringOSError as exc:
            return HealthReport(status=HealthStatus.UNAVAILABLE, message=str(exc))
        status = payload.get("status")
        if status != "ok":
            return HealthReport(
                status=HealthStatus.DEGRADED,
                message=f"unexpected health status: {status!r}",
                details=payload,
            )
        return HealthReport(status=HealthStatus.READY, details=payload)

    def readiness(self) -> HealthReport:
        try:
            payload = self._request_json("GET", "/readyz")
        except EngineeringOSHTTPError as exc:
            if exc.status == 503:
                return HealthReport(status=HealthStatus.UNAVAILABLE, message=str(exc))
            raise
        except EngineeringOSError as exc:
            return HealthReport(status=HealthStatus.UNAVAILABLE, message=str(exc))
        status = payload.get("status")
        if status == "ready":
            return HealthReport(status=HealthStatus.READY, details=payload)
        if status == "not_ready":
            return HealthReport(status=HealthStatus.UNAVAILABLE, details=payload)
        return HealthReport(
            status=HealthStatus.DEGRADED,
            message=f"unexpected readiness status: {status!r}",
            details=payload,
        )

    def system_modules(self) -> dict[str, Any]:
        payload = self._request_json("GET", "/api/v1/system/modules")
        modules = payload.get("modules")
        if not isinstance(modules, list):
            raise EngineeringOSContractError("system/modules response must contain a modules list")
        return payload

    def schema_version(self) -> str | None:
        payload = self.system_modules()
        value = payload.get("schema_version")
        return value if isinstance(value, str) and value.strip() else None

    def capabilities(self) -> set[EngineeringCapability]:
        payload = self.system_modules()
        capabilities: set[EngineeringCapability] = set()
        for module in payload["modules"]:
            if not isinstance(module, dict):
                raise EngineeringOSContractError("system/modules contains a non-object module")
            module_id = module.get("id")
            if isinstance(module_id, str):
                capabilities.update(_MODULE_CAPABILITIES.get(module_id, set()))
        return capabilities

    def list_projects(self) -> list[dict[str, Any]]:
        return self._items("/api/v1/projects", item_name="project")

    def get_project(self, project_id: str) -> dict[str, Any]:
        project_id = self._required_id(project_id, "project_id")
        return self._object("GET", f"/api/v1/projects/{project_id}")

    def list_jobs(self, *, project_id: str | None = None) -> list[dict[str, Any]]:
        if project_id is None:
            return self._items("/api/v1/jobs", item_name="job")
        project_id = self._required_id(project_id, "project_id")
        return self._items(f"/api/v1/projects/{project_id}/jobs", item_name="job")

    def get_job(self, job_id: str) -> dict[str, Any]:
        job_id = self._required_id(job_id, "job_id")
        return self._object("GET", f"/api/v1/jobs/{job_id}")

    def create_job(
        self,
        *,
        project_id: str,
        code: str,
        name: str,
        user_request: str,
        expected_deliverables: list[str] | None = None,
        priority: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "project_id": self._required_text(project_id, "project_id"),
            "code": self._required_text(code, "code"),
            "name": self._required_text(name, "name"),
            "user_request": self._required_text(user_request, "user_request"),
        }
        if expected_deliverables is not None:
            payload["expected_deliverables"] = list(expected_deliverables)
        if priority is not None:
            payload["priority"] = self._required_text(priority, "priority")
        if metadata is not None:
            payload["metadata"] = dict(metadata)
        return self._object("POST", "/api/v1/jobs", payload)

    def _items(self, path: str, *, item_name: str) -> list[dict[str, Any]]:
        payload = self._request_json("GET", path)
        items = payload.get("items")
        if not isinstance(items, list):
            raise EngineeringOSContractError(f"{path} response must contain an items list")
        for item in items:
            if not isinstance(item, dict):
                raise EngineeringOSContractError(f"{item_name} list contains a non-object item")
        return items

    def _object(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = self._request_json(method, path, payload)
        if not isinstance(result, dict):
            raise EngineeringOSContractError(f"{path} response must be a JSON object")
        return result

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        response = self.transport.request(
            method,
            f"{self.config.base_url}{path}",
            body=body,
            headers=headers,
            timeout=self.config.timeout_seconds,
        )
        decoded = self._decode_json(response.body, path)
        if not 200 <= response.status < 300:
            code = decoded.get("error") if isinstance(decoded, dict) else None
            message = decoded.get("message") if isinstance(decoded, dict) else None
            raise EngineeringOSHTTPError(response.status, code=code, message=message)
        if not isinstance(decoded, dict):
            raise EngineeringOSContractError(f"{path} response must be a JSON object")
        return decoded

    @staticmethod
    def _decode_json(body: bytes, path: str) -> Any:
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EngineeringOSContractError(f"{path} returned invalid JSON") from exc

    @staticmethod
    def _required_text(value: str, field: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{field} must not be empty")
        return value

    @classmethod
    def _required_id(cls, value: str, field: str) -> str:
        value = cls._required_text(value, field)
        if "/" in value or "?" in value or "#" in value:
            raise ValueError(f"{field} contains invalid path characters")
        return value
