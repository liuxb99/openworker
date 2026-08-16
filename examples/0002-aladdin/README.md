# 案例 0002：阿拉丁神燈 Source-to-Film

> 類型：大模型逐步操作手冊  
> Canonical owner：OpenWorker `examples/0002-aladdin/`  
> 目標：證明一個不知道各 repo 原始碼的大模型，可以只依本手冊與正式工具能力，完成從故事到可交付影片的 REAL 閉環。

## 1. 任務

輸入故事：

> Aladdin finds an old brass magic lamp in the ruins of a drought-stricken desert city. When he rubs it, a blue glowing Genie appears. Instead of asking for riches, Aladdin wishes for water for the city. The Genie summons rain clouds, the city comes alive again, and Aladdin quietly leaves with the lamp.

目標不是只生成一個 queue record，而是完成：

`使用者任務 → OpenWorker → go-tool → AI-Engineering-OS → Comfyx-Studio → ComfyX / ComfyUI / MiniMax H3 → physical artifacts → QC → Final Assembly → Artifact Registry → Delivery Revision → delivery/website/index.html`

正式工作目錄由 OpenWorker / OS 決定；不得由大模型自行猜絕對路徑。

本案例 temporal contract 固定為：

- target duration：20 秒。
- default shot：5 秒。
- `expected_shots = ceil(target_duration_sec / default_shot_seconds) = 4`。
- canonical sequence：`shot-1 → shot-2 → shot-3 → shot-4`。

Director / ProductionQueue 不得因上游 story planner 對連續 prose 只回一個 action block，就把一鏡成功當成整片成功。

## 2. 執行原則

- 先問工具，不先讀 owning repo 原始碼。
- 所有工具使用執行當下的最新正式提交；記錄 SHA 作 provenance，不 pin 舊版。
- consequential side effects 必須走受控工具與 self-hosted Action execution boundary。
- 如果 go-tool 無法回答「有什麼能力、怎麼用、需要哪些輸入、是否 ready、怎麼 dispatch、如何查結果」，先修工具資訊契約。
- 如果最新工具失敗，修最新 owning repo，不回退舊版繞過。
- 只有取得新鮮 physical artifact、工作區 materialization、provenance 與 QC 才算完成。
- REAL heavy job dispatch 前必須做 execution hygiene；不得把已知舊 queue / conflicting run 留給下一個案例自行撞上。

## 3. Step 1 — 健康檢查

向 go-tool 查 health。

驗收：runtime 可用；若不可用，停止案例並回報 runtime blocker，不直接改用 repo script。

## 4. Step 2 — 發現能力

列出 capabilities，尋找正式 Source-to-Film 能力。

目前 canonical capability：`engineering.source-to-film`。

不要因為知道 Studio / ComfyX 名稱就直接呼叫底層工具；先由正式 capability contract 決定 orchestration。

## 5. Step 3 — 讀 capability detail / schema

取得 `engineering.source-to-film` detail，確認 canonical inputs 至少能承載：

- `story`
- `title`
- `delivery_case`

若使用者輸入無法透過正式 schema 傳入，這是工具缺口，不可把故事偷偷寫死在 workflow/script。

## 6. Step 4 — Readiness

查 execution readiness。

必須 fail-closed 檢查必要依賴；不得因知道本機安裝位置而繞過 readiness。

## 7. Step 5 — Execution hygiene / queue drain

在新的 REAL dispatch 前先查同一 capability 的正式 workflow queue：

`GET /api/execution/queues/engineering.source-to-film`

若存在舊的 `queued / in_progress / waiting / pending` conflicting run，先做 drain：

`POST /api/execution/queues/engineering.source-to-film/drain`

如果 drain 是在目前 workflow 內執行，必須把目前 `GITHUB_RUN_ID` 放入 `exclude_run_ids`，避免清場時取消自己。

Queue drain 必須：

- 只作用於 capability 所註冊的 workflow，不能無差別取消同 repo 的其他工作；
- cancellation 後重新 query；
- conflicting queue 尚未清空時 fail-closed；
- 不得只因 GitHub cancel API 回 202 就當作清乾淨。

ComfyUI 本機 queue 也必須在 production 前 interrupt + clear + re-query，確認 running / pending 都為空。

## 8. Step 6 — Dispatch

用正式 capability dispatch 本案例，故事必須從 canonical input 傳入。

保存 execution id / target run id。正式 LIVE 驗證必須由這一步建立，不能直接手動觸發底層 OS Action 冒充。

## 9. Step 7 — 查 execution / job

透過 go-tool / OpenWorker 查：

- execution status
- job / target run
- blocker / failure
- artifact / delivery refs

若失敗，根據正式回覆定位 owning layer，修完後再由 Step 1–6 重新建立新 execution。

## 10. Step 8 — OpenWorker / OS / Director production contract

正式 execution 應進入：

