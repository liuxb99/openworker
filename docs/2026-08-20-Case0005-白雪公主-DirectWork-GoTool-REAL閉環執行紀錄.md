# Case0005 白雪公主：DirectWork + go-tool REAL 閉環執行紀錄

更新時間：2026-08-20 15:06（Asia/Taipei）

## 1. 案例目標與權威原則

Case0005 本輪沿 revision 15 工作清單完成最後成果閉環，不重新製作前段內容：

1. 0005-025：ODA 實機工作區取得 `presentation/storyboard-text-only.pptx` 實體成果。
2. 0005-026：DirectWork 作 durable business execution authority；go-tool `drive.file.publish-verified` 作純 Go Google Drive 上傳 + 獨立完整性驗證。
3. 0005-027：只有 0005-026 verified combined proof 成立後才進 LLM / 使用者 approval gate；到 gate 後停止。

固定機：`DESKTOP-ODAQN0D`（ODA）

workspace：`D:\AI-Work\jobs\0005-SNOW-WHITE`

PPTX：`D:\AI-Work\jobs\0005-SNOW-WHITE\presentation\storyboard-text-only.pptx`

Drive folder id：`1ORqerxTPVUcAmxiE0fcXMUS-XnDu3F9r`

GitHub Actions 只作 ingress / transport / receipt 回寫；不能當 business completion authority。

## 2. 正式 0005-026 → 0005-027 工具鏈

`CASE0005.PUBLISH-REVIEW`
→ ODA DirectWork `127.0.0.1:8787/v1/work`
→ durable accepted / claimed / running
→ Case driver
→ go-tool `127.0.0.1:8848/api/execution/local-work`
→ `drive.file.publish-verified`
→ pure-Go resumable upload
→ independent `drive.file.verify`
→ combined proof `evidence/0005-026-drive-publish-proof.json`
→ `openworker.review.await-drive`
→ 0005-027 approval gate。

禁止退回 Case-specific Python uploader。

## 3. dw01 / dw02：DirectWork transport quoted argv 缺口

### dw01

request：`case0005-publish-review-20260820-dw01`

work：`dw-20260820T060416-51efe43ad163af00`

accepted seq45 → claimed slot3 seq46 → running pid20392 seq47 → failed seq48 `0xfffd0000`。

### dw02

request：`case0005-publish-review-20260820-dw02`

work：`dw-20260820T062619-0a167adc742aaa9a`

accepted seq65 → claimed slot1 seq66 → running pid36504 seq67 → failed seq68 `0xfffd0000`。

Exact diagnostic 證明 PowerShell `-File` 收到 literal quoted path，business script 根本沒開始。

修復 commit：`f6479da2863d779b13bff2a8a3d618d48a24be8a`

修復：Case0005 DirectWork command 改成 bounded whitespace-free unquoted argv。

## 4. dw03：quoting 已跨過，暴露 stale go-tool contract

request：`case0005-publish-review-20260820-dw03`

receipt commit：`15fc66b2ad3607e7faf6d7be2fd30e666986e638`

work：`dw-20260820T063227-b0a02b53ec13a719`

accepted seq69 → claimed slot2 seq70 → running pid19736 seq71 → failed seq72，exit=1。

Exact diagnostic commit：`912aeb171ceedd1ba25f14af5775159845428e89`

8848 preflight：

- capability=`drive.file.publish-verified`
- supported=false
- route=`local_supervisor`
- GitHub fallback=false
- reason=`capability is not registered by the installed local executor contract`

所以 DirectWork transport 正常，真正缺口轉為 ODA live 8848 contract 過舊。

## 5. go-tool source 已有新 Drive contract

Registry commit：`cbb25ecd891385293855eaa57274cd9f4a61b13b`

已註冊：

- `drive.file.upload`
- `drive.file.verify`
- `drive.file.publish-verified`

Guidance commit：`49cc7a8d3db21826a19b60de3f1aea950696d30f`

Case0005 0005-026 正式要求 `drive.file.publish-verified`；exact upload file_id 直接傳給 independent verify，不用 filename lookup；file_id / SHA256 / exact size 必須跨 upload + verify 一致。

## 6. 第一次新版 deployment 為何沒生效

