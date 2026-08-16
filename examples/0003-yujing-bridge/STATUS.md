# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`READY TO EXECUTE / CASE-ONLY / NO TOOL DEVELOPMENT`

## 任務

使用既有工具，由 UL7 執行：

`臺南市玉井橋 → 真實位置解析 → 真實街景/地形參考 → Blender 3D 場景 → SceneX 匯入 → SceneX REAL 瀏覽`

## 已完成

- 案例 0003 canonical 入口建立於 OpenWorker `examples/0003-yujing-bridge/`。
- 已明確規定本案例不先開發工具，先用案例暴露既有工具缺口。
- 已定義 REAL 完成標準：真實位置、真實街景 provenance、terrain/AOI、Blender physical artifacts、SceneX 實際載入與 runtime 瀏覽證據。
- 已指定 UL7 為本案例 execution host。

## 下一個執行點

依 `README.md` 從 Step 1 開始：

1. 確認 UL7 self-hosted runner 在線且可接單。
2. 透過 go-tool 查 health / capabilities。
3. 發現既有 geocoding / street-view / terrain / Blender / SceneX 能力。
4. 以 canonical input `臺南市玉井橋` 做真實位置解析。
5. 不改工具；若任一步失敗，記錄 blocker、owning repo 與證據。

## 尚未完成

- 尚未建立正式 case 0003 execution。
- 尚未確認 UL7 runner identity / job id。
- 尚未取得玉井橋 canonical latitude / longitude。
- 尚未取得 street-view physical images。
- 尚未取得 terrain/AOI physical data。
- 尚未產生 `.blend` / GLB/GLTF 等 scene artifacts。
- 尚未進入 SceneX runtime。
- 尚未取得 SceneX browse evidence。

## CASE-ONLY 規則

本案例執行期間不得為了通過案例而直接改工具程式碼或加臨時 repo script。若現有正式工具不足，先停在該 gate、保存 evidence，再另行決定是否開工具修復批次。
