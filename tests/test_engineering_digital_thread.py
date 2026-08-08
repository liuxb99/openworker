import pytest

from coworker.engineering import (
    DigitalThread,
    EvidenceKind,
    EvidenceRef,
    RelationKind,
    add_all,
    bim_forge_artifact_ref,
    design_forge_artifact_ref,
    engsketch_version_refs,
    os_artifact_ref,
    os_job_ref,
)


def test_os_job_and_artifact_preserve_authoritative_identity():
    job = os_job_ref(
        {
            "id": "job_001",
            "project_id": "prj_001",
            "code": "RC-C1",
            "status": "review",
            "revision": 3,
            "working_dir": "work/job_001",
            "delivery_dir": "delivery/job_001",
        }
    )
    artifact = os_artifact_ref(
        {
            "id": "art_001",
            "project_id": "prj_001",
            "job_id": "job_001",
            "component_id": "column-C1",
            "kind": "calculation_trace",
            "revision": 2,
            "uri": "delivery/job_001/trace.json",
            "media_type": "application/json",
            "checksum": "abc123",
            "source_run_id": "run_001",
        }
    )
    assert job.kind is EvidenceKind.JOB
    assert job.revision == "3"
    assert artifact.checksum == "abc123"
    assert artifact.metadata["source_run_id"] == "run_001"


def test_design_forge_artifact_preserves_trace_and_versions():
    ref = design_forge_artifact_ref(
        {
            "artifact_id": "calculation:rc-column:column-C1",
            "artifact_type": "calculation_trace",
            "schema_version": "artifact/1.0.0",
            "calculation_run_id": "run-77",
            "semantic_id": "column-C1",
            "path": "artifacts/rc-column/column-C1.json",
            "media_type": "application/json",
            "sha256": "deadbeef",
            "engine_version": "v1.4.2",
            "formula_registry_version": "2026.08",
        }
    )
    assert ref.identifier == "calculation:rc-column:column-C1"
    assert ref.metadata["calculation_run_id"] == "run-77"
    assert ref.metadata["semantic_id"] == "column-C1"
    assert ref.metadata["formula_registry_version"] == "2026.08"


def test_engsketch_manifest_produces_version_and_hashed_artifact_refs():
    refs = engsketch_version_refs(
        "bridge-A",
        {
            "version": "v003",
            "timestamp": "2026-08-08T12:00:00Z",
            "parent_version": "v002",
            "checksum": "manifest-sha",
            "operation_summary": "move dimension",
            "schema_version": "1.0",
            "svg_sha256": "svg-sha",
            "png_sha256": "png-sha",
        },
    )
    assert [ref.kind for ref in refs] == [
        EvidenceKind.VERSION,
        EvidenceKind.ARTIFACT,
        EvidenceKind.ARTIFACT,
    ]
    assert refs[1].uri.endswith("/v003/output/drawing.svg")
    assert refs[2].checksum == "png-sha"


def test_bim_artifact_requires_hash_path_and_type():
    ref = bim_forge_artifact_ref(
        {
            "artifact_id": "ifc:2N$abc",
            "artifact_type": "ifc",
            "path": "out/model.ifc",
            "sha256": "ifc-sha",
        }
    )
    assert ref.system == "ai-bim-forge"
    assert ref.metadata["artifact_type"] == "ifc"
    with pytest.raises(ValueError):
        bim_forge_artifact_ref({"artifact_id": "ifc:x", "artifact_type": "ifc"})


def test_thread_links_cross_system_evidence_and_traces_deterministically():
    thread = DigitalThread()
    job = thread.add(EvidenceRef("ai-engineering-os", EvidenceKind.JOB, "job_1"))
    os_art = thread.add(
        EvidenceRef("ai-engineering-os", EvidenceKind.ARTIFACT, "art_1", checksum="os-sha")
    )
    forge = thread.add(
        EvidenceRef("ai-civildesign-forge", EvidenceKind.ARTIFACT, "forge-art", checksum="forge-sha")
    )
    thread.link(os_art, RelationKind.BELONGS_TO_JOB, job)
    thread.link(os_art, RelationKind.DERIVED_FROM, forge)

    links = thread.trace_from(os_art.key)
    assert [(link.relation, link.target) for link in links] == [
        (RelationKind.BELONGS_TO_JOB, job.key),
        (RelationKind.DERIVED_FROM, forge.key),
    ]
    payload = thread.to_dict()
    assert payload["schema_version"] == "openworker-digital-thread/1.0.0"
    assert [item["identifier"] for item in payload["evidence"]] == ["forge-art", "art_1", "job_1"]


def test_thread_rejects_conflicting_identity_and_unknown_link_endpoint():
    thread = DigitalThread()
    first = thread.add(EvidenceRef("system", EvidenceKind.ARTIFACT, "a", checksum="one"))
    with pytest.raises(ValueError):
        thread.add(EvidenceRef("system", EvidenceKind.ARTIFACT, "a", checksum="two"))
    with pytest.raises(KeyError):
        thread.link(first, RelationKind.DERIVED_FROM, "system:artifact:missing")


def test_add_all_registers_refs_once_and_duplicate_identical_ref_is_idempotent():
    thread = DigitalThread()
    refs = [
        EvidenceRef("system", EvidenceKind.VERSION, "v1"),
        EvidenceRef("system", EvidenceKind.ARTIFACT, "a1", checksum="sha"),
    ]
    add_all(thread, refs)
    thread.add(refs[0])
    assert len(thread.refs()) == 2


def test_blank_authoritative_fields_fail_closed():
    with pytest.raises(ValueError):
        os_job_ref({"id": ""})
    with pytest.raises(ValueError):
        os_artifact_ref(
            {
                "id": "art",
                "checksum": "",
                "uri": "x",
                "media_type": "application/json",
            }
        )
