# 0002 阿拉丁神燈 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`IMPLEMENTING / LAST REAL RUN FAILED / HYGIENE PREFLIGHT WIRED / BACKEND HEARTBEAT WIRED / VERIFYING`

## 已完成

- 案例 canonical 入口已收斂到 OpenWorker `examples/0002-aladdin/`。
- go-tool 正式 `engineering.source-to-film` contract 已能承載 `story / title / delivery_case`。
- OS production workflow 已能接收 canonical inputs，不再把阿拉丁故事寫死在 case script。
- 最新工具 contract gate 已在正式 production run 全綠。
- 固定 OpenWorker workspace 已建立。
- ComfyUI Desktop REAL / isolated readiness 曾 PASS。
- 正式 execution 由 go-tool 建立，不是直接手動觸發 OS workflow。

## 最近一次 REAL execution

- go-tool execution / target run：`engineering.source-to-film:31916089801`
- AI-Engineering-OS workflow：`Case 0002 OpenWorker REAL Production V3`
- OS run：`31916089801`
- production job：`95087955499`
- runner：`DESKTOP-ODAQN0D-R003`
- OS head：`86376b7ef635afa65de1aa1bd591b5908958812c`

該 run 已完成以下 gate：

- Route transport：PASS
- Checkout OS / OpenWorker / go-tool / Studio / ComfyX：PASS
- Verify information and execution contracts：PASS
- Prepare fixed OpenWorker workspace：PASS
- Ensure ComfyUI Desktop backend is REAL and isolated：PASS
- go-tool bootstrap / query：PASS
- OpenWorker job binding：PASS
- OS → Studio Source-to-Film dispatch：PASS

## 最近一次失敗點

Source-to-Film dispatch 已成功建立：

- OpenWorker Project：`prj_1357fb0aede5a80f389ba4f2eee54bc1`
- OS Job：`job_343aaa39fa6da28bb834812599f04fb4`
- Studio Project：`os-job_343aaa39fa6da28bb834812599f04fb4`
- ProductionQueue：`os-job_343aaa39fa6da28bb834812599f04fb4-production`
- generation：`1280x736`
- delivery：`1280x720`

但 production 等待 1800 秒後 timeout。關鍵 evidence 顯示：ComfyUI 在 run 開始時 `/object_info` 正常，之後 Intelligence 每 5 分鐘 discovery 都得到 `127.0.0.1:8188 connection refused`。因此這輪不能算 Shot 1 成功。

## 本批修復：go-tool execution hygiene

已在 `liuxb99/go-tool-runtime` 補正式 workflow-scoped queue drain：

1. `CapabilityWorkflowRuns`：只查 capability 註冊的 workflow，不再默認清整個 repository。
2. `DrainCapabilityWorkflow`：取消同一 capability workflow 的 conflicting queued / in_progress / waiting / pending runs。
3. 支援 `exclude_run_ids`：REAL workflow 可保留目前自己的 `GITHUB_RUN_ID`，不會清場時把自己取消。
4. cancellation 後持續 re-query，直到 conflicting queue 清空；超時則 `queue_drain_incomplete` fail-closed。
5. 新 API：
   - `GET /api/execution/queues/{capability_id}`
   - `POST /api/execution/queues/{capability_id}/drain`
6. `gtr-actions-queue` CLI 已改為 workflow-scoped 預設，新增 `--exclude-run-id` / `--verify-seconds`。
7. 已新增永久測試，驗證 current run preserve + conflicting run cancellation。

本批 go-tool 主要提交：

- `9dfe8c34fc5751c5bf113219b53f53f577b65fbb` — workflow-scoped queue drain service
- `9b6a454beb9cb2a7507a93808e07fa128285ba78` — queue preflight API
- `2aabcffd61b1df08addcb9c9f3afae51d2154b4b` — register queue API
- `a666b4750ef17d217a98bd681e0224c9a6cc9f12` — CLI self-preserving cleanup
- `99c20c0d56a8ab3fb9837d719e75811140546970` — permanent queue-drain tests

## 本批修復：ComfyUI backend heartbeat fail-fast

AI-Engineering-OS `scripts/cases/case0002_openworker_source_to_film.py` 已改為 production waiting 期間同步檢查 ComfyUI `/object_info`：

- 每次輪詢 Source-to-Film status 時做 backend heartbeat。
- backend 恢復時會記錄 recovered。
- 連續 3 次 heartbeat failure 立即報 backend died，不再等待完整 30 分鐘。
- heartbeat samples 寫入 `03a-backend-heartbeat.json` 作 REAL evidence。

初始 heartbeat 提交：`1fe87df87d31e4257492afa5ff95d6b7c05ec6e5`。

## 本批完成：0002 正式接上 go-tool hygiene preflight

不再只是「go-tool 有 queue 清理 API」。案例本身已在正式 Source-to-Film dispatch 前呼叫：

`POST /api/execution/queues/engineering.source-to-film/drain`

並傳入目前 `GITHUB_RUN_ID` 到 `exclude_run_ids`，因此：

- 舊的同 workflow conflicting run 會先取消；
- 目前正在執行的 0002 run 保留；
- queue 必須 re-query 到 `clean=true` 才能繼續；
- evidence 寫入 `01a-execution-hygiene.json`。

整合提交：`75f8e4bad4e4a1cafc56e2c29441255f722bf384`。

## 驗證狀態

本批 push 已觸發實機驗證：

- go-tool-runtime Win11 Local Verification：run `31919340953`，建立本紀錄時為 `queued`。
- AI-Engineering-OS Case 0002 REAL Production Trigger：run `31919334919`，建立本紀錄時為 `queued`。
- AI-Engineering-OS OpenWorker Win11 Baseline：run `31919334756`，建立本紀錄時已進入 `in_progress`。

因此本批目前只能標記 `IMPLEMENTED / VERIFYING`，不能提前標 `VERIFIED`。

## 下一個驗收點

下一個正式 0002 execution 必須依序證明：

`go-tool queue inspect/drain → preserve current run → queue clean → ComfyUI clean/ready → OpenWorker → OS → Studio → audited ComfyX → H3 REAL`

若 ComfyUI 再掉線，必須在約數個 heartbeat 週期內 fail-fast 並留下 `03a-backend-heartbeat.json`，不得再用 30 分鐘 timeout 才發現。

Shot 1 physical MP4 + execution correlation + Studio canonical workspace + SHA256 identity + visual semantic QC 全部 PASS 後才標記 Shot 1 ACCEPT；之後直接推進 Shot 2–4、1280×720 Final Assembly、字幕/QC、Artifact Registry、Delivery Revision、`delivery/website/index.html`。