# GitHub 工程專案盤點

更新日期：2026-08-08

本文件根據 GitHub Connector 對 `liuxb99` 帳號現有 repositories 的實際盤點整理，目的是決定哪些專案應由 OpenWorker 直接整合、哪些應由 AI-Engineering-OS 統一代理、哪些只是底層 runtime 或輔助工具。

## 一、A 級：OpenWorker 應優先整合的核心工程專案

### 1. AI-Engineering-OS

定位：AI 工程顧問公司的本機整合、編排、作業與成果交付平台。

已具備：Project／Job／Task／Workflow／Artifact／Review／Approval／Delivery、SQLite、Go 後台 UI、成果資料夾與離線成果網站。

**OpenWorker 整合策略：最高優先級。**

OpenWorker 不應重做 Job／Delivery 系統，而應把 AI-Engineering-OS 當作工程控制平面。

### 2. AI-CivilDesign-Forge

定位：權威工程設計計算核心。

已具備：18 類構件 Production Pipeline、Formula Registry、Calculation Trace、SVG／HTML／JSON Artifact、CLI、Tool Protocol。

**OpenWorker 整合策略：透過 AI-Engineering-OS 為主，必要時提供直接 Tool Adapter。**

### 3. AI-EngSketch

定位：確定性的工程圖／Draft Studio。

已具備：Engineering Model → Scene → SVG → PNG、版本、Patch、Diff、Undo／Redo、Proposal 工作流。

**OpenWorker 整合策略：用於圖面生成、修改、版本比對與成果預覽。**

### 4. AI-BIM-Forge

定位：Engineering Semantic Model → IFC 的標準 BIM 編譯工具鏈。

已具備：IFC Spatial Hierarchy、Wall／Column／Beam／Slab、Material、PropertySet、Classification、Quantity、Audit、Write／Reopen。

**OpenWorker 整合策略：以 ESM 為輸入，不直接讓 LLM 操作 IFC 文字。**

### 5. AI-CivilQuantity

定位：權威工程數量計算核心。

規格已明確定義 Quantity Trace、Knowledge Snapshot、Formula／Rule／Technique／Tool Version、Revision、PCCES／WBS／Schedule 下游關聯。

目前仍屬 Documentation Baseline 階段。

**OpenWorker 整合策略：列入正式能力，但 readiness 必須回報尚未 Production Ready。**

### 6. pcces-web

定位：PCCES C# 系統的 Web／Local Go 現代化與功能對等專案。

目前 Phase 0～8 已 VERIFIED，Phase 9 Production 最終證據待完成。

**OpenWorker 整合策略：預算、MRS、單價、契約、估驗、結算與報表的正式來源。**

### 7. AI-CivilSchedule

定位：工程 WBS、CPM／PERT、甘特圖、網圖、基線與實際進度。

目前仍在規格與初始化階段。

**OpenWorker 整合策略：先列 capability 與契約，readiness 回報未完成。**

### 8. KnowGraphGo

定位：嵌入式 Go Knowledge Graph Engine。

已具備 Graph Core、Ontology、Inference、Query、Evidence／Provenance、Explain、SQLite／Memory Store、CLI／Library。

**OpenWorker 整合策略：作為工程知識、證據、規則與推理的共用層。**

### 9. DWG_todo

定位：DWG／DXF 清圖、工程語意重建、Knowledge Graph、glTF／GLB 與 BIM 前處理。

已完成 DWG/DXF 匯入、圖元分組、構件候選、樓層推理、拓撲、KG、3D 裝配；IFC 與 AI BIM CLI 尚在 Roadmap。

**OpenWorker 整合策略：CAD ingestion 與 ESM 建立的主要入口。**

### 10. go-pdf-drawing-reconstructor

定位：PDF／掃描工程圖說的重建與 Engineering IR／ESM 前處理。

**OpenWorker 整合策略：作為 PDF 圖說 ingestion 能力。**

## 二、B 級：成果展示與媒體能力

### SceneX

用途：2D／3D 場景、工程視覺化與展示。

### ComfyX

