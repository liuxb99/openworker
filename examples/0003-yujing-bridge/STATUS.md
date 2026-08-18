# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-18 Asia/Taipei

狀態：`IMPLEMENTING / GEO ACCEPTED / IMAGERY+AOI REAL QC REQUIRED / CONSUMER+BLENDER+SCENEX LOCALIZED / OS ARTIFACT+DELIVERY LOCALIZED / REAL REVIEW GATE REQUIRED`

## 1. Canonical execution contract — 新版

- 固定主機：`DESKTOP-UL7V2VV`
- canonical workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- case mirror：`D:\AI-Example\0003`
- canonical input：`location_text = 臺南市玉井橋`
- OpenWorker = 本機總控、durable job / agent slot / cluster / host / workspace authority。
- go-tool-runtime = capability discovery + `localexec` registry。
- owning repo = 真正工程、影像、3D、OS delivery 邏輯的唯一權威來源。
- GitHub Actions = CI / fallback / bootstrap / evidence transport；**不是 canonical business execution plane**。
- REAL 成果只能由 physical / semantic / geometry / SHA256 gate 接受，不能由 Action success 或 job submitted 接受。

Canonical path：

```text
ChatGPT / local supervisor
→ OpenWorker 本機總控
→ durable jobs / agent slots / fixed UL7 / canonical workspace
→ go-tool localexec
→ owning repo local CLI / PowerShell / runtime
→ physical artifacts + evidence
→ QC
→ AI-Engineering-OS Artifact Registry / Review / Delivery
```

### 舊 GitHub-first 與新版 local-first 的差異

舊版常把日常 business work 綁在：

```text
workflow_dispatch → GitHub queue → runner labels / conditions → checkout → tool → Action artifact
```

新版把 execution authority 移回 OpenWorker，因此：

1. Street View / Orthophoto 等獨立工作直接分 agent slot 並行。
2. UL7 由 OpenWorker persisted state 固定，localexec 再驗證 `COMPUTERNAME`。
3. queue 阻塞時使用 OpenWorker one-call queue drain，不逐筆清 GitHub workflow。
4. 成果直接落 canonical workspace，不先繞 Action artifact。
5. 工具錯誤與 transport 錯誤分離，缺口直接修 owning repo。
6. GitHub 回到 code / CI / fallback / bootstrap / evidence transport 的角色。

## 2. 已接受

### Step 1/2 — OpenWorker / go-tool control plane

固定 UL7 / workspace continuity、capability discovery、durable work state 已建立。舊 GitHub run IDs 僅為歷史 provenance。

### Step 3 — geolocation

Accepted：

`D:\AI-Work\jobs\0003-YUJING-BRIDGE\geo\geolocation.json`

所有 Terrain / imagery / SceneX handler 必須讀 accepted state，不得自行硬寫座標。

## 3. Step 4 — Imagery

### Street View

舊四向黑圖 acceptance 已撤銷。Terrain producer 已補 semantic visibility fail-closed：

- `027915e7e4ddf8384ab680cdb4a1f5105834fad6`
- tests：`d1c58f96e5a0a6ca3448c45af79732bf1e9af96a`

REAL gate：0 / 90 / 180 / 270 四張 PNG 必須 decode、可視、非黑圖、manifest/SHA 一致。

### Orthophoto

已補 NLSC `PHOTO2` bounded WMTS、JPEG/mosaic、visibility、SHA provenance。

- local capability：`terrain.orthophoto.acquire`
- Windows same-path rerun-safe：`e4c427f7a7f805d437ee8254e0ea2677ce2d5846`
- rerun regression test：`d502506b78faaf33662dba4f4d51987882e4a247`

### 本機並行

OpenWorker：`scripts/case0003_local_imagery_parallel.ps1`

commit：`28613a83407f8dab92e4ea9f7dc1485182250d04`

Street View + Orthophoto 使用不同 locks，可由不同 agent slots 並行；`github_business_transport=false`。

## 4. Step 5 — Terrain AOI

Terrain owning local entrypoint：`scripts/terrain_aoi_local.ps1`

commit：`94c84762c9b19adb840062bc03e6541d0f2ab596`

go-tool：`terrain.aoi.build`

handler：`f720acdba979e6cd8f72dfbf9fe179ad49760140`

OpenWorker submit：`scripts/case0003_local_terrain_aoi.ps1`

commit：`c5a479336e69ef53082f60050fb03e7f273dbf4e`

REAL gate 必須有 10 個 non-empty artifacts：terrain context/build/grid/DXF/heightmap raw+json/OBJ/mesh/scene/SceneX handoff；並要求 `terrain-context/v1`、`usable_tiles > 0`、physical SHA evidence。

