# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-18 Asia/Taipei

狀態：`IMPLEMENTING / GEO ACCEPTED / STREETVIEW+ORTHOPHOTO REAL QC REQUIRED / AOI REAL REQUIRED / CONSUMER+BLENDER+SCENEX LOCALIZED / OS ARTIFACT REGISTRY NEXT`

## Canonical execution contract — 2026-08-18 新版

- 固定主機：`DESKTOP-UL7V2VV`
- canonical workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- case mirror：`D:\AI-Example\0003`
- canonical input：`location_text = 臺南市玉井橋`
- **OpenWorker 是本機總控、durable job / agent / cluster / workspace / host authority。**
- **go-tool-runtime 是 capability discovery + localexec registry。**
- REAL / consequential 工作 canonical path：`OpenWorker local jobs -> go-tool localexec -> owning repo local CLI/runtime -> workspace physical artifact -> QC`。
- GitHub Actions 僅保留 fallback / CI / bootstrap / evidence transport，不再是主要 business execution boundary。
- assigned host 與 workspace 必須來自 OpenWorker persisted state；localexec 再次驗證實際 `COMPUTERNAME`。
- Action success 不等於 business acceptance；實體檔案、schema、semantic/geometry diagnostics、SHA256 才是 gate。

## 舊版 GitHub-first vs 新版 OpenWorker local-first

舊版常見：

```text
ChatGPT
→ workflow_dispatch
→ GitHub Actions queue
→ runner labels / conditions / checkout
→ owning tool
→ Action artifact/log
→ 再判斷實際成果
```

新版：

```text
ChatGPT / local supervisor
→ OpenWorker 本機總控
→ durable jobs / agent slots / fixed host / canonical workspace
→ go-tool localexec
→ owning tool local entrypoint
→ physical artifact + evidence
→ semantic / physical QC
```

差異的核心不是把 YAML 換成 PowerShell，而是把 **business execution authority 從 GitHub Actions 移回 OpenWorker 本機總控**。因此：

1. Street View / Orthophoto 等獨立工作可直接分 agent slot 並行，不等 GitHub runner 排程。
2. UL7 由 OpenWorker persisted host authority 固定，localexec 再 fail-closed 驗證主機。
3. queue 阻塞時使用 OpenWorker 新版 one-call queue drain，不逐筆處理 GitHub workflow queue。
4. 成果直接落 canonical workspace，下游不必先上傳/下載 Action artifact。
5. 工具失敗與 transport 失敗分離，案例暴露的缺口直接回 owning repo 修。
6. GitHub 回到 code / CI / fallback / bootstrap / evidence transport 的角色。

## 已接受

### Step 1/2 — OpenWorker / go-tool control plane

固定 UL7 host/workspace continuity、capability discovery、durable work state 已建立。早期 GitHub run/job ID 僅保留歷史 provenance。

### Step 3 — geolocation

accepted state：

`D:\AI-Work\jobs\0003-YUJING-BRIDGE\geo\geolocation.json`

後續 Terrain / SceneX handler 必須讀這份 accepted state，不得自行硬寫座標。

## Step 4A — Street View：REAL rerun required

舊四向 PNG 因 producer 只驗證存在/非空/hash，黑畫面可能誤判，因此舊 acceptance 已撤銷。

Terrain repair：

- semantic visibility fail-closed：`027915e7e4ddf8384ab680cdb4a1f5105834fad6`
- tests：`d1c58f96e5a0a6ca3448c45af79732bf1e9af96a`

canonical local path：

```text
OpenWorker durable job
→ go-tool localexec terrain.streetview.acquire
→ Terrain_To_DXF terrain-streetview-render
→ 0 / 90 / 180 / 270 PNG
→ semantic visibility + SHA256
→ workspace/streetview/browser
```

接受條件：四張 PNG 都 decode、visibility PASS、非黑圖，manifest/SHA 一致。

