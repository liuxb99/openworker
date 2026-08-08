# OpenWorker 工程顧問版｜中文總覽

本目錄定義 `liuxb99/openworker` 作為 AI 工程顧問公司的 Agent／工作流／權限／Connector／MCP 前台時，如何與既有工程專案整合。

## 一、產品定位

`openworker` 不取代既有工程核心，也不重新實作工程公式。它負責：

- 以自然語言接受工程工作。
- 拆解任務、建立 Todo／Workflow。
- 調用專業工程引擎。
- 管理檔案、Connector、MCP、外部工具與本機服務。
- 在有副作用或涉及正式工程成果前設置 Approval Gate。
- 彙整成果、證據鏈與可交付 Artifact。

真正的專業計算、圖面、BIM、數量、預算、排程與知識仍由既有專案負責。

```text
使用者
  ↓
OpenWorker / Engineering Coworker
  ↓
Engineering Adapter Layer
  ↓
AI-Engineering-OS / 專業 Engine
  ├─ AI-CivilDesign-Forge
  ├─ AI-EngSketch
  ├─ AI-BIM-Forge
  ├─ AI-CivilQuantity
  ├─ pcces-web
  ├─ AI-CivilSchedule
  ├─ KnowGraphGo
  ├─ DWG_todo
  ├─ go-pdf-drawing-reconstructor
  ├─ SceneX
  └─ ComfyX
```

## 二、與 AI-Engineering-OS 的分工

`AI-Engineering-OS` 已經是本機工程顧問公司的正式整合與交付平台，負責 Project、Job、Workflow、Artifact、Review、Approval、Delivery、SQLite 與成果網站。

因此 `openworker` 不應再建立第二套工程專案資料庫或第二套工程工作單系統，而應把 AI-Engineering-OS 視為首要整合目標：

```text
OpenWorker = AI 員工與對話／操作層
AI-Engineering-OS = 工程作業與交付控制層
專業 Repo = 工程能力層
KnowGraphGo = 工程知識與證據層
```

首選架構是：OpenWorker 接收使用者任務後，優先呼叫 AI-Engineering-OS 的 Gateway／Tool／CLI 契約；只有在需要直接調用專業能力或開發測試時，才直接走各 Engine Adapter。

## 三、最高級原則

1. **不得複製工程公式**：公式只存在權威專業 Engine。
2. **不得繞過工程審批**：正式成果必須保留 Review／Approval。
3. **不得只保存最終數字**：需保存來源、版本、計算步驟、Evidence、Checksum。
4. **不得讓 LLM 取代決定性計算**：LLM 用於理解、規劃、映射與解釋；正式計算由 Engine 完成。
5. **OpenWorker Core 儘量少改**：工程能力以 Persona、Tool、MCP、HTTP、CLI、Adapter 擴充。
6. **優先接 AI-Engineering-OS**：避免 OpenWorker 與 AI-Engineering-OS 形成兩套互相競爭的 Workflow／Delivery 系統。
7. **所有副作用分類**：讀取、分析、草稿可自動；提交、發布、覆寫、刪除、正式核准必須走 Approval Gate。

## 四、工程能力分類

| 類別 | 權威專案 | OpenWorker 角色 |
|---|---|---|
| 工程工作／交付編排 | AI-Engineering-OS | 建 Job、查狀態、觸發 Workflow、讀 Artifact、送審 |
| 設計計算 | AI-CivilDesign-Forge | 準備輸入、觸發計算、解讀 Trace |
| 工程圖 | AI-EngSketch | 生成／修改圖面、讀版本與 Manifest |
| BIM / IFC | AI-BIM-Forge | ESM → IFC、Audit、Round-trip |
| 工程數量 | AI-CivilQuantity | Quantity Takeoff、Lineage、Revision |
| 預算／PCCES | pcces-web | 工項、MRS、單價、契約、估驗、報表 |
| 工程排程 | AI-CivilSchedule | WBS、CPM／PERT、甘特／網圖、基線 |
| 知識圖譜 | KnowGraphGo | Ontology、Evidence、Inference、Explain |
| DWG／DXF 語意化 | DWG_todo | CAD → ESM、KG、glTF／GLB |
| PDF 圖說重建 | go-pdf-drawing-reconstructor | PDF／掃描圖 → Engineering IR／ESM |
| 場景展示 | SceneX | 2D／3D 工程場景與展示 |
| 工程動畫／多媒體 | ComfyX | 工程動畫、生成式媒體成果 |

## 五、OpenWorker 第一階段應具備的工程工具

Engineering Coworker 首批 Tool 不直接綁死 repo 細節，先提供統一能力：

- `engineering_list_capabilities`
- `engineering_health_check`
- `engineering_create_job`
- `engineering_get_job`
- `engineering_run_workflow`
- `engineering_list_artifacts`
- `engineering_get_trace`
- `engineering_request_review`
- `engineering_publish_delivery`
- `engineering_query_knowledge`

Adapter 內部再決定走 AI-Engineering-OS、HTTP、CLI、MCP 或 Python／Go bridge。

## 六、中文文件索引

- [GitHub 專案盤點](./repo-inventory.zh-TW.md)
- [工程版架構](./architecture.zh-TW.md)
- [整合策略](./integration.zh-TW.md)
- [開發 Roadmap](./roadmap.zh-TW.md)
- [上游同步策略](./upstream-strategy.zh-TW.md)

## 七、目前結論

此 fork 的方向不是「把所有工程程式搬進 OpenWorker」，而是把 OpenWorker 做成整個 AI 工程顧問公司的 AI 員工層。工程能力維持在既有 repo，並以穩定 Adapter 契約接入。
