# 0002 阿拉丁神燈 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`IMPLEMENTING / OUTER GATES GREEN / FORMAL REAL REDISPATCH STARTED / HOST ROUTING FANOUT EXPANDED / WAITING ODAQ`

## 已完成

- canonical 入口：OpenWorker `examples/0002-aladdin/`。
- go-tool `engineering.source-to-film` 已承載 `story / title / delivery_case`。
- 0002 已在 production dispatch 前正式執行 workflow-scoped queue drain，支援 `exclude_run_ids` 保留目前 run，清不乾淨則 fail-closed。
- queue hygiene evidence：`01a-execution-hygiene.json`。
- production waiting 已加入 ComfyUI `/object_info` heartbeat；連續 3 次 failure 立即報 backend died。
- heartbeat evidence：`03a-backend-heartbeat.json`。
- go-tool Win11 核心 gate run `31919459618`：`success`。
- go-tool Operator E2E run `31919939846`：`success`。
- AI-Engineering-OS OpenWorker Source-to-Film baseline run `31919947413`：`success`。

## 最近一次失敗的 REAL production

execution：`engineering.source-to-film:31916089801`

- OS run：`31916089801`
- production job：`95087955499`
- runner：`DESKTOP-ODAQN0D-R003`
- OpenWorker Project：`prj_1357fb0aede5a80f389ba4f2eee54bc1`
- OS Job：`job_343aaa39fa6da28bb834812599f04fb4`
- Studio Project：`os-job_343aaa39fa6da28bb834812599f04fb4`
- ProductionQueue：`os-job_343aaa39fa6da28bb834812599f04fb4-production`

該 run 在 initial ComfyUI readiness 後 production 中途失去 `127.0.0.1:8188`，舊流程等滿 1800 秒才 timeout，因此 Shot 1 未 ACCEPT。此缺口現已由 backend heartbeat fail-fast 覆蓋。

## 已補：正式 0002 dispatch 自帶 Actions queue authority

go-tool 的 queue-drain 已是正式 production preflight，但原 `operator-e2e-0002-comfyx-studio.yml` 只有 `contents: read`，runtime 是否能取得 Actions write credential 仍依賴 runner 本機 service account。

已修：

- workflow permissions 加入 `actions: write`。
- bounded token 明確注入 `GITHUB_TOKEN` / `GH_TOKEN`。
- 不再依賴 ODAQ runner service account 是否剛好有 local credential DB。

提交：`09c83e70af39e47ba9b55ed6d8af08670b1cf2a0`。

## 本批新發現：兩個 hostname candidate 會產生「假綠」

正式 redispatch run `31920059499` 的兩個 matrix candidate 最後都被非 production host 接走；其中 job `95098397014` 明確跑在 `DESKTOP-O87PJNR-R030`，log 顯示：

`0002_DISPATCH_SKIP_WRONG_HOST slot=2 host=DESKTOP-O87PJNR`

兩個 candidate 都 clean skip，整個 workflow 卻仍是 success，實際正式 dispatch 次數為 0。因此這個 success 不能當作 0002 production success。

## 本批修復：hostname routing fan-out 由 2 擴成 24

依目前設計仍只使用 `COMPUTERNAME == DESKTOP-ODAQN0D` 作為 production host 判斷，不重新引入脆弱的自訂 runner label。

已修改 `operator-e2e-0002-comfyx-studio.yml`：

- matrix slot：`2 → 24`。
- `max-parallel: 24`。
- timeout：`20 → 30` 分鐘。
- 每個非 ODAQ candidate 只 clean skip。
- ODAQ 上仍靠 host-local lock `D:\AI-Example\0002\.locks\gtr-dispatch-<run>-<attempt>` 保證只有一個 candidate 真正 dispatch。
- queue hygiene 的 bounded Actions token 保持不變。

提交：`b4718f0977f91f2889d393da0ecddafa3cede666`。

新的正式 routing run：`31920155718`。

建立本紀錄時，24 個 candidate 全部已進 queue，等待 self-hosted runners；只要 ODAQ runner 在線並接到其中一個，才會執行 `go run ./cmd/e2e-0002-dispatch`，其餘 candidate 即使跑到其他 host 也只會退出。

## 目前驗收鏈

`go-tool dispatch runner → ODAQ host route → go-tool queue inspect/drain → preserve current run → queue clean → ComfyUI clean/ready → OpenWorker → OS → Studio → audited ComfyX → H3 REAL → heartbeat → physical MP4`

下一個真驗收點不是 workflow 是否顯示綠色，而是 log 必須出現：

`0002_DISPATCH_HOST_OK ... host=DESKTOP-ODAQN0D`

並且隨後產生新的 `engineering.source-to-film:<run_id>` execution。

Shot 1 必須同時具備：physical MP4、ComfyX execution correlation、Studio canonical workspace MP4、SHA256 byte identity、visual semantic QC，才標記 ACCEPT。

Shot 1 通過後直接推進 Shot 2–4、1280×720 Final Assembly、字幕/QC、Artifact Registry、Delivery Revision、`delivery/website/index.html`。