`OpenWorker binding → AI-Engineering-OS job/workspace → Studio Director planning → ProductionQueue → audited ComfyX execution`

驗收至少包含：

- 使用最新 OS / OpenWorker / go-tool / Studio / ComfyX 工具版本；
- contract verification 全綠；
- 固定工作區建立；
- ComfyUI Desktop REAL readiness；
- 非指定 runner candidate fail-closed / clean skip；
- Director 必須使用 duration contract 建立 shot budget：`expected_shots = ceil(target_duration_sec / default_shot_seconds)`；
- 本案例必須精確建立 `shot-1`、`shot-2`、`shot-3`、`shot-4`，不能只有 Shot 1；
- 若來源是連續 prose，上游 planner 只產一個 action block，Director 必須在 queue compile 前正規化成 duration contract 所要求的語意 beats。

本案例預期語意 beats：

1. 找到神燈。
2. 精靈現身。
3. 許願並召雨。
4. 雨後城市恢復，阿拉丁帶著同一盞神燈離開。

## 11. Step 9 — REAL H3 Shot 1 + backend heartbeat

Shot 1 必須由 Studio 語意一路傳到 ComfyX H3 prompt。

Production waiting 期間必須持續檢查 ComfyUI backend heartbeat。若 `/object_info` 連續多次無法連線，立即把這輪視為 backend death並留下 heartbeat evidence；不得一路等到 30 分鐘 timeout 才發現。

目前 0002 gate：連續 3 次 heartbeat failure 即 fail-fast，evidence 寫入 `03a-backend-heartbeat.json`。

最低 Shot 1 gate：

- prompt 具有 `Aladdin` / `magic lamp` 故事語意；
- profile 使用正式最新策略（目前預設五種官方模式走 LightX2V H3 4-step；顯式 Standard 保持 Standard contract）；
- 產生 fresh physical MP4；
- execution ledger 有 execution_id / prompt_id / job_id / shot_id / physical path / size / mtime / SHA256；
- Studio canonical workspace 中存在 materialized MP4；
- source MP4 SHA256 = Studio canonical MP4 SHA256 = ledger artifact SHA256。

Shot 1 視覺 semantic QC PASS 後標記 ACCEPT，不再無意義重跑。

## 12. Step 10 — 四鏡完整性與完成影片

Shot 1 ACCEPT 後不是直接把 queue 判成功，而是繼續 Shot 2–4。

案例級 `04a-case-shot-contract.json` 必須證明精確存在：

- `shot.generate:shot-1`
- `shot.generate:shot-2`
- `shot.generate:shot-3`
- `shot.generate:shot-4`

每一鏡都必須同時具有：

- `status == succeeded`
- 非空 `execution_id`
- 非空 `prompt_id`
- 非空 `tool_id`
- 至少一個非空 physical artifact

缺任一鏡或任一 provenance 欄位都 fail-closed。四鏡通過後完成：

`shots → 1280×720 Final Assembly → subtitles → semantic/technical QC → OS Artifact Registry → Delivery Revision → delivery/website/index.html`

每個 accepted artifact 都要保留 provenance；失敗 artifact 不得冒充 accepted delivery。

## 13. 完成標準

只有以下全部成立才可標 `LIVE_VERIFIED / DELIVERABLE`：

1. 本案例由 go-tool 正式 dispatch 建立 execution。
2. 使用者故事由 canonical input 傳入，沒有腳本寫死。
3. Dispatch 前 execution hygiene 已確認無 conflicting workflow queue。
4. OpenWorker / OS / Studio / ComfyX 走唯一正式 production path。
5. Director 依 20/5 duration contract 物化精確四鏡。
6. Production 期間 backend heartbeat 可辨識 ComfyUI death，不會只靠長 timeout。
7. Shot 1–4 每一鏡都有 fresh REAL H3 physical MP4 與完整 execution provenance。
8. `04a-case-shot-contract.json` PASS。
9. Studio / OS workspace 與 artifact registry 有 canonical artifact。
10. 視覺與技術 QC PASS。
11. Final Assembly / subtitles 完成。
12. Delivery Revision 完成。
13. `delivery/website/index.html` 存在且引用 accepted delivery。
14. `STATUS.md` 與 `evidence/README.md` 記錄本次真實證據。

## 14. 相關 owning repos

- OpenWorker：案例入口、worker binding、workspace / mission / execution governance。
- go-tool-runtime：能力發現、schema、readiness、queue hygiene、dispatch、execution query 的資訊權威。
- AI-Engineering-OS：Job、workspace、artifact、delivery lifecycle，以及案例 production heartbeat/evidence。
- Comfyx-Studio：故事、劇本、分鏡、duration-driven shot budget、production semantics、final assembly。
- ComfyX：ComfyUI / MiniMax H3 真實生成、execution ledger、physical artifact provenance。

這些 repo 可以保存 implementation 文件，但**案例操作手冊的 canonical copy 固定在 OpenWorker**。
