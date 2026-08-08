"""Direct adapters for authoritative engineering specialist repositories.

These adapters are deliberately thin. They expose capability, health and a small set of
explicit operations while leaving all domain rules in the specialist repositories.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Mapping, Protocol, Sequence

from .adapters import EngineeringCapability
from .contracts import AdapterDescriptor, ApprovalPolicy


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner(Protocol):
    def run(self, argv: Sequence[str], *, timeout: float) -> CommandResult: ...


class SubprocessCommandRunner:
    """Production command runner. Never invokes a shell."""

    def run(self, argv: Sequence[str], *, timeout: float) -> CommandResult:
        completed = subprocess.run(
            list(argv), capture_output=True, text=True, timeout=timeout, check=False, shell=False
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _json_object(text: str, context: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{context} returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{context} must return a JSON object")
    return value


def _json_value(text: str, context: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{context} returned invalid JSON") from exc


@dataclass
class DesignForgeAdapter:
    binary: str = "civilforge-tool"
    timeout_seconds: float = 30.0
    runner: CommandRunner | None = None

    name = "ai-civildesign-forge"
    capabilities = {EngineeringCapability.STRUCTURAL, EngineeringCapability.REPORTING}

    @property
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name=self.name,
            capabilities=frozenset(c.value for c in self.capabilities),
            transport="cli-json",
            version="tool-protocol/1.0.0",
            approval_policy=ApprovalPolicy.MUTATING,
            operations=("capabilities", "execute"),
            metadata={"repository": "liuxb99/AI-CivilDesign-Forge"},
        )

    def _runner(self) -> CommandRunner:
        return self.runner or SubprocessCommandRunner()

    def health(self) -> dict[str, Any]:
        if self.runner is None and shutil.which(self.binary) is None:
            return {"status": "unavailable", "message": f"binary not found: {self.binary}"}
        try:
            result = self._runner().run([self.binary, "capabilities"], timeout=self.timeout_seconds)
            if result.returncode != 0:
                return {"status": "unavailable", "message": result.stderr.strip() or "capabilities failed"}
            payload = _json_value(result.stdout, "civilforge-tool capabilities")
            if not isinstance(payload, (list, dict)):
                return {"status": "degraded", "message": "unexpected capability payload"}
            return {"status": "ready", "protocol_version": "tool-protocol/1.0.0"}
        except Exception as exc:
            return {"status": "unavailable", "message": str(exc)}

    def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation == "capabilities":
            result = self._runner().run([self.binary, "capabilities"], timeout=self.timeout_seconds)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "civilforge-tool capabilities failed")
            return {"capabilities": _json_value(result.stdout, "civilforge-tool capabilities")}
        if operation != "execute":
            raise ValueError(f"unsupported Design Forge operation: {operation}")
        request = payload.get("request")
        if not isinstance(request, dict):
            raise ValueError("execute requires payload.request object")
        with tempfile.TemporaryDirectory(prefix="openworker-forge-") as tmp:
            request_path = Path(tmp) / "request.json"
            request_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            result = self._runner().run([self.binary, "execute", str(request_path)], timeout=self.timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "civilforge-tool execute failed")
        return _json_object(result.stdout, "civilforge-tool execute")


@dataclass
class EngSketchAdapter:
    binary: str = "draftforge-cli"
    timeout_seconds: float = 30.0
    runner: CommandRunner | None = None

    name = "ai-engsketch"
    capabilities = {EngineeringCapability.DRAWING, EngineeringCapability.REPORTING}

    @property
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name=self.name,
            capabilities=frozenset(c.value for c in self.capabilities),
            transport="cli",
            approval_policy=ApprovalPolicy.MUTATING,
            operations=("themes", "validate", "versions"),
            metadata={"repository": "liuxb99/AI-EngSketch"},
        )

    def _runner(self) -> CommandRunner:
        return self.runner or SubprocessCommandRunner()

    def health(self) -> dict[str, Any]:
        if self.runner is None and shutil.which(self.binary) is None:
            return {"status": "unavailable", "message": f"binary not found: {self.binary}"}
        try:
            result = self._runner().run([self.binary, "themes"], timeout=self.timeout_seconds)
            return {"status": "ready" if result.returncode == 0 else "unavailable", "stderr": result.stderr.strip()}
        except Exception as exc:
            return {"status": "unavailable", "message": str(exc)}

    def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation == "themes":
            argv = [self.binary, "themes"]
        elif operation in {"validate", "versions"}:
            project = str(payload.get("project", "")).strip()
            if not project or any(ch in project for ch in "\r\n"):
                raise ValueError(f"{operation} requires a safe project name")
            argv = [self.binary, operation, "--project", project]
        else:
            raise ValueError(f"unsupported EngSketch operation: {operation}")
        result = self._runner().run(argv, timeout=self.timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"draftforge-cli {operation} failed")
        return {"operation": operation, "stdout": result.stdout}


@dataclass
class KnowGraphAdapter:
    dsn: str
    binary: str = "knowgraph"
    namespace: str = "default"
    timeout_seconds: float = 30.0
    runner: CommandRunner | None = None

    name = "knowgraphgo"
    capabilities = {EngineeringCapability.KNOWLEDGE_GRAPH}

    @property
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name=self.name,
            capabilities=frozenset(c.value for c in self.capabilities),
            transport="cli-json",
            approval_policy=ApprovalPolicy.MUTATING,
            operations=("check", "node_list"),
            metadata={"repository": "liuxb99/KnowGraphGo", "namespace": self.namespace},
        )

    def _runner(self) -> CommandRunner:
        return self.runner or SubprocessCommandRunner()

    def health(self) -> dict[str, Any]:
        if not self.dsn.strip():
            return {"status": "unavailable", "message": "KnowGraphGo dsn is not configured"}
        if self.runner is None and shutil.which(self.binary) is None:
            return {"status": "unavailable", "message": f"binary not found: {self.binary}"}
        try:
            result = self._runner().run([self.binary, "--dsn", self.dsn, "check"], timeout=self.timeout_seconds)
            return {"status": "ready" if result.returncode == 0 else "unavailable", "stderr": result.stderr.strip()}
        except Exception as exc:
            return {"status": "unavailable", "message": str(exc)}

    def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation == "check":
            argv = [self.binary, "--dsn", self.dsn, "check"]
        elif operation == "node_list":
            namespace = str(payload.get("namespace") or self.namespace).strip()
            if not namespace or any(ch in namespace for ch in "\r\n"):
                raise ValueError("node_list requires a safe namespace")
            argv = [self.binary, "--dsn", self.dsn, "--json", "node", "list", "--ns", namespace]
        else:
            raise ValueError(f"unsupported KnowGraphGo operation: {operation}")
        result = self._runner().run(argv, timeout=self.timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"knowgraph {operation} failed")
        if operation == "node_list":
            return {"items": _json_value(result.stdout, "knowgraph node list")}
        return {"ok": True, "stdout": result.stdout}


@dataclass
class BIMForgeAdapter:
    api_module: str = "aibim.api"

    name = "ai-bim-forge"
    capabilities = {EngineeringCapability.BIM_IFC, EngineeringCapability.QUANTITY}
    _OPERATIONS = (
        "build_ifc_model",
        "build_and_write_ifc",
        "reopen_and_audit",
        "get_element_quantities",
    )

    @property
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name=self.name,
            capabilities=frozenset(c.value for c in self.capabilities),
            transport="python-api",
            approval_policy=ApprovalPolicy.MUTATING,
            operations=self._OPERATIONS,
            metadata={"repository": "liuxb99/AI-BIM-Forge", "module": self.api_module},
        )

    def _api(self):
        return importlib.import_module(self.api_module)

    def health(self) -> dict[str, Any]:
        try:
            api = self._api()
            missing = [name for name in self._OPERATIONS if not callable(getattr(api, name, None))]
            if missing:
                return {"status": "degraded", "message": "missing canonical API", "missing": missing}
            return {"status": "ready"}
        except Exception as exc:
            return {"status": "unavailable", "message": str(exc)}

    def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation not in self._OPERATIONS:
            raise ValueError(f"unsupported BIM Forge operation: {operation}")
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        if not isinstance(args, list):
            raise ValueError("BIM Forge payload.args must be a list")
        if not isinstance(kwargs, Mapping):
            raise ValueError("BIM Forge payload.kwargs must be an object")
        func = getattr(self._api(), operation)
        result = func(*args, **dict(kwargs))
        return {"operation": operation, "result": result}


def core_specialist_adapters(*, knowgraph_dsn: str | None = None) -> list[Any]:
    """Build the canonical first-wave specialist adapter set.

    KnowGraphGo is included only when a DSN is configured because its CLI is database-bound.
    """
    adapters: list[Any] = [DesignForgeAdapter(), EngSketchAdapter(), BIMForgeAdapter()]
    if knowgraph_dsn:
        adapters.append(KnowGraphAdapter(dsn=knowgraph_dsn))
    return adapters