run：`32338686187`

ODA job：`96333184523`

固定機、checkout、start marker、refresh 均 PASS；在 targeted tests compile 階段失敗：

`google_drive_file_upload.go:234:6: fileSHA256 redeclared in this block`

另一 declaration：`comfyx_video.go:118:6`。

因此 build/install/bootstrap/REAL verify 全部沒發生。

## 7. compile blocker 已補齊

修復 commit：`9d28d311de65e170478e16a8b76f7462fa4ec31e`

- Drive helper 保留 `fileSHA256`
- ComfyX helper 改 `comfyXFileSHA256`
- 行為不變，只解除 package symbol collision。

Regression commit：`3b89b93b646a199bd8abb7d3dc061ee1822180ab`

新增 `TestDistinctLocalexecSHA256HelpersAgree`，固定驗證兩個 helper 對同 bytes 得到相同 SHA256。

## 8. 第二次 deployment：編譯與 install 已成功，但 terminal verify 被 concurrency 取消

run：`32341891483`

ODA job：`96342525268`

實際 source root：

`C:\github-runners\go-tool-runtime\_work\go-tool-runtime\go-tool-runtime\gtr-deploy-32341891483-ODA`

checkout 初始為 `3b89b93b...`，之後 refresh 到當時 main lineage；完整 source checkout 存在。

ODA 實際成功步驟：

1. fixed host PASS。
2. checkout PASS。
3. deployment start marker PASS。
4. refresh PASS。
5. targeted tests PASS：execution / localexec / operationalinfo / server 全部 ok。
6. build additive local tools PASS。
7. stop old local-work tasks/processes PASS。
8. install binaries PASS。
9. `install-gtr-local-work-runtime.ps1` PASS。
10. runtime 回報：`GTR_LOCAL_WORK_RUNTIME_READY host=DESKTOP-ODAQN0D queue=http://127.0.0.1:8848 mode=scheduled-task parallel=4`。
11. Tailscale ingress 顯示 target queue ready，credential DB exists。
12. 接著 workflow 因 concurrency cancellation 結束；後續 persistent control-plane verify、REAL four-slot verify、terminal deployment receipt 未執行。

重要：**binary copy / bootstrap PASS 不等於 live contract 已經 refresh**，仍必須以 8848 preflight 驗證。

## 9. dw04：實測證明 live 8848 contract 仍是舊版

request：`case0005-publish-review-20260820-dw04`

DirectWork work：`dw-20260820T070127-6fcd3224467d85b3`

DirectWork 已 accepted / claimed / running，最後 exit=1。

Exact dw04 diagnostic 已取回；8848 再次回覆 `drive.file.publish-verified` 不在 installed local executor contract。

因此第二次 deployment 雖已 build/copy/bootstrap，新 binary 並未可靠成為目前 servicing request 的完整四元 runtime contract，或 runtime restart/owner convergence 尚未完成。這個缺口不能再靠盲目重發 0005-026 解決。

## 10. 補缺口：改用正式 `go-tool.runtime.update-local` detached self-update

舊 8848 contract 本身已支援 `go-tool.runtime.update-local`，所以改用它讓本機總控升級自己，而不是再靠 Action 安裝流程。

此 capability 的硬約束：

- Windows-only。
- assigned_host 必須同時匹配 claim + input + local hostname。
- source_root 必須是 already-present 完整 checkout；不 fetch、不 pull。
- install_root 只能是 `%ProgramData%\go-tool-runtime\work-agent`。
- update 前跑 Go tests。
- 一次 stage 四 binary：`tool-runtime.exe`、`gtr-work-agent.exe`、`gtr-work-executor.exe`、`gtr-local-exec.exe`。
- durable update work 必須先寫成 completed，再由 detached updater 停 resident runtime。
- 以原 runtime mode 重啟。
- 驗證 `:8848/health`。
- 跑 REAL four-slot smoke 並要求 verification endpoint=`REAL_VERIFIED`。
- 任一 health / REAL 驗證失敗：四 binary 一起 rollback，重啟 previous runtime。

本次 allowlisted source root 使用上述真實 ODA checkout：

`C:\github-runners\go-tool-runtime\_work\go-tool-runtime\go-tool-runtime\gtr-deploy-32341891483-ODA`

