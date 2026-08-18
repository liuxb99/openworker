# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-18 Asia/Taipei

狀態：`IMPLEMENTING / GEO ACCEPTED / IMAGERY STRICT REAL QC REQUIRED / AOI+CONSUMER+BLENDER+SCENEX LOCALIZED / OS ARTIFACT+DELIVERY LOCALIZED / DRIVE REVIEW RETURN LOOP LOCALIZED / UL7 REAL REQUIRED`

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
→ immutable Drive review ZIP
→ ChatGPT connector review
→ WorkLedger accept / deliver
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

## 3. Step 4 — Imagery：producer 已修，strict REAL acceptance 待 UL7

### Street View

舊四向黑圖 acceptance 已撤銷。Terrain producer 已補 semantic visibility fail-closed：

- `027915e7e4ddf8384ab680cdb4a1f5105834fad6`
- tests：`d1c58f96e5a0a6ca3448c45af79732bf1e9af96a`

Producer 現在會 decode PNG、做 panorama visibility analysis，黑/近黑/近均勻圖直接失敗；成功 receipt 帶 physical SHA256。

Strict REAL gate 必須同時滿足：

- 0 / 90 / 180 / 270 四張、不得重複 heading；
- `streetview-browser-screenshots/v2`、`transport=localexec`、assigned host = UL7；
- producer = Google / `headless-render-webgl` / `angle-swiftshader-webgl`；
- 1920×1080、bytes > 0；
- 每張 PNG physical SHA256 = producer receipt SHA256；
- receipt output path = manifest physical path。

### Orthophoto

已補 NLSC `PHOTO2` bounded WMTS、JPEG/mosaic、visibility、SHA provenance。

- local capability：`terrain.orthophoto.acquire`
- Windows same-path rerun-safe：`e4c427f7a7f805d437ee8254e0ea2677ce2d5846`
- rerun regression test：`d502506b78faaf33662dba4f4d51987882e4a247`
- go-tool workspace QC manifest：`5fd7f65bcf416646040c52ac824b10d3860fe3bd`

Canonical workspace acceptance manifest：

`orthophoto\nlsc-photo2\orthophoto-photo2-workspace.json`

Strict REAL gate：

- schema `orthophoto-workspace/v1`、`transport=localexec`、assigned host = UL7；
- producer schema `orthophoto-nlsc-photo2/v1`；
- provider = `nlsc`、layer = `PHOTO2`、zoom = 19、tile count 1..25；
- `visibility.visible=true`；
- useful pixel ratio >= 0.20；
- luma stddev >= 0.02；
- luma range >= 0.10；
- physical JPEG SHA256 = producer `output_sha256`；
- dimensions / bytes > 0。

舊只有 `orthophoto-photo2-evidence.json` 的成果不再足以 PASS；缺 workspace QC manifest 會自動重新取得正射影像。

### 本機並行

OpenWorker：`scripts/case0003_local_imagery_parallel.ps1`

目前 schema：`openworker/case0003-local-imagery-parallel/v3`

Street View + Orthophoto 使用不同 locks，可由不同 agent slots 並行；單邊已 strict PASS 時只重跑缺失的另一邊；`github_business_transport=false`。

## 4. Step 5 — Terrain AOI

Terrain owning local entrypoint：`scripts/terrain_aoi_local.ps1`

go-tool：`terrain.aoi.build`

OpenWorker submit：`scripts/case0003_local_terrain_aoi.ps1`

REAL gate 必須有 10 個 non-empty artifacts：terrain context/build/grid/DXF/heightmap raw+json/OBJ/mesh/scene/SceneX handoff；並要求 `terrain-context/v1`、`usable_tiles > 0`、physical SHA evidence。

## 5. Step 6 — Consumer orchestration

Terrain owning entrypoint：`scripts/terrain_consumer_local.ps1`

go-tool capability：`terrain.consumer.orchestrate`

OpenWorker submit：`scripts/case0003_local_consumer.ps1`

REAL gate：七個 consumer artifacts、`consumer-orchestration/v1`、實體 terrain mesh。

## 6. Step 7A — Blender REAL

