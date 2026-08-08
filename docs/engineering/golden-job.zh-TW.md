# E6 RC 柱 Golden Job

## 目的

E6 建立第一條可重複驗收的工程基準路徑；E6.1 再把它閉合到 AI-Engineering-OS 的正式 `review` 狀態。它不是第二套 Workflow Engine，OpenWorker 只負責編排現有權威系統。

## E6.1 正式路徑

```text
Engineering Coworker / caller
→ AI-Engineering-OS readiness
→ AI-CivilDesign-Forge readiness
→ 建立 RC Column Job (draft)
→ queued
→ running
→ forge.rc-column / tool-protocol/1.0.0
→ Design Forge Calculation Artifact
→ AI-Engineering-OS Artifact registration
→ Job review
→ E5 Digital Thread
```

目前不自動 `completed` 或 `published`。AI-Engineering-OS 雖有這些狀態，但正式 HTTP surface 尚沒有獨立 Review/Approval 決策 API；Golden Job 在 `review` 停止，避免越過人工審查邊界。

## RC 柱輸入

依 `AI-CivilDesign-Forge/schemas/tools/rc-column-input-v1.json` 要求：`semantic_id`、`width_mm`、`depth_mm`、`clear_height_mm`、`concrete_grade`、`steel_grade`、`axial_force_kn`、`moment_x_knm`。

`project_id` 由控制平面注入；若輸入另帶不同 project_id，直接 fail-closed。

## Job 狀態機

依 AI-Engineering-OS 現有 Job 狀態機：

```text
draft → queued → running → review
```

每次 transition 都使用來源 Job 的 `expected_revision`，不自行猜 revision。若 Design Forge、Artifact 驗證或 Artifact registration 在 `running` 後失敗，Golden Job 會嘗試走 OS 合法的 `running → cancelled` 補償；補償失敗不覆蓋原始錯誤。

## Artifact registration

Design Forge 成功回應的每個正式 Artifact 會以來源資料登錄 AI-Engineering-OS：

- job_id：本次 Golden Job Job
- component_id：semantic_id
- kind：artifact_type
- uri：path
- media_type：來源 media_type
- checksum：來源 sha256
- source_run_id：來源 calculation_run_id（若有）

OpenWorker 不重新計算 checksum，也不改寫來源 Artifact ID。

## Digital Thread

E6.1 會同時建立三類 Evidence：

```text
Design Forge source Artifact
        ↑ derived_from
AI-Engineering-OS registered Artifact
        ↓ belongs_to_job
AI-Engineering-OS Job (review)
```

因此可同時回答「正式 OS Artifact 屬於哪個 Job」以及「它源自哪個專業引擎 Artifact」。

## Protocol 與工程結果

Design Forge 固定使用：

- tool_id: `forge.rc-column`
- version: `1.0.0`
- nested `arguments.input`

`status=succeeded` 代表協議/執行成功；`data.design_ok` 表示工程檢核結果。`design_ok=false` 不等於 transport failure，不得被 OpenWorker 偷換成系統錯誤。

## Fail-closed

以下情況會停止：dependency 未 ready、必要輸入缺失、Project identity 衝突、revision 缺失、Tool Protocol failure、semantic identity mismatch、沒有正式 Artifact、Artifact 缺 path/SHA256/media type、OS Artifact registration 失敗、Job transition 失敗。

## 尚未完成

E6.1 仍不宣稱：

- EngSketch 正式產圖 mutation 已加入 Golden Job。
- AI-BIM-Forge 正式 IFC mutation 已加入 Golden Job。
- 獨立 Review decision / Approval API 已接入。
- Job completed / published 自動化。
- Delivery publication 已接入。
- 真實多 repo runtime E2E 已驗證。

這些必須依來源系統真正存在的契約逐步加入，不能以 mock 或狀態名稱冒充完成。
