"""H10 packaged Harness integration asset and launch capability resolver."""
from __future__ import annotations

import json
import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class HarnessPackagingError(RuntimeError):
    pass


@dataclass(frozen=True)
class HarnessPackageLayout:
    root: Path
    upstream_lock: Path
    cordis_plugin: Path


@dataclass(frozen=True)
class HarnessLaunchCapability:
    available: bool
    command: tuple[str, ...]
    layout: HarnessPackageLayout | None
    reason: str


def _candidate_roots(env: Mapping[str, str]) -> list[Path]:
    candidates: list[Path] = []
    override = env.get("OPENWORKER_HARNESS_ASSET_DIR", "").strip()
    if override:
        candidates.append(Path(override))
    resource = env.get("OPENWORKER_RESOURCE_DIR", "").strip()
    if resource:
        candidates.append(Path(resource) / "harness")

    # Tauri production layout places the PyInstaller onedir sidecar in
    # <resources>/sidecar/openworker-server[.exe] and this integration directory
    # in <resources>/harness.  Infer the sibling from sys.executable so the
    # packaged server does not depend on a shell-provided environment variable.
    try:
        executable = Path(sys.executable).resolve()
        candidates.append(executable.parent.parent / "harness")
    except (OSError, RuntimeError):
        pass

    package_root = Path(__file__).resolve().parents[2]
    candidates.append(package_root / "harness")

    # Preserve order while avoiding repeated filesystem probes.
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = os.path.normcase(os.path.abspath(str(candidate)))
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def resolve_harness_layout(env: Mapping[str, str] | None = None) -> HarnessPackageLayout:
    env = os.environ if env is None else env
    for root in _candidate_roots(env):
        lock = root / "upstream-lock.json"
        plugin = root / "upstream-plugin" / "openworker-engineering-tools.ts"
        if lock.is_file() and plugin.is_file():
            try:
                payload = json.loads(lock.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise HarnessPackagingError(f"invalid Harness upstream lock at {lock}: {exc}") from exc
            commit = payload.get("commit") if isinstance(payload, dict) else None
            if not isinstance(commit, str) or len(commit.strip()) < 12:
                raise HarnessPackagingError(f"Harness upstream lock missing commit: {lock}")
            return HarnessPackageLayout(root.resolve(), lock.resolve(), plugin.resolve())
    raise HarnessPackagingError("OpenWorker Harness integration assets are not installed")


def _parse_command(raw: str) -> tuple[str, ...]:
    raw = raw.strip()
    if not raw:
        return ()
    if raw.startswith("["):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HarnessPackagingError("OPENWORKER_HARNESS_COMMAND is invalid JSON") from exc
        if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
            raise HarnessPackagingError("OPENWORKER_HARNESS_COMMAND JSON must be a non-empty string array")
        return tuple(value)
    return tuple(shlex.split(raw, posix=os.name != "nt"))


def harness_launch_capability(env: Mapping[str, str] | None = None) -> HarnessLaunchCapability:
    env = os.environ if env is None else env
    try:
        layout = resolve_harness_layout(env)
    except HarnessPackagingError as exc:
        return HarnessLaunchCapability(False, (), None, str(exc))
    try:
        command = _parse_command(env.get("OPENWORKER_HARNESS_COMMAND", ""))
    except HarnessPackagingError as exc:
        return HarnessLaunchCapability(False, (), layout, str(exc))
    if not command:
        return HarnessLaunchCapability(
            False,
            (),
            layout,
            "OPENWORKER_HARNESS_COMMAND is not configured; packaged integration assets alone are not an ACP runtime",
        )
    return HarnessLaunchCapability(True, command, layout, "ready")


__all__ = [
    "HarnessLaunchCapability",
    "HarnessPackageLayout",
    "HarnessPackagingError",
    "harness_launch_capability",
    "resolve_harness_layout",
]