Terrain owning entrypoint：`scripts/terrain_blender_local.ps1`

go-tool capability：`terrain.blender.execute`

OpenWorker submit：`scripts/case0003_local_blender.ps1`

REAL gate：`.blend`、render、request/evidence/handoff，scene/render SHA256 必須一致。

## 7. Step 7B — SceneX REAL

SceneX business logic 已抽回 owning repo；local entrypoint：`scripts/scenex_terrain_real_browse_local.ps1`。

go-tool capability：`scenex.terrain.real_browse`。

OpenWorker submit：`scripts/case0003_local_scenex.ps1`。

Gate：非 fallback Region Pack、active chunks > 0、terrain geometry > 0、viewport 1280×720、screenshot/pack/evidence SHA 一致。

SceneX 只依賴 accepted Terrain + geo，因此可與 Consumer→Blender 鏈並行。

## 8. Step 8 — AI-Engineering-OS Artifact Registry：已 localize

OS 權威規格負責 Artifact Registry / Review / Approval / Delivery Revision / SQLite / delivery website。Case 不另造 registry。

`job.ArtifactStager` 會把 OpenWorker canonical workspace 的外部成果安全 stage 入 OS Job WorkingDir，重驗 SHA256，再允許 Registry 登錄；不放寬 JobPathValidator。

OS ingest：`AI-Engineering-OS/cmd/engineering-os-artifact-ingest`

go-tool capability：`engineering_os.artifacts.ingest`

OpenWorker：`scripts/case0003_local_os_artifacts.ps1`

OS project/job identity 現由 canonical JobBinding `workspace\.openworker\job-binding.json` 提供；explicit override 若與 JobBinding 不一致則 fail-closed，不再要求人工每次重填。

## 9. Step 9 — OS Review / Approval / Delivery Revision

OS current Artifact revisions 必須全部有最新 approved review 才能發布；Case 0003 不自動替成果 approve。

OS local publish：`AI-Engineering-OS/scripts/engineering_os_publish_local.ps1`

go-tool capability：`engineering_os.delivery.publish`

OpenWorker：`scripts/case0003_local_os_delivery.ps1`

publish 後仍驗證 delivery manifest、checksum manifest、website 與 delivery revision。

## 10. Step 10 — Google Drive / ChatGPT Review：local-first return loop 已補齊

Google Drive 只作審查交換面，不作 business execution transport。

### Prepare + immutable ZIP

- `scripts/case0003_prepare_drive_review.py`
- `scripts/case0003_seal_drive_review.py`
- `scripts/case0003_local_drive_review_prepare.ps1`

Prepare schema：`openworker-case0003-drive-review-prepare/v2`

每個 review revision 會建立 immutable review folder 與 deterministic `<revision_id>.zip`；本機 ZIP 與 Drive sync ZIP SHA256 必須一致。若 prepare 已成功而 seal/sync 暫時失敗，重跑會 resume seal，不建立第二個 review revision。

### ChatGPT connector review receipt

Drive-synced revision folder 的 canonical return inbox：

`connector-review-receipt.json`

receipt 必須綁定 current revision、bundle manifest SHA、immutable ZIP SHA、connector-observed Drive folder/file IDs 與 `transport=google-drive-connector`。

OpenWorker ingress：`scripts/case0003_local_apply_drive_review.ps1`

connector apply schema：`openworker-case0003-connector-review-apply/v3`

PASS 只進 `ACCEPTED_PENDING_FINALIZE`；不直接標記 delivered。

### Reviewed delivery finalizer

- `scripts/case0003_finalize_reviewed_delivery.py`
- `scripts/case0003_local_finalize_reviewed_delivery.ps1`
- semantic finalizer schema：`openworker-case0003-reviewed-delivery-finalize/v3`

Finalizer 再次綁定 current OS Delivery identity、manifest/checksum/website physical SHA、Drive folder/ZIP identity 與 WorkLedger accepted pointer；而且 current OS delivery bytes 必須與 ChatGPT 當時審過的 bundle 中 delivery-manifest/checksum-manifest/delivery-index bytes 完全一致，否則舊 PASS 失效。

## 11. Case 0003 一鍵 local-first continuation controller