## 5. Step 6 — Consumer orchestration

Terrain owning entrypoint：`scripts/terrain_consumer_local.ps1`

commit：`fb78a23fe31468dfd11900cc0278188e288d4ae1`

go-tool capability：`terrain.consumer.orchestrate`

OpenWorker submit：`scripts/case0003_local_consumer.ps1`

commit：`1f7b8eb4620e85bc33e5713ca35cf53bf16a33c4`

REAL gate：七個 consumer artifacts、`consumer-orchestration/v1`、實體 terrain mesh。

## 6. Step 7A — Blender REAL

Terrain owning entrypoint：`scripts/terrain_blender_local.ps1`

commit：`490023ef10200d23f872439325a11712f02c47bb`

go-tool capability：`terrain.blender.execute`

OpenWorker submit：`scripts/case0003_local_blender.ps1`

commit：`d81eeb1976f82c08789ced04b8956cc09a994815`

REAL gate：`.blend`、1280×720 render、request/evidence/handoff，scene/render SHA256 必須一致。

## 7. Step 7B — SceneX REAL

舊 `operator-terrain-real-browse.yml` 的真實 Godot business logic 已抽回 SceneX owning repo，不重寫 runtime。

- Godot resolver local reusable：`648797a1f2a7c87d8aef452981bf8a0ca86c69f5`
- local entrypoint `scripts/scenex_terrain_real_browse_local.ps1`：`c86fa714398200173b5734bd22c9e90720f6599f`
- go-tool `scenex.terrain.real_browse` handler：`7481f00fccf72ec599e2ad2550b035e5f75f3671`
- gtr registration：`e758f8e9ff6e9f5e8fb209f8d3be641ce71a2c71`
- handler tests：`4ff58fe1e4c549a63c9908c673d37634ee18e129`
- OpenWorker `scripts/case0003_local_scenex.ps1`：`fe2c3357e6d39fd6f6adb9cab903e084e5fdf05a`

REAL path：

```text
Terrain grid/context + accepted geo
→ SceneX Region Pack
→ Godot 4.6.3 / forward_plus / D3D12
→ REAL 1280x720 browse
→ screenshot + geometry diagnostics + SHA manifest
```

Gate：非 fallback Region Pack、active chunks > 0、terrain geometry > 0、viewport 1280×720、screenshot/pack/evidence SHA 一致。

SceneX 只依賴 accepted Terrain + geo，因此可與 Consumer→Blender 鏈並行。

## 8. Step 8 — AI-Engineering-OS Artifact Registry：已 localize

OS 權威規格本來就要求：Artifact Registry / Review / Approval / Delivery Revision / SQLite / delivery website 由 AI-Engineering-OS 擁有。Case 不另造 registry。

發現的關鍵既有能力：`job.ArtifactStager` 會把外部本機成果安全搬入 OS Job WorkingDir，重新驗 SHA256，再允許 Artifact Registry 登錄。因此 **不放寬 JobPathValidator**。

### OS owning ingest CLI

`AI-Engineering-OS/cmd/engineering-os-artifact-ingest`

- commit：`af8144d2508fa1a694adf0b49cdd6056e88a9f6d`
- validation tests：`8abebcbe64118b355dc8e8a95954b85c947a4285`
- manifest schema：`artifact-ingest/v1`
- 使用正式 config + SQLite + JobStore + ArtifactStager + ArtifactService。
- `project_id` / `job_id` 必須是真正 OS persisted identities。
- 每個來源先 stage + SHA verify，再註冊 Artifact revision，最後 SyncManifest。

### go-tool

Capability：`engineering_os.artifacts.ingest`

- handler：`e70c596161cec5945802a94ac488b3c1788a262d`
- identity decode fix：`0491c5c41ebb590832dd6c38f6a7141f69afeba2`
- gtr registration：`1931b7a046860d099292ed658a5efb81d1430c6f`
- routing tests：`9f7a65e7d29399caed26ce3435a2a6d0f6d6f77c`

### OpenWorker Case 0003

`scripts/case0003_local_os_artifacts.ps1`

commit：`d64387ebee9e1e2184c8e90ebbb97b74949bd1f9`

只有 Blender + SceneX physical evidence 存在並通過基本 schema/geometry gate 時才建立 ingest manifest。首批正式登錄 11 項 Terrain / Blender / SceneX artifacts，全部由目前實體檔重新計算 SHA256。

OS identity 來源：

- `ENGINEERING_OS_PROJECT_ID`
- `ENGINEERING_OS_JOB_ID`

