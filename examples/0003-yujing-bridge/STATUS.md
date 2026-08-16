# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`IMPLEMENTING / GEO+STREETVIEW ACCEPTED / TERRAIN DTM FULL BOOTSTRAP`

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

### Step 4 — Street View

已透過 Terrain headless browser formal Operator 取得四向 Google Maps Street View：

- heading `0 / 90 / 180 / 270`
- 實體 PNG
- manifest + SHA256
- OpenWorker accepted

證據：`evidence/0004-street-view-acquisition.md`

## 目前 Step 5 — terrain / elevation AOI

已新增正式能力：

- Terrain Operator：`terrain.aoi.build`
- `Terrain_To_DXF` commit：`da41d2c24563fbcb50599f99b1dad9c661e16d2a`
- go-tool capability registry commit：`d99e8d22...`
- AI-Engineering-OS resume-aware driver commit：`0ed3a893...`

第一個 REAL terrain AOI：

- outer OS run：`31923998028`
- Terrain target run：`31924030088`
- UL7 job：`95108616144`
- runner：`DESKTOP-UL7V2VV-R006`

fail-closed blocker：

```text
D:\TaiwanDTM\catalog\dtm_catalog.sqlite missing
```

## 使用者決策：本機沒有 DEM 就完整重新下載

因此不做玉井橋單點 workaround，而是完整建立 UL7 共用 Taiwan 20m DTM 基礎資料：

```text
D:\TaiwanDTM
  catalog\
  raw\
  extracted\
  normalized\
  cog\
```

官方 dataset `176927` 第一層只有約 5.42 KB CSV index，不是 DEM 本體。

REAL index probe：

- run `31924300126`
- UL7 job `95109313914`
- runner `DESKTOP-UL7V2VV-R006`

索引確認包含正式 TGOS ZIP：各縣市分幅 + schema + 不分幅全台 20m DEM。

Owning gap 已補：

- recursive official index downloader：`tools/download_taiwan_dtm_recursive.py`
- commit：`a6adfb387bf9ac8a5ce81fc5725d55e1dda63c2c`
- full bootstrap workflow：`.github/workflows/operator-dtm-bootstrap-full.yml`
- latest commit：`48e104fcc75fc0c64ce91a843cc39e781468e144`

目前 REAL full download：

- run：`31924347661`
- business job：`95109431249`
- runner：`DESKTOP-UL7V2VV-R006`
- current step：`Recursively expand official index and fully download all resources`

完整過程：`evidence/0005-terrain-aoi-and-dtm-bootstrap.md`

## 下一步

1. 完成官方 TGOS ZIP 全量下載與 safe extract。
2. 檢查實際解壓格式與 CRS。
3. 將全量資料 normalize / materialize 成 canonical raster/COG。
4. 建立 `D:\TaiwanDTM\catalog\dtm_catalog.sqlite` + RTree。
5. 驗證玉井橋 AOI 可 query 到 `ready=true` tile。
6. 由 AI-Engineering-OS / go-tool **重跑同一個 `terrain.aoi.build`**。
7. 接既有 Terrain consumer orchestration → REAL Blender 5.2 → Blender QC。
8. SceneX import → REAL renderer/screenshot browse。
9. OS Artifact Registry → Delivery Revision → `delivery/website/index.html`。

任何新缺口仍依同一規則：找 owning repo → generic 修復 → local Action 驗證 → 同 Step REAL 重跑 → OpenWorker append-only evidence。
