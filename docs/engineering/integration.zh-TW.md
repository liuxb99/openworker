# OpenWorker 工程能力整合策略

## 一、整合總原則

OpenWorker 不直接綁死任何單一專業 repo，而是透過 Engineering Adapter Registry 對外暴露穩定能力。

優先級如下：

```text
第一優先：OpenWorker → AI-Engineering-OS Gateway
第二優先：OpenWorker → 專業 Engine Tool / HTTP / MCP
第三優先：OpenWorker → CLI / Local Process
最後手段：直接 Python / Go Library 嵌入
```

原因：AI-Engineering-OS 已經統一管理 Job、Workflow、Artifact、Review、Approval、Delivery；若 OpenWorker 對所有專業 repo 都直接操作，會產生第二套控制平面。

## 二、第一批應接的能力

### A. AI-Engineering-OS Adapter

首批功能：

- create_project
- create_job
- get_job
- list_workflows
- run_workflow
- list_artifacts
- get_artifact
- request_review
- approve_revision
- publish_delivery
- get_delivery_manifest

正式發布與核准動作必須要求 Approval Gate。

### B. KnowGraphGo Adapter

首批功能：

- query_entity
- find_related
- find_path
- explain_relation
- explain_inference
- resolve_rule
- get_evidence

初期可使用 CLI 或 Library bridge；若 AI-Engineering-OS 已提供 Gateway，優先透過 Gateway。

### C. AI-CivilDesign-Forge Adapter

首批功能：

- list_component_types
- validate_input
- compute
- get_calculation_trace
- render_svg
- render_report

OpenWorker 必須顯示構件成熟度，不能把 M2／M3 結果包裝成已完成 M4/M5 專業驗證。

### D. AI-EngSketch Adapter

首批功能：

- generate_drawing
- validate_model
- render_png
- propose_patch
- apply_patch
- diff_versions

Patch apply 若會建立正式版本，至少列為 Approval Level 2。

### E. pcces-web Adapter

首批功能：

- map_quantity_to_item
- get_mrs
- calculate_unit_price
- get_budget
- get_contract
- get_estimate
- generate_report

牽涉契約、估驗、付款或正式預算 Revision 的操作必須提高 Approval 等級。

## 三、第二批能力

### AI-BIM-Forge

- build_ifc
- audit_ifc
- reopen_and_audit
- get_element_quantities

### DWG_todo

- import_dwg
- import_dxf
- analyze_drawing
- build_semantic_model
- query_semantic_object
- export_gltf

### go-pdf-drawing-reconstructor

- import_pdf
- reconstruct_drawing
- export_engineering_ir
- export_esm

這三者組成主要 ingestion pipeline：

```text
PDF / DWG / DXF
  ↓
Engineering IR / ESM
  ↓
Knowledge Graph
  ↓
Design / Drawing / BIM / Quantity
```

## 四、第三批能力

### AI-CivilQuantity

待 Production Code 與契約成熟後再升級為正式 Adapter。目前應先支持 capability discovery 與 readiness reporting，避免 Agent 誤用未完成能力。

### AI-CivilSchedule

同理，先整合資料契約與 readiness，等 CPM 核心與永久測試完成後再開啟正式 run capability。

### SceneX / ComfyX

放在核心工程成果完成之後，用於：

- 工程 2D／3D 展示
- 施工模擬
- 工程解說影片
- 成果動畫

媒體輸出不能成為工程計算的權威來源。

## 五、統一 Transport 設計

Adapter 應至少支援：

```text
transport = gateway | http | mcp | cli | local_process | library
```

每個 Adapter 必須提供：

- health()
- capabilities()
- version()
- invoke()
- normalize_result()

不得讓 Persona 直接拼接 shell 命令。

## 六、錯誤與降級原則

若專業 Engine 不可用：

1. 明確回報 Engine 名稱與 readiness。
2. 不得靜默改用 LLM 猜工程答案。
3. 可提供「只分析、不計算」模式。
4. 若有替代 Engine，必須明確標示不是權威來源。
5. 所有 fallback 都要寫入 Audit Trace。

## 七、最終目標

使用者只需要說：

> 幫我把這份圖做成可交付的工程成果。

Engineering Coworker 就能：

```text
建立 Job
→ 判斷輸入類型
→ PDF/DWG ingestion
→ 建 ESM
→ 查 Knowledge Graph
→ 設計計算
→ 畫工程圖
→ BIM
→ Quantity
→ PCCES
→ Schedule
→ Review
→ Approval
→ Delivery
```

但每一步都由權威專業 Engine 執行，OpenWorker 只做理解、編排、工具調用、權限與交付協調。