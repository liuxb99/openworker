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
- E4 Direct Specialist Adapters：`NOT_STARTED`。
- E5 Digital Thread / Artifact Provenance：`NOT_STARTED`。
- E6 Golden Job：`NOT_STARTED`。
- E7 Media / Company Coworker：`NOT_STARTED`。

## E1 完成內容

- `AdapterDescriptor`、`HealthStatus`、`HealthReport`、`ApprovalPolicy`。
- legacy health 相容、exception containment、deterministic inventory、ready adapter filtering。
- descriptor/name/capability consistency validation 與永久 regression tests。

## E2 完成內容

- `EngineeringOSConfig`、stdlib HTTP transport、injectable transport。
- health / readiness / system modules / schema version / capability discovery。
- Project list/get。
- Job list/get/create。
- timeout / transport / HTTP / contract error 分類。
- path injection 與 payload fail-closed。
- Bridge 中文規格與永久 regression tests。

## E3 完成內容

- `coworker/engineering/tools.py` Tool Facade。
- `engineering_system_readiness`。
- `engineering_list_projects` / `engineering_get_project`。
- `engineering_list_jobs` / `engineering_get_job`。
- `engineering_create_job`。
- 唯讀工具 `requires_approval=False`。
- `engineering_create_job` `requires_approval=True`，沿用 OpenWorker 標準 `RiskClass.EXTERNAL` / Approval gate。
- `engineering_os` 正式加入 platform-owned Catalog。
- Engineering persona frontmatter 加入 `engineering_os` capability。
- Persona prompt 明確規定 Project / Job ID 與狀態不得虛構。
- Tool Facade 與 Persona wiring 永久 regression tests。
- 中文 `engineering-tool-facade.zh-TW.md`。

## 目前 P0 / P1

### P0

1. **E1～E3 尚待完整 repository 驗證**：需要完整 checkout 執行 pytest / compileall / diff check。
2. **尚無專業 Engine direct adapter**：目前 Engineering Coworker 能操作控制平面，但還不能在需要時直接探測或調用獨立專業 Engine。

### P1

- Artifact lineage / provenance 尚未統一。
- Golden Job 與完整 E2E 尚未建立。
- adapter endpoint/config persistence 尚未建立。
- 專業 Engine audit event schema 尚未建立。

## Segment E1 — Capability Registry / Readiness Contract

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

- [x] Typed descriptor / health。
- [x] deterministic inventory / ready filtering。
- [x] legacy compatibility / permanent tests。
- [ ] 完整 checkout pytest / compileall / diff check。

## Segment E2 — AI-Engineering-OS Tool Bridge

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

- [x] health / readiness / modules。
- [x] Project list/get。
- [x] Job list/get/create。
- [x] transport / timeout / HTTP / contract errors。
- [x] 永久 tests 與中文規格。
- [ ] 完整 checkout pytest / compileall / diff check。

## Segment E3 — Engineering Tool Facade + Persona Wiring

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

**目標**：讓 Engineering Coworker 透過 OpenWorker 原生 Tool / Permission / Approval 架構操作 AI-Engineering-OS。

**驗收**：

- [x] platform catalog 有 `engineering_os` capability。
- [x] Engineering persona 宣告該 capability。
- [x] readiness / Project / Job 唯讀工具。
- [x] create Job 工具。
- [x] read tools 不要求 approval。
- [x] create Job 必須走 approval。
- [x] 不修改 `engine.py` 做 engineering 特例。
- [x] 永久 Tool / Persona wiring tests。
- [x] 中文規格。
- [ ] 完整 checkout pytest / compileall / diff check。

## Segment E4 — Direct Specialist Adapters

**狀態**：`NOT_STARTED`

**目標**：建立受控的專業 Engine direct adapters，用於 readiness、能力探測與控制平面之外的明確專業操作；不得取代 AI-Engineering-OS 的 Job / Delivery 權威。

優先順序：

1. AI-CivilDesign-Forge
2. AI-EngSketch
3. AI-BIM-Forge
4. KnowGraphGo
5. pcces-web
6. AI-CivilQuantity
7. AI-CivilSchedule
8. DWG_todo / PDF reconstruction

## Segment E5 — Digital Thread / Artifact Provenance

**狀態**：`NOT_STARTED`

建立 Requirement → Job → Workflow → Engine → Artifact → Review → Approval → Delivery 的跨系統追溯契約。

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
