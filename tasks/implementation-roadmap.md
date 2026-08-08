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

### 已完成

- E0 工程版定位與中文架構文件。
- Engineering Coworker Persona 基礎。
- `coworker.engineering` Adapter Protocol 基礎。
- Adapter Registry 最小註冊／查詢能力。
- GitHub 工程專案盤點與責任邊界。
- upstream 同步策略。

### 尚未完成

- Capability Registry 完整 metadata 契約。
- Adapter readiness / health / version / approval 模型。
- AI-Engineering-OS Tool Bridge。
- Engineering Tool Facade 與 Persona 實際工具掛載。
- 專業 Engine direct adapters。
- Digital Thread / Artifact provenance 對接。
- Golden Job E2E。
- Media / SceneX / ComfyX 交付鏈。

## P0 / P1 缺口

### P0

1. **能力發現不足**：目前 Registry 只能依名稱與 capability 找 adapter，無法可靠表達 transport、版本、readiness 與 approval 要求。
2. **健康狀態契約不足**：`health()` 只回傳任意 dict，調度層無法安全判定 ready / degraded / unavailable。
3. **正式控制平面尚未連接**：Engineering Coworker 尚不能透過 AI-Engineering-OS 建立／查詢 Job。
4. **Persona 尚未有工程 Tool Facade**：工程 Persona 雖存在，但還沒有正式工程工具閉環。

### P1

- 專業 Engine direct adapter 尚未建立。
- Artifact lineage / provenance 尚未統一。
- approval metadata 尚未落入工具層。
- Golden Job 與完整 E2E 尚未建立。

## Segment 順序

### Segment E1 — Capability Registry / Readiness Contract

**目標**：關閉工程 Adapter 可發現性、健康狀態、版本與批准 metadata 缺口。

**範圍**：

- `coworker/engineering/adapters.py`
- `coworker/engineering/__init__.py`
- `tests/test_engineering_adapters.py`
- 必要中文文件同步

**禁止範圍**：

- 不呼叫 AI-Engineering-OS。
- 不修改 `engine.py`。
- 不把專業 repo 程式碼複製進 OpenWorker。

**驗收標準**：

- Adapter descriptor 有穩定 schema。
- Health status 為 typed contract。
- Registry 可輸出 deterministic capability inventory。
- Registry 可判斷 ready adapters。
- duplicate / invalid descriptor 有永久回歸測試。
- 舊版最小 Adapter Protocol 相容或有明確 migration path。

### Segment E2 — AI-Engineering-OS Tool Bridge

**目標**：建立 OpenWorker → AI-Engineering-OS 的正式控制平面橋接。

**範圍**：

- 設定與 endpoint contract。
- health / version / capabilities。
- Project / Job 查詢與 Job 建立最小閉環。
- timeout / transport error / invalid response。
- 永久測試（以 fake transport / mock server 為主）。

**禁止範圍**：

- 不直接實作 Design / BIM / Quantity 等專業算法。

### Segment E3 — Engineering Tool Facade

**目標**：讓 Engineering Coworker 可透過 OpenWorker Tool 介面安全操作工程控制平面。

**範圍**：

- list capabilities
- system readiness
- list/get projects
- list/get/create jobs
- approval classification
- Persona tool wiring

### Segment E4 — Direct Specialist Adapters

優先順序：

1. AI-CivilDesign-Forge
2. AI-EngSketch
3. AI-BIM-Forge
4. KnowGraphGo
5. pcces-web
6. AI-CivilQuantity
7. AI-CivilSchedule
8. DWG_todo / PDF reconstruction

Direct adapter 只作為控制平面之外的受控專業能力入口，不取代 AI-Engineering-OS 的 Job / Delivery 權威。

### Segment E5 — Digital Thread / Artifact Provenance

建立 Requirement → Job → Workflow → Engine → Artifact → Review → Approval → Delivery 的跨系統追溯契約。

### Segment E6 — Golden Job

第一條正式閉環：

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

接入 SceneX / ComfyX 等展示能力，並擴充公司級工程 Coworker 工作流。

## 技術債

- 目前工程 extension 尚未接入 OpenWorker Tool runtime。
- 初始 Adapter Protocol 的 `health()` / `invoke()` 型別過寬。
- 尚無 adapter config persistence。
- 尚無 transport abstraction。
- 尚無工程專用 audit event schema。

## 驗證原則

每個 Segment 必須：

- Production Code 完成。
- 永久 Regression Tests 完成。
- 自我 Code Review 完成。
- 可執行的 unit tests / static checks 通過。
- 無法在 ChatGPT 環境完整執行者，標記 `IMPLEMENTED — WAITING FOR FULL VERIFICATION`，不得聲稱 VERIFIED。
- 每 Segment 獨立 Commit / Push。

## 上下文接續點

只在完整 Segment 邊界停下。下一 Segment 尚未開始時才允許建立跨對話接續摘要。
