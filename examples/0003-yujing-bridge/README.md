# 案例 0003：臺南市玉井橋真實街景 → Blender 地形場景 → SceneX 瀏覽 → OS 成果網站交付

> 類型：大模型逐步操作手冊  
> Canonical owner：OpenWorker `examples/0003-yujing-bridge/`  
> 固定執行主機：UL7（Windows `DESKTOP-UL7V2VV`）  
> 目標：證明一個不知道各 repo 原始碼的大模型，可以只依本手冊與正式工具能力，完成「真實地點 → 真實街景/地形資料 → Blender 3D 場景 → SceneX 可瀏覽成果 → OS 成果網站」的 REAL 閉環。

## 0. 本案例同時是後續操作手冊

本案例不是一次性 smoke test。**每一次真實執行都要把實際操作過程詳實寫回本手冊與 `STATUS.md` / `evidence/README.md`，讓文檔逐步演化成可讓後續大模型照著重做的正式操作手冊。**

每一個 Step 至少記錄：

- 使用者 / canonical input；
- 實際使用 capability / tool / workflow；
- owning repo 與執行當下 commit SHA；
- Action run id / job id / runner name / `COMPUTERNAME`；
- readiness / schema / dispatch / query 的正式輸入與輸出摘要；
- physical artifact path / size / mtime / SHA256；
- PASS / FAIL / BLOCKED 的判定依據；
- 發現的缺口、根因、真正 owning repo；
- 缺口修復 commit / tests / Action 驗證；
- 修復後重新執行同一步的結果；
- 最後 accepted 的正確操作方式。

禁止只寫「成功」「失敗」「已完成」。文檔必須能回答：**做了什麼、用什麼做、在哪台機器做、產生什麼、如何驗證、哪裡壞、怎麼修、修完如何證明。**

## 1. 任務

使用者指定地點：

> 臺南市玉井橋

完整目標：

`使用者地點 → OpenWorker → go-tool → 地理/街景能力 → 真實位置解析 → 真實街景與地形參考 → Blender 建模/場景組裝 → physical 3D artifacts → SceneX 匯入/載入 → 實際可瀏覽場景 → OS Artifact Registry / Delivery Revision → delivery/website/index.html → evidence`

正式工作目錄由 OpenWorker / OS 決定；不得由大模型自行猜絕對路徑。

## 2. 案例原則

- 優先使用現有正式工具完成成果。
- 先問工具資訊契約，再讀 owning repo；只有案例暴露真缺口時才進 owning repo 修復。
- 所有工具使用執行當下的最新正式提交；記錄 SHA 作 provenance，不 pin 舊版。
- 使用者輸入只給「臺南市玉井橋」；座標、街景 pano、道路方向、地形範圍必須由正式工具解析，不可偷偷寫死。
- consequential side effects 必須走受控工具與 self-hosted Action execution boundary。
- 本案例固定由 UL7（`DESKTOP-UL7V2VV`）執行；其他 Windows runner 只能 clean skip，不得代做成果。
- **案例中一旦發現真正缺口，就補真正 owning repo 的缺口；不得繞過、假造或用臨時腳本遮蔽。**
- 修工具後必須用最新 commit 從原來失敗的案例 Step 重新跑；不能只用 unit test 宣稱案例已修復。
- 每次缺口與修復結果都要回寫本手冊，讓下一次執行不需要重新摸索。
- 舊 artifact、示意圖、假資料、無 provenance 截圖、空 Blender scene 都不能冒充 REAL 完成。
- SceneX 可瀏覽只是中間 gate；依 OS 規則，最終成果必須是一個成果網站。

## 3. Step 1 — UL7 健康與路由檢查

確認固定執行主機 UL7（Windows `DESKTOP-UL7V2VV`）的 self-hosted runner 在線且可接單。

Action 可使用 `[self-hosted, Windows, X64]` routing 讓 runner 接單，但 consequential case steps 必須先驗證 `COMPUTERNAME == DESKTOP-UL7V2VV`；非 UL7 runner必須 clean skip。

同一輪還要查：

- go-tool health；
- Blender CLI readiness；
- 地理/街景能力 readiness；
- SceneX import / launch / browse readiness；
- OS Artifact Registry / Delivery Revision / website delivery readiness。

### Step 1 記錄模板

- run id：
- job id：
- runner name：
- `COMPUTERNAME`：
- OpenWorker SHA：
- go-tool SHA：
- health output：
- Blender path/version：
- SceneX readiness：
- OS delivery readiness：
- verdict：`PASS / FAIL / BLOCKED`
- blocker / owning repo：
- fix commit / verification（如有）：

## 4. Step 2 — 發現正式 capabilities

