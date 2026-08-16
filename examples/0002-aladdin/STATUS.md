# 0002 阿拉丁神燈 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`IMPLEMENTING / SHOT-1 REAL VERIFIED / FALSE-SUCCESS CLOSED / STUDIO 4-SHOT BUDGET IMPLEMENTED / FORMAL REAL RERUN IN PROGRESS`

## Canonical 驗收目標

0002 固定故事長度為 20 秒，default shot 為 5 秒，因此 Director / ProductionQueue 必須精確物化 4 鏡：

1. `shot.generate:shot-1`：找到神燈。
2. `shot.generate:shot-2`：精靈現身。
3. `shot.generate:shot-3`：許願並召雨。
4. `shot.generate:shot-4`：雨後城市恢復、阿拉丁離開。

每一鏡都必須具備 `status=succeeded + execution_id + prompt_id + tool_id + 非空 artifact`。4 鏡全部通過後才可進入 Final Assembly / subtitles / QC / Artifact Registry / Delivery Revision / website；只有完整交付後才可標記 `LIVE_VERIFIED`。

## 已完成的正式執行基礎

- go-tool `engineering.source-to-film`：正式 capability，承載 `story / title / delivery_case`。
- workflow-scoped queue drain：production dispatch 前清理衝突 run，支援保留目前 `GITHUB_RUN_ID`，證據 `01a-execution-hygiene.json`。
- ComfyUI backend heartbeat：production 中連續 3 次 `/object_info` failure 即 fail-fast，證據 `03a-backend-heartbeat.json`。
- ODAQ hostname routing：24-slot fan-out，只接受 `COMPUTERNAME == DESKTOP-ODAQN0D`，host-local lock 保證單一正式 dispatch。
- duplicate ODAQ candidate 已明確 `exit /b 0`，不再把正常 skip 標成 failure；go-tool commit `cc9d49bd50feea7a1ddf2a1d980962dea6e93794`。
- go-tool 核心 Win11 gate `31919459618`：success。
- go-tool Operator E2E baseline `31919939846`：success。
- OS OpenWorker Source-to-Film baseline `31919947413`：success。

## REAL 已證明：正式鏈可生成 Shot 1 真實 H3 MP4

正式 go-tool execution：`engineering.source-to-film:31920165702`。

- OS run：`31920165702`。
- production job：`95098676890`。
- runner：`DESKTOP-ODAQN0D-R003`。
- workspace：`D:\AI-Work\jobs\0002-ALADDIN`。
- OpenWorker project：`prj_1357fb0aede5a80f389ba4f2eee54bc1`。
- OS job：`job_343aaa39fa6da28bb834812599f04fb4`。
- Studio project：`os-job_343aaa39fa6da28bb834812599f04fb4`。
- queue：`os-job_343aaa39fa6da28bb834812599f04fb4-production`。
- queue hygiene：`clean=True`。
- Shot 1 execution：`comfyui:32c105b3-6cfe-4574-bf42-7cdfd7410353`。
- Shot 1 artifact：`MiniMax_H3_00011_.mp4`。

因此 `go-tool → ODAQ → OpenWorker → OS → Studio → ComfyX → ComfyUI/H3 → physical MP4` 已有 REAL 證據。

## 四鏡 fail-closed gate 已抓到舊假成功

AI-Engineering-OS commit `ed5573f1df1a768460ead54ac74b651f9e22099a` 新增案例級 `04a-case-shot-contract.json`：只有精確 4 鏡且每鏡 execution / prompt / tool / artifact 完整才接受。

正式 go-tool run `31920483000` 第一次 ODAQ 執行建立 OS run `31920513455`，production job `95099566422`。該輪再次取得 Shot 1：

- execution：`comfyui:ff365b9e-f15a-47e2-9396-d3e50544b0a1`
- artifact：`MiniMax_H3_00011_.mp4`

但案例 gate 正確打紅：

`CASE0002 shot contract failed: expected exactly 4 shot.generate items, got 1`

這證明舊的 Source-to-Film `succeeded` 只是「至少一鏡成功」的假成功；目前已不再接受。

## 本批根因：Director 沒有把 target duration 轉成 shot budget

追查 Comfyx-Studio 後確認：

