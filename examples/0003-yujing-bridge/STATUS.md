# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`EXECUTING / UL7 ROUTING / CASE-ONLY / OS WEBSITE DELIVERY REQUIRED`

## 任務

使用既有工具，固定由 UL7（Windows `DESKTOP-UL7V2VV`）執行 consequential work：

`臺南市玉井橋 → 真實位置解析 → 真實街景/地形參考 → Blender 3D 場景 → SceneX 匯入 → SceneX REAL 瀏覽 → OS Artifact Registry → Delivery Revision → delivery/website/index.html`

## 固定執行邊界

- 本案例只允許 UL7（`DESKTOP-UL7V2VV`）執行 consequential case steps。
- routing workflow 可由 `[self-hosted, Windows, X64]` runner 接單；非 UL7 主機必須 clean skip。
- 不 fallback 到其他電腦產生成果。
- 案例 workflow：`.github/workflows/case-0003-yujing-bridge-ul7.yml`。
- 本案例不先開發工具，先用案例暴露現有能力缺口。

## OS 最終交付規則

- SceneX 可瀏覽不是最終交付，只是中間驗收 gate。
- 最終成果必須進 OS Artifact Registry，建立 Delivery Revision。
- 最終 physical delivery 必須有：`delivery/website/index.html`。
- 成果網站必須展示/索引玉井橋真實位置、街景/地形 provenance、Blender 場景、SceneX REAL captures、QC、artifact hashes、execution provenance。
- SceneX PASS 但沒有成果網站，不得標記案例完成。

## 已完成

- 案例 0003 canonical 入口建立於 OpenWorker `examples/0003-yujing-bridge/`。
- 已明確規定本案例不先開發工具，先用案例暴露既有工具缺口。
- 已定義 REAL 完成標準：真實位置、真實街景 provenance、terrain/AOI、Blender physical artifacts、SceneX 實際載入與 runtime 瀏覽證據。
- 已修正 UL7 routing：UL7 是簡稱，正式 Windows 主機為 `DESKTOP-UL7V2VV`；不再要求不存在的 `UL7` runner label。
- routing workflow head：`22379efa04b55020508d2a3aced418714af0bdc6`。
- 最新 route run：`31919992683`。
- run `31919992683` 已建立 8 個 `[self-hosted, Windows, X64]` route slots；截至最近一次查詢均仍為 queued，尚未取得 runner identity。
- 已將 OS 成果網站交付規則補進 canonical 手冊。

## 目前 gate

Step 1 — UL7 runner identity / readiness。

等待 run `31919992683` 的 self-hosted Windows jobs 被 runner 接單後：

- 非 `DESKTOP-UL7V2VV` → clean skip；
- `DESKTOP-UL7V2VV` → 執行 go-tool / Blender readiness，繼續案例。

UL7 PASS 後依序推進：

`capability discovery → geocoding → street-view → terrain/AOI → Blender → Blender QC → SceneX import → SceneX browse → Artifact Registry → Delivery Revision →成果網站`

## 下一個執行點

1. 追 run `31919992683` jobs，取得 runner name / COMPUTERNAME。
2. 找到 `DESKTOP-UL7V2VV` 後執行既有工具 readiness。
3. 透過 go-tool 查 health / capabilities。
4. 發現既有 geocoding / street-view / terrain / Blender / SceneX / OS delivery 能力。
5. 以 canonical input `臺南市玉井橋` 做真實位置解析。
6. 不改工具；若任一步失敗，記錄 blocker、owning repo 與證據。

## 尚未完成

- 尚未確認本次 UL7 runner identity / job id。
- 尚未完成 go-tool / Blender readiness probe。
- 尚未取得玉井橋 canonical latitude / longitude。
- 尚未取得 street-view physical images。
- 尚未取得 terrain/AOI physical data。
- 尚未產生 `.blend` / SceneX exchange artifacts。
- 尚未進入 SceneX runtime。
- 尚未取得 SceneX browse evidence。
- 尚未完成 OS Artifact Registry。
- 尚未建立 Delivery Revision。
- 尚未產生 `delivery/website/index.html`。

## CASE-ONLY 規則

本案例執行期間不得為了通過案例而直接改工具程式碼或加臨時 repo script。若現有正式工具不足，先停在該 gate、保存 evidence，再另行決定是否開工具修復批次。