**不得用 OpenWorker work code 冒充 OS Job ID。** 缺 identity 時 fail-closed。

controller 的 OS Registry gate 還會把 registry receipt 中每個 checksum 與目前 canonical workspace 原始實體檔重新比對；成果變更後舊 receipt 自動失效。

## 9. Step 9 — Review / Approval / Delivery Revision：publish 已 localize，approval 不自動化

OS 原生 review gate 的規則：只允許 current `(component_id, kind)` Artifact revision 有最新 `approved` review 時發布；historical revisions 保留追溯但不阻塞。

**Case 0003 不會自動替未經 REAL QC 的成果寫 approved。**

### OS owning local publish entrypoint

`AI-Engineering-OS/scripts/engineering_os_publish_local.ps1`

commit：`142d8aceea0a3a36b1504fa094605f211af87758`

流程：

```text
OS healthz
→ resolve persisted Job
→ GET approval-status
→ 必須 approved=true
→ POST /api/v1/jobs/{id}/publish
→ OS Delivery Service
→ delivery manifest + checksum manifest + website
→ physical file/schema/revision verification
```

它仍使用 OS 自己的 Publish Service，所以仍會再執行 ApprovalGate、Artifact SHA、stage/copy、Delivery Manifest、website 等原生驗證。

go-tool：`engineering_os.delivery.publish`

- handler：`d0fcf1c4232a2c7e77bafe46ed7d0f5cfd500749`
- gtr registration：`f3ffe5b8492171ee2c9bb1a0ed7d5f741138b794`

OpenWorker：`scripts/case0003_local_os_delivery.ps1`

commit：`cc381bfbd5fe51983f987afb6546315a9d8ab6e3`

OpenWorker 在 durable submit 前也先讀 approval-status；未核准不提交 publish job。

## 10. Case 0003 一鍵 local-first continuation controller

入口：`scripts/case0003_local_continue.ps1`

目前 schema：`openworker/case0003-local-continue/v4`

最新 commit：`f9fd30b9bcd7d317d9912c81e25987e6e846ea62`

目前依 physical gates 自動續跑：

```text
Imagery incomplete
→ Street View + Orthophoto parallel

Terrain incomplete + DTM catalog ready
→ AOI

Terrain accepted physically
├→ SceneX
└→ imagery accepted → Consumer → Blender

Blender + SceneX physically pass
→ Engineering OS Artifact ingest

OS artifacts current + all current revisions approved
→ Engineering OS Delivery publish

Delivery published + manifest/site physical gate
→ GOOGLE_DRIVE_CHATGPT_FINAL_QC_REQUIRED
```

controller 不把「submitted」當完成；每次重跑重新讀 workspace 與 OS authoritative state。

## 11. 目前 acceptance boundary

**目前只有 GEO 可稱 ACCEPTED。**

尚不得稱 ACCEPTED：Street View、Orthophoto、AOI、Consumer、Blender、SceneX、OS Artifact Registry、Review/Approval、Delivery。

原因：這個 ChatGPT 執行環境目前不能直接連入 UL7 的 `127.0.0.1:8787`，所以這一輪完成的是 code path / fail-closed gates / local-first orchestration，不是假裝完成 UL7 REAL run。

## 12. UL7 下一個 REAL 執行順序

1. 確認 OpenWorker node / agents online；阻塞時使用 one-call queue drain。
2. 確認 `GO_TOOL_ROOT`、`TERRAIN_ROOT`、`SCENEX_ROOT`、`ENGINEERING_OS_ROOT`。
3. 從 OS persisted state 提供真正 `ENGINEERING_OS_PROJECT_ID` / `ENGINEERING_OS_JOB_ID`。
4. 執行 `scripts/case0003_local_continue.ps1`。
5. 驗 Street View 四向可視 PNG / SHA。
6. 驗 PHOTO2 mosaic / SHA。
7. 驗 Terrain 10 artifacts / usable tiles / SHA。
8. Terrain gate 後並行推 SceneX 與 Consumer→Blender。
9. 驗 Blender REAL render、SceneX REAL screenshot / geometry / SHA。
10. 進 OS Artifact Registry；由 ChatGPT / reviewer 對實體成果做品質審查。
11. current Artifact revisions 全部 approved 後，controller 才允許 Delivery publish。
12. 驗 delivery-manifest、checksum-manifest、成果網站。
13. 將正式 Delivery Revision 送 Google Drive，做 ChatGPT final QC；不合格則 rework，不直接 ACCEPTED。

任何新缺口：案例暴露缺口 → 修 owning repo / go-tool local handler → OpenWorker local REAL rerun → physical artifact QC → OS review/delivery → append-only evidence。
