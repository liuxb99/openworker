"""Thin CLI for the EngineeringHarnessHost.

No agent logic lives here. The command selects a Project Workspace and one user
request, then streams events from the existing Harness runtime.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from .engine import ApprovalOutcome, PermissionRequest
from .events import EventType
from .permissions import Mode
from .runtimes.engineering_host import EngineeringHarnessHost


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openworker-engineering",
        description="Run one OpenWorker engineering Harness session from a Project Workspace",
    )
    parser.add_argument("request", nargs="*", help="User request. When omitted, read TASK.md only.")
    parser.add_argument("--workspace", default=os.getcwd())
    parser.add_argument("--engineering-os-url", default="")
    parser.add_argument("--tool-runtime-url", default="")
    parser.add_argument("--component-id", default="")
    parser.add_argument(
        "--allow-publish",
        action="store_true",
        help="Enable the AI-Engineering-OS publish capability. Each consequential call still requires OpenWorker approval.",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Explicitly approve consequential engineering calls for this CLI session.",
    )
    parser.add_argument("--json-events", action="store_true")
    return parser


def _resolve_request(workspace: Path, parts: list[str]) -> str:
    direct = " ".join(parts).strip()
    if direct:
        return direct
    task = workspace / "TASK.md"
    if not task.is_file():
        raise SystemExit("No request supplied and Project Workspace has no TASK.md")
    text = task.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit("TASK.md is empty")
    return text


async def _interactive_approver(request: PermissionRequest) -> ApprovalOutcome:
    summary = json.dumps(request.arguments, ensure_ascii=False, default=str)
    prompt = f"Approve {request.tool_name} {summary}? [y/N/a(always tool)] "
    answer = (await asyncio.to_thread(input, prompt)).strip().lower()
    if answer in {"y", "yes"}:
        return ApprovalOutcome.ONCE
    if answer in {"a", "always"}:
        return ApprovalOutcome.ALWAYS_TOOL
    return ApprovalOutcome.DENY


async def _approve_once(_request: PermissionRequest) -> ApprovalOutcome:
    return ApprovalOutcome.ONCE


async def _run(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.is_dir():
        raise SystemExit(f"Project Workspace does not exist: {workspace}")
    request = _resolve_request(workspace, list(args.request))
    approver = _approve_once if args.auto_approve else _interactive_approver
    host = EngineeringHarnessHost(
        workspace=workspace,
        engineering_os_base_url=args.engineering_os_url or None,
        tool_runtime_base_url=args.tool_runtime_url or None,
        mode=Mode.INTERACTIVE,
        approver=approver,
        allow_publish=bool(args.allow_publish),
        component_id=args.component_id,
    )
    failed = False
    try:
        async for event in host.run(request, source={"surface":"openworker-engineering-cli"}):
            if args.json_events:
                print(json.dumps({"type":event.type.value,"data":event.data}, ensure_ascii=False, default=str))
                continue
            if event.type is EventType.ASSISTANT_MESSAGE:
                text = event.data.get("content") or event.data.get("text")
                if text:
                    print(text)
            elif event.type is EventType.ERROR:
                failed = True
                print(f"error: {event.data.get('error')}", file=sys.stderr)
            elif event.type is EventType.INTERRUPTED:
                failed = True
                print("interrupted", file=sys.stderr)
        health = await host.health()
        if args.json_events:
            print(json.dumps({"type":"host_health","data":health}, ensure_ascii=False, default=str))
    finally:
        await host.aclose()
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
