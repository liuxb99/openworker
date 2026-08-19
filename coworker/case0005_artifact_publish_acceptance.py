"""Case 0005 acceptance mapping for local Google Drive handoff."""
from __future__ import annotations

from typing import Any, Mapping

from .case_worklist import CaseWorklistError

_ARTIFACT_PUBLISH_ACTION = "openworker.case.publish-artifacts"


class Case0005ArtifactPublishAcceptanceMixin:
    def _acceptance_evidence(self, step, local_result: Mapping[str, Any]) -> dict[str, Any]:
        action = str(local_result.get("capability_id", "")).strip()
        if action != _ARTIFACT_PUBLISH_ACTION:
            return super()._acceptance_evidence(step, local_result)
        if str(local_result.get("status", "")).strip().lower() != "completed":
            raise CaseWorklistError("artifact publish result did not report completed")
        evidence = local_result.get("evidence")
        if not isinstance(evidence, Mapping):
            raise CaseWorklistError("artifact publish result missing evidence object")
        if str(evidence.get("transport", "")).strip().lower() != "google-drive-api":
            raise CaseWorklistError("artifact transport must be google-drive-api")
        if bool(evidence.get("github_action_used_for_artifact_transport")):
            raise CaseWorklistError("artifact transport must not use GitHub Actions")
        published = evidence.get("published_artifacts")
        if not isinstance(published, list) or not published or any(not isinstance(item, Mapping) for item in published):
            raise CaseWorklistError("artifact publish must contain physical artifacts")
        relpaths = [str(item.get("relative_path", "")).strip().replace("\\", "/") for item in published]
        digests = [str(item.get("sha256", "")).strip().lower() for item in published]
        if any(not path for path in relpaths) or any(len(digest) != 64 for digest in digests):
            raise CaseWorklistError("published artifact path/SHA256 evidence is incomplete")

        if step.step_id == "0005-026":
            expected = ["presentation/storyboard-text-only.pptx"]
        elif step.step_id == "0005-056":
            expected = ["presentation/storyboard-illustrated.pptx"]
        elif step.step_id == "0005-090":
            expected = None  # dynamic WorkLedger manifest + canonical final MP4
            if "final/final.mp4" not in {path.lower() for path in relpaths}:
                raise CaseWorklistError("final review bundle must include final/final.mp4")
            if not any(path.lower().startswith(".openworker/revisions/") and path.lower().endswith("/manifest.json") for path in relpaths):
                raise CaseWorklistError("final review bundle must include immutable WorkLedger revision manifest")
            if len(relpaths) != 2:
                raise CaseWorklistError("final review bundle must contain exactly final MP4 and revision manifest")
        else:
            raise CaseWorklistError(f"artifact publish acceptance is not mapped for {step.step_id}")
        if expected is not None and [path.lower() for path in relpaths] != [path.lower() for path in expected]:
            raise CaseWorklistError(f"artifact publish mismatch expected={expected!r} actual={relpaths!r}")

        mapped = {
            "review_bundle": evidence.get("review_bundle"),
            "drive_receipt": evidence.get("drive_receipt"),
            "drive_folder_id": evidence.get("drive_folder_id"),
            "manifest_sha256": evidence.get("manifest_sha256"),
            "published_artifacts": relpaths,
            "published_artifact_sha256": digests,
            "artifact_transport": "google-drive-api",
            "github_action_used_for_artifact_transport": False,
        }
        return self._require_keys(mapped, step.acceptance)
