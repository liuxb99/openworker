# 0004 — Street View Browser Screenshot acquisition

## 1. 本 Step 目的

Case 0003 的 Street View 正式路徑採用 `Terrain_To_DXF` 最新 Browser URL / Headless Render 設計，不再把 Google Static Street View API snapshot 當成本案例的街景視覺取得方式。

Canonical user input 仍只有：

- `location_text = 臺南市玉井橋`
- `delivery_case = 0003`

System binding：

- assigned host：`DESKTOP-UL7V2VV`
- canonical workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- case mirror：`D:\AI-Example\0003`

座標必須由前一步正式 `terrain.geo.resolve` 產生；案例、LLM 與 Street View workflow 都不得硬寫玉井橋 lat/lng。

## 2. Latest-design audit

`Terrain_To_DXF/docs/16-streetview-browser-url-mode.zh-TW.md` 已定義 GEO-STREETVIEW-07：

```text
Browser URL Mode
  → official Google Maps pano URL
Headless Render Mode
  → controlled Chrome/Edge
  → bounded viewport / timeout
  → browser viewport screenshot
  → bytes / SHA256 / render evidence
```

正式 URL contract：

```text
https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=<lat>,<lng>
```

Headless Render 的安全邊界：

- 只允許 `www.google.com/maps/@` pano URL；
- Chrome/Edge 由工具自行 discovery，不接受模型指定 arbitrary executable；
- 不解析 undocumented XHR / tile URL；
- 不下載、拼接或攔截 panorama tiles；
- screenshot 只是 browser viewport render，不能冒充 Static Street View API 原始影像或工程幾何真值。

最新版程式已存在：

- `internal/streetview/browser_url.go`
- `internal/streetview/headless.go`

其中 headless renderer 已實作 browser discovery、allowlist、viewport/timeout bounds、PNG artifact、bytes、SHA256、render timestamp。

## 3. 本案例暴露的缺口

先前新增的 `terrain.streetview.acquire` Operator 錯接到較舊 Static API acquisition CLI：

```text
location_text
→ Google geocode
→ Street View metadata
→ Static API 四向 snapshots
```

而且 workflow 要求 repository secret `GOOGLE_MAPS_API_KEY`。

這與 Case 0003 要使用的最新 Headless Render 設計不一致。此問題不是核心 Street View renderer 缺失，而是「新版核心能力已存在，但 AI-facing Operator 沒接到最新版 contract」。

因此舊的 Static snapshot Operator path 在 Case 0003 中標記為 **SUPERSEDED**，不得作為 accepted Street View visual acquisition procedure。

## 4. Owning-repo repair

### 4.1 Headless Render CLI

新增：

- `cmd/terrain-streetview-render/main.go`
- commit `7559c40faa4687e09ea39c93114b02f1dafbb3ec`

CLI 依原 GEO-STREETVIEW-07D 設計：

```text
lat/lng + heading/pitch/fov
→ BuildBrowserURL
→ DiscoverChromium
→ RenderBrowserScreenshot
→ PNG + JSON evidence
```

限制：

- viewport：640×480 ~ 1920×1080；
- timeout：1 ~ 60 秒；
- output 必須為 PNG；
- URL 必須通過 Google Maps pano allowlist。

### 4.2 Self-hosted compile/test gate

Terrain Win11 local Action：

- run `31922461910`
- head `7559c40faa4687e09ea39c93114b02f1dafbb3ec`
- conclusion：`SUCCESS`

因此新 `terrain-streetview-render` 已通過既有 Go test / vet / build self-hosted gate；這個 gate 只驗證程式與 build，不能代替玉井橋 REAL screenshot run。

### 4.3 Street View Operator 改接 Headless Render

Operator：

- `.github/workflows/operator-streetview-acquire.yml`
- initial screenshot switch commit `3e35b6e068f1d65feb81cda6d120f0c8864df64c`
- workspace-backed correction commit `2752db1d596375dd06e067dcb58597926348385f`

Accepted execution：

