# OpenWorker 工程版獨立分段開發 Roadmap

更新日期：2026-08-08

## 專案定位

OpenWorker 工程版是 AI 工程顧問公司的 AI 員工與自然語言操作層；AI-Engineering-OS 保持 Project / Job / Workflow / Artifact / Review / Delivery lifecycle 權威，專業 Engine 保持工程算法權威。

## 目前完成度

- E0 工程版定位與中文架構文件：`IMPLEMENTED`
- E1 Capability Registry / Readiness：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E2 AI-Engineering-OS Bridge：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E3 Tool Facade + Persona Wiring：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E4 Direct Specialist Adapters：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E5 Digital Thread / Provenance：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6 RC Column Golden Job：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.1 Lifecycle Closure：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.2 Review / Approval / Delivery Closure：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E7 Media / Company Coworker：`NOT_STARTED`

## E6.2 權威來源盤點

直接核對 AI-Engineering-OS 啟動程式與 domain code 後確認，Review / Approval / Delivery 並非缺失，只是先前 OpenWorker bridge 尚未接入：

- `GET /api/v1/jobs/{id}/reviews`
- `GET /api/v1/jobs/{id}/approval-status`
- `GET /api/v1/artifacts/{id}/reviews`
- `POST /api/v1/artifacts/{id}/reviews`
- `GET /api/v1/jobs/{id}/deliveries`
- `GET /api/v1/jobs/{id}/deliveries/latest`
- `POST /api/v1/jobs/{id}/publish`

AI-Engineering-OS 的 Approval 語義是衍生狀態，不是另一張 Approval entity：每一個 Job 目前最新 Artifact revision 都必須有最新 `approved` Review，`ApprovalStatus.Approved` 才為 true。全部核准時 Review Service 會把 Job 從 `review → completed`；發布時 Delivery Service 再次執行 `RequireApproved()`，驗證成果 checksum 並在成功後 `completed → published`。

## OpenWorker E6.2 已完成

`EngineeringOSClient` 新增：

- `list_job_reviews()`
- `list_artifact_reviews()`
- `approval_status()`
- `submit_artifact_review()`
- `list_deliveries()`
- `latest_delivery()`
- `publish_job()`

Tool Facade 新增：

- `engineering_get_approval_status`：唯讀，不需 approval。
- `engineering_list_job_reviews`：唯讀，不需 approval。
- `engineering_submit_artifact_review`：會改變治理狀態，`requires_approval=True`。
- `engineering_list_deliveries`：唯讀，不需 approval。
- `engineering_publish_job`：正式發布外部副作用，`requires_approval=True`。

RC Column Golden Job 新增顯式治理階段：

```text
run()
→ Job review state
→ approve_for_delivery(reviewer=...)
   → 對每個 registered Artifact 提交 approved Review
   → AI-Engineering-OS derived approval status
   → Job completed
→ publish(publisher=...)
   → AI-Engineering-OS RequireApproved
   → checksum / delivery staging / website rebuild
   → Job published
```

`run()` 絕不自動呼叫 approve/publish。審查人與發布人必須由顯式操作提供，且 Agent Tool 層仍會經 OpenWorker Approval Gate。

## 目前 P0

1. E1～E6.2 尚待完整 checkout + dependencies 的 pytest / compileall / diff check。
2. 真實 AI-Engineering-OS + civilforge-tool 多 repo runtime E2E 尚未執行。
3. Golden Job 尚未把 EngSketch production drawing mutation 與 AI-BIM-Forge IFC mutation納入正式交付物。

## P1

- EngSketch production drawing mutation 接入 Golden Job。
- AI-BIM-Forge production IFC mutation 接入 Golden Job。
- pcces-web / Quantity / Schedule / DWG/PDF 第二批 adapters。
- adapter config persistence 與 Digital Thread persistence。
- Review / Delivery evidence 納入 Digital Thread schema 的下一版。

## E6 系列驗收

- [x] RC Column schema / identity fail-closed。
- [x] dependency readiness 在 side effect 前檢查。
- [x] 建立 AI-Engineering-OS Job。
- [x] `draft → queued → running → review` authoritative transitions。
- [x] 呼叫 `forge.rc-column` / `1.0.0`。
- [x] protocol status 與 `design_ok` 分離。
- [x] Design Artifact 正式註冊 AI-Engineering-OS Artifact。
- [x] failure compensation `running → cancelled`。
- [x] OS Artifact ↔ Design Artifact ↔ Job Digital Thread。
- [x] Artifact Review bridge。
- [x] derived Approval Status bridge。
- [x] 全部 Artifact approved 後確認 Job `completed`。
- [x] Delivery publish bridge，並由 OS 再次執行 approval / checksum gate。
- [x] 發布後由 OS 轉為 `published`。
- [x] governance mutating tools 維持 OpenWorker `requires_approval=True`。
- [x] permanent regression tests / 中文規格 / self-review。
- [ ] full repository verification。
- [ ] real multi-repo runtime E2E。
- [ ] EngSketch / BIM production mutation。

## 下一階段

E6.3：把 EngSketch 正式圖面與 AI-BIM-Forge IFC Artifact 接入同一 Golden Job，讓 Approval Gate 不只核准 calculation trace，而是核准「計算 + 圖面 + BIM」的完整當前成果集合。

## 驗證原則

每個 Segment 必須包含 Production Code、永久 Regression Tests、自我 Code Review、Commit/Push。無法完整執行者維持 `IMPLEMENTED — WAITING FOR FULL VERIFICATION`，不得聲稱 `VERIFIED`。
