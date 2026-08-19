# Case 0005：Go Case Engine Terminal Reconciliation 實作進度

更新時間：2026-08-19 13:36 +08:00

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

## 2. Terminal reconciliation 已 SOURCE IMPLEMENTED

OpenWorker commit：`52b8e70ece18823e9c01fed523d5ef539c288b97`

`go-runtime/internal/casecontroller/continue.go` 已新增：

- current durable work 優先 reconciliation；
- `pending / claimed / running` 不重提；
- `completed` 驗證 acceptance 後 atomic 寫回 worklist；
- `failed` 寫 `FAILED + blocker`，fail-closed；
- completed ledger：`go_step_reconciled_completed`；
- failed ledger：`go_step_reconciled_failed`。

## 3. 0005-020 mapping 已實作

同一 commit `52b8e70e...` 已加入：

- step：`0005-020`
- capability：`comfyx-studio.storyboard.plan`
- deterministic work_id 繼續使用 `case + step + action + revision` hash

Director receipt 的 `director_plan` 是 workspace 下 canonical 絕對路徑。Go Engine 會先轉成 bounded relative path、拒絕 workspace escape 並驗證檔案存在，之後才把 `director_plan_relpath` 傳給 leaf capability。

## 4. 0005-025 text-only PPTX mapping 已實作

OpenWorker commit：`181b1ad0ebd047ed123f21e456512f8e50e7b149`

已新增：

- step：`0005-025`
- capability：`presentation.openmaic`
- parent：必須是 `0005-020 = SUCCEEDED`
- input evidence：`0005-020.storyboard_request`
- request path：必須位於 Case workspace 內且真實存在
- 固定輸出：`presentation/storyboard-text-only.pptx`
- 不允許由 work evidence 傳任意 absolute output path

因此目前 Go Case Engine 已能在 source contract 上連續處理：

`0005-010 Director`
→ `0005-020 storyboard request + visual requirements`
→ `0005-025 text-only storyboard PPTX`

全程不需要 Python Case controller。

### 0005-025 回歸測試

Commit：`fcc3e143e62e0a84752726bd23817d2589a921d3`

新增測試驗證：

1. `storyboard_request` 在 workspace 內時，正確轉成 bounded relative path；
2. output 固定為 `presentation/storyboard-text-only.pptx`；
3. request 指向 workspace 外部時 fail-closed。

## 5. OpenMAIC evidence contract 已對齊 Case acceptance

go-tool-runtime commit：`1978e685be07e3813fa4c4c0b50589b09b2ab8bc`

`presentation.openmaic` 保留通用 evidence：

- `pptx`
- `manifest`
- `sha256`
- `media_count`
- `slide_count`

同時正式提供 storyboard aliases：

- `storyboard_pptx`
- `storyboard_manifest`
- `storyboard_pptx_sha256`
- `image_count`
- `reopen_receipt`

因此 Case 0005 `0005-025` acceptance：

- `storyboard_pptx`
- `storyboard_manifest`
- `storyboard_pptx_sha256`
- `slide_count`
- `reopen_receipt`
- `image_count`

不再與 leaf capability result 命名漂移。

## 6. ODA claim runtime 自癒已 REAL 部署

`gtr-work-agent` resident mode 原本可能因單一 slot 的 non-retryable error 讓整個 agent process 結束，四個 claim slots 一起消失。

修復 commit：`55e0204ec1f5762c2e664feb166fd5fc175cf4f1`

現在 resident mode：

- slot error 不再殺掉整個 agent；
- individual slot 自動重啟；
- backoff：1 → 2 → 4 → 5 秒；
- `--once` 測試模式仍保留 fail-fast。

ODA deployment run：`32218984221`

已完成：

- targeted tests success
- build success
- install success
- persistent local-work control plane success
- REAL four-slot verifier success
- deployment receipt success

## 7. Upgrade workflow 六槽搶機缺口已修

舊 Upgrade V3 的 6 個 generic `[self-hosted, Windows, X64]` jobs 已退休。

目前改為 Upgrade V4：

- ODA 一個固定 label job
- O87 一個固定 label job
- UL7 一個固定 label job

不再六個 generic jobs 搶三台機器。

相關 commits：

- `68bcfa0e0bf3eb831617852828c4b4b6f6be8476`
- `f579d7010073e5cdaac77475be3031b26225d9f4`

## 8. Work readback 可觀測性

exact durable work readback 已併入 transient command transport：

- `9d4023847a1b916eb5dc059dfc368114c4166966`
- `1a53adaf743a5952c74dee21c568de6458f1383e`
- `98910af4e2f93b3dd94b47bf3597f7f6aca063d3`

固定只讀命令：`case_work_status`

只讀：

- exact work item
- exact work events
- local supervisor status

不 claim、不 clear、不 retry、不 continue。

目前 request：

`20260819-1323-oda-case0005-work-status-001`

尚未取得 immutable final receipt；因此仍不得憑推測宣稱 `0005-010` terminal。

## 9. REAL 驗收狀態

### 已 REAL

- ODA 4 claim + 4 executor supervisor
- claim-slot self-heal deployment
- deterministic `0005-010` durable submission
- Go-native bootstrap / continue transport chain

### SOURCE IMPLEMENTED，等待最新 ODA resident full-Go gate

- terminal reconciliation
- 0005-020 mapping
- 0005-025 mapping
- 025 workspace path guard tests

ODA resident workflow gate 已提升為 `go test ./...`，trigger commit：

`f36f1b366bd1c3b570059981c4f870ab4b45d835`

## 10. 下一個合法動作

1. 讀回 `case0005-0005-010-r000014-17b8b780` exact durable status。
2. 若 pending：只修 claim/runtime，不重提 work。
3. 若 claimed/running：只追 status。
4. 若 failed：修 Director leaf capability 真實錯誤。
5. 若 completed：使用新 Go reconciliation 驗證六項 evidence，進 `0005-020`。
6. 020 completed 後自動進 `0005-025`，生成 text-only storyboard PPTX。
7. 025 acceptance 通過後再開始 `0005-026` Google Drive publish，不提前發布。