由 go-tool / OpenWorker 正式列出並查 detail/schema/readiness：

1. geocoding / 地點文字解析；
2. 真實街景取得；
3. elevation / terrain / map data；
4. Blender CLI 建模、匯入、材質、輸出；
5. SceneX 場景匯入、啟動、瀏覽、驗證；
6. OS Artifact Registry / Delivery Revision；
7. 成果網站 materialization。

不得憑 repo 名稱猜 capability 名稱。

## 5. Step 3 — 真實位置解析

canonical input：

- `location_text = 臺南市玉井橋`
- `delivery_case = 0003`

至少保存：標準化地名、latitude / longitude、provider/source、解析時間、同名候選排除證據。

## 6. Step 4 — 真實街景取得

以 canonical location 取得可用最高解析度街景，至少涵蓋橋體、道路方向、橋頭/周邊環境；保存 pano 或等價 identity、heading / pitch / FOV / capture metadata 與 physical image hashes。

## 7. Step 5 — 真實地形 / 場地資料

以玉井橋建立 AOI；保存 elevation / terrain / map source、bbox/radius、座標系、scale、north。資料必須能轉入 Blender 並與街景方向對齊。

## 8. Step 6 — Blender REAL 場景

由 UL7 上正式 Blender 能力建立至少包含 terrain、橋梁位置、道路走向、橋體/護欄/路面/河道或周邊主要視覺結構、north/scale/origin metadata、SceneX spawn/camera 的場景。

最低 physical artifacts：`.blend`、SceneX 可接受交換格式、preview / viewport evidence、manifest（path / size / mtime / SHA256）。

## 9. Step 7 — Blender 視覺與幾何 QC

檢查 bridge / road / terrain 無明顯漂浮穿插、比例合理、方向與街景相符、非空場景、材質與主要物件有效。保存 accepted Blender SHA256。

## 10. Step 8 — SceneX 匯入

使用正式 SceneX 能力載入 accepted Blender/export artifact；記錄 SceneX scene/project identity、imported artifact SHA256、主要 objects 與有效 spawn。

## 11. Step 9 — SceneX REAL 瀏覽

實際啟動 SceneX。至少取得橋頭、橋面、周邊地形三個新鮮 runtime captures；runtime 不崩潰，內容可辨識為本案例。

## 12. Step 10 — OS Artifact Registry / Delivery Revision

把 accepted geolocation/source manifest、street-view、terrain、`.blend`、exchange artifact、SceneX identity、preview/captures、所有 hashes 與 execution provenance 登錄 OS Artifact Registry，建立 Delivery Revision。

## 13. Step 11 — OS 成果網站

canonical website entry：

`delivery/website/index.html`

成果網站至少包含：案例名稱、真實位置摘要、街景 provenance、terrain/AOI、Blender preview、SceneX 三個 accepted captures、SceneX identity/瀏覽入口、artifact 索引/下載入口、QC、Artifact Registry / Delivery Revision identity、execution/job/runner/tool SHA provenance。

網站必須是本次 execution 新鮮 physical artifact，無 placeholder / broken links，內容可明確辨識為「臺南市玉井橋」。

## 14. 發現缺口時的正式修復閉環

案例遇到 FAIL / BLOCKED 時固定使用：

`案例 Step 失敗 → 保存原始 evidence → 確認 owning repo → 更新 STATUS 缺口 → 修真正 owning repo → tests/build → 推最新 commit → 回到同一案例 Step → 用 UL7 Action 重跑 → 比對新 evidence → PASS 後把正確操作回寫手冊`

修復原則：

- 不寫案例特例來繞過正式 capability；
- 不降級到舊 commit；
- 不以人工操作取代原應由大模型/工具完成的能力；
- 不因 unit test PASS 就跳過 REAL case rerun；
- 若缺口跨 repo，分別修真正 owner，但最終仍由 0003 同一路徑做整體驗收。

## 15. 完成標準

只有全部成立才可標 `LIVE_VERIFIED / DELIVERABLE`：

1. consequential work 固定由 UL7 執行。
2. 真實位置由正式工具解析。
3. 真實街景有 provenance / SHA256。
4. 真實 terrain/AOI 有來源與尺度資訊。
5. 有新鮮 `.blend` 與交換 artifact。
6. Blender QC PASS。
7. SceneX 實際載入 accepted artifact。
8. SceneX REAL 瀏覽 PASS 且有三個 accepted captures。
9. accepted artifacts 已登錄 OS Artifact Registry。
10. Delivery Revision 已建立。
11. physical `delivery/website/index.html` 已存在且可正常瀏覽。
12. 本案例每一步的實際操作、缺口、修復、重跑與 evidence 已完整回寫文檔，使其可作下一輪正式操作手冊。
