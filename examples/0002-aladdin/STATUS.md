# 0002 阿拉丁神燈 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`IMPLEMENTING / FORMAL REAL REACHED SHOT-1 / FALSE-SUCCESS GAP FOUND / 4-SHOT CONTRACT ENFORCED / VERIFYING`

## 已完成的基礎鏈

- canonical 入口：OpenWorker `examples/0002-aladdin/`。
- go-tool `engineering.source-to-film` 已承載 `story / title / delivery_case`。
- production dispatch 前正式執行 workflow-scoped queue drain，支援 `exclude_run_ids` 保留目前 run，清不乾淨則 fail-closed。
- queue hygiene evidence：`01a-execution-hygiene.json`。
- production waiting 已加入 ComfyUI `/object_info` heartbeat；連續 3 次 failure 立即報 backend died。
- heartbeat evidence：`03a-backend-heartbeat.json`。
- go-tool Win11 核心 gate run `31919459618`：`success`。
- go-tool Operator E2E 0001 run `31919939846`：`success`。
- AI-Engineering-OS OpenWorker Source-to-Film baseline run `31919947413`：`success`。

## 本輪已真正命中 ODAQ 並完成正式 REAL dispatch

上一輪兩個候選都被非 ODAQ runner 接走，只得到假綠；因此 hostname routing fan-out 已由 2 擴成 24，仍只以 `COMPUTERNAME == DESKTOP-ODAQN0D` 判定 production host，並使用 host-local lock 保證只 dispatch 一次。

提交：`b4718f0977f91f2889d393da0ecddafa3cede666`。

正式 routing run：`31920155718`。

本輪已出現真正的 production host 命中：

- go-tool job：`95098649472`（`e2e (2)`）。
- runner：`DESKTOP-ODAQN0D-R002`。
- log：`0002_DISPATCH_HOST_OK ... host=DESKTOP-ODAQN0D`。
- 正式 go-tool execution：`engineering.source-to-film:31920165702`。

因此這一輪不是直接手動觸發 OS，而是正式由 go-tool 建立 Source-to-Film execution。

## 最新 REAL production：Shot 1 已實際生成

AI-Engineering-OS 正式 production：

- run：`31920165702`。
- assigned production job：`95098676890`（`production (4)`）。
- runner：`DESKTOP-ODAQN0D-R003`。
- workspace：`D:\AI-Work\jobs\0002-ALADDIN`。
- OpenWorker project：`prj_1357fb0aede5a80f389ba4f2eee54bc1`。
- OS job：`job_343aaa39fa6da28bb834812599f04fb4`。
- Studio project：`os-job_343aaa39fa6da28bb834812599f04fb4`。
- ProductionQueue：`os-job_343aaa39fa6da28bb834812599f04fb4-production`。
- generation：`1280x736`。
- delivery contract：`1280x720`。

本輪 preflight / runtime evidence：

- ComfyUI isolated readiness：PASS，queue empty。
- go-tool information query：PASS。
- execution hygiene：`cancelled=[] preserved=[31920165702] clean=True`。
- OpenWorker binding：PASS。
- OS → Studio Source-to-Film dispatch：PASS。
- backend heartbeat：未觸發 3-consecutive-failure fail-fast。
- Source-to-Film platform status：`succeeded`。

已取得真實 Shot 1 execution evidence：

- queue item：`shot.generate:shot-1`。
- status：`succeeded`。
- attempt：`1`。
- ComfyX execution：`comfyui:32c105b3-6cfe-4574-bf42-7cdfd7410353`。
- prompt id：`32c105b3-6cfe-4574-bf42-7cdfd7410353`。
- tool：`comfyx.minimax_h3.generate`。
- artifact：`MiniMax_H3_00011_.mp4`。

本輪 workspace evidence 已落地：

- `00-dispatch-input.json`
- `00-go-tool-bootstrap.json`
- `01-go-tool-query-source-to-film.json`
- `01a-execution-hygiene.json`
- `02-openworker-job-binding.json`
- `03-openworker-source-to-film-dispatch.json`
- `03a-backend-heartbeat.json`
- `04-openworker-source-to-film-terminal.json`

