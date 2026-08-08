# OpenWorker 工程版獨立分段開發 Roadmap

更新日期：2026-08-08

## 專案定位

OpenWorker 工程版是 AI 工程顧問公司的 AI 員工與自然語言操作層。

```text
OpenWorker
= AI Coworker / Persona / Tools / Permissions / Approval / Connectors / MCP
        ↓
AI-Engineering-OS
= Project / Job / Workflow / Artifact / Review / Approval / Delivery
        ↓
專業工程 Engines
= Design / Drawing / BIM / Quantity / PCCES / Schedule / CAD / PDF / Media
        ↓
KnowGraphGo
= Knowledge / Evidence / Inference / Explain
```

不得在 OpenWorker 內複製第二套工程公式、工程 Job 控制平面或專業 Engine 實作。

## 目前完成度

- E0 工程版定位與中文架構文件：`IMPLEMENTED`。
- E1 Capability Registry / Readiness Contract：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`。
- E2 AI-Engineering-OS Tool Bridge：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`。
- E3 Engineering Tool Facade + Persona Wiring：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`。
- E4 Direct Specialist Adapters：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`。
- E5 Digital Thread / Artifact Provenance：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`。
- E6 Golden Job：`NOT_STARTED`。
- E7 Media / Company Coworker：`NOT_STARTED`。

## E1～E3 已完成內容

- Typed Adapter descriptor / health / readiness contract。
- AI-Engineering-OS health、modules、Project、Job Bridge。
- Engineering Tool Facade 與 Persona wiring。
- `engineering_create_job` 沿用 OpenWorker Permission / Approval gate。

## E4 已完成內容

第一批 Direct Specialist Adapters：

1. `DesignForgeAdapter`：`civilforge-tool` / `tool-protocol/1.0.0`。
2. `EngSketchAdapter`：DraftForge CLI allowlist。
3. `BIMForgeAdapter`：lazy Python canonical API。
4. `KnowGraphAdapter`：KnowGraphGo CLI / DSN fail-closed。

共同安全契約：argv list、`shell=False`、operation allowlist、timeout / exit-code / JSON validation，且 Direct Adapter 不取代 AI-Engineering-OS lifecycle 權威。

## E5 已完成內容

新增 `coworker/engineering/digital_thread.py`：

- `EvidenceKind`
- `RelationKind`
- `EvidenceRef`
- `ProvenanceLink`
- `DigitalThread`
- deterministic serialization：`openworker-digital-thread/1.0.0`
- conflicting identity fail-closed
- unknown provenance endpoint fail-closed
- identical EvidenceRef idempotency
- breadth-first provenance tracing

來源映射：

- `os_job_ref()`：AI-Engineering-OS Job identity / revision / status / dirs。
- `os_artifact_ref()`：AI-Engineering-OS Artifact / revision / checksum / source_run_id。
- `design_forge_artifact_ref()`：CalculationRun / semantic_id / engine / formula registry / SHA256。
- `engsketch_version_refs()`：version manifest + SVG / PNG hash references。
- `bim_forge_artifact_ref()`：AI-BIM-Forge Tool Protocol ArtifactRef。

E5 原則：只引用來源系統權威身份，不建立第二套 Artifact Store、不重新計算 checksum、不自行推斷 lineage。

永久測試：`tests/test_engineering_digital_thread.py`。
中文規格：`docs/engineering/digital-thread.zh-TW.md`。

## 目前 P0 / P1

### P0

1. **E1～E5 尚待完整 repository 驗證**：需要完整 checkout + dependencies 執行 pytest / compileall / diff check。
2. **Golden Job 尚未完成**：目前已有控制平面、Tool、Specialist Adapter 與 Digital Thread，但尚未組成一條可驗收 RC 柱端到端流程。

### P1

- pcces-web / AI-CivilQuantity / AI-CivilSchedule / DWG/PDF adapters 尚未進入第二批。
- adapter config persistence 尚未建立。
- 專業 Engine audit event schema 尚未建立。
- Digital Thread 尚未持久化至 AI-Engineering-OS；E5 第一版僅提供 OpenWorker 端 deterministic reference graph。

## Segment E1 — Capability Registry / Readiness Contract

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

## Segment E2 — AI-Engineering-OS Tool Bridge

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

## Segment E3 — Engineering Tool Facade + Persona Wiring

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

## Segment E4 — Direct Specialist Adapters

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

第二批 specialist integrations（P1）：pcces-web → AI-CivilQuantity → AI-CivilSchedule → DWG_todo / PDF reconstruction。

## Segment E5 — Digital Thread / Artifact Provenance

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

**驗收**：

- [x] AI-Engineering-OS Job identity 可轉為 EvidenceRef。
- [x] AI-Engineering-OS Artifact identity / checksum / source_run_id 可保留。
- [x] Design Forge Artifact / CalculationRun / Semantic ID / versions 可保留。
- [x] EngSketch immutable version / parent / SVG / PNG checksum 可引用。
- [x] BIM Forge ArtifactRef 可引用。
- [x] cross-system provenance relation schema。
- [x] deterministic serialization。
- [x] identity conflict / unknown endpoint fail-closed。
- [x] 永久 regression tests。
- [x] 中文規格。
- [ ] 完整 checkout pytest / compileall / diff check。

## Segment E6 — Golden Job

**狀態**：`NOT_STARTED`

```text
Engineering Coworker
→ 建立 RC 柱設計 Job
→ AI-Engineering-OS
→ AI-CivilDesign-Forge
→ AI-EngSketch
→ AI-BIM-Forge
→ Digital Thread
→ Review / Approval
→ Delivery
→ OpenWorker 回傳正式成果與追溯資訊
```

E6 必須使用真實 Project / Job / Artifact identity，不得用 hard-coded 假 ID 冒充端到端完成。

## Segment E7 — Media / Company Coworker

**狀態**：`NOT_STARTED`

接入 SceneX / ComfyX 等展示能力，並擴充公司級工程 Coworker 工作流。

## 驗證原則

每個 Segment 必須：Production Code、永久 Regression Tests、自我 Code Review、可執行靜態/單元驗證、Commit/Push 均完成。無法完整執行者維持 `IMPLEMENTED — WAITING FOR FULL VERIFICATION`，不得聲稱 `VERIFIED`。
