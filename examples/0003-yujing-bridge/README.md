# 案例 0003：臺南市玉井橋真實街景 → Blender 地形場景 → SceneX 瀏覽

> 類型：大模型逐步操作手冊  
> Canonical owner：OpenWorker `examples/0003-yujing-bridge/`  
> 執行主機：UL7  
> 目標：證明一個不知道各 repo 原始碼的大模型，可以只依本手冊與既有正式工具能力，完成「真實地點 → 真實街景/地形資料 → Blender 3D 場景 → SceneX 可瀏覽成果」的 REAL 閉環。

## 1. 任務

使用者指定地點：

> 臺南市玉井橋

目標不是只產生腳本、JSON、截圖或一個 Blender project，而是完成：

`使用者地點 → OpenWorker → go-tool → 既有地理/街景能力 → 真實位置解析 → 真實街景與地形參考 → Blender 建模/場景組裝 → physical 3D artifacts → SceneX 匯入/載入 → 實際可瀏覽場景 → evidence`

正式工作目錄由 OpenWorker / OS 決定；不得由大模型自行猜絕對路徑。

## 2. 案例原則

- 本案例優先使用**現有工具**完成成果，不先開發新工具。
- 先問工具，不先讀 owning repo 原始碼。
- 所有工具使用執行當下的最新正式提交；記錄 SHA 作 provenance，不 pin 舊版。
- 使用者輸入只給「臺南市玉井橋」；座標、街景 pano、道路方向、地形範圍必須由正式工具解析，不可在 workflow/script 偷偷寫死。
- consequential side effects 必須走受控工具與 self-hosted Action execution boundary。
- 如果工具缺能力，先把缺口記錄到 `STATUS.md` / evidence；案例本身不直接改工具。
- 舊 artifact、示意圖、假資料、Google 搜尋截圖、只建立空 Blender scene，都不能冒充 REAL 完成。
- 只有取得新鮮 physical artifact、來源 provenance、Blender scene、SceneX 實際載入與可瀏覽證據才算完成。

## 3. Step 1 — UL7 健康檢查

確認 UL7 self-hosted runner 在線且可接單。

向 go-tool 查 health，確認案例需要的既有能力可以被發現與呼叫。

驗收：

- UL7 runner online / idle / 可執行；
- go-tool runtime 可用；
- Blender CLI readiness 可查；
- 真實地理/街景取得能力可查；
- SceneX import / launch / browse 能力可查。

若任何一項不可用，記錄 blocker；不得私下改用 repo script 冒充正式案例路徑。

## 4. Step 2 — 發現既有能力

從 go-tool / OpenWorker 列出 capabilities，尋找能完成下列工作的正式能力：

1. 地點文字解析 / geocoding；
2. 真實街景取得；
3. 真實地形或可建立地形的 elevation / map data；
4. Blender CLI 建模、匯入、材質、場景輸出；
5. SceneX 場景匯入、啟動、瀏覽與驗證。

本案例不預設 capability 名稱；以執行當下工具資訊契約為準。

## 5. Step 3 — 真實位置解析

canonical input：

- `location_text = 臺南市玉井橋`
- `delivery_case = 0003`

正式工具必須解析出唯一或可驗證的真實位置，至少保存：

- 標準化地名；
- latitude / longitude；
- 解析來源；
- 解析時間；
- 若存在同名候選，必須保留 disambiguation 證據。

驗收：解析結果必須能合理對應臺南市玉井區的玉井橋；不得只因字串相似就接受錯誤地點。

## 6. Step 4 — 真實街景取得

以 Step 3 的 canonical location 取得真實街景參考。

最低要求：

- 使用既有正式街景能力；
- 優先取得可用最高解析度；
- 至少涵蓋橋體、道路方向、橋頭/周邊環境；
- 能保留 pano / heading / pitch / FOV / capture metadata 或等價 provenance；
- 街景影像必須 materialize 到案例 workspace；
- 每個 accepted image 記錄 size / mtime / SHA256。

若只能取得瀏覽器畫面，仍必須保存來源位置與視角 metadata，不能只留無法追溯的截圖。

## 7. Step 5 — 真實地形 / 場地資料

取得足以重建橋梁周邊地形的現有資料來源。

最低 gate：

- 以玉井橋為中心建立明確 AOI；
- 保存 elevation / terrain / map reference 的來源與範圍；
- 保留座標系 / scale / north direction；
- 地形資料能轉入 Blender，且與街景方向可對齊。

