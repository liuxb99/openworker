"""Case 0005 acceptance mapping for local Google Drive approval handoff."""
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
            raise CaseWorklistError("approval artifact transport must be google-drive-api")
        if bool(evidence.get("github_action_used_for_artifact_transport")):
            raise CaseWorklistError("approval artifact transport must not use GitHub Actions")
        published = evidence.get("published_artifacts")
        if not isinstance(published, list) or len(published) != 1 or not isinstance(published[0], Mapping):
            raise CaseWorklistError("approval artifact publish must contain exactly one physical artifact")
        item = published[0]
        relpath = str(item.get("relative_path", "")).strip().replace("\\", "/")
        digest = str(item.get("sha256", "")).strip()
        if step.step_id == "0005-026":
            expected = "presentation/storyboard-text-only.pptx"
        elif step.step_id == "0005-056":
            expected = "presentation/storyboard-illustrated.pptx"
        else:
            raise CaseWorklistError(f"artifact publish acceptance is not mapped for {step.step_id}")
        if relpath.lower() != expected.lower():
            raise CaseWorklistError(f"approval artifact mismatch expected={expected!r} actual={relpath!r}")
        if len(digest) != 64:
            raise CaseWorklistError("published approval artifact is missing SHA256")
        mapped = {
            "review_bundle": evidence.get("review_bundle"),
            "drive_receipt": evidence.get("drive_receipt"),
            "drive_folder_id": evidence.get("drive_folder_id"),
            "manifest_sha256": evidence.get("manifest_sha256"),
            "published_artifact": relpath,
            "published_artifact_sha256": digest,
            "artifact_transport": "google-drive-api",
            "github_action_used_for_artifact_transport": False,
        }
        return self._require_keys(mapped, step.acceptance)
