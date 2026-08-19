# Case 0005：Go Case Engine Terminal Reconciliation 缺口

更新時間：2026-08-19 13:26 +08:00

## 1. 現況

Case 0005 已成功由 Go-native Case Engine 提交第一個 durable business work：

- step：`0005-010`
- capability：`comfyx-studio.director.preproduction`
- work_id：`case0005-0005-010-r000014-17b8b780`
- revision：`14`
- authority：`go-tool-runtime :8848 durable local-work`

目前禁止重提新的 `case_continue`，直到該 work terminal。

## 2. 新發現的 Go Case Engine 缺口

`go-runtime/internal/casecontroller/continue.go` 目前流程為：

1. 讀 workspace `.openworker/case-worklist.json`；
2. 用 snapshot 內 `PENDING` 狀態計算 ready step；
3. 目前只允許 `0005-010`；
4. 建 deterministic work_id；
5. POST 到 `:8848/api/execution/local-work`；
6. 將 submit ACK 寫入 `case-controller-last.json`；
7. 結束。

缺少：

- 讀已提交 work 的最新 durable status；
- completed 後驗證 result acceptance；
- 將 worklist snapshot step 改成 `SUCCEEDED`；
- 將 result evidence 寫回 step；
- failed 後將 step 改成 `FAILED` / blocker；
- append terminal reconciliation ledger event；
- 重新計算下一個 ready step；
- 進入 `0005-020`。

因此即使 `0005-010` 真實完成，如果不補 reconciliation，workspace worklist 仍會把它視為 `PENDING`，Case Engine 無法自然前進。

## 3. 本批目標

### G2.1 Durable terminal reconciliation

新增 Go-native reconciliation：

- 如果 `case-controller-last.json` 有 current work_id，先 GET：
  - `/api/execution/local-work/<work_id>`
  - 必要時 `/events`
- `pending/claimed/running`：不得重新提交；回傳 existing work 狀態。
- `completed`：
  - result 必須是 JSON object；
  - 逐項驗證該 step 的 `acceptance` keys；
  - 0005-010 必須存在：`run_id`, `director_plan`, `director_plan_sha256`, `shot_count`, `character_count`, `scene_bible_count`；
  - worklist snapshot step → `SUCCEEDED`；
  - evidence=result；
  - atomic write worklist snapshot；
  - ledger append `go_step_reconciled_completed`。
- `failed`：
  - step → `FAILED`；
  - blocker 取 durable error；
  - ledger append `go_step_reconciled_failed`；
  - fail-closed，不跳步。

### G2.2 0005-020 mapping

0005-010 reconcile success 後，下一 ready step：

`0005-020 Materialize Snow White storyboard presentation request and visual requirements`

固定 capability：

`comfyx-studio.storyboard.plan`

需要從 0005-010 evidence 帶入 Director plan identity，提交 deterministic work_id 到同一 `:8848` durable queue。

0005-020 acceptance：

- `storyboard_request`
- `visual_requirements`
- `visual_asset_count`
- `reference_asset_ids`

## 4. 強制邊界

1. 不新增第二套 queue。
2. 不使用 Python controller。
3. GitHub Action 不做 reconciliation / business execution；reconciliation 在 resident Go Case Engine。
4. deterministic work_id 保持 revision-bound idempotency。
5. terminal work 未驗證 acceptance 前不得把 step 標為成功。
6. failed work 不自動 skip。
7. 目前已接受的 `0005-010` 不 clear、不換 work_id、不重提。

## 5. 驗收

- Go unit test：pending current work 不會再次 POST submit。
- Go unit test：completed 0005-010 缺任何 acceptance key → fail-closed。
- Go unit test：完整 0005-010 result → worklist snapshot `SUCCEEDED` + evidence persisted。
- Go unit test：reconcile 0005-010 後可生成 `0005-020` deterministic work_id 並 submit一次。
- REAL：ODA 上讀回 `0005-010` terminal result，reconcile 後才進 `0005-020`。
