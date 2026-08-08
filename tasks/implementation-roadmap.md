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
- E5 Digital Thread / Artifact Provenance：`NOT_STARTED`。
- E6 Golden Job：`NOT_STARTED`。
- E7 Media / Company Coworker：`NOT_STARTED`。

## E1～E3 已完成內容

- Typed Adapter descriptor / health / readiness contract。
- AI-Engineering-OS health、modules、Project、Job Bridge。
- Engineering Tool Facade 與 Persona wiring。
- `engineering_create_job` 沿用 OpenWorker Permission / Approval gate。

## E4 已完成內容

第一批 Direct Specialist Adapters：

1. `DesignForgeAdapter`
   - 權威來源：`AI-CivilDesign-Forge`
   - transport：`civilforge-tool` machine-readable CLI
   - protocol：`tool-protocol/1.0.0`
   - operations：`capabilities`、`execute`
   - capabilities：`structural`、`reporting`

2. `EngSketchAdapter`
   - 權威來源：`AI-EngSketch`
   - transport：`draftforge-cli`
   - operations：`themes`、`validate`、`versions`
   - capabilities：`drawing`、`reporting`
   - E4 不開 generic shell / patch apply escape hatch

3. `BIMForgeAdapter`
   - 權威來源：`AI-BIM-Forge`
   - transport：lazy Python API `aibim.api`
   - canonical operations：`build_ifc_model`、`build_and_write_ifc`、`reopen_and_audit`、`get_element_quantities`
   - capabilities：`bim_ifc`、`quantity`

4. `KnowGraphAdapter`
   - 權威來源：`KnowGraphGo`
   - transport：`knowgraph` CLI
   - operations：`check`、`node_list`
   - capability：`knowledge_graph`
   - DSN 未配置時 fail-closed

共同安全契約：

- subprocess 使用 argv list，不透過 shell。
- operation allowlist，不接受任意 command string。
- timeout、exit code、JSON shape 明確處理。
- Direct Adapter 不取代 AI-Engineering-OS 的 Project / Job / Artifact / Delivery 權威。
- Adapter 可呼叫不代表自動暴露為 Agent Tool；mutating Tool 仍須顯式 approval classification。

永久測試：`tests/test_engineering_specialists.py`。
中文規格：`docs/engineering/direct-specialist-adapters.zh-TW.md`。

## 目前 P0 / P1

### P0

1. **E1～E4 尚待完整 repository 驗證**：需要完整 checkout + dependencies 執行 pytest / compileall / diff check。
2. **Digital Thread 尚未統一**：專業引擎輸出雖有各自 Artifact / Trace，但 OpenWorker 尚無統一 Requirement → Job → Engine → Artifact lineage contract。

### P1

- pcces-web / AI-CivilQuantity / AI-CivilSchedule / DWG/PDF adapters 尚未進入第二批。
- Golden Job 與完整 E2E 尚未建立。
- adapter config persistence 尚未建立。
- 專業 Engine audit event schema 尚未建立。

## Segment E1 — Capability Registry / Readiness Contract

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

## Segment E2 — AI-Engineering-OS Tool Bridge

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

## Segment E3 — Engineering Tool Facade + Persona Wiring

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

## Segment E4 — Direct Specialist Adapters

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

**驗收**：

- [x] AI-CivilDesign-Forge direct adapter。
- [x] AI-EngSketch direct adapter。
- [x] AI-BIM-Forge direct adapter。
- [x] KnowGraphGo direct adapter。
- [x] transport 依各 repo 真實契約選擇，不假設共同 HTTP API。
- [x] subprocess 無 shell、operation allowlist。
- [x] readiness fail-closed。
- [x] 永久 regression tests。
- [x] 中文規格。
- [ ] 完整 checkout pytest / compileall / diff check。

第二批 specialist integrations（P1）：pcces-web → AI-CivilQuantity → AI-CivilSchedule → DWG_todo / PDF reconstruction。

## Segment E5 — Digital Thread / Artifact Provenance

**狀態**：`NOT_STARTED`

建立 Requirement → Job → Workflow → Engine → Artifact → Review → Approval → Delivery 的跨系統追溯契約。優先統一 AI-CivilDesign-Forge Calculation Trace / artifact、EngSketch version manifest、AI-BIM-Forge IFC audit 與 AI-Engineering-OS Job/Artifact identity。

## Segment E6 — Golden Job

**狀態**：`NOT_STARTED`

```text
Engineering Coworker
→ 建立 RC 柱設計 Job
→ AI-Engineering-OS
→ AI-CivilDesign-Forge
→ AI-EngSketch
→ AI-BIM-Forge
→ Review / Approval
→ Delivery
→ OpenWorker 回傳正式成果與追溯資訊
```

## Segment E7 — Media / Company Coworker

**狀態**：`NOT_STARTED`

接入 SceneX / ComfyX 等展示能力，並擴充公司級工程 Coworker 工作流。

## 驗證原則

每個 Segment 必須：Production Code、永久 Regression Tests、自我 Code Review、可執行靜態/單元驗證、Commit/Push 均完成。無法完整執行者維持 `IMPLEMENTED — WAITING FOR FULL VERIFICATION`，不得聲稱 `VERIFIED`。
