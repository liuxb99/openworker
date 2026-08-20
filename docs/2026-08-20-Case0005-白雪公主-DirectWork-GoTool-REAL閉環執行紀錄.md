# Case0005 白雪公主：DirectWork + go-tool REAL 閉環執行紀錄

更新時間：2026-08-20 14:49（Asia/Taipei）

## 1. 案例目標與目前權威狀態

Case0005 的本輪目標不是重新製作前段內容，而是沿 revision 15 工作清單完成最後成果閉環：

1. 0005-025：在 ODA 實機工作區取得 `presentation/storyboard-text-only.pptx` 實體成果。
2. 0005-026：使用最新版 DirectWork 作 durable business execution authority，並由最新版 go-tool `drive.file.publish-verified` 執行純 Go Google Drive 上傳 + 獨立完整性驗證。
3. 0005-027：只有在 0005-026 取得 verified combined proof 後才進入 LLM / 使用者 approval gate；到 gate 後停止，不擅自繼續後續製片。

固定執行機：`DESKTOP-ODAQN0D`（ODA）

固定 workspace：`D:\AI-Work\jobs\0005-SNOW-WHITE`

預期成果：`D:\AI-Work\jobs\0005-SNOW-WHITE\presentation\storyboard-text-only.pptx`

Drive folder id：`1ORqerxTPVUcAmxiE0fcXMUS-XnDu3F9r`

重要原則：GitHub Actions 只負責 ingress / transport / receipt 回寫，不作 Case business execution authority。DirectWork durable work / go-tool local-work / REAL artifact / Drive proof 才是完成依據。

## 2. 最新工具鏈

本輪採用：

`CASE0005.PUBLISH-REVIEW` 密語
→ GitHub transport
→ ODA DirectWork `127.0.0.1:8787/v1/work`
→ DirectWork durable work accepted / claimed / running
→ ODA PowerShell case driver
→ go-tool `127.0.0.1:8848/api/execution/local-work`
→ capability `drive.file.publish-verified`
→ 純 Go Google Drive uploader
→ independent `drive.file.verify`
→ combined proof `evidence/0005-026-drive-publish-proof.json`
→ `openworker.review.await-drive`
→ 0005-027 approval gate。

本輪明確禁止退回舊 Case-specific Python uploader；Google Drive 正式路徑使用 go-tool 的純 Go uploader / verifier。

## 3. DirectWork dw01：第一次 durable evidence

request：`case0005-publish-review-20260820-dw01`

DirectWork work id：`dw-20260820T060416-51efe43ad163af00`

ODA 已實際建立 durable work，事件序列：

- seq 45 accepted：durable work created
- seq 46 claimed：slot=3，machine=`DESKTOP-ODAQN0D`
- seq 47 running：pid=20392
- seq 48 failed：`exit status 0xfffd0000`

結論：DirectWork ingress、durable queue、claim slot、ODA executor 均有 REAL evidence；失敗點不是「沒有接單」。

後續 ODA diagnostic 抓到 stderr，確認 Windows PowerShell 收到的 `-File` 值含 literal quote，形如：

`-File '"C:\WINDOWS\TEMP\case0005-publish-review-...ps1"'`

PowerShell 因此判定 script path 無效，Case driver 根本尚未開始；所以 dw01 不可歸因於 Drive 或 go-tool。

## 4. DirectWork dw02：確認同一 transport bug 可重現

request：`case0005-publish-review-20260820-dw02`

DirectWork work id：`dw-20260820T062619-0a167adc742aaa9a`

事件：

- seq 65 accepted
- seq 66 claimed：slot=1，ODA
- seq 67 running：pid=36504
- seq 68 failed：`exit status 0xfffd0000`

finished_at：`2026-08-20T06:26:20.0119924Z`

result：null；artifact：空。

結論：再次證明 DirectWork 能接案，但舊 quoted argv 使 PowerShell 在 business script 之前立即失敗。

## 5. 修復：DirectWork Windows argv quoting

DirectWork commit：`f6479da2863d779b13bff2a8a3d618d48a24be8a`

修復內容：Case0005 publish workflow 不再把 `-File`、request id、workspace、PPTX、receipt path 等值包成會被 DirectWork tokenizer 保留為 literal 的雙引號。Case0005 本輪所有相關 path / ID 均不含空白，因此改成 unquoted argv。

這是 transport 修復，不改變 Case business semantics，也不把 GitHub Actions 升格為 business executor。

## 6. DirectWork dw03：quoting 修復已生效，但進入下一層錯誤

request：`case0005-publish-review-20260820-dw03`

