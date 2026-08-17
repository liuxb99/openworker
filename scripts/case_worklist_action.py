from __future__ import annotations

import argparse
import json
from pathlib import Path

from coworker.engineering.case_worklist import CaseWorklist, CaseWorklistError, CaseWorklistStore


def load_manifest(path: Path) -> CaseWorklist:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise CaseWorklistError("worklist manifest root must be an object")
    return CaseWorklist.from_dict(raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["ensure", "show", "start", "record", "pass", "block"])
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--step-id")
    parser.add_argument("--action-id")
    parser.add_argument("--key")
    parser.add_argument("--value")
    parser.add_argument("--reason")
    args = parser.parse_args()

    store = CaseWorklistStore(args.workspace_root)

    if args.command == "ensure":
        if store.path.is_file():
            worklist = store.load()
        else:
            if not args.manifest:
                raise CaseWorklistError("--manifest is required when creating a worklist")
            worklist = load_manifest(Path(args.manifest).resolve())
            if Path(worklist.workspace_root).resolve() != Path(args.workspace_root).resolve():
                raise CaseWorklistError("manifest workspace_root does not match --workspace-root")
            store.save(worklist)
        print(json.dumps(worklist.as_dict(), ensure_ascii=False, indent=2))
        print(f"CASE_WORKLIST_READY path={store.path} next={worklist.as_dict()['canonical_next_step_id']}")
        return 0

    worklist = store.load()

    if args.command == "show":
        print(json.dumps(worklist.as_dict(), ensure_ascii=False, indent=2))
        return 0

    if not args.step_id:
        raise CaseWorklistError("--step-id is required")

    if args.command == "start":
        if not args.action_id:
            raise CaseWorklistError("--action-id is required for start")
        worklist.start(args.step_id, args.action_id)
    elif args.command == "record":
        if not args.key:
            raise CaseWorklistError("--key is required for record")
        if args.value is None:
            raise CaseWorklistError("--value is required for record")
        worklist.record_evidence(args.step_id, args.key, args.value)
    elif args.command == "pass":
        worklist.pass_step(args.step_id)
    elif args.command == "block":
        if not args.reason:
            raise CaseWorklistError("--reason is required for block")
        worklist.block(args.step_id, args.reason)

    store.save(worklist)
    print(json.dumps(worklist.as_dict(), ensure_ascii=False, indent=2))
    print(
        f"CASE_WORKLIST_UPDATED command={args.command} step={args.step_id} "
        f"next={worklist.as_dict()['canonical_next_step_id']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"CASE_WORKLIST_FAIL: {exc}")
        raise SystemExit(2)
