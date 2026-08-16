# OpenWorker 工程顧問版架構

## 一、核心架構

OpenWorker 工程版採四層責任分離：

```text
[Layer 1] OpenWorker Agent Layer
  Engineering Coworker / Approval / Connectors / MCP / Conversation

[Layer 2] Engineering Control Plane
  AI-Engineering-OS
  Project / Job / Workflow / Artifact / Review / Approval / Delivery

[Layer 3] Specialist Engineering Engines
  Design / Drawing / BIM / Quantity / Budget / Schedule / CAD / PDF / Media

[Layer 4] Knowledge & Evidence Layer
  KnowGraphGo + Calculation Trace + Provenance + Checksum + Revision
```

這四層不得互相越權。

## 二、Layer 1：OpenWorker

OpenWorker 負責：

- 理解使用者要求。
- 將自然語言轉成工程工作意圖。
- 建立可視 Todo 與任務步驟。
- 判斷需要哪些工程能力。
- 執行 read-only 查詢。
- 呼叫 Engineering Adapter。
- 顯示執行進度與成果。
- 對提交、發布、核准、刪除、覆寫等副作用要求人工批准。

OpenWorker 不負責：

- 工程公式。
- 工程量計算規則。
- IFC 幾何算法。
- PCCES 單價邏輯。
- CPM 核心算法。
- 工程成果的最終專業核准。

## 三、Layer 2：AI-Engineering-OS

AI-Engineering-OS 已經具備正式的工程 Job 與 Delivery 模型，因此 OpenWorker 應把它視為工程控制平面。

建議正式資料流：

```text
使用者：「幫我做這座 RC 橋墩的設計、圖、數量與預算」
  ↓
Engineering Coworker
  ↓
engineering_create_job
  ↓
AI-Engineering-OS 建立 Project / Job / Workflow
  ↓
依 Workflow 調用專業 Engine
  ↓
Artifact / Trace / Review 寫回 OS
  ↓
OpenWorker 顯示成果與需要人工決策的位置
  ↓
Approval
  ↓
AI-Engineering-OS 發布 Delivery Revision
```

OpenWorker 不建立第二個 Project／Job／Artifact DB。

## 四、Layer 3：專業工程 Engine

### 設計計算

`AI-CivilDesign-Forge`

輸入：Engineering IR／Tool Input／ESM Adapter。

輸出：設計結果、Formula Registry 引用、Calculation Trace、JSON／SVG／HTML Artifact。

### 圖面

`AI-EngSketch`

輸入：Engineering Model／Sketch Markdown／Patch。

輸出：SVG、PNG、版本 Manifest、Diff。

### CAD 語意化

`DWG_todo`

輸入：DWG／DXF。

輸出：Engineering Semantic Model、Knowledge Graph 關聯、glTF／GLB、CAD trace。

### PDF 圖說重建

`go-pdf-drawing-reconstructor`

輸入：PDF／掃描圖說。

輸出：Engineering IR／ESM，供下游設計、BIM、數量與圖面使用。

### BIM

`AI-BIM-Forge`

輸入：ESM。

輸出：IFC、Audit、Quantity、Round-trip 驗證。

### Quantity

`AI-CivilQuantity`

輸入：Engineering IR／ESM／IFC／Design Result／人工輸入 + Knowledge Snapshot。

輸出：Quantity Revision、Calculation Run／Step、Lineage、PCCES／WBS／Schedule Mapping。

### PCCES

`pcces-web`

輸入：核准數量、工項、資源、單價與契約資料。

輸出：MRS、單價分析、預算、契約、估驗、結算、報表。

### Schedule

`AI-CivilSchedule`

輸入：WBS、Quantity、Productivity、Calendar、Dependencies。

輸出：CPM／PERT、關鍵路徑、Float、甘特與網圖、Baseline／Actual。

### Media

`SceneX`、`ComfyX`

輸入：工程成果與場景資料。

輸出：2D／3D 展示、動畫與多媒體成果。

## 五、Layer 4：Knowledge / Evidence

`KnowGraphGo` 不只是搜尋庫，而是全平台的知識與證據層。

至少保存：

- Ontology
- Engineering Entity / Relation
- Provenance
- Evidence
- Formula / Rule / Technique / Tool Metadata
- Inference
- Explain
- Cross-repository stable IDs

正式工程成果必須同時保存「專業 Engine Trace」與「知識 Evidence」。

## 六、統一 Engineering Adapter Contract

OpenWorker 只認統一的工程能力，不應直接知道每個 repo 的內部 package。

建議抽象：

```text
EngineeringCapability
- id
- domain
- description
- readiness
- transport
- endpoint
- version
- destructive_level
- requires_approval

EngineeringRequest
- project_id
- job_id
- capability
- input_artifacts
- parameters
- knowledge_snapshot

EngineeringResult
- status
- artifacts
- trace_ids
- warnings
- evidence
- engine_version
- checksum
```

Transport 可為：

- AI-Engineering-OS Gateway
- HTTP
- MCP
- CLI
- Local Process
- Python Worker
- Go Library（僅同程序情境）

## 七、Readiness 模型

每個能力必須明確回報成熟度，不可讓 Agent 把「存在 repo」誤認成「可以正式使用」。

建議狀態：

```text
UNAVAILABLE
DOCUMENTATION_ONLY
EXPERIMENTAL
IMPLEMENTED
VERIFIED
PRODUCTION_READY
BLOCKED
```

例如目前：

- AI-CivilDesign-Forge：IMPLEMENTED，部分構件尚未 M4/M5。
- AI-EngSketch：IMPLEMENTED。
- AI-BIM-Forge：IMPLEMENTED，最終完整驗證仍應持續。
- AI-CivilQuantity：DOCUMENTATION_ONLY / EARLY IMPLEMENTATION，依實際程式碼更新。
- pcces-web：IMPLEMENTED / VERIFIED，大部分完成，Final CI Evidence pending。
- AI-CivilSchedule：DOCUMENTATION_ONLY / INITIALIZING。
- KnowGraphGo：IMPLEMENTED，Phase 1/2 已完成。

## 八、Approval 分級

### Level 0：自動

- 查詢知識。
- 讀檔。
- 列出專案／Job／Artifact。
- Health check。
- 產生草稿與分析。

### Level 1：可自動但需留下 Audit

- 觸發可重算、非破壞性計算。
- 建立暫存 Artifact。
- 生成 Preview。

### Level 2：必須人工批准

- 建立正式 Revision。
- 覆寫既有工程輸入。
- 提交 Review。
- 修改 Baseline。
- 對外發布成果。

### Level 3：高風險，必須二次確認／專業審核

- 正式工程核准。
- 刪除正式資料。
- 修改已發布成果。
- 可能影響契約、付款、估驗或施工依據的操作。

## 九、Artifact 與 Trace

OpenWorker 顯示成果時，不只顯示檔案，而需顯示：

```text
Artifact
├─ artifact_id
├─ revision
├─ source_job
├─ engine
├─ engine_version
├─ input_revision
├─ knowledge_snapshot
├─ calculation_trace
├─ evidence
├─ checksum
├─ review_status
├─ approval_status
└─ delivery_status
```

這會讓 Engineering Coworker 從一般「會叫工具的 Agent」升級成真正可以管理工程 Digital Thread 的 AI 員工。
