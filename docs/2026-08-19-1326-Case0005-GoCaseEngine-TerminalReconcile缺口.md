# Case 0005：Go Case Engine Terminal Reconciliation 實作進度

更新時間：2026-08-19 14:00 +08:00

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

Commit：`52b8e70ece18823e9c01fed523d5ef539c288b97`

- capability：`comfyx-studio.storyboard.plan`
- parent：`0005-010 = SUCCEEDED`
- Director plan 必須是真實 workspace 內檔案
- absolute canonical path 轉 bounded relative path 後才傳給 leaf capability

## 4. 0005-025 text-only PPTX mapping 已實作

OpenWorker commit：`181b1ad0ebd047ed123f21e456512f8e50e7b149`

- capability：`presentation.openmaic`
- parent：`0005-020 = SUCCEEDED`
- input：`0005-020.storyboard_request`
- request 必須位於 workspace 內且真實存在
- 固定 output：`presentation/storyboard-text-only.pptx`

回歸測試 commit：`fcc3e143e62e0a84752726bd23817d2589a921d3`

## 5. OpenMAIC evidence contract 已對齊 Case acceptance

go-tool-runtime commit：`1978e685be07e3813fa4c4c0b50589b09b2ab8bc`

除通用 evidence 外，正式提供：

- `storyboard_pptx`
- `storyboard_manifest`
- `storyboard_pptx_sha256`
- `image_count`
- `reopen_receipt`

因此 `0005-025` 可以由 Go reconciliation 正式驗收，不需要 Case-specific Python 轉換。

## 6. 0005-026 text-only storyboard → Google Drive mapping 已 SOURCE IMPLEMENTED

OpenWorker commit：`25aef4642364374b2a6c8e446d54ef99cecefd64`

Go Case Engine 已加入：

- step：`0005-026`
- capability：`openworker.case.publish-artifacts`
- parent：必須 `0005-025 = SUCCEEDED`
- artifact inputs：
  - `storyboard_pptx`
  - `storyboard_manifest`
  - `reopen_receipt`
- 每個 artifact 都必須是真實 workspace 內檔案；轉成 bounded relative path 後才交給 publisher。
- deterministic revision identity：`case0005-text-storyboard-r000014`
- deterministic work code：`CASE0005-TEXT-STORYBOARD-R000014`
- GitHub Action 不允許作 artifact transport。
- artifact publication 必須 ODA 本機經 Google Drive API 完成。

### Drive publisher evidence alias 修復

go-tool-runtime commit：`ec8fbaa7ca053b768a20ad8add18d8b994a8261e`

`openworker.case.publish-artifacts` 原本提供 `published_artifacts` 與 `drive_files`，但 Case worklist acceptance 另要求：

- `published_artifact_sha256`
- `drive_file_ids`
- `drive_file_links`

現在 leaf capability 已正式輸出這三個穩定 alias，保留原始結構化欄位，不再靠 Case controller 猜測／重算。

因此 `0005-026` acceptance contract 已可與 leaf capability 對齊：

- `review_bundle`
- `manifest_sha256`
- `published_artifacts`
- `published_artifact_sha256`
- `drive_receipt`
- `drive_folder_id`
- `drive_revision_web_view_link`
- `drive_file_ids`
- `drive_file_links`
- `transport`
- `chatgpt_review_ready`
- `github_action_used_for_artifact_transport`

## 7. ODA claim runtime 自癒已 REAL 部署

`gtr-work-agent` resident mode 原本可能因單一 slot non-retryable error 讓整個 4-slot agent process 結束。

修復 commit：`55e0204ec1f5762c2e664feb166fd5fc175cf4f1`

現在 resident mode：

- slot error 不殺整個 agent；
- individual slot 自動重啟；
- backoff：1 → 2 → 4 → 5 秒；
- `--once` 仍 fail-fast。

ODA deployment run：`32218984221`，REAL four-slot verifier success。

## 8. Upgrade workflow 六槽搶機缺口已修

舊 Upgrade V3 的 6 個 generic `[self-hosted, Windows, X64]` jobs 已退休；目前固定：

- ODA 一個 label job
- O87 一個 label job
- UL7 一個 label job

相關 commits：

- `68bcfa0e0bf3eb831617852828c4b4b6f6be8476`
- `f579d7010073e5cdaac77475be3031b26225d9f4`

## 9. Current durable work 可觀測性正在收斂到 resident-node authority

獨立 probe / transient status 曾出現 push-trigger 不穩定，因此 latest resident-node workflow 已直接增加：

- exact `.openworker/case-controller-last.json` work_id 讀取
- `GET :8848/api/execution/local-work/<work_id>`
- `GET :8848/api/execution/local-work/<work_id>/events`
- local supervisor status
- immutable receipt：`case-evidence/case0005-current-work/latest.json`

workflow commit：`dff9159f9c16cfe94597747952b956bd1a3693a8`

觸發 commit：`898c2c6bf03e19b774ef28245224002dd9a59073`

這條 workflow 在 publish current-work receipt 前會先：

- `go test ./...`
- build resident Go node
- install / upgrade service
- verify running commit / target commit
- verify `/v1/cases/continue` 非 404
- publish immutable resident-node receipt

目前 `case-evidence/case0005-current-work/latest.json` 尚未出現，因此仍不得宣稱 `0005-010` terminal。

## 10. 目前 Go-native Case 0005 主鏈

SOURCE contract 已接到：

`0005-010 Director`
→ `0005-020 storyboard request + visual requirements`
→ `0005-025 text-only storyboard PPTX`
→ `0005-026 Google Drive review publish`

全程：

- Python Case controller = false
- durable queue = `:8848`
- deterministic work_id
- workspace path safety
- acceptance fail-closed
- Google Drive artifact transport only at leaf publisher

## 11. 下一個合法動作

1. 等 resident current-work immutable receipt 寫回。
2. 若 0005-010 pending：只修 claim/runtime，不重提。
3. 若 claimed/running：只追 status。
4. 若 failed：修 Director leaf capability。
5. 若 completed：使用 Go reconciliation 驗收六項 evidence，立即進 `0005-020`。
6. 020 completed → 0005-025 text-only PPTX。
7. 025 completed → 0005-026 ODA → Google Drive publish。
8. 026 完成後才進 `0005-027` approval gate，不提前生成插圖。
