# 0002 阿拉丁神燈 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`IMPLEMENTING / HYGIENE PREFLIGHT WIRED / BACKEND HEARTBEAT WIRED / GO-TOOL CORE GREEN / OUTER GATES REPAIRED / VERIFYING`

## 已完成

- 案例 canonical 入口已收斂到 OpenWorker `examples/0002-aladdin/`。
- go-tool 正式 `engineering.source-to-film` contract 已能承載 `story / title / delivery_case`。
- OS production workflow 已能接收 canonical inputs，不再把阿拉丁故事寫死在 case script。
- 固定 OpenWorker workspace 已建立。
- 正式 execution 由 go-tool 建立，不是直接手動觸發 OS workflow。
- 0002 已在 production dispatch 前正式呼叫 go-tool workflow-scoped queue drain。
- 0002 production waiting 已加入 ComfyUI backend heartbeat fail-fast。

## 最近一次 REAL production 結果

最近一次正式 execution：`engineering.source-to-film:31916089801`

- OS run：`31916089801`
- production job：`95087955499`
- runner：`DESKTOP-ODAQN0D-R003`
- OpenWorker Project：`prj_1357fb0aede5a80f389ba4f2eee54bc1`
- OS Job：`job_343aaa39fa6da28bb834812599f04fb4`
- Studio Project：`os-job_343aaa39fa6da28bb834812599f04fb4`
- ProductionQueue：`os-job_343aaa39fa6da28bb834812599f04fb4-production`
- generation：`1280x736`
- delivery：`1280x720`

該 run 的 go-tool bootstrap、OpenWorker binding、OS → Studio dispatch、ComfyUI initial readiness 都 PASS；production 中途 ComfyUI `127.0.0.1:8188` 失聯，最後 1800 秒 timeout，因此 Shot 1 未 ACCEPT。

## 已補：go-tool execution hygiene

`liuxb99/go-tool-runtime` 現已具備 workflow-scoped queue hygiene：

- `CapabilityWorkflowRuns`
- `DrainCapabilityWorkflow`
- `exclude_run_ids` 保留目前自己的 run
- queued / in_progress / waiting / pending conflicting runs 取消
- cancellation 後 re-query，直到 clean；未清乾淨則 fail-closed
- `GET /api/execution/queues/{capability_id}`
- `POST /api/execution/queues/{capability_id}/drain`
- `gtr-actions-queue --exclude-run-id ... --verify-seconds ...`

主要提交：

- `9dfe8c34fc5751c5bf113219b53f53f577b65fbb`
- `9b6a454beb9cb2a7507a93808e07fa128285ba78`
- `2aabcffd61b1df08addcb9c9f3afae51d2154b4b`
- `a666b4750ef17d217a98bd681e0224c9a6cc9f12`
- `fced16eedede6a213cd886212d98c93361b93e37` — 修正永久測試使用真正 registered workflow。

## 已補：0002 正式 preflight 接線

AI-Engineering-OS 0002 case 會在 Source-to-Film dispatch 前呼叫：

`POST /api/execution/queues/engineering.source-to-film/drain`

並把目前 `GITHUB_RUN_ID` 放入 `exclude_run_ids`。只有回傳 `clean=true` 才繼續 production；結果寫入 `01a-execution-hygiene.json`。

整合提交：`75f8e4bad4e4a1cafc56e2c29441255f722bf384`。

## 已補：ComfyUI backend heartbeat

Production waiting 期間每個 status poll 同步 probe `/object_info`：

- 正常：failure counter 歸零。
- 恢復：記錄 recovered。
- 連續 3 次失敗：立即報 `ComfyUI backend died during source-to-film`。
- evidence：`03a-backend-heartbeat.json`。

初始 heartbeat 提交：`1fe87df87d31e4257492afa5ff95d6b7c05ec6e5`。

## go-tool 核心驗證已綠

go-tool Win11 Local Verification run `31919459618` 已 `success`：full regression、vet、Windows build、Actions provider、environment probe、workspace bootstrap、Engineering OS bridge、runner heartbeat、readiness fail-closed、production security、observability、Agent information pack 全部 PASS。

## 本批新發現：外層 E2E / baseline 本身不符合目前正式環境

### 1. go-tool Operator E2E 0001 credential bootstrap

舊 run `31919459625` 被排到 `DESKTOP-O87PJNR-R030`，runtime 啟動後找不到可用 local GitHub credential，`/api/execution/credentials/github/bootstrap` 回 `local_credential_source_missing`。另外 artifact storage quota 仍滿，但 artifact upload 已是 `continue-on-error`，不應當作產品 gate。

本批已修 workflow：

- 明確給 `actions: write`。
- 把 `${{ secrets.GH_TOKEN || github.token }}` 注入 `GITHUB_TOKEN` 與 `GH_TOKEN`，讓 runtime bootstrap 在任一合法 self-hosted runner 都有 bounded credential source。
- artifact upload 保留為非阻塞 evidence mirror。

提交：`f0ab9bf14fa5088b33f46dabae2917e9915b8537`。

新驗證：

- Operator E2E 0001 run `31919939846`：建立本紀錄時 `in_progress`。
- Win11 Local Verification run `31919939848`：建立本紀錄時 `in_progress`。

### 2. AI-Engineering-OS OpenWorker baseline 驗錯舊版

舊 run `31919403381` checkout 的是早期固定 SHA `468d581...`，並跑整套 1238+ tests；失敗包含 Windows symlink privilege、NetworkService ACL、舊 engineering state expectation、relay timing 等，與目前 0002 Source-to-Film contract 無直接關係。

本批已修 baseline：

- checkout 改為目前工程分支 `engineering-h11-workspace-bootstrap`。
- 不再宣稱早期 pre-H1 SHA 是 current baseline。
- baseline 改驗 0002 真正依賴的 contract：project lifecycle、source-to-film、source-to-film status、job binding。

提交：`92472d12d10e2f080f15f4c0d3f4239528265347`。

新 OpenWorker baseline run：`31919947413`，建立本紀錄時為 `in_progress/queued-to-runner`。

## 下一個驗收點

上述兩個 repaired outer gate 綠後，重新從 go-tool 正式 dispatch 0002：

`go-tool queue inspect/drain → preserve current run → queue clean → ComfyUI clean/ready → OpenWorker → OS → Studio → audited ComfyX → H3 REAL`

若 backend 再掉線，應在連續 3 個 heartbeat failure 後立即失敗並留下 `03a-backend-heartbeat.json`，不再等待 30 分鐘。

Shot 1 physical MP4 + execution correlation + Studio canonical workspace + SHA256 identity + visual semantic QC 全部 PASS 後才標 Shot 1 ACCEPT；接著推進 Shot 2–4、1280×720 Final Assembly、字幕/QC、Artifact Registry、Delivery Revision、`delivery/website/index.html`。