並要求 marker：`internal/localexec/file_hash_helpers_test.go`，避免誤用 compile blocker 修復前 checkout。

## 11. 新增 Case0005 bounded runtime-repair 密語

DirectWork workflow commit：`b02c23987dd3a464b1113d9f83cffb22eba81f4a`

workflow：`.github/workflows/secret-case0005-runtime-repair-oda.yml`

密語：`CASE0005.RUNTIME-REPAIR`

規則：GitHub Action 只把 request 送進 DirectWork；business repair 由 DirectWork durable command 呼叫 ODA 8848 `go-tool.runtime.update-local`，`github_action_used_for_business_execution=false`。

repair request commit：`f7f010f47cd245a4364e3a17e8a6ee6dc5a62cd6`

request：`case0005-runtime-repair-20260820-r01`

repair workflow 會：

1. 驗證 ODA hostname。
2. 驗證 source root 為唯一 allowlisted checkout。
3. 驗證 go.mod / regression marker / Drive publish implementation marker。
4. DirectWork 建 durable work。
5. durable work 向舊 8848 submit `go-tool.runtime.update-local`。
6. 等 work completed。
7. detached updater 等 durable completion 後停止舊 runtime、四 binary swap、restart。
8. health check。
9. REAL four-slot verifier。
10. verification endpoint 必須 `REAL_VERIFIED`。
11. 將 DirectWork events + update work + health + verification 回寫 receipt。

目前 repair request 已送出；未取得 receipt 前不宣告 runtime 升級成功。

## 12. 0005-025 / 026 / 027 驗收規則

### 0005-025

`storyboard-text-only.pptx` 必須是 ODA 非空實體檔並取得 size + SHA256。若已存在，不重做前段白雪公主內容。

### 0005-026

必須存在：

- `evidence/0005-026-drive-upload.json`
- `evidence/0005-026-drive-verify.json`
- `evidence/0005-026-drive-publish-proof.json`

combined proof：schema=`go-tool-google-drive-publish-verified/v1`、status=`verified`、exact file_id 非空、本地 SHA256 與 proof 相同、exact size 相同、nested upload/verify 綁同 file_id/SHA/size。

### 0005-027

只有 0005-026 proof 成立才允許 `openworker.review.await-drive`。gate 還要重新驗證 canonical PPTX bytes + fresh Drive metadata，然後才進 approval boundary。

## 13. 負面知識

1. Action success ≠ Case completion。
2. deployment start marker ≠ deployment complete。
3. binary copied ≠ live servicing process 已載入新 contract。
4. DirectWork accepted/claimed/running ≠ artifact complete。
5. dw01/dw02 `0xfffd0000` = quoted argv bug；dw03/dw04 不得再用此原因解釋。
6. dw03/dw04 exact root cause = live 8848 contract 缺 `drive.file.publish-verified`。
7. repo capability 存在 ≠ installed runtime capability 存在。
8. 不得只換 `tool-runtime.exe`；四 binary 必須同一 bounded update。
9. 不得用 GitHub Action 當 runtime self-update business fallback。
10. 不得退回 Case-specific Python Drive uploader。
11. 沒有 exact file_id + SHA256 + size verified combined proof，不得進 0005-027。
12. 0005-025 已有 artifact 時不得因 runtime/transport 修復重做故事內容。

## 14. checkpoint（2026-08-20 15:06 Asia/Taipei）

- DirectWork ingress：REAL。
- argv quoting：FIXED。
- duplicate `fileSHA256` compile blocker：FIXED + regression。
- second deployment tests/build/install/bootstrap：PASS；terminal REAL verify：被 concurrency cancel，不能算 complete。
- dw04：證明 live 8848 仍 stale。
- bounded `go-tool.runtime.update-local` repair：已由 `CASE0005.RUNTIME-REPAIR` 發出，等待 durable receipt + REAL verification evidence。
- 0005-026：尚未完成。
- 0005-027：尚未進入。

下一 authority checkpoint：runtime repair receipt → `REAL_VERIFIED` → 8848 preflight 支援 `drive.file.publish-verified` → 發 dw05 → combined Drive proof → 0005-027 gate。