DirectWork receipt commit：`15fc66b2ad3607e7faf6d7be2fd30e666986e638`

DirectWork work id：`dw-20260820T063227-b0a02b53ec13a719`

實際 command 已變為 unquoted argv，例如：

`powershell.exe ... -File C:\WINDOWS\TEMP\case0005-publish-review-case0005-publish-review-20260820-dw03.ps1 ...`

這證明 `f6479da` 的 quoting 修復確實已進入 REAL ODA dispatch。

事件：

- seq 69 accepted：`2026-08-20T06:32:27.2739433Z`
- seq 70 claimed：slot=2，machine=ODA
- seq 71 running：pid=19736
- seq 72 failed：`exit status 1`

finished_at：`2026-08-20T06:32:27.7791535Z`

這次 exit code 已從 `0xfffd0000` 變為普通 `1`，表示舊的 `-File literal quote` 問題已被跨過；目前已進入下一層實際 PowerShell / Case driver failure。由於 receipt 的 `result=null`、artifact 空，尚不能聲稱已進入或完成 `drive.file.publish-verified`。

## 7. 目前正在做的診斷

已更新 DirectWork diagnostic workflow，使其額外抓取：

- `dw-20260820T063227-b0a02b53ec13a719.stdout.log`
- `dw-20260820T063227-b0a02b53ec13a719.stderr.log`
- 同時保留 dw02 / dw01 對照。

workflow 更新 commit：`3da6bdf9e87914a440497887faa96cbcb9a8e597`

診斷 request commit：`b41d3c05bc62fbf60438b50477e355b8c17b4cb1`

診斷 request token：`case0005-directwork-log-diagnostic-20260820-03`

下一步必須以 dw03 exact stderr/stdout 為 authority，不以猜測判定原因。

## 8. 0005-025 / 0005-026 / 0005-027 判定規則

### 0005-025

只有 ODA 上 `storyboard-text-only.pptx` 為非空實體檔，且取得 size + SHA256，才算 artifact evidence。若檔案不存在，應回到 0005-025 生成；若已存在，不重做前段故事內容。

### 0005-026

必須由 `drive.file.publish-verified` 完成並產生 combined proof。預期 evidence：

- `evidence/0005-026-drive-upload.json`
- `evidence/0005-026-drive-verify.json`
- `evidence/0005-026-drive-publish-proof.json`

combined proof 至少必須滿足：

- schema = `go-tool-google-drive-publish-verified/v1`
- status = `verified`
- exact `file_id` 非空
- proof SHA256 = ODA 本地 PPTX SHA256
- proof size = ODA 本地 PPTX exact size
- upload 與 independent verify 指向同一 exact file_id

未滿足以上條件，0005-026 不得標記完成。

### 0005-027

只有 0005-026 verified proof 成立後，才提交 `openworker.review.await-drive`。目標 evidence：`evidence/0005-027-drive-gate.json`。

Case 到達 WAITING_LLM_REVIEW / approval gate 後停止，等待 ChatGPT / 使用者審查 storyboard-text-only PPTX。

## 9. 已知失敗與負面知識

1. GitHub Action success 不能當成 Case business completion。
2. DirectWork accepted / claimed / running 只能證明 durable execution 已開始，不代表成果完成。
3. `0xfffd0000` 在本次 dw01/dw02 是 PowerShell `-File` literal quote transport bug，不是 Drive auth failure。
4. 修復 quoting 後 dw03 已進入 exit code 1；不得再用舊 quoting 根因解釋 dw03。
5. 不得為 Case0005 再發明 Python Drive uploader；正式單檔發布使用 go-tool `drive.file.publish-verified`。
6. 沒有 exact file_id + SHA256 + size matching combined proof，不得進 0005-027。
7. 若 0005-025 artifact 已存在，不得為了修 transport 重做前段白雪公主內容。

## 10. 目前 checkpoint

截至 2026-08-20 14:49 Asia/Taipei：

- DirectWork REAL durable ingress：已證明。
- ODA claim / executor slot：已證明。
- Windows quoted argv bug：已定位並修復。
- dw03：已跨過舊 `0xfffd0000`，目前 exit code 1。
- dw03 exact stderr/stdout：已發 diagnostic request，等待 REAL 回寫。
- 0005-026 Drive verified publish：尚未有 combined proof，不可宣告完成。
- 0005-027 approval gate：尚未進入。

下一個 checkpoint：讀取 dw03 exact stderr/stdout → 修下一個實際 failure → 重新發 `CASE0005.PUBLISH-REVIEW` → 取得 `drive.file.publish-verified` combined proof → 進 0005-027 gate → 停止等待審查。