## Step 4B — Orthophoto：REAL run required

已補 NLSC `PHOTO2` bounded WMTS acquisition、JPEG decode、mosaic、visibility QC、tile/mosaic SHA256 provenance。

- local capability：`terrain.orthophoto.acquire`
- canonical output：`workspace\orthophoto\nlsc-photo2\`
- bounded acquisition：預設 z19 / radius 1
- Windows same-path rerun-safe 修正：`e4c427f7a7f805d437ee8254e0ea2677ce2d5846`
- rerun regression test：`d502506b78faaf33662dba4f4d51987882e4a247`

Street View + Orthophoto 並行提交入口：

`scripts/case0003_local_imagery_parallel.ps1`

commit：`28613a83407f8dab92e4ea9f7dc1485182250d04`

## Step 5 — Terrain AOI：已 localize，REAL UL7 run required

Owning local entrypoint：

`Terrain_To_DXF/scripts/terrain_aoi_local.ps1`

commit：`94c84762c9b19adb840062bc03e6541d0f2ab596`

go-tool：`terrain.aoi.build`

主要 handler commit：`f720acdba979e6cd8f72dfbf9fe179ad49760140`

OpenWorker durable submit：

`scripts/case0003_local_terrain_aoi.ps1`

commit：`c5a479336e69ef53082f60050fb03e7f273dbf4e`

REAL gate 必須有且非空：

- `terrain-context.json`
- `terrain-build.json`
- `terrain-grid.json`
- `terrain.dxf`
- `terrain-heightmap.raw`
- `terrain-heightmap.json`
- `terrain.obj`
- `terrain-mesh.json`
- `terrain-scene.json`
- `scenex-terrain-scene.json`

並要求 `terrain-context/v1`、`usable_tiles > 0`、物理 SHA evidence。

## Step 6 — Consumer orchestration：已 localize

Terrain owning entrypoint：

`Terrain_To_DXF/scripts/terrain_consumer_local.ps1`

commit：`fb78a23fe31468dfd11900cc0278188e288d4ae1`

go-tool capability：`terrain.consumer.orchestrate`

handler：`internal/localexec/terrain_downstream_local.go`

OpenWorker durable submit：

`scripts/case0003_local_consumer.ps1`

commit：`1f7b8eb4620e85bc33e5713ca35cf53bf16a33c4`

REAL gate：七個 consumer artifacts + `consumer-orchestration/v1` + physical terrain mesh。

## Step 7A — Blender REAL：已 localize

Terrain owning entrypoint：

`Terrain_To_DXF/scripts/terrain_blender_local.ps1`

commit：`490023ef10200d23f872439325a11712f02c47bb`

go-tool capability：`terrain.blender.execute`

OpenWorker durable submit：

`scripts/case0003_local_blender.ps1`

commit：`d81eeb1976f82c08789ced04b8956cc09a994815`

REAL gate：

- `terrain-scene.blend`
- `terrain-render.png`
- `blender-execution-request.json`
- `blender-scene-evidence.json`
- `blender-render-handoff.json`
- schema + scene/render SHA256 必須一致。

## Step 7B — SceneX REAL terrain browse：已 localize

舊 SceneX `operator-terrain-real-browse.yml` 已有完整 REAL Region Pack → Godot → screenshot → geometry diagnostics 邏輯；2026-08-18 已抽成 owning local entrypoint，不重新發明 runtime。

SceneX local entrypoint：

`SceneX/scripts/scenex_terrain_real_browse_local.ps1`

commit：`c86fa714398200173b5734bd22c9e90720f6599f`

Godot resolver 已從 Actions-only 改為本機可直接復用：

`648797a1f2a7c87d8aef452981bf8a0ca86c69f5`

go-tool local capability：

`scenex.terrain.real_browse`

handler commit：`7481f00fccf72ec599e2ad2550b035e5f75f3671`

`gtr-local-exec` registration：`e758f8e9ff6e9f5e8fb209f8d3be641ce71a2c71`

handler tests：`4ff58fe1e4c549a63c9908c673d37634ee18e129`

OpenWorker durable submit：

`scripts/case0003_local_scenex.ps1`

commit：`fe2c3357e6d39fd6f6adb9cab903e084e5fdf05a`

canonical path：

```text
OpenWorker durable job
→ go-tool localexec scenex.terrain.real_browse
→ SceneX owning local script
→ Terrain grid/context + accepted geo
→ SceneX Region Pack
→ Godot 4.6.3 / forward_plus / D3D12 / 1280x720
→ REAL terrain browse
→ terrain-browse.png + evidence + SHA manifest
```

SceneX REAL gate：

- `scenex-workspace-browse/v1`, `ok=true`
- `terrain-browse.png` 非空且 SHA 一致
- Region Pack 非 fallback-generated，SHA 一致
- `active_chunks > 0`
- `terrain_geometry_count > 0`
- viewport = 1280×720
- evidence SHA 一致。

SceneX 只依賴 accepted Terrain + geo，不依賴 Blender；因此 Terrain REAL gate 通過後可與 consumer/Blender 鏈並行。

## Case 0003 一鍵本機續跑 controller

OpenWorker：

`scripts/case0003_local_continue.ps1`

目前 schema：`openworker/case0003-local-continue/v2`

最新 commit：`ea7f9044493a72c350b98e4a4ce7e7df7d224776`

此 controller 不以「job submitted」當完成，而是讀 canonical workspace physical gates 後決定下一步：

```text
imagery 不完整
→ Street View + Orthophoto 並行提交

