# Case0005 白雪公主：DirectWork + go-tool REAL 閉環執行紀錄

更新時間：2026-08-20 14:59（Asia/Taipei）

## 1. 案例目標與目前權威狀態

Case0005 本輪沿 revision 15 工作清單完成最後成果閉環，不重新製作前段內容：

1. 0005-025：ODA 實機工作區取得 `presentation/storyboard-text-only.pptx` 實體成果。
2. 0005-026：最新版 DirectWork 作 durable business execution authority；最新版 go-tool `drive.file.publish-verified` 作純 Go Google Drive 上傳 + 獨立完整性驗證。
3. 0005-027：0005-026 verified combined proof 成立後才進 LLM / 使用者 approval gate；到 gate 後停止。

固定執行機：`DESKTOP-ODAQN0D`（ODA）

固定 workspace：`D:\AI-Work\jobs\0005-SNOW-WHITE`

預期成果：`D:\AI-Work\jobs\0005-SNOW-WHITE\presentation\storyboard-text-only.pptx`

Drive folder id：`1ORqerxTPVUcAmxiE0fcXMUS-XnDu3F9r`

權威原則：GitHub Actions 只作 ingress / transport / receipt 回寫；DirectWork durable work、go-tool local-work、REAL artifact、Drive proof 才是業務完成依據。

## 2. 最新工具鏈

`CASE0005.PUBLISH-REVIEW` 密語
→ GitHub transport
→ ODA DirectWork `127.0.0.1:8787/v1/work`
→ DirectWork durable accepted / claimed / running
→ ODA Case driver
→ go-tool `127.0.0.1:8848/api/execution/local-work`
→ `drive.file.publish-verified`
→ 純 Go resumable Drive upload
→ independent `drive.file.verify`
→ `evidence/0005-026-drive-publish-proof.json`
→ `openworker.review.await-drive`
→ 0005-027 approval gate。

禁止退回 Case-specific Python uploader。

## 3. dw01：DirectWork 已接案，最初 transport failure

request：`case0005-publish-review-20260820-dw01`

work id：`dw-20260820T060416-51efe43ad163af00`

事件：accepted seq45 → claimed slot3 seq46 → running pid20392 seq47 → failed seq48 `0xfffd0000`。

ODA diagnostic 證明 PowerShell `-File` 收到 literal quoted path，business script 根本未開始。故 dw01 不能歸因 Drive/go-tool。

## 4. dw02：同一 quoted argv bug 重現

request：`case0005-publish-review-20260820-dw02`

work id：`dw-20260820T062619-0a167adc742aaa9a`

事件：accepted seq65 → claimed slot1 seq66 → running pid36504 seq67 → failed seq68 `0xfffd0000`。

result=null、artifact 空。再次確認 DirectWork durable ingress 正常，錯在 Windows argv quoting。

## 5. DirectWork argv 修復

commit：`f6479da2863d779b13bff2a8a3d618d48a24be8a`

Case0005 publish workflow 改為 DirectWork tokenizer 可接受的 unquoted argv。這是 transport 修復，不改變 business authority。

## 6. dw03：已跨過 quoting，精確根因改為 go-tool installed contract 過舊

request：`case0005-publish-review-20260820-dw03`

receipt commit：`15fc66b2ad3607e7faf6d7be2fd30e666986e638`

work id：`dw-20260820T063227-b0a02b53ec13a719`

事件：

- seq69 accepted：`2026-08-20T06:32:27.2739433Z`
- seq70 claimed：slot=2，ODA
- seq71 running：pid=19736
- seq72 failed：exit status 1

exact diagnostic commit：`912aeb171ceedd1ba25f14af5775159845428e89`

### dw03 exact stderr

go-tool local supervisor 回應：

- `assigned_host=DESKTOP-ODAQN0D`
- `capability_id=drive.file.publish-verified`
- `capability_supported=false`
- `execution_route=local_supervisor`
- `github_action_fallback_allowed=false`
- `github_action_used_for_business_execution=false`
- reason：`capability is not registered by the installed local executor contract`
- schema：`gtr-local-capability-preflight/v1`
- status：`rejected`

ODA 當時 installed contract 列出的 capabilities 包含 `drive.review.publish`、`openworker.review.await-drive`、`presentation.openmaic` 等，但沒有 `drive.file.upload`、`drive.file.verify`、`drive.file.publish-verified`。

因此 dw03 的真正失敗點：DirectWork transport 已修好；ODA `127.0.0.1:8848` installed local executor contract 尚未註冊新版純 Go Drive capabilities。這不是 Drive credential error、PPTX error，也不是 DirectWork 不接案。

## 7. repo capability 與 ODA runtime 差異

go-tool main registry binding commit：`cbb25ecd891385293855eaa57274cd9f4a61b13b`，已註冊：

- `drive.file.upload`
- `drive.file.verify`
- `drive.file.publish-verified`

capability guidance commit：`49cc7a8d3db21826a19b60de3f1aea950696d30f`，明確指定 Case0005 0005-026 優先使用 `drive.file.publish-verified`，並要求 exact file_id + SHA256 + exact size 一致。

