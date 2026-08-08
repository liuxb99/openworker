# OpenWorker 工程版獨立分段開發 Roadmap

更新日期：2026-08-08

## 專案定位

OpenWorker 工程版是 AI 工程顧問公司的 AI 員工與自然語言操作層；AI-Engineering-OS 保持 Project / Job / Workflow / Artifact lifecycle 權威，專業 Engine 保持工程算法權威。

## 目前完成度

- E0 工程版定位與中文架構文件：`IMPLEMENTED`
- E1 Capability Registry / Readiness：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E2 AI-Engineering-OS Bridge：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E3 Tool Facade + Persona Wiring：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E4 Direct Specialist Adapters：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E5 Digital Thread / Provenance：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6 RC Column Golden Job：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.1 Lifecycle Closure：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E7 Media / Company Coworker：`NOT_STARTED`

## E6.1 已完成內容

AI-Engineering-OS 現有 HTTP API 已確認包含：

- `POST /api/v1/jobs/{id}/transitions`
- `GET /api/v1/jobs/{id}/artifacts`
- `POST /api/v1/projects/{id}/artifacts`
- `GET /api/v1/artifacts/{id}`

OpenWorker `EngineeringOSClient` 已新增對應 bridge：

- `transition_job()`
- `list_job_artifacts()`
- `register_artifact()`
- `get_artifact()`

RC Column Golden Job 現在走：

```text
draft
→ queued
→ running
→ forge.rc-column
→ Design Forge Artifact
→ AI-Engineering-OS Artifact registration
→ review
→ Digital Thread
```

Digital Thread 同時保存 Design Forge source Artifact、AI-Engineering-OS registered Artifact 與 review-state Job，並建立：

```text
OS Artifact --belongs_to_job--> OS Job
OS Artifact --derived_from--> Design Forge Artifact
```

失敗補償：進入 `running` 後若專業計算、Artifact validation 或 Artifact registration 失敗，Golden Job 會嘗試走 AI-Engineering-OS 合法的 `running → cancelled` transition；不直接修改 OS 儲存層。

## 目前 P0

1. E1～E6.1 尚待完整 checkout + dependencies 的 pytest / compileall / diff check。
2. 真實 AI-Engineering-OS + civilforge-tool 多 repo runtime E2E 尚未執行。
3. AI-Engineering-OS 正式 HTTP surface 目前未見獨立 Review decision / Approval / Delivery endpoint，因此 Golden Job 必須停在 `review`，不得自動冒充 completed/published。

## P1

- 建立/接入正式 Review / Approval / Delivery API 後，延伸 Golden Job 至 completed / published。
- EngSketch production drawing mutation 接入 Golden Job。
- AI-BIM-Forge production IFC mutation 接入 Golden Job。
- pcces-web / Quantity / Schedule / DWG/PDF 第二批 adapters。
- adapter config persistence 與 Digital Thread persistence。

## Segment E6 / E6.1 驗收

- [x] RC Column schema / identity fail-closed。
- [x] dependency readiness 在 side effect 前檢查。
- [x] 建立 AI-Engineering-OS Job。
- [x] `draft → queued → running` authoritative transitions。
- [x] 呼叫 `forge.rc-column` / `1.0.0`。
- [x] protocol status 與 `design_ok` 分離。
- [x] authoritative hashed Artifact validation。
- [x] Design Artifact 正式註冊 AI-Engineering-OS Artifact。
- [x] `running → review`。
- [x] failure compensation `running → cancelled`。
- [x] OS Artifact ↔ Design Artifact ↔ Job Digital Thread。
- [x] permanent regression tests / 中文規格 / self-review。
- [ ] full repository verification。
- [ ] real multi-repo runtime E2E。
- [ ] approval / delivery closure。
- [ ] EngSketch / BIM mutation。

## 下一階段

在 E7 前，優先處理 E6.2：確認 AI-Engineering-OS 是否已有尚未暴露的 Review / Approval / Delivery domain service；若存在則補 HTTP + OpenWorker bridge，若不存在則只做明確缺口規格，不在 OpenWorker 私造第二套 lifecycle。

## 驗證原則

每個 Segment 必須包含 Production Code、永久 Regression Tests、自我 Code Review、Commit/Push。無法完整執行者維持 `IMPLEMENTED — WAITING FOR FULL VERIFICATION`，不得聲稱 `VERIFIED`。
