"""CLI for asking OpenWorker about durable project work state."""
from __future__ import annotations
import argparse
import json
import os
from .project_knowledge import ProjectKnowledgeStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="openworker-project-query")
    parser.add_argument("--cwd", "--workspace", dest="workspace", default=os.getcwd())
    parser.add_argument("-q", "--question", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = ProjectKnowledgeStore(args.workspace).query(args.question)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["answer"])
        if result["evidence_event_ids"]:
            print("evidence_event_ids=" + ",".join(result["evidence_event_ids"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())