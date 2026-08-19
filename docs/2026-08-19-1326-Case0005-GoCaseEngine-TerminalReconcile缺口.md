# Case 0005：Go Case Engine Terminal Reconciliation 實作進度

更新時間：2026-08-19 13:30 +08:00

## 1. 現況

Case 0005 已成功由 Go-native Case Engine 提交第一個 durable business work：

- step：`0005-010`
- capability：`comfyx-studio.director.preproduction`
- work_id：`case0005-0005-010-r000014-17b8b780`
- revision：`14`
- authority：`go-tool-runtime :8848 durable local-work`

目前仍禁止重提新的 `0005-010`。原 work_id 保持不變，SQLite durable queue 不 clear。

ODA 已於 go-tool deployment run `32218984221` REAL 安裝 claim-slot 自癒版本：

- source commit：`55e0204ec1f5762c2e664feb166fd5fc175cf4f1`
- deployment receipt commit：`a4ead02dda92a3924d82ec042c68fee048175535`
- REAL four-slot verifier：success
- GitHub Action business execution：false

## 2. Terminal reconciliation 缺口已進入 SOURCE IMPLEMENTED

OpenWorker commit：`52b8e70ece18823e9c01fed523d5ef539c288b97`

`go-runtime/internal/casecontroller/continue.go` 已新增：

### 2.1 既有 current work 優先 reconciliation

如果 `.openworker/case-controller-last.json` 有 `work_id`：

- GET `:8848/api/execution/local-work/<work_id>`；
- `pending / claimed / running`：直接回傳 existing work，禁止再 POST submit；
- `completed`：抽取 localexec result evidence、逐項驗證 step acceptance；
- `failed`：將 step 改 `FAILED` 並寫 blocker，fail-closed。

### 2.2 Completed persistence

completed 且 acceptance 完整時：

- step.status → `SUCCEEDED`
- step.evidence → durable result evidence
- atomic rewrite `.openworker/case-worklist.json`
- ledger append `go_step_reconciled_completed`
- 重新計算 ready step

### 2.3 Failed persistence

failed 時：

- step.status → `FAILED`
- step.blocker → durable work error
- ledger append `go_step_reconciled_failed`
- 不 skip、不自動提交後續步驟

## 3. 0005-020 mapping 已實作

同一 commit `52b8e70e...` 已加入：

- step：`0005-020`
- capability：`comfyx-studio.storyboard.plan`
- deterministic work_id 繼續使用 `case + step + action + revision` hash

Director receipt 的 `director_plan` 路徑語義亦已由 Comfyx-Studio source 確認：

- canonical absolute path：`<workspace>\director\project-plan.json`
- archive path：`<workspace>\runs\<run_id>\director\project-plan.json`

Go Engine 不直接信任 receipt 給的絕對路徑；會：

1. `filepath.Abs()` 正規化；
2. 以 workspace 做 `filepath.Rel()`；
3. 拒絕 `..` / absolute escape；
4. 驗證 canonical plan file 真實存在；
5. 只把 bounded relative path 傳給 leaf capability，例如：
   `director\project-plan.json`。

這符合 `ComfyXStudioStoryboardPlan` 的 input contract：

- `workspace_root`
- `assigned_host`
- `director_plan_relpath`

## 4. 回歸測試已補

Commit：`d927290ebac684074de96de0489d4b9f2a5a86b5`

`go-runtime/internal/casecontroller/continue_test.go` 已覆蓋：

1. 首次 0005-010 submit 後，第二次看到 `pending` 只 GET status，POST submit count 保持 1。
2. completed 0005-010 + 六項完整 evidence：
   - worklist 010 → SUCCEEDED
   - evidence persisted
   - 自動選中 0005-020
   - 只 submit 一次 `comfyx-studio.storyboard.plan`
   - `director_plan_relpath` 必須為 bounded relative path。
3. completed 0005-010 缺任一 acceptance：fail-closed，不 submit 020。
4. failed 0005-010：worklist → FAILED + blocker，不 resubmit。

## 5. 目前驗收狀態

### SOURCE

- terminal reconciliation：IMPLEMENTED
- 0005-020 mapping：IMPLEMENTED
- regression tests：ADDED

### REAL ODA

尚未宣稱完成。

因為 `d927290e...` 會觸發固定三機 Upgrade V4，必須取得 ODA 的：

- Go test success
- build success
- resident install success
- running commit / target commit 正確
- upgrade_verified=true

在 REAL receipt 出現前，只能寫 SOURCE IMPLEMENTED。

## 6. Work readback 可觀測性補強

原獨立 `probe-case0005-work-oda.yml` 沒有穩定留下 evidence，因此 exact durable work readback 已併入既有 transient command transport：

- `9d4023847a1b916eb5dc059dfc368114c4166966`：wrapper 新增 `case_work_status`
- `1a53adaf743a5952c74dee21c568de6458f1383e`：ODA transient runner 支援該 read-only command
- `98910af4e2f93b3dd94b47bf3597f7f6aca063d3`：workflow allowlist 支援該 command

`case_work_status` 只讀：

- exact work item
- exact work events
- local supervisor status

不 claim、不 clear、不 retry、不 continue。

目前 read-only request：

`20260819-1323-oda-case0005-work-status-001`

仍等待 immutable receipt；不得以尚未返回的 probe 推論 work terminal 狀態。

## 7. 下一個合法動作

1. 收 `d927290e...` 的固定三機 Upgrade V4 ODA REAL 結果。
2. 收 `case_work_status` exact durable evidence。
3. 如果 0005-010 仍 pending：只修 claim/runtime 根因，不重提 Case work。
4. 如果 claimed/running：只追 status。
5. 如果 failed：修 Director leaf capability 真實錯誤。
6. 如果 completed：確認六項 acceptance 後，使用新 Go reconciliation 進入 `0005-020`。
