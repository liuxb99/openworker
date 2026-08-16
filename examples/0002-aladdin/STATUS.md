# 0002 阿拉丁神燈 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`IMPLEMENTING / HYGIENE PREFLIGHT WIRED / BACKEND HEARTBEAT WIRED / GO-TOOL REGRESSION GREEN / VERIFYING`

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

## 本批新發現與修復

go-tool Win11 run `31919340953` 的 full regression 失敗原因不是 queue-drain implementation，而是新永久測試硬編碼了錯誤 workflow 名 `test.yml`；共用 `testConfig()` 真正 registered workflow 是 `run.yml`。

已修正測試，讓永久測試直接驗 capability 真正註冊的 workflow。

修復提交：`fced16eedede6a213cd886212d98c93361b93e37`。

## 目前驗證

修正後 go-tool Win11 Local Verification run `31919459618` 已通過：

- Full regression suite：PASS
- Vet：PASS
- Build Windows executable：PASS
- GitHub Actions execution provider tests：PASS
- Immediate environment probe：PASS
- Empty workspace bootstrap：PASS
- Engineering OS live bridge：PASS
- services/models/jobs/artifacts：PASS
- runner heartbeat：PASS
- readiness fail-closed：PASS
- production security：PASS
- observability：PASS
- Agent information pack：PASS

建立本紀錄時只剩 post-checkout cleanup 尚在收尾，因此功能 gate 已全綠。

其他仍在驗證：

- go-tool Operator E2E 0001：run `31919459625`。
- AI-Engineering-OS OpenWorker Win11 Baseline：run `31919403381`，Full Python baseline suite 執行中。

前一個 OS baseline `31919334756` 是被後續同分支 push supersede/cancel，不視為產品失敗。

## 下一個驗收點

剩餘 baseline / E2E gate 綠後，重新從 go-tool 正式 dispatch 0002：

`go-tool queue inspect/drain → preserve current run → queue clean → ComfyUI clean/ready → OpenWorker → OS → Studio → audited ComfyX → H3 REAL`

若 backend 再掉線，應在連續 3 個 heartbeat failure 後立即失敗並留下 `03a-backend-heartbeat.json`，不再等待 30 分鐘。

Shot 1 physical MP4 + execution correlation + Studio canonical workspace + SHA256 identity + visual semantic QC 全部 PASS 後才標 Shot 1 ACCEPT；接著推進 Shot 2–4、1280×720 Final Assembly、字幕/QC、Artifact Registry、Delivery Revision、`delivery/website/index.html`。