ODA deployment run `32338686187` 雖寫入 start marker，但 terminal run conclusion=`failure`，所以沒有新的 REAL verified deployment receipt 取代舊版本。

## 8. deployment run 32338686187 的精確失敗原因

ODA job id：`96333184523`

流程已成功到：

- Verify fixed machine：PASS，machine=`DESKTOP-ODAQN0D`
- checkout：PASS
- Persist deployment start marker：PASS
- Refresh checkout：PASS

在 `Targeted local-work and localexec tests` 編譯失敗，Go compiler 原文：

`internal\localexec\google_drive_file_upload.go:234:6: fileSHA256 redeclared in this block`

另一個 declaration：

`internal\localexec\comfyx_video.go:118:6: other declaration of fileSHA256`

所以後續 Build / Stop old runtime / Install / Bootstrap 8848 / REAL four-slot verification / terminal receipt 全部被 skipped。這完整解釋為什麼 repo 已有新 capability、ODA runtime 還停在舊 contract。

## 9. 已補齊 compile blocker

修復 commit：`9d28d311de65e170478e16a8b76f7462fa4ec31e`

修法：保留 Google Drive helper `fileSHA256`；將 ComfyX 私有 helper 改名為 `comfyXFileSHA256`，同步修改 `copyFileSHA256Atomic` 呼叫點。兩者功能不變，只解除同 package symbol collision。

新增 regression commit：`3b89b93b646a199bd8abb7d3dc061ee1822180ab`

新增 `internal/localexec/file_hash_helpers_test.go`，驗證 Drive helper 與 ComfyX helper 對同一 bytes 算得完全相同 SHA256，防止未來再次因共用 helper 命名而破壞行為。

修復 commit 已觸發 deployment run `32341842391`，ODA 已寫入 start marker `b59bfc10cbcd160d31dd556741db5b7830dc3f06`。但隨後 regression commit 進 main，workflow concurrency `cancel-in-progress=true` 令 run `32341842391` conclusion=`cancelled`；這是新 commit 取代舊 deploy attempt，不應誤判為編譯修復失敗。

目前等待以 `3b89b93...` 為 head 的最新 deploy attempt 成為 authority；不再追加無關 commit，避免再次把 deploy run cancel 掉。

## 10. 0005-025 / 026 / 027 完成規則

### 0005-025

ODA `storyboard-text-only.pptx` 必須是非空實體檔並取得 size + SHA256。已存在就不重做前段內容。

### 0005-026

必須取得：

- `evidence/0005-026-drive-upload.json`
- `evidence/0005-026-drive-verify.json`
- `evidence/0005-026-drive-publish-proof.json`

combined proof 必須：schema=`go-tool-google-drive-publish-verified/v1`、status=`verified`、exact file_id 非空、SHA256 與本地一致、size 與本地一致、upload/verify 綁定同一 exact file_id。

### 0005-027

只有 0005-026 proof 成立才允許 `openworker.review.await-drive`。最新 go-tool gate 還要求重新驗證 canonical PPTX bytes 與 fresh Drive metadata，通過後才可進 approval boundary。

## 11. 負面知識

1. Action success ≠ Case completion。
2. DirectWork accepted/claimed/running ≠ artifact complete。
3. dw01/dw02 的 `0xfffd0000` = quoted `-File` transport bug。
4. dw03 exact root cause = installed local executor contract 不支援 `drive.file.publish-verified`。
5. repo capability 定義存在 ≠ ODA runtime 已載入；必須以 8848 preflight / terminal deployment receipt 為 authority。
6. deployment start marker ≠ deployment complete；run `32338686187` 已證明可能 start 後在 compile 階段失敗。
7. `fileSHA256` duplicate symbol 是本輪真實 deployment blocker，已補 code + regression。
8. 不得退回舊 Python uploader。
9. 沒有 exact file_id + SHA256 + size verified combined proof，不得進 0005-027。
10. 0005-025 已有 artifact 時不得因 transport/runtime 修復重做故事內容。

## 12. checkpoint（2026-08-20 14:59 Asia/Taipei）

- DirectWork durable ingress：REAL 已證明。
- ODA claim / executor slots：REAL 已證明。
- Windows argv quoting：已修復。
- dw03 exact root cause：已取得。
- go-tool repo registry：已有 `drive.file.publish-verified`。
- 舊 ODA deployment failure：已定位到 duplicate `fileSHA256` compile error。
- compile blocker：已修 commit `9d28d311`。
- regression：已補 commit `3b89b93b`。
- ODA runtime contract refresh：正在由最新 deploy attempt 接續，尚未取得新 terminal REAL receipt。
- 0005-026：尚未完成。
- 0005-027：尚未進入。

下一 checkpoint：取得 ODA 新 deployment terminal receipt → 8848 preflight 列出 `drive.file.publish-verified` → 發新 `CASE0005.PUBLISH-REVIEW` → combined proof verified → 0005-027 approval gate → 停止等待審查。