- `aigc_director_queue_compiler.go` 會正確把 `plan.Scenes[].Shots[]` 全部編成 `shot.generate`，queue compiler 不是根因。
- 上游 Director plan 本身只有 1 shot。
- Studio 把一整段 prose 交給 ComfyX story planner；story planner 以 screenplay/action block 為單位，連續 prose 只會 flush 成 1 shot。
- `TargetDurationSec=20` 原本只寫回 Director plan metadata，沒有參與 shot 數量規劃。
- `DefaultShotSeconds=5` 只控制既有 shot duration，因此原流程不會推導 `ceil(20/5)=4`。

## 本批已修：Studio duration-driven shot-budget normalization

Owning repo：`liuxb99/Comfyx-Studio`，branch `main`。

新 contract：

`expected_shots = ceil(target_duration_sec / default_shot_seconds)`

當 story planner 對連續 prose 回傳的 shot 數與 duration contract 不一致時，Director 在 production queue 編譯前進行 normalization：

- 以 `。！？；!?;` 與換行切成連續 narrative beats。
- 把 beats 按 shot budget 分成精確 N 組；多出的子句優先放在後段，6 個 beat / 4 shot 會形成 `1 / 1 / 2 / 2`，符合阿拉丁的「找到 → 精靈 → 許願+召雨 → 雨後+離開」。
- Canonical shot ID 重建為 `shot-1...shot-N`。
- 依賴鏈重建為前一鏡。
- duration 依 default shot 秒數配置，最後一鏡承接 remainder，例如 12 秒 / 5 秒 = `5 + 5 + 2`。
- 保留 scene / character / camera template bindings。
- 不把舊 dialogue 盲目複製到新切分 beat，避免錯誤 speaker provenance。
- scene duration 重新由 normalized shots 計算。

實作提交：

- `30a04280ac1251030c4497a408745d0680629a60` — 新增通用 Director shot-budget normalizer。
- `840dd14e10e50f765f902061d43243c8fe8ba7e1` — 正式接入 `AIGCDirectorLLMPlanner.Generate`。
- `9bd30c4eb93921f7e614c5e2007a3f01e1fd4d03` — 永久測試：一段阿拉丁 prose + upstream 1 shot + 20/5 contract 必須生成精確 4 個不同語意 shot；另驗證 ceil/remainder/template preservation。
- `8b684d9b29214021314907385be3c90a6fec891c` — 修復既有 parity test 的 gofmt baseline，讓產品 gate 能真正跑到測試。

## Studio 最新驗證

AIGC Domain Win11 Gate：run `31920881869`，job `95100465474`。

已確認：

- Format check：PASS。
- AIGC targeted tests：PASS。
- Go vet：PASS。
- Full Go tests：PASS。
- Race tests：PASS。
- Production build：PASS。

建立本紀錄時只剩 GitHub `Post Checkout` 收尾，因此 shot-budget code 與永久測試的實質 gate 已全綠。

前一輪 `31920837724` 在 format check 失敗是既有 `aigc_comfyx_h3_parity_test.go` gofmt 差異，不是 shot-budget 編譯/測試失敗；已由 `8b684d9...` 修正。

## 最新正式 REAL 重跑

不是直接手動啟動 OS，而是重新執行已命中 ODAQ 的 go-tool harness：

- go-tool run：`31920483000`，attempt 2。
- ODAQ job：`95100495714`（`e2e (23)`）。
- runner：`DESKTOP-ODAQN0D-R002`。
- log：`0002_DISPATCH_HOST_OK slot=23 attempt=2 host=DESKTOP-ODAQN0D`。
- 正式 execution：`engineering.source-to-film:31920903429`。
- 新 OS run：`31920903429`。
- assigned production candidate：`95100520525`（`production (4)`）。

建立本紀錄時 OS 已進入 checkout 最新 Comfyx-Studio；後續必須確認它實際 checkout `8b684d9b29214021314907385be3c90a6fec891c` 或更新 main，然後完整執行 4 個 H3 shots。

## 下一個驗收點

本批不把單元測試或 Action 綠燈當成產品完成。下一步只接受新的 formal REAL evidence：

`shot-1 + shot-2 + shot-3 + shot-4 → 每鏡 fresh execution/prompt/artifact → 04a-case-shot-contract.json PASS`

四鏡 REAL 通過後，立即繼續：

`Studio canonical workspace provenance / SHA identity → semantic QC → 1280×720 Final Assembly → subtitles/QC → OS Artifact Registry → Delivery Revision → delivery/website/index.html`

目前 **NOT LIVE_VERIFIED**。
