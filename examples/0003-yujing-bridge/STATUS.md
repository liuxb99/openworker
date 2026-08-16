# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`BLOCKED / UL7 RUNNER OFFLINE-OR-UNAVAILABLE / MANUAL-EVOLVING / GAP-FIX-CLOSURE / OS WEBSITE DELIVERY REQUIRED`

## 任務

固定由 UL7（Windows `DESKTOP-UL7V2VV`）執行 consequential work：

`臺南市玉井橋 → 真實位置解析 → 真實街景/地形參考 → Blender 3D 場景 → SceneX 匯入 → SceneX REAL 瀏覽 → OS Artifact Registry → Delivery Revision → delivery/website/index.html`

## 文檔即操作手冊

本案例每一步都必須詳實記錄，文檔不是事後摘要，而是後續大模型直接照著執行的正式操作手冊。

每一步至少記錄：canonical input、tool/capability/workflow、owning repo/SHA、run/job/runner/COMPUTERNAME、輸入/輸出、artifact path/size/mtime/SHA256、PASS/FAIL/BLOCKED 依據、缺口根因、修復 commit/tests、修復後 REAL rerun、最終 accepted 操作方式。

## 缺口修復規則

案例執行時若發現正式能力缺口：保存原始 evidence → 確認 owning repo → 寫入 STATUS/evidence → 修真正 owning repo → tests/build/CI → 使用最新 commit 回原 Step → 固定 UL7 REAL 重跑 → PASS 後寫回手冊。

不得用案例特例、舊 commit、人工替代或臨時 script 掩蓋正式能力缺口。

## 固定執行邊界

- consequential case steps 只允許 `DESKTOP-UL7V2VV`。
- OpenWorker routing workflow：`.github/workflows/case-0003-yujing-bridge-ul7.yml`。
- 已新增跨 repo UL7 probe：`liuxb99/DWG_todo/.github/workflows/case-0003-yujing-ul7-probe.yml`。
- 不 fallback 到 O87/ODAQ 產生成果。

## OS 最終交付規則

- SceneX REAL browse 是中間 gate。
- accepted artifacts 必須進 OS Artifact Registry。
- 必須建立 Delivery Revision。
- 最終 physical delivery：`delivery/website/index.html`。

## 已完成 / 已證實

1. canonical 案例入口與完整主流程已建立於 `examples/0003-yujing-bridge/`。
2. OS 成果網站已列為硬性最終交付 gate。
3. 已修 G-0003-001：文檔更新不再自動取消正式案例 run。
4. 已修 G-0003-002：移除固定 concurrency，避免舊 queued run 阻塞新驗證。
5. OpenWorker 最新正式 routing run `31920291957` 已能正常建立 8 個 `[self-hosted, Windows, X64]` jobs，但仍全部 queued、沒有 runner identity。
6. 已確認同時間 O87、ODAQ self-hosted runners 可在其他 repo 正常接單，因此 GitHub Actions 平台與 Windows selector 並未整體故障。
7. 已找到 UL7 歷史正式成功證據：`DWG_todo` run `31316843916`、job `93253413948`、runner `DESKTOP-UL7V2VV-R011`、labels `[self-hosted, Windows, X64, ai-ci]`、SUCCESS。
8. 已新增使用同 repo + 同 `ai-ci` selector 的 Case 0003 readiness probe，commit `8b351993cd655800df3d63dcaab0c59ccbfe712b`。
9. 新 probe run `31920589306`、job `95099748288` 目前仍 `queued`，`runner_id=null`、`runner_name=null`。

## 目前 gate

**Step 1 — UL7 runner identity / readiness：BLOCKED。**

最新權威 probe：

- repo：`liuxb99/DWG_todo`
- workflow：`Case 0003 Yujing UL7 Readiness`
- run：`31920589306`
- job：`95099748288`
- selector：`[self-hosted, Windows, X64, ai-ci]`
- current status：`queued`
- runner：尚未指派

由於這是曾經能由 `DESKTOP-UL7V2VV-R011` 成功接單的同 repo + 同 selector，現在仍 queued，因此 G-0003-003 已收斂為：

**UL7 runner service / registration / online availability 當前未能接 GitHub queue。**

這不是 go-tool、Blender、街景、terrain 或 SceneX readiness FAIL；那些 steps 尚未開始。

## UL7 一恢復後，同一 probe 會直接驗證

1. `COMPUTERNAME == DESKTOP-UL7V2VV`；
2. 實際 `RUNNER_NAME`；
3. checkout 最新 `openworker@main`；
4. checkout 最新 `go-tool-runtime@main`；
5. go-tool `go test ./...`、build、`--help`；
6. Blender CLI executable/version；
7. PASS 後進 Step 2 capability discovery。

## 下一個執行點

- 首先看 `31920589306 / 95099748288` 是否被 UL7 接走。
- 一旦 Step 1 PASS：立即查 go-tool capabilities/schema/readiness，接著只用 `location_text=臺南市玉井橋` 做 canonical geolocation。
- 後續逐步取得 REAL Street View / terrain → Blender → SceneX → OS website；每一步都更新手冊。

## 尚未完成

- UL7 runner identity / readiness。
- go-tool / Blender / SceneX / OS delivery readiness。
- 玉井橋 canonical geolocation。
- street-view physical images。
- terrain/AOI physical data。
- `.blend` / SceneX exchange artifacts。
- Blender QC。
- SceneX REAL browse evidence。
- OS Artifact Registry。
- Delivery Revision。
- `delivery/website/index.html`。