GitHub artifact mirror 因帳號 Actions artifact storage quota 已滿而無法上傳，但該步為 non-blocking mirror；本機固定 workspace evidence 已存在，不能把 quota 當成產品失敗。

## 本輪發現真正的語意缺口：只生成 1 鏡也會被判整片成功

0002 canonical contract 是：

- target duration：20 秒。
- default shot：5 秒。
- canonical shots：4 鏡。
- 必須是 `shot-1 → shot-2 → shot-3 → shot-4`。

但是 run `31920165702` 的 terminal evidence 只列出一個 `shot.generate`：`shot.generate:shot-1`。舊 OpenWorker generic validator 只要求「至少存在一個 succeeded shot 且有 artifact」，因此 Shot 1 成功就足以讓 Source-to-Film platform 回 `succeeded`。

所以 `31920165702` 雖然 GitHub Action 是綠色，**仍不是 Case 0002 LIVE_VERIFIED，也不能視為四鏡影片完成**。

## 已補：Case 0002 精確四鏡 fail-closed contract

AI-Engineering-OS `scripts/cases/case0002_openworker_source_to_film.py` 現新增案例級驗收：

- `TARGET_DURATION_SEC = 20`。
- `DEFAULT_SHOT_SECONDS = 5`。
- `EXPECTED_SHOT_COUNT = 4`。
- terminal 必須精確存在：
  - `shot.generate:shot-1`
  - `shot.generate:shot-2`
  - `shot.generate:shot-3`
  - `shot.generate:shot-4`
- 每一鏡必須：
  - `status == succeeded`
  - `execution_id` 非空
  - `prompt_id` 非空
  - `tool_id` 非空
  - 至少一個非空 artifact
- 任何一項不符立即 fail-closed，不再接受「只有 Shot 1 的 succeeded」。
- 新 evidence：`04a-case-shot-contract.json`。
- 全部通過才輸出 `CASE0002_SHOT_CONTRACT_OK count=4 ...`。

提交：`ed5573f1df1a768460ead54ac74b651f9e22099a`。

## 已補：ODAQ duplicate candidate 不再假紅

24-slot fan-out 命中 ODAQ 後，其他同一台 ODAQ candidate 會因 host-local lock 正確判成 duplicate；但舊 cmd block 沒有顯式清除 `mkdir` 的 `errorlevel=1`，所以正常 duplicate skip 會被 GitHub 標成 failure。

已在 duplicate branch 加 `exit /b 0`，並在 route step 尾端明確 `exit /b 0`。正常 duplicate / wrong-host 都只能 clean skip，不再污染正式 production 結果。

提交：`cc9d49bd50feea7a1ddf2a1d980962dea6e93794`。

新 go-tool 驗證：

- Operator E2E 0002：run `31920483000`，建立本紀錄時 `queued`。
- Win11 Local Verification：run `31920482977`，建立本紀錄時 `queued`。

## 目前真正缺口

目前已證明：

`go-tool → ODAQ → queue hygiene → OpenWorker → OS → Studio → ComfyX → H3 REAL → Shot 1 MP4`

已經能閉環。

但 Studio / Source-to-Film production planning 仍只產出一個 `shot.generate`，沒有把 20 秒 / 5 秒 contract 轉成完整四鏡 queue。因此下一個 owning gap 已收斂為：**Studio production plan / queue creation 必須把 canonical 4 shots 全部排入並逐鏡執行，而不是 Shot 1 完成後就把整個 queue 標 succeeded。**

## 下一個驗收點

重新由 go-tool 正式 dispatch 0002。新的四鏡 gate 預期會把「只有 Shot 1」明確打紅，並留下 `04a-case-shot-contract.json`；接著依該 evidence 修 Comfyx-Studio 真正的 multi-shot queue owning code。

只有在 Shot 1–4 都有 fresh physical MP4 + execution correlation + canonical workspace provenance 後，才進入：

`1280×720 Final Assembly → subtitles/QC → OS Artifact Registry → Delivery Revision → delivery/website/index.html`

完成上述整條交付鏈後才可標記 `LIVE_VERIFIED`。