Canonical auto entrypoint：

`scripts/case0003_local_continue_auto.ps1`

執行順序：

```text
persisted machine-root registry / node inventory
→ JobBinding OS identity
→ case0003_local_preflight.ps1
→ canonical physical-gate controller
```

OpenWorker machine roots 由持久 registry 提供，預設 `%ProgramData%\OpenWorker\machine-roots.json`；service 不必碰巧繼承 interactive user shell environment。

REAL preflight 在任何 business job submit 前先驗 UL7 identity、required tools/roots、workspace/JobBinding、DTM catalog、Engineering OS health；失敗時不提交 business jobs。

內部 controller：`scripts/case0003_local_continue.ps1`

目前 schema：`openworker/case0003-local-continue/v9`

v9 最大變更：Imagery gate 已升成 `SHA + producer provenance + semantic visibility` authority；舊 file-exists evidence 不再能解鎖 Consumer。

目前依 physical / identity gates 自動續跑：

```text
Strict imagery incomplete
→ Street View + Orthophoto parallel / missing-side-only retry

Terrain incomplete + DTM catalog ready
→ AOI

Terrain physical gate
├→ SceneX
└→ Strict imagery pass → Consumer → Blender

Blender + SceneX pass
→ OS Artifact Registry

OS current artifacts approved
→ OS Delivery publish

OS Delivery pass
→ Drive review prepare + immutable ZIP

Drive review prepared, receipt absent
→ CHATGPT_GOOGLE_DRIVE_CONNECTOR_REVIEW_REQUIRED

connector-review-receipt.json synced back
→ OpenWorker local connector review apply

PASS
→ reviewed delivery finalizer
→ CASE0003_DELIVERED
```

Controller 對 queued/running stages 做 duplicate suppression，不把 submitted 視為完成；每次重跑重新讀 canonical workspace、OS authoritative state、Drive return receipt 與 SHA。

## 12. 目前 acceptance boundary

**目前只有 GEO 可稱 ACCEPTED。**

尚不得稱 ACCEPTED/DELIVERED：Street View、Orthophoto、AOI、Consumer、Blender、SceneX、OS Artifact Registry、OS Approval、Delivery、Drive Review。

原因：此 ChatGPT 執行環境仍不能直接連入 UL7 的 `127.0.0.1:8787`。目前完成的是最新版 local-first execution/review contract 與 fail-closed orchestration，不是假裝完成 UL7 REAL run。

## 13. UL7 下一個 REAL 執行順序

1. OpenWorker service 使用 persisted machine-root registry；必要時先執行 `scripts/openworker_set_machine_roots.ps1`。
2. 確認 OpenWorker node / agents online；若確有 queue blockage，再使用 one-call queue drain，不無條件清其他案例工作。
3. 執行 `scripts/case0003_local_continue_auto.ps1`。
4. auto entrypoint 從 node inventory / JobBinding 解析 roots 與 OS identity，先跑 REAL preflight。
5. v9 controller 會把舊 imagery evidence 視為 incomplete，提交 Street View / Orthophoto 缺失側的 local durable jobs。
6. 驗四向 Street View producer provenance + physical SHA；驗 NLSC PHOTO2 visibility thresholds + physical SHA。
7. strict imagery + Terrain gate 後才推 Consumer→Blender；Terrain gate 可並行推 SceneX。
8. 驗 Blender REAL render、SceneX REAL screenshot / geometry / SHA。
9. 進 OS Artifact Registry；完成 current Artifact review / approval。
10. Controller 發布 OS Delivery，驗 manifest/checksum/site。
11. Controller 自動準備 Drive revision folder + immutable ZIP。
12. ChatGPT connector 實際查看 Blender render、SceneX screenshot、evidence、delivery website，產生 PASS / TUNE / FAIL / TOOL_GAP receipt。
13. receipt 回到 Drive sync folder 後 controller 自動 apply；PASS 才 finalizer → WorkLedger delivered。

任何新缺口：案例暴露缺口 → 修 owning repo / go-tool local handler → OpenWorker local REAL rerun → physical artifact QC → OS review/delivery → Drive connector review → append-only WorkLedger evidence。
