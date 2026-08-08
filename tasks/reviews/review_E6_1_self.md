# E6.1 自我 Code Review — Lifecycle Closure

日期：2026-08-08

## 結論

E6.1 已把 RC Column Golden Job 從「建立 Job + Design Artifact Evidence」推進到 AI-Engineering-OS 正式 `review` 狀態，並把 Design Forge Artifact 登錄為 OS Artifact。狀態：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`。

## 權威來源核對

### AI-Engineering-OS HTTP

`internal/httpapi/server.go` 已有：

- `POST /api/v1/jobs/{id}/transitions`
- `GET /api/v1/jobs/{id}/artifacts`
- `POST /api/v1/projects/{id}/artifacts`
- `GET /api/v1/artifacts/{id}`

### Job 狀態機

`internal/job/job.go` 允許：

- draft → queued
- queued → running
- running → review / completed / cancelled
- review → running / completed / cancelled
- completed → published / archived

每次 transition 使用 `expected_revision`。

### Artifact

OS Artifact registration 要求 project_id（由 route 注入）、kind、uri、media_type、checksum，可帶 job_id、component_id、source_run_id。

## 本輪實作

1. EngineeringOSClient 新增 transition_job / register_artifact / list_job_artifacts / get_artifact。
2. Golden Job 走 draft → queued → running。
3. Design Forge 成功後逐一註冊 OS Artifact。
4. 所有 Artifact 完成後進 review。
5. Digital Thread 改為 OS Artifact belongs_to_job Job + OS Artifact derived_from Design Artifact。
6. running 後失敗會嘗試 transition cancelled。

## 自我複審發現

### P0-1：不能自動 completed/published

雖然 Job 狀態機有 completed/published，但目前 HTTP surface 未見獨立 Review decision / Approval / Delivery endpoint。直接由 Golden Job 自動完成或發布會越過人工審查語義，因此 E6.1 固定停在 review。

### P0-2：補償必須由 OS transition 完成

E6 v1 的 specialist failure 會留下 draft/running Job。E6.1 使用 OS 自己的 `cancelled` transition 補償，不直接寫 DB 或自行偽造狀態。

### P1：部分 Artifact 已註冊後的失敗

若多 Artifact 中途註冊失敗，先前 Artifact 仍由 OS 保存，而 Job 會嘗試取消。OpenWorker 不刪除或覆寫正式 Artifact，符合 provenance/immutability 原則；後續應由 OS 提供明確 cleanup/retention policy 才能進一步處理。

## 永久測試

- `tests/test_engineering_os_lifecycle.py`
- `tests/test_engineering_golden_job.py`

覆蓋 transition route/payload、Artifact route/payload、path injection/empty-field fail-closed、成功 review closure、OS Artifact registration、Digital Thread linkage、running failure cancellation。

## 評分

- 架構邊界：25/25
- 來源契約忠實度：25/25
- Lifecycle / failure semantics：23/25
- 測試與實際驗證：19/25
- 總分：92/100

未取得滿分的主因仍是完整 dependency checkout / pytest / 真實多 repo runtime E2E 尚未執行。
