# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-18 Asia/Taipei

狀態：`IMPLEMENTING / GEO ACCEPTED / STREETVIEW REPAIR-RERUN REQUIRED / ORTHOPHOTO NEW GATE / TERRAIN DTM CONTINUES`

## Canonical execution contract

- 固定主機：`DESKTOP-UL7V2VV`
- canonical workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- case mirror：`D:\AI-Example\0003`
- canonical input：`location_text = 臺南市玉井橋`
- REAL / consequential work：一律由本機 self-hosted GitHub Action 執行
- OpenWorker persisted JobBinding / workspace 是 host/workspace authority；Action labels / matrix 只負責 transport fan-out。

## 已接受

### Step 1/2 — UL7 routing + go-tool formal execution

已完成：

- UL7 exact-host routing
- canonical go-tool local credential bootstrap
- cross-repo formal dispatch
- capability discovery / schema / readiness / run/jobs query
- OpenWorker live project state continuity

正式 OS closure run：

- `31923397881`
- business job：`95106955378`

### Step 3 — geolocation

已透過 Terrain formal Operator 取得並 materialize `workspace\geo\geolocation.json`，OpenWorker accepted。

## Step 4 — Street View：舊 acceptance 作廢，必須同 Step REAL rerun

舊 STATUS 曾把四向 headless PNG 標成 accepted；2026-08-18 依案例實際回報重新審查後，確認舊 headless producer 只驗證「PNG 存在 / 非 0 bytes / SHA256」，沒有對 headless screenshot 本身做 semantic visibility gate，因此黑畫面或近乎不可讀畫面仍可能被誤判成功。

因此：

- 舊 Street View business acceptance **撤銷**；
- 舊 PNG 只能保留作歷史 evidence，不得再餵給 Blender / consumer orchestration；
- `Terrain_To_DXF` 已補 headless screenshot semantic visibility fail-closed；
- 修復 commit：`027915e7e4ddf8384ab680cdb4a1f5105834fad6`；
- 測試同步 commit：`d1c58f96e5a0a6ca3448c45af79732bf1e9af96a`；
- 必須由最新版 `terrain.streetview.acquire` 在 UL7 重跑同一 Step；
- 四向 0/90/180/270 每張都必須 decode、通過 visibility gate、存在於 bound workspace、SHA256 與 manifest 一致後，才可重新標 `ACCEPTED`。

證據主檔：`evidence/0004-street-view-acquisition.md`。

## 新增 Step 4B — 正射影像 Orthophoto

案例回報顯示「正射影像沒有成功」並非單純 runner failure，而是原本 go-tool 正式 capability registry 根本沒有 orthophoto imagery acquisition。

Owning repair 已新增到 `Terrain_To_DXF`：

- NLSC PHOTO2 bounded WMTS acquisition / JPEG decode / mosaic / tile SHA256 provenance；
- CLI：`terrain-orthophoto-acquire`；
- Operator：`.github/workflows/operator-orthophoto-acquire.yml`；
- workspace output：`orthophoto\nlsc-photo2\`；
- 禁止全臺大量 cache；只允許 bounded AOI tile window；
- imagery 只能做 visual/reference truth，不得取代 DTM elevation geometry truth。

2026-08-18 已正式註冊 go-tool capability fragment：

- capability：`terrain.orthophoto.acquire`
- registry：`go-tool-runtime/capabilities.d/terrain-orthophoto.yaml`
- commit：`09e8e4da7d749fc6f46f5eda10da50a42f5fd63e`

接受條件：

1. go-tool discovery 能看見 `terrain.orthophoto.acquire`；
2. schema / readiness / preflight PASS；
3. UL7 assigned-host gate PASS；
4. 從 accepted `geo/geolocation.json` 取得中心點，不硬寫 lat/lng；
5. REAL NLSC PHOTO2 tiles 全部 HTTP / JPEG decode PASS；
6. bounded mosaic 非空且可視；
7. tile/mosaic physical SHA256 與 evidence 一致；
8. 成果 materialize 到 `D:\AI-Work\jobs\0003-YUJING-BRIDGE\orthophoto\nlsc-photo2`；
9. OpenWorker append-only evidence 記錄 run/job/runner/producer SHA；
10. 只有以上全部成立才標 `ACCEPTED`。

## Terrain / elevation AOI

既有正式能力：

- Terrain Operator：`terrain.aoi.build`
- 第一個 REAL terrain AOI 曾因 `D:\TaiwanDTM\catalog\dtm_catalog.sqlite missing` fail-closed。

使用者已決策：本機沒有 DEM 就完整重新下載，因此共用 Taiwan 20m DTM bootstrap 路線維持不變：

```text
D:\TaiwanDTM
  catalog\
  raw\
  extracted\
  normalized\
  cog\
```

既有 bootstrap evidence：`evidence/0005-terrain-aoi-and-dtm-bootstrap.md`。

## 目前正確下一步

1. 用最新版 go-tool 驗證 `terrain.streetview.acquire` 與 `terrain.orthophoto.acquire` discovery/schema/readiness。
2. UL7 重跑 Street View，同 Step 驗證四向 PNG semantic visibility，不接受僅有 bytes 的假成功。
3. UL7 執行 Orthophoto REAL acquisition，產生 PHOTO2 bounded mosaic + tile evidence。
4. 把 Street View / Orthophoto REAL run/job/runner/artifact hashes 即時回寫 evidence。
5. 兩個 imagery gate 都重新 accepted 後，consumer orchestration 才能引用新 artifacts。
6. DTM bootstrap / AOI 繼續完成，geometry truth 仍以 DTM 為權威。
7. 接 Terrain consumer orchestration → REAL Blender 5.2 → Blender QC。
8. SceneX import → REAL renderer/screenshot browse。
9. OS Artifact Registry → Delivery Revision → `delivery/website/index.html`。

任何新缺口仍依同一規則：找 owning repo → generic 修復 → local Action 驗證 → 同 Step REAL 重跑 → OpenWorker append-only evidence。