若現有工具只能取得其中一部分，照實做出目前能做到的成果並記錄缺口，不製造假 DEM 或假地形冒充真實資料。

## 8. Step 6 — Blender REAL 場景

由 UL7 上既有 Blender CLI 能力建立玉井橋 3D 場景。

場景至少包含：

- 具真實比例基準的 terrain；
- 橋梁位置與道路走向；
- 依真實街景建立的橋體/護欄/路面/河道或周邊主要視覺結構；
- 真實街景作為建模/材質/視覺參考，而非只把照片平貼在背景；
- north / scale / origin metadata；
- 可供 SceneX 使用的 camera / spawn point。

最低 physical artifacts：

- `.blend` canonical scene；
- SceneX 可接受的交換格式（依既有正式能力決定，例如 GLB/GLTF 或其他）；
- Blender preview render / viewport evidence；
- manifest：來源資料、版本、檔案路徑、size、mtime、SHA256。

## 9. Step 7 — Blender 視覺與幾何 QC

不得因 Blender CLI exit code 0 就算成功。

至少檢查：

- bridge / road / terrain 沒有明顯漂浮或穿插；
- scale 合理；
- 地形與橋梁位置相符；
- 主要街景視角在 Blender 中可找到對應場景；
- 沒有空場景、全部物件在原點、材質全失效等技術錯誤。

保存 accepted Blender scene 的 SHA256，後續 SceneX 必須使用同一 accepted artifact 或有可追溯的轉換 artifact。

## 10. Step 8 — SceneX 匯入

使用 SceneX 現有正式能力載入 accepted Blender/export artifact。

最低 gate：

- import / load 成功；
- SceneX 中出現對應玉井橋場景；
- camera / player spawn 位於有效位置；
- terrain / bridge / road 的主要物件實際存在；
- 記錄 imported artifact SHA256 與 SceneX scene/project identity。

不得以「檔案格式可以被解析」冒充 SceneX 已完成載入。

## 11. Step 9 — SceneX REAL 瀏覽

必須實際啟動 SceneX 並瀏覽成果。

最低驗收：

- 可從 spawn point 移動/觀看場景；
- 至少走訪或觀察橋頭、橋面、周邊地形三個視角；
- SceneX runtime 不崩潰；
- 取得新鮮 screenshot / capture evidence；
- 截圖內容需能辨識為本案例場景，不接受空白畫面或 editor chrome 畫面當成果。

## 12. 完成標準

只有以下全部成立才可標 `LIVE_VERIFIED / DELIVERABLE`：

1. 案例由 UL7 正式 self-hosted execution 執行。
2. 使用者只提供「臺南市玉井橋」，真實位置由正式工具解析。
3. 真實街景已取得並有 provenance / SHA256。
4. 真實地形/場地資料已取得並保留來源、AOI、座標與比例資訊。
5. Blender 產生新鮮 physical `.blend` 與 SceneX 交換 artifact。
6. Blender visual/geometric QC PASS。
7. SceneX 實際載入 accepted artifact。
8. SceneX 可實際瀏覽玉井橋場景並保存 runtime evidence。
9. physical artifacts 全部可追溯到本次 execution 與最新工具 SHA。
10. `STATUS.md` 與 `evidence/README.md` 記錄真實證據與任何缺口。

## 13. 案例遇到缺口時的規則

本案例的目的之一就是讓缺口自然暴露。

若現有工具無法完成某一步：

1. 不在案例裡偷偷補臨時 script；
2. 不把人工操作冒充大模型工具能力；
3. 在 `STATUS.md` 記錄 blocker；
4. 在 evidence 保存失敗輸入、回覆、execution/job/run identity；
5. 標明真正 owning repo；
6. 後續若決定修工具，才另開開發批次；修完後從本手冊正規步驟重新驗證。

## 14. 相關 owning repos / systems

- OpenWorker：案例入口、execution governance、workspace、證據索引。
- go-tool-runtime：能力發現、schema、readiness、dispatch、execution query。
- 既有地理/街景工具：位置解析、街景、地形/參考資料取得。
- Blender integration：3D terrain / bridge / scene 建立與 physical artifact 輸出。
- SceneX：場景匯入、runtime、實際瀏覽驗證。

這些 repo 可以保存 implementation 文件，但**案例操作手冊的 canonical copy 固定在 OpenWorker**。
