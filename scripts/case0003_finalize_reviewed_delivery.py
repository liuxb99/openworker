"""Finalize Case 0003 WorkLedger delivery after connector-grounded ChatGPT PASS.

This step is intentionally separate from review application. It binds the already
accepted review revision to the current Engineering OS Delivery receipt and the
exact Google Drive publication identity that ChatGPT reviewed. No historical
GitHub run/delivery constants are trusted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coworker.work_ledger import WorkLedger

JOB_CODE = "OWJ-20260816030152-03D90D"

class FinalizeError(RuntimeError):
    pass


def _load(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise FinalizeError(f"{label} missing/empty: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise FinalizeError(f"{label} invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FinalizeError(f"{label} must be a JSON object")
    return value


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _same_sha(path: Path, expected: Any, label: str) -> str:
    if not path.is_file() or path.stat().st_size <= 0:
        raise FinalizeError(f"{label} physical file missing/empty: {path}")
    actual = _sha256(path)
    want = str(expected or "").strip().lower().removeprefix("sha256:")
    if len(want) != 64 or actual != want:
        raise FinalizeError(f"{label} SHA mismatch expected={want} actual={actual}")
    return actual


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workspace", required=True)
    p.add_argument("--revision-id", required=True)
    p.add_argument("--review-apply", default="")
    p.add_argument("--os-delivery-receipt", default="")
    args = p.parse_args(argv)

    workspace = Path(args.workspace).expanduser().resolve()
    revision_id = str(args.revision_id).strip()
    if not workspace.is_dir() or not revision_id:
        raise FinalizeError("workspace and revision-id are required")

    acceptance = workspace / "acceptance" / "openworker-final"
    review_apply_path = Path(args.review_apply).expanduser().resolve() if args.review_apply else acceptance / f"connector-review-apply-{revision_id}.json"
    os_receipt_path = Path(args.os_delivery_receipt).expanduser().resolve() if args.os_delivery_receipt else workspace / "evidence" / "case0003-os-delivery-receipt.json"
    review = _load(review_apply_path, "connector review apply")
    os_delivery = _load(os_receipt_path, "Engineering OS delivery receipt")

    if review.get("schema_version") not in {"openworker-case0003-connector-review-apply/v2"}:
        raise FinalizeError("connector review apply schema mismatch")
    if str(review.get("revision_id") or "") != revision_id:
        raise FinalizeError("connector review revision identity mismatch")
    if str(review.get("verdict") or "").upper() != "PASS":
        raise FinalizeError("only connector-grounded PASS can finalize delivery")
    if str(review.get("status") or "") != "ACCEPTED_PENDING_FINALIZE":
        raise FinalizeError("review apply is not in ACCEPTED_PENDING_FINALIZE")
    if str(review.get("accepted_revision_id") or "") != revision_id:
        raise FinalizeError("accepted revision identity mismatch")
    if str(review.get("delivered_revision_id") or ""):
        raise FinalizeError("review apply unexpectedly already declares delivery")

    cloud = review.get("cloud_publication") or {}
    if not isinstance(cloud, dict):
        raise FinalizeError("cloud_publication must be an object")
    for key in ("drive_revision_folder_id", "drive_file_id", "cloud_zip_sha256", "bundle_manifest_sha256"):
        if not str(cloud.get(key) or "").strip():
            raise FinalizeError(f"cloud publication missing {key}")
    bundle_sha = str(review.get("bundle_manifest_sha256") or "").strip().lower()
    if bundle_sha != str(cloud.get("bundle_manifest_sha256") or "").strip().lower():
        raise FinalizeError("review/cloud bundle manifest identity mismatch")
    local_bundle_manifest = workspace / ".openworker" / "reviews" / revision_id / "manifest.json"
    _same_sha(local_bundle_manifest, bundle_sha, "review bundle manifest")

    if os_delivery.get("ok") is not True or os_delivery.get("schema_version") != "engineering-os-local-delivery-receipt/v1":
        raise FinalizeError("Engineering OS delivery receipt rejected")
    if str(os_delivery.get("status") or "") != "published":
        raise FinalizeError("Engineering OS delivery is not published")
    delivery_id = str(os_delivery.get("delivery_id") or "").strip()
    os_job_id = str(os_delivery.get("job_id") or "").strip()
    os_project_id = str(os_delivery.get("project_id") or "").strip()
    delivery_revision = int(os_delivery.get("revision") or 0)
    if not delivery_id or not os_job_id or not os_project_id or delivery_revision <= 0:
        raise FinalizeError("Engineering OS delivery identity is incomplete")

    manifest_path = Path(str(os_delivery.get("manifest_path") or "")).expanduser().resolve()
    checksum_path = Path(str(os_delivery.get("checksum_manifest") or "")).expanduser().resolve()
    website_path = Path(str(os_delivery.get("website_entry") or "")).expanduser().resolve()
    manifest_sha = _same_sha(manifest_path, os_delivery.get("manifest_sha256"), "OS delivery manifest")
    checksum_sha = _same_sha(checksum_path, os_delivery.get("checksum_manifest_sha256"), "OS checksum manifest")
    if not website_path.is_file() or website_path.stat().st_size <= 0:
        raise FinalizeError(f"OS delivery website missing/empty: {website_path}")
    website_sha = _sha256(website_path)

    delivery_manifest = _load(manifest_path, "OS delivery manifest")
    if delivery_manifest.get("schema_version") != "delivery-manifest/1.0":
        raise FinalizeError("OS delivery manifest schema mismatch")
    if str(delivery_manifest.get("delivery_id") or "") != delivery_id:
        raise FinalizeError("OS delivery manifest delivery_id mismatch")
    if str(delivery_manifest.get("job_id") or "") != os_job_id:
        raise FinalizeError("OS delivery manifest job_id mismatch")
    if str(delivery_manifest.get("project_id") or "") != os_project_id:
        raise FinalizeError("OS delivery manifest project_id mismatch")
    if int(delivery_manifest.get("revision") or 0) != delivery_revision:
        raise FinalizeError("OS delivery manifest revision mismatch")

    ledger = WorkLedger(workspace / ".openworker" / "work-ledger.sqlite")
    try:
        work = ledger.get_work_by_code(JOB_CODE)
        revision = ledger.get_revision(revision_id)
        if revision["work_id"] != work["work_id"]:
            raise FinalizeError("revision does not belong to Case 0003 work")
        if revision["status"] != "accepted" or work.get("accepted_revision_id") != revision_id:
            raise FinalizeError("WorkLedger revision is not the accepted review revision")
        existing = str(work.get("delivered_revision_id") or "")
        if existing and existing != revision_id:
            raise FinalizeError(f"another revision is already delivered: {existing}")
        if not existing:
            ledger.deliver_revision(
                revision_id,
                delivery={
                    "case_id": "0003",
                    "transport": "openworker-local-first+google-drive-connector-review",
                    "engineering_os": {
                        "project_id": os_project_id,
                        "job_id": os_job_id,
                        "delivery_id": delivery_id,
                        "delivery_revision": delivery_revision,
                        "manifest_path": str(manifest_path),
                        "manifest_sha256": manifest_sha,
                        "checksum_manifest_path": str(checksum_path),
                        "checksum_manifest_sha256": checksum_sha,
                        "website_entry": str(website_path),
                        "website_sha256": website_sha,
                    },
                    "google_drive": {
                        "drive_revision_folder_id": cloud["drive_revision_folder_id"],
                        "drive_file_id": cloud["drive_file_id"],
                        "cloud_zip_sha256": cloud["cloud_zip_sha256"],
                        "bundle_manifest_sha256": bundle_sha,
                    },
                },
            )
        final_work = ledger.get_work(work["work_id"])
        if final_work.get("delivered_revision_id") != revision_id or final_work.get("status") != "delivered":
            raise FinalizeError("WorkLedger delivery pointer verification failed")
        output = {
            "schema_version": "openworker-case0003-reviewed-delivery-finalize/v1",
            "case_id": "0003",
            "revision_id": revision_id,
            "status": "DELIVERED",
            "ok": True,
            "accepted_revision_id": final_work.get("accepted_revision_id"),
            "delivered_revision_id": final_work.get("delivered_revision_id"),
            "engineering_os": {
                "project_id": os_project_id,
                "job_id": os_job_id,
                "delivery_id": delivery_id,
                "delivery_revision": delivery_revision,
                "manifest_sha256": manifest_sha,
                "checksum_manifest_sha256": checksum_sha,
                "website_sha256": website_sha,
            },
            "google_drive": {
                "drive_revision_folder_id": cloud["drive_revision_folder_id"],
                "drive_file_id": cloud["drive_file_id"],
                "cloud_zip_sha256": cloud["cloud_zip_sha256"],
                "bundle_manifest_sha256": bundle_sha,
            },
            "ledger": ledger.snapshot(work["work_id"]),
        }
        acceptance.mkdir(parents=True, exist_ok=True)
        out = acceptance / f"reviewed-delivery-finalize-{revision_id}.json"
        latest = acceptance / "reviewed-delivery-finalize.json"
        payload = json.dumps(output, ensure_ascii=False, indent=2, default=str)
        out.write_text(payload, encoding="utf-8")
        latest.write_text(payload, encoding="utf-8")
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, default=str))
        return 0
    finally:
        ledger.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"CASE0003_REVIEWED_DELIVERY_FINALIZE_FAIL {exc}", file=sys.stderr)
        raise
