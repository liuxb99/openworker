# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`EXECUTING / UL7 RUNNER GATE / CASE-ONLY / NO TOOL DEVELOPMENT`

## 任務

使用既有工具，固定由 UL7 執行：

`臺南市玉井橋 → 真實位置解析 → 真實街景/地形參考 → Blender 3D 場景 → SceneX 匯入 → SceneX REAL 瀏覽`

## 固定執行邊界

- 本案例只允許 UL7 self-hosted Action 執行。
- workflow runner selector：`[self-hosted, Windows, X64, UL7]`。
- 不使用多機 candidate、不 fallback 到其他 runner。
- UL7 離線、忙碌或 label 不匹配時，案例停在 runner gate，不換機。
- 案例 workflow：`.github/workflows/case-0003-yujing-bridge-ul7.yml`。

## 已完成

- 案例 0003 canonical 入口建立於 OpenWorker `examples/0003-yujing-bridge/`。
- 已明確規定本案例不先開發工具，先用案例暴露既有工具缺口。
- 已定義 REAL 完成標準：真實位置、真實街景 provenance、terrain/AOI、Blender physical artifacts、SceneX 實際載入與 runtime 瀏覽證據。
- 已建立 UL7 專屬 self-hosted workflow，只做 runner identity 與既有工具 readiness probe，不修改工具。
- 正式 UL7 probe run 已建立：`31919878274`。
- probe head：`99d6a000204b40f7ee2c061174b671f65a02fdcf`。
- 截至本次更新，run `31919878274` 狀態為 `queued`。

## 目前 gate

Step 1 — UL7 runner identity / readiness。

等待 run `31919878274` 被帶有 `UL7` label 的 self-hosted runner 接單後，必須取得：

- GitHub runner name；
- Windows `COMPUTERNAME`；
- runner OS / arch；
- go-tool 是否可直接呼叫；
- Blender CLI 是否可直接呼叫。

只有 UL7 實際接單後才進 Step 2 capability discovery。

## 下一個執行點

1. 查 run `31919878274` 是否由 UL7 接單。
2. 取得 job id 與 runner identity。
3. 讀 readiness probe 結果。
4. UL7 gate PASS 後，透過 go-tool 查 health / capabilities。
5. 發現既有 geocoding / street-view / terrain / Blender / SceneX 能力。
6. 以 canonical input `臺南市玉井橋` 做真實位置解析。
7. 不改工具；若任一步失敗，記錄 blocker、owning repo 與證據。

## 尚未完成

- 尚未確認 UL7 runner identity / job id。
- 尚未完成 go-tool / Blender readiness probe。
- 尚未取得玉井橋 canonical latitude / longitude。
- 尚未取得 street-view physical images。
- 尚未取得 terrain/AOI physical data。
- 尚未產生 `.blend` / GLB/GLTF 等 scene artifacts。
- 尚未進入 SceneX runtime。
- 尚未取得 SceneX browse evidence。

## CASE-ONLY 規則

本案例執行期間不得為了通過案例而直接改工具程式碼或加臨時 repo script。若現有正式工具不足，先停在該 gate、保存 evidence，再另行決定是否開工具修復批次。
