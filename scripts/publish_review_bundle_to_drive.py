"""Publish an existing OpenWorker review bundle to Google Drive and bind it to WorkLedger."""
from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path

from coworker.review_cycle import DEFAULT_DRIVE_FOLDER_ID
from coworker.review_drive_ledger import publish_review_bundle_to_ledger
from coworker.work_ledger import WorkLedger


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--revision-id", required=True)
    parser.add_argument("--work-code", required=True)
    parser.add_argument("--bundle")
    parser.add_argument("--ledger")
    parser.add_argument(
        "--drive-folder-id",
        default=os.environ.get("OPENWORKER_REVIEW_DRIVE_FOLDER_ID", DEFAULT_DRIVE_FOLDER_ID),
    )
    parser.add_argument("--machine-id", default=platform.node())
    parser.add_argument("--case-id", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--run-id", default="")
    return parser


def main() -> int:
    args = _parser().parse_args()
    workspace = Path(args.workspace).expanduser().resolve()
    revision_id = str(args.revision_id).strip()
    bundle = Path(args.bundle).expanduser().resolve() if args.bundle else workspace / ".openworker" / "reviews" / revision_id
    ledger_path = Path(args.ledger).expanduser().resolve() if args.ledger else workspace / ".openworker" / "work-ledger.sqlite"
    metadata = {
        key: value
        for key, value in {
            "case_id": str(args.case_id).strip(),
            "job_id": str(args.job_id).strip(),
            "run_id": str(args.run_id).strip(),
        }.items()
        if value
    }

    ledger = WorkLedger(ledger_path)
    try:
        receipt = publish_review_bundle_to_ledger(
            ledger,
            revision_id,
            bundle,
            work_code=args.work_code,
            root_folder_id=args.drive_folder_id,
            machine_id=args.machine_id,
            metadata=metadata,
        )
    finally:
        ledger.close()
    print(json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
