"""Cross-system Digital Thread contracts for engineering artifacts.

This module does not replace source-system schemas. It creates immutable references to
existing Job/Artifact/Version/Trace identities so OpenWorker can explain provenance across
AI-Engineering-OS and specialist engines without inventing new domain facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


class EvidenceKind(str, Enum):
    JOB = "job"
    ARTIFACT = "artifact"
    CALCULATION_RUN = "calculation_run"
    VERSION = "version"
    ENGINE_RUN = "engine_run"
    SEMANTIC_ENTITY = "semantic_entity"


class RelationKind(str, Enum):
    PRODUCED_BY = "produced_by"
    DERIVED_FROM = "derived_from"
    BELONGS_TO_JOB = "belongs_to_job"
    BELONGS_TO_PROJECT = "belongs_to_project"
    REPRESENTS = "represents"
    SUPERSEDES = "supersedes"


@dataclass(frozen=True)
class EvidenceRef:
    """Stable reference to an identity owned by another system."""

    system: str
    kind: EvidenceKind
    identifier: str
    revision: str | None = None
    checksum: str | None = None
    uri: str | None = None
    media_type: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.system.strip():
            raise ValueError("evidence system must not be empty")
        if not self.identifier.strip():
            raise ValueError("evidence identifier must not be empty")
        if self.checksum is not None and not self.checksum.strip():
            raise ValueError("evidence checksum must not be blank")

    @property
    def key(self) -> str:
        suffix = f"@{self.revision}" if self.revision else ""
        return f"{self.system}:{self.kind.value}:{self.identifier}{suffix}"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "system": self.system,
            "kind": self.kind.value,
            "identifier": self.identifier,
        }
        if self.revision:
            payload["revision"] = self.revision
        if self.checksum:
            payload["checksum"] = self.checksum
        if self.uri:
            payload["uri"] = self.uri
        if self.media_type:
            payload["media_type"] = self.media_type
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class ProvenanceLink:
    source: str
    relation: RelationKind
    target: str

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.target.strip():
            raise ValueError("provenance link endpoints must not be empty")
        if self.source == self.target:
            raise ValueError("provenance link cannot point to itself")

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "relation": self.relation.value,
            "target": self.target,
        }


@dataclass
class DigitalThread:
    """Deterministic graph of external identities and their provenance relations."""

    _refs: dict[str, EvidenceRef] = field(default_factory=dict)
    _links: set[ProvenanceLink] = field(default_factory=set)

    def add(self, ref: EvidenceRef) -> EvidenceRef:
        current = self._refs.get(ref.key)
        if current is not None and current != ref:
            raise ValueError(f"conflicting evidence reference: {ref.key}")
        self._refs[ref.key] = ref
        return ref

    def link(
        self,
        source: EvidenceRef | str,
        relation: RelationKind,
        target: EvidenceRef | str,
    ) -> ProvenanceLink:
        source_key = source.key if isinstance(source, EvidenceRef) else source
        target_key = target.key if isinstance(target, EvidenceRef) else target
        if source_key not in self._refs:
            raise KeyError(f"source evidence is not registered: {source_key}")
        if target_key not in self._refs:
            raise KeyError(f"target evidence is not registered: {target_key}")
        link = ProvenanceLink(source_key, relation, target_key)
        self._links.add(link)
        return link

    def refs(self) -> list[EvidenceRef]:
        return [self._refs[key] for key in sorted(self._refs)]

    def links(self) -> list[ProvenanceLink]:
        return sorted(
            self._links,
            key=lambda item: (item.source, item.relation.value, item.target),
        )

    def trace_from(self, key: str) -> list[ProvenanceLink]:
        if key not in self._refs:
            raise KeyError(f"evidence is not registered: {key}")
        seen: set[str] = set()
        queue = [key]
        found: list[ProvenanceLink] = []
        adjacency: dict[str, list[ProvenanceLink]] = {}
        for link in self.links():
            adjacency.setdefault(link.source, []).append(link)
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            for link in adjacency.get(current, []):
                found.append(link)
                if link.target not in seen:
                    queue.append(link.target)
        return found

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "openworker-digital-thread/1.0.0",
            "evidence": [ref.to_dict() for ref in self.refs()],
            "links": [link.to_dict() for link in self.links()],
        }


def _required_text(payload: Mapping[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"{context} missing required field: {key}")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{context} field must not be empty: {key}")
    return text


def os_job_ref(job: Mapping[str, Any]) -> EvidenceRef:
    return EvidenceRef(
        system="ai-engineering-os",
        kind=EvidenceKind.JOB,
        identifier=_required_text(job, "id", "AI-Engineering-OS Job"),
        revision=str(job.get("revision")) if job.get("revision") is not None else None,
        metadata={
            key: job[key]
            for key in ("project_id", "code", "status", "working_dir", "delivery_dir")
            if job.get(key) not in (None, "")
        },
    )


def os_artifact_ref(artifact: Mapping[str, Any]) -> EvidenceRef:
    return EvidenceRef(
        system="ai-engineering-os",
        kind=EvidenceKind.ARTIFACT,
        identifier=_required_text(artifact, "id", "AI-Engineering-OS Artifact"),
        revision=str(artifact.get("revision")) if artifact.get("revision") is not None else None,
        checksum=_required_text(artifact, "checksum", "AI-Engineering-OS Artifact"),
        uri=_required_text(artifact, "uri", "AI-Engineering-OS Artifact"),
        media_type=_required_text(artifact, "media_type", "AI-Engineering-OS Artifact"),
        metadata={
            key: artifact[key]
            for key in ("project_id", "job_id", "component_id", "kind", "source_run_id")
            if artifact.get(key) not in (None, "")
        },
    )


def design_forge_artifact_ref(artifact: Mapping[str, Any]) -> EvidenceRef:
    return EvidenceRef(
        system="ai-civildesign-forge",
        kind=EvidenceKind.ARTIFACT,
        identifier=_required_text(artifact, "artifact_id", "Design Forge Artifact"),
        revision=str(artifact.get("schema_version")) if artifact.get("schema_version") else None,
        checksum=_required_text(artifact, "sha256", "Design Forge Artifact"),
        uri=_required_text(artifact, "path", "Design Forge Artifact"),
        media_type=_required_text(artifact, "media_type", "Design Forge Artifact"),
        metadata={
            key: artifact[key]
            for key in (
                "artifact_type",
                "calculation_run_id",
                "semantic_id",
                "ifc_guid",
                "engine_version",
                "formula_registry_version",
            )
            if artifact.get(key) not in (None, "")
        },
    )


def engsketch_version_refs(
    project: str,
    manifest: Mapping[str, Any],
) -> list[EvidenceRef]:
    project = project.strip()
    if not project:
        raise ValueError("EngSketch project must not be empty")
    version = _required_text(manifest, "version", "EngSketch manifest")
    manifest_checksum = _required_text(manifest, "checksum", "EngSketch manifest")
    common = {
        "project": project,
        "parent_version": manifest.get("parent_version"),
        "operation_summary": manifest.get("operation_summary"),
        "schema_version": manifest.get("schema_version"),
        "timestamp": manifest.get("timestamp"),
    }
    refs = [
        EvidenceRef(
            system="ai-engsketch",
            kind=EvidenceKind.VERSION,
            identifier=f"{project}:{version}",
            revision=version,
            checksum=manifest_checksum,
            metadata={k: v for k, v in common.items() if v not in (None, "")},
        )
    ]
    for artifact_type, key, filename, media_type in (
        ("drawing_svg", "svg_sha256", "drawing.svg", "image/svg+xml"),
        ("drawing_png", "png_sha256", "drawing.png", "image/png"),
    ):
        digest = manifest.get(key)
        if digest:
            refs.append(
                EvidenceRef(
                    system="ai-engsketch",
                    kind=EvidenceKind.ARTIFACT,
                    identifier=f"{project}:{version}:{artifact_type}",
                    revision=version,
                    checksum=str(digest).strip(),
                    uri=f"workspace/{project}/versions/{version}/output/{filename}",
                    media_type=media_type,
                    metadata={"artifact_type": artifact_type, "project": project},
                )
            )
    return refs


def bim_forge_artifact_ref(artifact: Mapping[str, Any]) -> EvidenceRef:
    return EvidenceRef(
        system="ai-bim-forge",
        kind=EvidenceKind.ARTIFACT,
        identifier=_required_text(artifact, "artifact_id", "BIM Forge Artifact"),
        checksum=_required_text(artifact, "sha256", "BIM Forge Artifact"),
        uri=_required_text(artifact, "path", "BIM Forge Artifact"),
        metadata={
            "artifact_type": _required_text(artifact, "artifact_type", "BIM Forge Artifact")
        },
    )


def add_all(thread: DigitalThread, refs: Iterable[EvidenceRef]) -> list[EvidenceRef]:
    added = []
    for ref in refs:
        added.append(thread.add(ref))
    return added