```text
OpenWorker bound workspace
→ geo/geolocation.json
→ read accepted lat/lng
→ Chrome/Edge headless
→ heading 0° screenshot 1920×1080
→ heading 90° screenshot 1920×1080
→ heading 180° screenshot 1920×1080
→ heading 270° screenshot 1920×1080
→ per-image SHA256
→ streetview-browser-screenshots.json
→ workspace/streetview/browser/*
```

Street View screenshot Step 本身不再依賴 `GOOGLE_MAPS_API_KEY`。

### 4.4 Geolocation / workspace handoff correction

`terrain.geo.resolve` 仍負責把使用者文字解析成正式 geolocation。新 Operator 原本把 repo secret 空值寫進 `GOOGLE_MAPS_API_KEY`，會覆蓋 self-hosted runner 既有 machine-local environment credential。

修正：

- commit `e56e6beeb1e2a717ed030c87a9202ae7d3b79a6a`
- repository secret 若存在則優先；否則保留 machine-local `GOOGLE_MAPS_API_KEY`；兩者皆無才 fail-closed。

之後又補正式 workspace materialization：

- commit `1b6d4183fc2937439bc70f161a0f0ee7a872ea7c`

成功 geolocation 必須 materialize：

```text
D:\AI-Work\jobs\0003-YUJING-BRIDGE\geo\geolocation.json
```

Street View Operator 只讀這個 accepted state，不由案例重新解析或硬寫座標。

## 5. go-tool contract repair

`go-tool-runtime/config.yaml` 已把 `terrain.streetview.acquire` 改成正式 Headless Browser Screenshot contract：

- commit `5bdf57fcfe27ca06863d0996d03a1a2079e6bdc2`
- 移除舊 `radius_m` / Static API 描述；
- required system inputs：`workspace_root`、`assigned_host`；
- artifact pattern：`terrain-streetview-browser-operator-*`。

`terrain.geo.resolve` 同步增加 `workspace_root`，讓 accepted geolocation 進 OpenWorker-bound workspace。

Case 0003 go-tool E2E harness 亦更新：

- commit `9e70e661b69ddd6678bec7b318100f88c1def701`
- formal workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- geo success 後驗證 workspace `geo/geolocation.json`；
- Street View dispatch 不傳 lat/lng，只傳 workspace + assigned host；
- screenshot success 後驗證 workspace manifest 包含 0/90/180/270 四個 heading。

## 6. REAL execution state

最新版 go-tool formal Case0003 run：

- run `31922591331`
- head `9e70e661b69ddd6678bec7b318100f88c1def701`
- workflow：`Operator E2E 0003 Yujing Bridge`
- 當前狀態：queued，等待 generic self-hosted transport candidate 被 runner 接單；只有 `DESKTOP-UL7V2VV` 可以通過 consequential execution host gate。

因此目前不能把 REAL 玉井橋 Street View 標成 PASS。

## 7. Accepted procedure

本案例後續 Street View 不得再：

- 把 Static Street View API snapshot 當本案例正式視覺取得路徑；
- 在案例碼寫死玉井橋 lat/lng；
- 讓 Street View Operator 自己重做 geocode；
- 從任意 URL / arbitrary browser executable 截圖；
- 把 screenshot 宣稱成 survey / terrain geometry 真值。

正式程序固定為：

```text
OpenWorker persisted JobBinding
→ go-tool terrain.geo.resolve
→ UL7 local Action
→ workspace/geo/geolocation.json
→ go-tool terrain.streetview.acquire
→ UL7 local Action
→ official Google Maps pano Browser URL
→ bounded Chrome/Edge headless screenshot
→ four 1920×1080 PNGs + SHA256 + manifest/evidence
→ workspace/streetview/browser
→ AI Vision / Blender visual reference only
```

Terrain / DEM / DTM 仍是 geometry/elevation 真值。

## 8. Next acceptance gate

追 run `31922591331`：

1. UL7 selected candidate；
2. go-tool discovery/schema/readiness；
3. `terrain.geo.resolve` target run；
4. `geo/geolocation.json` materialized；
5. `terrain.streetview.acquire` target run；
6. Chrome/Edge headless REAL render；
7. 四張非空 PNG；
8. 每張 SHA256 與 manifest 一致；
9. 寫回本手冊 run/job/runner/artifact evidence；
10. 通過後才進 Terrain AOI / Blender scene。
