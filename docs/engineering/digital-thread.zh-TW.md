# E5：Digital Thread / Artifact Provenance 中文規格

更新日期：2026-08-08

## 1. 目的

OpenWorker 工程版需要能回答：

- 這個成果屬於哪一個 Project / Job？
- 它由哪一個專業 Engine 產生？
- 它引用哪一次計算、哪個 Semantic ID、哪個版本？
- 前一版是什麼？
- 檔案內容是否可用 checksum 驗證？
- 這個成果是直接產生，還是由另一個成果衍生？

E5 不建立新的工程成果權威資料庫，而是把各來源系統已存在的身份與 checksum 以引用方式串成 Digital Thread。

## 2. 權威來源

### AI-Engineering-OS

Job 權威欄位：

- `id`
- `project_id`
- `code`
- `status`
- `revision`
- `working_dir`
- `delivery_dir`

Artifact 權威欄位：

- `id`
- `project_id`
- `job_id`
- `component_id`
- `kind`
- `revision`
- `uri`
- `media_type`
- `checksum`
- `source_run_id`

AI-Engineering-OS 仍是 Project / Job / Artifact lifecycle 的權威。

### AI-CivilDesign-Forge

Forge Artifact 契約包含：

- `artifact_id`
- `artifact_type`
- `schema_version`
- `calculation_run_id`
- `semantic_id`
- `ifc_guid`
- `path`
- `media_type`
- `sha256`
- `engine_version`
- `formula_registry_version`

同一 CalculationRun 的 JSON / SVG / HTML 不得各自重新計算。

### AI-EngSketch

Version manifest 包含：

- `version`
- `timestamp`
- `parent_version`
- `checksum`
- `operation_summary`
- `schema_version`
- `svg_sha256`
- `png_sha256`

OpenWorker 以版本身份與 hash 引用它，不取代 immutable version history。

### AI-BIM-Forge

Tool Protocol ArtifactRef 包含：

- `artifact_id`
- `artifact_type`
- `path`
- `sha256`

例如 IFC build 會產生 `ifc:<project_global_id>` 的 Artifact ID。

## 3. OpenWorker Digital Thread schema

目前版本：

```text
openworker-digital-thread/1.0.0
```

主要型別：

- `EvidenceRef`
- `ProvenanceLink`
- `DigitalThread`

`EvidenceRef` 不宣稱自己是來源 Artifact，而是對來源 Artifact / Job / Version 的不可變引用。

```text
system + kind + identifier + optional revision
```

共同 key：

```text
<system>:<kind>:<identifier>[@revision]
```

例如：

```text
ai-engineering-os:job:job_001@3
ai-engineering-os:artifact:art_001@2
ai-civildesign-forge:artifact:calculation:rc-column:column-C1@artifact/1.0.0
ai-engsketch:version:bridge-A:v003@v003
ai-bim-forge:artifact:ifc:2N$abc
```

## 4. Relation

E5 第一版定義：

- `produced_by`
- `derived_from`
- `belongs_to_job`
- `belongs_to_project`
- `represents`
- `supersedes`

關係只能連接已註冊的 EvidenceRef；未知 endpoint fail-closed。

## 5. 衝突與不可變性

如果相同 Digital Thread key 第二次加入完全相同 Reference，視為 idempotent。

如果相同 key 卻帶不同 checksum / metadata / URI，直接拒絕：

```text
conflicting evidence reference
```

OpenWorker 不自動猜哪一份是真的，也不覆蓋舊值。

## 6. Source adapters

`coworker/engineering/digital_thread.py` 提供：

- `os_job_ref()`
- `os_artifact_ref()`
- `design_forge_artifact_ref()`
- `engsketch_version_refs()`
- `bim_forge_artifact_ref()`

這些函式只做欄位映射與基本 fail-closed validation，不重新計算 checksum，也不改寫來源 Artifact。

## 7. 典型 RC 柱追溯

```text
AI-Engineering-OS Job
        ↑ belongs_to_job
AI-Engineering-OS Artifact
        ↓ derived_from
Design Forge calculation_trace
        ↓ derived_from / represents
EngSketch v003 / drawing.svg
        ↓ derived_from
BIM Forge IFC artifact
```

實際關係必須由執行時已有證據建立，不能因為『流程理論上應該如此』就自動填入。

## 8. 邊界

E5 不做：

- 不建立第二套 Artifact Store。
- 不修改來源 repo 的 Artifact ID。
- 不重新計算工程結果。
- 不推斷不存在的 parent / run / semantic identity。
- 不把 URI 當身份。
- 不因 path 相同就認定兩個 Artifact 相同。

## 9. 驗證

永久測試：

```text
tests/test_engineering_digital_thread.py
```

覆蓋：

- AI-Engineering-OS Job / Artifact 映射。
- Design Forge Calculation Trace / version metadata 映射。
- EngSketch version + SVG / PNG hash 引用。
- BIM Forge ArtifactRef 映射。
- cross-system provenance links。
- deterministic serialization。
- conflicting identity fail-closed。
- unknown link endpoint fail-closed。
- identical reference idempotency。

完整 repository pytest / compileall 仍須在已安裝 OpenWorker dependencies 的完整 checkout 執行。