用途：生成工作流、Knowledge Graph、ComfyUI／Bernini／音樂與工程動畫等多媒體輸出。

### Comfyx-Studio

用途：完整影片製作工作台。較適合做「工程成果影片／解說影片」的上層 Studio，而不是 OpenWorker 的底層工程核心。

### Bernini-Director-Go / framepack-Nomi-go / framepack-nomi-cli

用途：影片與動畫生成執行能力，可經 ComfyX 或媒體 Adapter 間接調用。

## 三、C 級：專業輔助與垂直專案

### freeCivilcad

可作為 CAD／Civil CAD 能力參考或輔助工具，但不應與 DWG_todo、AI-EngSketch 的權威責任重疊。

### BridgeModeler / Bridge_Types / Terrain_To_DXF / zengwen-bridge

屬橋梁、地形、專案型或特定領域工具。後續應以「專業 Plugin／Domain Adapter」接入，不應先塞入通用 Engineering Coworker 核心。

### AI_CivilTools

可作為既有工程工具集合與前台參考。若與 AI-Engineering-OS 的正式入口重疊，應以 AI-Engineering-OS 為主要控制平面，避免重複建立工作流。

### ai-budget-go / AI_PCCES

需視其與 `pcces-web` 的現況與責任邊界決定是否保留為底層模組、舊版或實驗分支；OpenWorker 不應同時把多個相同預算核心視為權威來源。

## 四、D 級：Agent、遠端控制與公司運營工具

- `opencode-manager`
- `opencode-telegram-bot`
- `ai-telegram-remote-control`
- `one-person-company`
- `AI-Company-Handbook`
- `OPC-Tools`
- `HubOne`
- `AI_System`

這些與 OpenWorker 的 Agent／公司運營概念有交集，但第一階段不直接混入工程專業 Adapter。可在後續作為「公司運營 Coworker」「遠端執行」「開發 Agent 管理」等獨立 Persona／Connector。

## 五、E 級：本地模型與推理 Runtime

- `go-qwen-moe-runtime`
- `go-hybrid-moe-runtime`
- `go-mistralrs-hybrid-moe-runtime`
- `go-xinfer-hybrid-moe-runtime`
- `MoE-Streaming-Slice-Runtime`
- `local-llm-utility-runtime`
- `llamacpp-manager-go`
- `llama.cpp-b9986`
- `llama.cpp-deepseek-v4-flash-gpu`
- `llama.cpp-reason-pipeline`
- `flash-moe`
- `ktransformers`
- `xinfer-win`

這些是 Model Runtime／Inference Infrastructure，不屬工程業務能力。OpenWorker 只需要透過模型 Provider／OpenAI-compatible endpoint／本機 Router 使用它們，不應在 Engineering Adapter 中直接綁定模型實作。

## 六、建議權威責任圖

```text
OpenWorker
  = AI 員工、自然語言、工具調用、權限、Approval、Connector、MCP

AI-Engineering-OS
  = Project / Job / Workflow / Artifact / Review / Delivery 控制平面

KnowGraphGo
  = 工程知識、規則、Evidence、Inference、Explain

AI-CivilDesign-Forge
  = 設計計算權威

AI-EngSketch
  = 工程圖權威

DWG_todo
  = CAD → Engineering Semantic Model

go-pdf-drawing-reconstructor
  = PDF → Engineering IR / ESM

AI-BIM-Forge
  = ESM → IFC

AI-CivilQuantity
  = 工程數量權威

pcces-web
  = 預算 / PCCES / 契約 / 估驗權威

AI-CivilSchedule
  = 排程 / CPM / PERT 權威

SceneX / ComfyX
  = 視覺化 / 動畫 / 多媒體成果
```

## 七、第一階段不要接入的方式

- 不把所有 repo source code 複製進 OpenWorker。
- 不讓 OpenWorker 直接修改各專案 SQLite。
- 不在 OpenWorker 重寫工程公式。
- 不把每個 repo 都直接暴露成數十個低階 Tool。
- 不在 Engineering Coworker 裡硬編每個 repo 的路徑。

第一階段只建立穩定的能力層與 Adapter Registry，再逐步把成熟專案接入。