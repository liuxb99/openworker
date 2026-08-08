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

### 已完成／已實作

- E0 工程版定位與中文架構文件：`IMPLEMENTED`。
- Engineering Coworker Persona 基礎：`IMPLEMENTED`。
- Adapter Protocol / Registry 基礎：`IMPLEMENTED`。
- GitHub 工程專案盤點與責任邊界：`IMPLEMENTED`。
- upstream 同步策略：`IMPLEMENTED`。
- E1 Capability Registry / Readiness Contract：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`。
- E2 AI-Engineering-OS Tool Bridge：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`。

### E1 已完成內容

- `AdapterDescriptor`：name、capabilities、transport、version、approval policy、operations、metadata。
- `HealthStatus` / `HealthReport` typed readiness contract。
- 舊版 `{"ok": bool}` health payload 相容轉換。
- health probe exception containment。
- deterministic capability inventory。
- ready adapter 過濾與 capability selection。
- descriptor/name/capability consistency validation。
- 永久 regression tests。

### E2 已完成內容

- `EngineeringOSConfig` 與 base URL / timeout 驗證。
- stdlib `urllib` Production transport。
- injectable transport protocol。
- `/healthz` 與 `/readyz` typed readiness。
- `/api/v1/system/modules` schema version 與 capability discovery。
- Project list/get。
- Job list/get/create。
- AI-Engineering-OS `job.CreateInput` payload 對齊。
- timeout / transport / HTTP / contract error 分類。
- path injection 與空白必填欄位 fail-closed。
- fake transport 與 urllib failure 永久 regression tests。
- 中文 Bridge 契約文件。

### 驗證狀態

```text
E1 代表性 Contract Tests：PASS（ChatGPT 隔離 Python 環境）
E1 完整 repository pytest：NOT RUN（執行環境無法解析 github.com，無法 clone branch）
E2 自我 Code Review：PASS，並修正 EngineeringCapability 錯誤 import
E2 完整 repository pytest：NOT RUN（同一 checkout 限制）
compileall：NOT RUN against full checkout
GitHub branch diff：可讀取，僅工程 extension / tests / docs / roadmap
狀態：E1 / E2 均為 IMPLEMENTED — WAITING FOR FULL VERIFICATION
```

完整驗證成功前不得把 E1 或 E2 標為 `VERIFIED`。

## 尚未完成

- E3 Engineering Tool Facade 與 Persona 實際工具掛載。
- E4 專業 Engine direct adapters。
- E5 Digital Thread / Artifact provenance。
- E6 Golden Job E2E。
- E7 Media / SceneX / ComfyX 交付鏈與公司級 Coworker。

## P0 / P1 缺口

### P0

1. **Persona 尚未有工程 Tool Facade**：Bridge 已完成，但 Engineering Coworker 尚不能透過 OpenWorker 正式 Tool surface 呼叫它。
2. **E1 / E2 尚待完整 repo 驗證**：需在可取得完整 checkout 的環境執行 pytest / compileall / diff check。

### P1

- 專業 Engine direct adapter 尚未建立。
- Artifact lineage / provenance 尚未統一。
- approval metadata 尚未落入 OpenWorker Tool 執行層。
- Golden Job 與完整 E2E 尚未建立。

## Segment 順序

### Segment E1 — Capability Registry / Readiness Contract

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

**驗收標準**：

- [x] Adapter descriptor 有穩定 schema。
- [x] Health status 為 typed contract。
- [x] Registry 可輸出 deterministic capability inventory。
- [x] Registry 可判斷 ready adapters。
- [x] duplicate / invalid descriptor 有永久回歸測試。
- [x] 舊版最小 Adapter Protocol 保持相容。
- [ ] 完整 checkout 執行正式 pytest / compileall / git diff --check。

### Segment E2 — AI-Engineering-OS Tool Bridge

**狀態**：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

**目標**：建立 OpenWorker → AI-Engineering-OS 的正式控制平面橋接。

**驗收標準**：

- [x] 設定與 endpoint contract。
- [x] health / readiness。
- [x] schema version / module capabilities。
- [x] Project list/get。
- [x] Job list/get/create。
- [x] timeout / transport / HTTP / invalid JSON / invalid shape 處理。
- [x] injectable transport 與永久 regression tests。
- [x] 未修改 `engine.py` 或複製專業算法。
- [ ] 完整 checkout 執行正式 pytest / compileall / git diff --check。

### Segment E3 — Engineering Tool Facade

**狀態**：`NOT_STARTED`

讓 Engineering Coworker 可透過 OpenWorker Tool 介面安全操作工程控制平面：list capabilities、system readiness、Project／Job 查詢與 Job 建立、approval classification、Persona tool wiring。

### Segment E4 — Direct Specialist Adapters

**狀態**：`NOT_STARTED`

優先順序：AI-CivilDesign-Forge → AI-EngSketch → AI-BIM-Forge → KnowGraphGo → pcces-web → AI-CivilQuantity → AI-CivilSchedule → DWG_todo / PDF reconstruction。

Direct adapter 不取代 AI-Engineering-OS 的 Job / Delivery 權威。

### Segment E5 — Digital Thread / Artifact Provenance

**狀態**：`NOT_STARTED`

建立 Requirement → Job → Workflow → Engine → Artifact → Review → Approval → Delivery 的跨系統追溯契約。

### Segment E6 — Golden Job

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

### Segment E7 — Media / Company Coworker

**狀態**：`NOT_STARTED`

接入 SceneX / ComfyX 等展示能力，並擴充公司級工程 Coworker 工作流。

## 技術債

- 工程 extension 尚未接入 OpenWorker Tool runtime。
- `invoke()` 回傳仍為寬型別，後續由 Tool Facade / operation contracts 繼續收斂。
- 尚無 adapter config persistence。
- 尚無工程專用 audit event schema。

## 驗證原則

每個 Segment 必須：

- Production Code 完成。
- 永久 Regression Tests 完成。
- 自我 Code Review 完成。
- 可執行的 unit tests / static checks 通過。
- 無法在 ChatGPT 環境完整執行者，標記 `IMPLEMENTED — WAITING FOR FULL VERIFICATION`，不得聲稱 VERIFIED。
- 每 Segment Commit / Push 並保持清楚邊界。

## 上下文接續點

只在完整 Segment 邊界停下。下一 Segment 尚未開始時才允許建立跨對話接續摘要。
