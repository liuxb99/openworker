# E6 RC 柱 Golden Job

## 目的

E6 建立第一條可重複驗收的工程端到端基準路徑。它不是第二套 Workflow Engine，而是一個固定的 orchestration fixture，用來證明 OpenWorker 能把 AI-Engineering-OS 控制平面、AI-CivilDesign-Forge 工程計算與 E5 Digital Thread 接成同一條可追溯鏈。

## 第一版範圍

```text
Engineering Coworker / caller
→ AI-Engineering-OS readiness
→ AI-CivilDesign-Forge readiness
→ 建立 RC Column Job
→ forge.rc-column / tool-protocol/1.0.0
→ Calculation Artifact
→ Digital Thread
```

E6 v1 刻意不假裝已完成 EngSketch、BIM、Review、Approval、Delivery 的真實執行。這些步驟只有在各來源 repo 提供足夠且穩定的 machine contract、以及 AI-Engineering-OS 提供對應 lifecycle API 後才能加入 Golden Job。

## RC 柱輸入

依 `AI-CivilDesign-Forge/schemas/tools/rc-column-input-v1.json`，Golden Job 要求：

- semantic_id
- width_mm
- depth_mm
- clear_height_mm
- concrete_grade
- steel_grade
- axial_force_kn
- moment_x_knm

`project_id` 由 Golden Job 的控制平面參數注入；若輸入另帶不同 project_id，直接 fail-closed。

## 執行協議

Design Forge 請求固定使用：

- tool_id: `forge.rc-column`
- version: `1.0.0`
- nested `arguments.input`

工程設計是否通過由 `data.design_ok` 表達；`design_ok=false` 不等於 transport/protocol failure。Golden Job 只要求 Tool Protocol `status=succeeded`，並完整保留工程結果。

## Evidence

成功回應必須至少含一個符合 E5 source mapping 的權威 Artifact：

- artifact_id
- artifact_type
- path
- sha256
- media_type

Golden Job 將 AI-Engineering-OS Job 與 Design Forge Artifact 放入 Digital Thread，並建立 `artifact --belongs_to_job--> job` 關係。這個關係是本次 orchestrator 實際建立與執行所得，不靠名稱猜測。

## Fail-closed

以下情況不得繼續：

1. AI-Engineering-OS 未 ready。
2. AI-CivilDesign-Forge 未 ready。
3. RC 柱必要欄位缺失。
4. project identity 衝突。
5. Tool Protocol status 不是 succeeded。
6. 回傳 semantic_id 與請求不一致。
7. 沒有權威 Artifact。
8. Artifact 缺 checksum/path/media type 等 E5 必要證據。

## 尚未宣稱完成的部分

E6 v1 不把下列內容寫成已完成：

- EngSketch 正式產圖 mutation。
- AI-BIM-Forge 正式 IFC mutation。
- AI-Engineering-OS Job transition / Artifact registration。
- Review / Approval / Delivery lifecycle。
- 真實多 repo runtime E2E。

這些是後續 Golden Job 擴展或下一 Segment 的工作，不以 mock 結果冒充 production integration。
