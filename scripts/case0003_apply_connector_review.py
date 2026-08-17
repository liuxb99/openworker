"""Apply a ChatGPT review grounded by the connected Google Drive."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coworker.review_cycle import ReviewCycle
from coworker.review_gap import apply_review_finding
from coworker.work_ledger import WorkLedger

JOB_CODE = "OWJ-20260816030152-03D90D"

def _load(path: Path, label: str) -> dict:
    if not path.is_file() or path.stat().st_size <= 0: raise RuntimeError(f"{label} unavailable: {path}")
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise RuntimeError(f"{label} must be a JSON object")
    return value

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--workspace",required=True); p.add_argument("--revision-id",required=True); p.add_argument("--receipt",required=True); a=p.parse_args(argv)
    workspace=Path(a.workspace).expanduser().resolve(); revision_id=str(a.revision_id).strip(); receipt_path=Path(a.receipt).expanduser().resolve(); receipt=_load(receipt_path,"connector review receipt")
    if str(receipt.get("revision_id") or "").strip()!=revision_id: raise RuntimeError("connector review receipt revision_id mismatch")
    if str(receipt.get("transport") or "").strip()!="google-drive-connector": raise RuntimeError("connector review receipt transport mismatch")
    cloud=receipt.get("cloud_publication") or {}
    if not isinstance(cloud,dict): raise RuntimeError("cloud_publication must be an object")
    for key in ("drive_revision_folder_id","drive_file_id","cloud_zip_sha256","bundle_manifest_sha256"):
        if not str(cloud.get(key) or "").strip(): raise RuntimeError(f"connector review receipt missing cloud_publication.{key}")
    if str(cloud.get("bundle_manifest_sha256")).lower()!=str(receipt.get("bundle_manifest_sha256") or "").lower(): raise RuntimeError("cloud publication manifest SHA does not match review receipt")
    request=_load(workspace/".openworker"/"reviews"/revision_id/"review-request.json","review request")
    ledger=WorkLedger(workspace/".openworker"/"work-ledger.sqlite")
    try:
        work=ledger.get_work_by_code(JOB_CODE); revision=ledger.get_revision(revision_id)
        if revision["work_id"]!=work["work_id"]: raise RuntimeError("revision does not belong to Case 0003 work")
        result=apply_review_finding(ReviewCycle(workspace),ledger,revision_id,receipt,allowed_parameter_keys=request.get("allowed_parameter_keys") or [],current_parameters=request.get("current_parameters") or {})
        verdict=str(result.get("verdict") or "").upper(); accepted_revision_id=""
        if verdict=="PASS": accepted_revision_id=ledger.accept_revision(revision_id)["revision_id"]; status="ACCEPTED"
        elif verdict=="TUNE": status="TUNING_REQUIRED"
        else: status="TOOL_GAP_REWORK_REQUIRED" if result.get("finding_type")=="TOOL_GAP" else "REWORK_REQUIRED"
        output={"schema_version":"openworker-case0003-connector-review-apply/v1","case_id":"0003","revision_id":revision_id,"verdict":str(receipt.get("verdict") or "").upper(),"finding_type":result.get("finding_type",receipt.get("verdict")),"status":status,"accepted_revision_id":accepted_revision_id,"next_revision_id":result.get("next_revision_id",""),"owning_repo":result.get("owning_repo",""),"gap_capability":result.get("gap_capability",""),"verification_plan":result.get("verification_plan",[]),"cloud_publication":cloud,"ledger":ledger.snapshot(work["work_id"])}
        out=workspace/"acceptance"/"openworker-final"/f"connector-review-apply-{revision_id}.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(output,ensure_ascii=False,indent=2,default=str),encoding="utf-8"); print(json.dumps(output,ensure_ascii=False,sort_keys=True,default=str)); return 0 if verdict=="PASS" else 4
    finally: ledger.close()
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc: print(f"CASE0003_CONNECTOR_REVIEW_APPLY_FAIL {exc}",file=sys.stderr); raise
