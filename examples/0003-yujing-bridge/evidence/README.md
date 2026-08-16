# 0003 臺南市玉井橋 — Evidence Index

本目錄只保存**證據索引與驗收規則**；大型街景影像、terrain data、`.blend`、GLB/GLTF、SceneX scene/runtime capture 等二進位成果保存在正式 execution workspace，不複製進 Git。

## Canonical input

- location_text：`臺南市玉井橋`
- delivery_case：`0003`
- assigned host：`UL7`

## 必須收集的 evidence

1. 工具版本 provenance：OpenWorker / go-tool / 地理街景工具 / Blender integration / SceneX 實際使用 SHA。
2. go-tool health / capabilities / capability detail / readiness / dispatch response。
3. execution id / target run id / job id / runner identity。
4. geocoding result：標準化地名、latitude、longitude、來源、解析時間、候選排除證據。
5. street-view provenance：pano 或等價 identity、heading / pitch / FOV、capture/source metadata。
6. accepted street-view physical files：path / size / mtime / SHA256。
7. terrain/AOI：bbox/radius、coordinate reference、scale、north、來源資料與 physical file hashes。
8. Blender scene evidence：`.blend` path / size / mtime / SHA256、scene units、origin、north、主要 objects、preview render。
9. Blender → SceneX transfer artifact：format / path / size / mtime / SHA256。
10. SceneX import identity：scene/project/runtime identity 與 imported artifact correlation。
11. SceneX runtime evidence：橋頭、橋面、周邊地形至少三個新鮮視角或等價 capture。
12. blocker evidence：任何既有工具無法完成步驟時的正式輸入、輸出、錯誤、owning repo、run/job identity。

## REAL 驗收規則

- workflow success 本身不是成果。
- geocoding 成功但位置錯誤，不算成功。
- 網頁搜尋圖片、無來源截圖、示意地形不能冒充真實資料。
- Blender CLI exit code 0 但沒有 physical `.blend` / scene artifact，不算成功。
- SceneX 只成功解析檔案格式但沒有實際 runtime 場景，不算成功。
- SceneX 打開空白 editor、預設場景或無法辨識為玉井橋的畫面，不算成功。
- 舊 artifact、mtime 不新鮮、無 execution correlation，不算成功。
- accepted artifact 需要有 SHA256 與 provenance chain。
- 每次重跑都記錄當下最新工具 SHA；SHA 是 provenance，不是 compatibility pin。

## 最終證據鏈

完成時應可從一個 SceneX runtime capture 反查：

`SceneX capture → SceneX scene → imported 3D artifact SHA → accepted Blender scene SHA → terrain/street-view source SHA → canonical 玉井橋 geolocation → case execution/job → tool SHAs`

完成後由 `STATUS.md` 指向本索引中的最終 accepted evidence。
