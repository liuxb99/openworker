# 案例 0003：臺南市玉井橋真實街景 → Blender 地形場景 → SceneX 瀏覽 → OS 成果網站交付

> 類型：大模型逐步操作手冊  
> Canonical owner：OpenWorker `examples/0003-yujing-bridge/`  
> 固定執行主機：UL7（Windows `DESKTOP-UL7V2VV`）  
> Canonical workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`  
> Case mirror：`D:\AI-Example\0003`  
> 執行邊界：**所有 REAL / consequential 工作一律由本機 self-hosted GitHub Action 執行**  
> 目標：證明一個不知道各 repo 原始碼的大模型，可以只依本手冊與正式工具能力，完成「真實地點 → 真實街景/地形資料 → Blender 3D 場景 → SceneX 可瀏覽成果 → OS 成果網站」的 REAL 閉環。

## 0. 本案例就是後續正式使用手冊

本案例不是一次性 smoke test。**每一次真實執行都必須把完整操作過程詳實寫回本手冊與 `STATUS.md` / `evidence/`，讓案例本身逐步演化成後續大模型可以直接照著重做的正式使用手冊。**

### 0.1 執行鐵律：全部用本機 Action

凡是會讀寫本機工作區、探測本機 runtime、取得真實外部資料、產生或修改 physical artifact、啟動 Blender / SceneX、執行 OS workflow、建立 Delivery Revision / website 的操作，**一律由 self-hosted GitHub Action 在指定本機執行**。

ChatGPT / GitHub connector 只負責：

- 讀最新 repo / 文檔 / contract；
- 建立或修正正式 workflow / owning repo 代碼；
- dispatch / 查詢 Action；
- 讀 Action evidence / artifact metadata；
- 將完整過程回寫案例手冊；
- 發現缺口時修真正 owning repo，再由本機 Action 重跑同一步。

禁止以 connector 端、雲端 runner、臨時人工 shell、未受控遠端執行取代本應由本機 Action 完成的 REAL 工作。

### 0.2 每一步必須保存的完整 provenance

每一個 Step 至少記錄：

- 使用者 / canonical input；
- OpenWorker project / execution / job / binding / workspace identity；
- 實際使用 capability / tool / workflow；
- owning repo 與**執行當下最新正式 commit SHA**；
- Action workflow、run id、attempt、job id、runner name、runner labels、`COMPUTERNAME`；
- go-tool AgentInformationPack / current facts 摘要；
- capability discovery / detail / schema / readiness / preflight / dispatch / result-query 的正式輸入與輸出摘要；
- OS job / execution / artifact / delivery identity；
- physical artifact canonical path、size、mtime、SHA256；
- stdout/stderr 或 bounded log evidence；
- PASS / FAIL / BLOCKED 的判定依據；
- 發現的缺口、根因、真正 owning repo；
- 缺口修復 commit / tests / Action 驗證；
- 修復後重新執行**同一步**的 run/job/evidence；
- 最後 accepted 的正確操作方式；
- 舊做法若被新版設計取代，記錄「deprecated / replaced by」而不是偷偷覆蓋歷史。

禁止只寫「成功」「失敗」「已完成」。文檔必須能回答：**做了什麼、為什麼這樣做、用什麼做、在哪台機器做、輸入是什麼、輸出是什麼、產生什麼、如何驗證、哪裡壞、怎麼修、修完如何證明、下次應該怎麼重做。**

### 0.3 每一步的標準文檔結構

`evidence/NNNN-*.md` 應按下列順序記錄：

1. Step 目的與 canonical input
2. 執行前 latest-design audit（相關 owning repos / SHAs / canonical contract）
3. OpenWorker current state / JobBinding / workspace
4. go-tool current information / capability discovery
5. readiness / schema / queue preflight
6. self-hosted Action dispatch
7. runner identity 與 host gate
8. REAL execution log 摘要
9. physical artifacts / hashes / provenance
10. QC / acceptance 判定
11. gap / root cause（如有）
12. owning-repo repair / tests / commit（如有）
13. 同 Step REAL rerun（如有）
14. accepted procedure（後續手冊應採用的方法）
15. next Step

## 1. 任務

使用者指定地點：

> 臺南市玉井橋

完整目標：

`使用者地點 → OpenWorker → go-tool → 地理/街景能力 → 真實位置解析 → 真實街景與地形參考 → Blender 建模/場景組裝 → physical 3D artifacts → SceneX 匯入/載入 → 實際可瀏覽場景 → OS Artifact Registry / Delivery Revision → delivery/website/index.html → evidence`

Canonical workspace 沿用案例 0002 已驗證的 OpenWorker/OS 固定工作目錄規則：

- workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- case mirror：`D:\AI-Example\0003`
- binding file：`D:\AI-Work\jobs\0003-YUJING-BRIDGE\.openworker\job-binding.json`

此路徑必須由 OpenWorker persisted JobBinding 驗證 host/workspace/project/job identity；不得只因 YAML 寫了該路徑就視為 binding 成立。

## 2. 案例原則

- **每個 Step 開始前先 audit 相關 owning repo 最新 main 的設計與 contract；所有專案都可能已補新缺口，不得沿用過期假設。**
- 優先使用現有最新正式工具完成成果。
- OpenWorker 是 project work state / ledger / binding authority；go-tool-runtime 是 Agent current information / capability / readiness / formal dispatch 入口；AI-Engineering-OS 與各 owning tool 負責真正 execution / mutate。
- 先問工具資訊契約，再讀 owning repo；只有案例暴露真缺口時才進 owning repo 修復。
- 所有工具使用執行當下的最新正式提交；記錄 SHA 作 provenance，不 pin 舊版。
- 使用者輸入只給「臺南市玉井橋」；座標、街景 pano、道路方向、地形範圍必須由正式工具解析，不可偷偷寫死。
- **所有 consequential side effects 必須走本機 self-hosted Action execution boundary。**
- 本案例固定由 UL7（`DESKTOP-UL7V2VV`）執行；其他 Windows runner 只能 clean skip，不得代做成果。
- OpenWorker persisted JobBinding / assigned host / workspace 是 execution authority；Action matrix / labels 只是 transport fan-out，不得把「哪台 runner 搶到 job」誤當成 authority。
- **案例中一旦發現真正缺口，就補真正 owning repo 的缺口；不得繞過、假造或用臨時腳本遮蔽。**
- 修工具後必須用最新 commit 從原來失敗的案例 Step 重新跑；不能只用 unit test 宣稱案例已修復。
- 每次缺口與修復結果都要回寫本手冊，讓下一次執行不需要重新摸索。
- 舊 artifact、示意圖、假資料、無 provenance 截圖、空 Blender scene 都不能冒充 REAL 完成。
- SceneX 可瀏覽只是中間 gate；依 OS 規則，最終成果必須是一個成果網站。

## 3. Step 1 — OpenWorker 工作狀態、UL7 binding 與本機 Action readiness

先由 OpenWorker 恢復 / 建立 CASE-0003 project work state，確認 persisted JobBinding 固定：

- assigned host：`DESKTOP-UL7V2VV`
- workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- mirror：`D:\AI-Example\0003`
- project / job / execution identity：由正式 API 建立或恢復

再由 go-tool 取得 current AgentInformationPack / environment / operational facts，並透過正式 Action routing 送到 self-hosted Windows runner。

Action transport 可使用共享 labels / candidate fan-out，但 consequential case steps 必須同時通過：

1. persisted JobBinding host/workspace 驗證；
2. `COMPUTERNAME == DESKTOP-UL7V2VV`；
3. latest tool/repo SHA provenance；
4. readiness / queue preflight。

非 UL7 runner 必須 clean skip，不得產生 consequential side effects。

### Step 1 REAL 結論（2026-08-16）

Cross-repo readiness run `31921072421` 已由 `DESKTOP-UL7V2VV-R002` 接單並輸出 `CASE0003_UL7_IDENTITY_PASS`，因此 UL7 online / registered / accepting jobs 已確認。該 run 後續失敗是外層 workflow 直接 checkout private `go-tool-runtime` 時的 credential scope 問題，不是 runner availability 問題。

正式修正：後續不再由 Case workflow 自己 checkout/build private tools；改由 UL7 上既有 go-tool-runtime 依其正式 credential/capability provider 執行。

## 4. Step 2 — 用最新版 go-tool 發現正式 capabilities

在 UL7 本機 Action 中，由最新版 go-tool / OpenWorker 正式列出並查 detail/schema/readiness/preflight：

1. geocoding / 地點文字解析；
2. 真實街景取得（目前候選 owner 包含 Terrain_To_DXF，但仍以 runtime discovery 為準）；
3. elevation / terrain / map data；
4. Blender 3D runtime / 建模、匯入、材質、輸出；
5. SceneX 場景匯入、啟動、瀏覽、runtime capture / 驗證；
6. OS Artifact Registry / Delivery Revision；
7. 成果網站 materialization。

不得憑 repo 名稱、舊文檔或歷史記憶猜 capability 名稱。若 go-tool 無法發現一個實際已存在的最新正式能力，這本身就是 go-tool / registry integration gap，必須修 owner 後重跑 Step 2。

目前已知候選 gap：`Terrain_To_DXF` main 已有 Street View metadata / snapshot / route scan / highest-resolution tile acquisition / native panorama stitch 等能力，而目前 go-tool registry 明確可見的 Terrain capability 仍是 `terrain.dxf.generate`；需確認 Street View/location 是否已有正式 Operator workflow，若無則補 owner + registry。

## 5. Step 3 — 真實位置解析

canonical input：

- `location_text = 臺南市玉井橋`
- `delivery_case = 0003`

由 UL7 self-hosted Action 透過 Step 2 accepted capability 執行。至少保存：標準化地名、latitude / longitude、provider/source、解析時間、同名候選排除證據與 result-query provenance。

## 6. Step 4 — 真實街景取得

由 UL7 self-hosted Action 以 canonical location 取得可用最高解析度街景，至少涵蓋橋體、道路方向、橋頭/周邊環境；保存 pano 或等價 identity、heading / pitch / FOV / capture metadata、master/tile provenance（若 capability 提供）與 physical image hashes。

## 7. Step 5 — 真實地形 / 場地資料

由 UL7 self-hosted Action 以玉井橋建立 AOI；保存 elevation / terrain / map source、bbox/radius、座標系、scale、north。資料必須能轉入 Blender 並與街景方向對齊。

## 8. Step 6 — Blender REAL 場景

由 UL7 self-hosted Action 透過 AI-Engineering-OS 最新 canonical Blender 3D runtime 建立至少包含 terrain、橋梁位置、道路走向、橋體/護欄/路面/河道或周邊主要視覺結構、north/scale/origin metadata、SceneX spawn/camera 的場景。

最低 physical artifacts：`.blend`、SceneX 可接受交換格式、preview / viewport evidence、manifest（path / size / mtime / SHA256）。

## 9. Step 7 — Blender 視覺與幾何 QC

由本機 Action 執行 QC：檢查 bridge / road / terrain 無明顯漂浮穿插、比例合理、方向與街景相符、非空場景、材質與主要物件有效。保存 accepted Blender SHA256。

## 10. Step 8 — SceneX 匯入

由 UL7 self-hosted Action 使用最新版正式 SceneX 能力載入 accepted Blender/export artifact；記錄 SceneX scene/project identity、imported artifact SHA256、主要 objects 與有效 spawn。

## 11. Step 9 — SceneX REAL 瀏覽

由 UL7 self-hosted Action 實際啟動 SceneX。至少取得橋頭、橋面、周邊地形三個新鮮 runtime captures；runtime 不崩潰，內容可辨識為本案例。

## 12. Step 10 — OS Artifact Registry / Delivery Revision

由 UL7 self-hosted Action 把 accepted geolocation/source manifest、street-view、terrain、`.blend`、exchange artifact、SceneX identity、preview/captures、所有 hashes 與 execution provenance 登錄 OS Artifact Registry，建立 Delivery Revision。

## 13. Step 11 — OS 成果網站

由 UL7 self-hosted Action materialize canonical website entry：

`delivery/website/index.html`

成果網站至少包含：案例名稱、真實位置摘要、街景 provenance、terrain/AOI、Blender preview、SceneX 三個 accepted captures、SceneX identity/瀏覽入口、artifact 索引/下載入口、QC、Artifact Registry / Delivery Revision identity、execution/job/runner/tool SHA provenance。

網站必須是本次 execution 新鮮 physical artifact，無 placeholder / broken links，內容可明確辨識為「臺南市玉井橋」。

## 14. 發現缺口時的正式修復閉環

案例遇到 FAIL / BLOCKED 時固定使用：

`案例 Step 本機 Action 失敗 → 保存原始 evidence → 確認 owning repo → 更新案例 gap → 修真正 owning repo → tests/build → 推最新 commit → 回到同一案例 Step → 用 UL7 本機 Action 重跑 → 比對新 evidence → PASS 後把正確操作回寫手冊與 OpenWorker ledger`

修復原則：

- 不寫案例特例來繞過正式 capability；
- 不降級到舊 commit；
- 不以人工操作取代原應由大模型/工具完成的能力；
- 不因 unit test PASS 就跳過 REAL case rerun；
- 若缺口跨 repo，分別修真正 owner，但最終仍由 0003 同一路徑做整體驗收；
- 修復本身可由 GitHub connector 修改 repo，但**修復後的產品驗證與案例 REAL rerun 必須由本機 Action 執行**。

## 15. 完成標準

只有全部成立才可標 `LIVE_VERIFIED / DELIVERABLE`：

1. 所有 REAL / consequential work 都有 self-hosted Action run/job/runner evidence。
2. consequential work 固定由 UL7 執行，且符合 OpenWorker persisted binding。
3. 真實位置由正式工具解析。
4. 真實街景有 provenance / SHA256。
5. 真實 terrain/AOI 有來源與尺度資訊。
6. 有新鮮 `.blend` 與交換 artifact。
7. Blender QC PASS。
8. SceneX 實際載入 accepted artifact。
9. SceneX REAL 瀏覽 PASS 且有三個 accepted captures。
10. accepted artifacts 已登錄 OS Artifact Registry。
11. Delivery Revision 已建立。
12. physical `delivery/website/index.html` 已存在且可正常瀏覽。
13. 本案例每一步的 latest-design audit、正式輸入/輸出、Action 執行、缺口、修復、同 Step 重跑與 evidence 已完整回寫文檔，使其可作下一輪正式操作手冊。
