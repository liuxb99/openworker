# 0002 阿拉丁神燈 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`IMPLEMENTING / FOUR-SHOT REAL VERIFIED / WORKSPACE MATERIALIZATION IMPLEMENTED / FINAL DELIVERY RERUN NEXT`

## Canonical 驗收目標

0002 固定 20 秒、default shot 5 秒，必須精確產生 `shot-1..shot-4`。每鏡必須有 succeeded + execution_id + prompt_id + tool_id + physical non-empty MP4，並物化到固定工作目錄：

`D:\AI-Work\jobs\0002-ALADDIN\production\shots\shot-N\video.mp4`

之後才可 Final Assembly → subtitles/QC → OS Artifact Registry → Delivery Revision → `delivery/website/index.html` → `result.json live_verified=true`。

## 四鏡 REAL 已通過

正式 go-tool → ODAQ → OpenWorker → OS → Studio → ComfyX → ComfyUI/H3 run：`31920903429`，production job `95100520525`。

四鏡全部 fresh REAL succeeded：

- shot-1：`MiniMax_H3_00012_.mp4`
- shot-2：`MiniMax_H3_00013_.mp4`
- shot-3：`MiniMax_H3_00014_.mp4`
- shot-4：`MiniMax_H3_00015_.mp4`

`CASE0002_SHOT_CONTRACT_OK count=4` 已出現在正式 log。queue hygiene clean，ComfyUI heartbeat 沒有重現先前 backend death。

這證明 Studio duration-driven shot budget `ceil(20/5)=4` 已在 REAL production 生效，而不只是單元測試。

## 新缺口：ComfyUI artifact 尚未 canonical materialize 到工作目錄

四鏡 REAL terminal 的 queue artifact 仍只回 `MiniMax_H3_0001x_.mp4` 類 filename。這不足以證明固定工作目錄內存在可供 Final Assembly 使用的實體影片，因此不能 LIVE_VERIFIED。

追查 owning path：`AIGCDirectorProductionQueueExecutor.generateShot` 原本只把 ComfyX status/trace artifacts 原樣回傳，沒有把 physical `video_full_path` 複製到 OpenWorker job workspace。

## 本批修復：Studio workspace materialization

Owning repo：`liuxb99/Comfyx-Studio`，main。

- commit `da786068937c2b830d80f8cb22b845c0bf9c7a88`：shot.generate terminal 後要求找到 physical non-empty source artifact，原子 copy 到 `<workspace>/production/shots/<shotID>/video.mp4`；若只有 filename、來源不存在、copy 失敗或 destination 為空，整個 shot fail-closed，不再允許 succeeded。
- queue output `artifacts` 改為 canonical workspace path，並保留 `source_artifacts` / `workspace_artifacts` provenance。
- workspace root 優先讀 queue input `workspace_root`，否則使用 formal Action 已設定的 `OPENWORKER_WORKSPACE`。
- commit `f7a7bd22080b2bc88834aaa4ee69b5f4070a5023`：永久測試要求 byte-identical canonical `production/shots/shot-2/video.mp4`，並驗證 filename-only artifact 必須 fail-closed。

Studio AIGC Domain Win11 Gate：`31922370496` / job `95104226995`，建立本紀錄時正在執行。

## Final delivery harness 已往前接

AI-Engineering-OS `scripts/cases/case0002_openworker_source_to_film.py` 已擴展四鏡之後的閉環：

1. 呼叫 Studio Director `/finalize`，輸出 `D:\AI-Work\jobs\0002-ALADDIN\output\final.mp4`（1280×720）。
2. 要求 final MP4 physical non-empty，計算 SHA256。
3. 透過 OS 正式 Artifact Registry 註冊 final video。
4. 把 OS Job 推進 review，對 registry artifacts 建立 approved review。
5. approval gate green 後完成 Job。
6. 呼叫 OS publish，建立 Delivery Revision 與 `delivery/website/index.html`。
7. 最後才寫 `result.json`，要求 `live_verified=true / success=true / production_result=completed / artifact_registry_count>=1 / delivery_revision_count>=1 / final_video / delivery_index / delivery_website`。

AI-Engineering-OS commit：`a41f87a4770333570b95ad25e06009d04780ceea`。

## 下一步

先等 Studio gate `31922370496` terminal。全綠後從 go-tool 正式入口重跑 0002，不走旁路；新 REAL 必須同時驗證四個 canonical workspace MP4，再繼續 Final Assembly / Registry / Delivery。任何一層缺 formal operation 或 evidence 就修 owning repo 後沿同一路徑重跑。

目前仍 **NOT LIVE_VERIFIED**；但四鏡 REAL generation 已閉環，當前 blocker 已收斂為 workspace materialization → final delivery。