Terrain 不完整 + DTM catalog 存在
→ AOI durable job

Terrain REAL gate 通過
├→ SceneX durable job（可獨立並行）
└→ imagery 也通過後 → Consumer
                         ↓
                       Blender

Blender + SceneX physical gates 都通過
→ OS_ARTIFACT_REGISTRY_REQUIRED
```

controller 也會重新計算 SceneX screenshot / Region Pack / evidence SHA，而不是只相信 JSON 內宣告值。

輸出：

`workspace\evidence\case0003-local-continue.json`

`github_business_transport=false`

## 目前 acceptance boundary

**尚不得標記 STREETVIEW / ORTHOPHOTO / AOI / CONSUMER / BLENDER / SCENEX 為 ACCEPTED。**

目前完成的是 local-first execution path 與 fail-closed gate；這個 ChatGPT 執行環境無法直接連入 UL7 的 `127.0.0.1:8787`，因此不得用 GitHub Actions 假裝已完成 UL7 REAL run。

## 目前正確下一步

1. UL7 上確認 OpenWorker node / agents online；若 queue 阻塞，使用新版 one-call queue drain。
2. 確認 `GO_TOOL_ROOT`、`TERRAIN_ROOT`、`SCENEX_ROOT` 為本機 authority。
3. 執行 `scripts/case0003_local_continue.ps1`，由 physical gate 自動提交下一批 durable jobs。
4. 驗證 Street View 四向 PNG visibility / SHA。
5. 驗證 NLSC PHOTO2 mosaic visibility / SHA。
6. 驗證 AOI 十項 terrain physical artifacts、`usable_tiles > 0`、SHA。
7. Terrain 通過後，SceneX 與 consumer/Blender 可按依賴關係並行推進。
8. SceneX 驗證 REAL screenshot、active chunks、terrain geometry、SHA；Blender 驗證 REAL render/scene、SHA。
9. Blender + SceneX 都 PASS 後，進 **OS Artifact Registry**。
10. 再做 Delivery Revision / Google Drive review / 最終 acceptance / website（如本案例 delivery scope 要求）。

任何新缺口：案例暴露缺口 → 修 owning repo / go-tool local handler → OpenWorker local REAL rerun → physical artifact QC → append-only evidence。
