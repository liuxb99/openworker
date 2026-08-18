# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-18 Asia/Taipei

狀態：`IMPLEMENTING / GEO ACCEPTED / LOCAL STREETVIEW RERUN REQUIRED / LOCAL ORTHOPHOTO NEW GATE / TERRAIN DTM CONTINUES`

## Canonical execution contract — 2026-08-18 新版

- 固定主機：`DESKTOP-UL7V2VV`
- canonical workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- case mirror：`D:\AI-Example\0003`
- canonical input：`location_text = 臺南市玉井橋`
- **OpenWorker 是本機總控、durable job/agent/cluster/workspace/host authority。**
- **go-tool-runtime 是 capability discovery + local execution registry。**
- REAL / consequential 工作優先走 `OpenWorker local jobs -> go-tool localexec -> owning repo local CLI/runtime`。
- OpenWorker 可把互不依賴的工作分配不同 agent slots 並行；本案例 Street View 與 Orthophoto 共用 accepted geolocation，但輸出互相獨立，因此應並行。
- GitHub Actions 不再是本案例主要 business execution boundary；既有 operator workflows 僅保留作 fallback、CI、遠端 bootstrap 或 evidence transport，不能因 Action success 就宣稱 business success。
- assigned host 與 workspace 仍由 persisted OpenWorker state 決定；localexec 必須再次檢核 `claim.assigned_host == local COMPUTERNAME`，不允許模型自行換機。

## 新舊架構差異：GitHub-first → OpenWorker local-first

### 舊版：GitHub-first business execution

舊流程常見路徑：

```text
ChatGPT / operator
→ workflow_dispatch
→ GitHub Actions queue
→ self-hosted runner routing / label / condition
→ checkout / environment bootstrap
→ owning tool
→ Action artifact / log
→ 再判斷 business result
```

這個模式的主要問題不是 GitHub Actions 本身不能用，而是它被放在了不適合的位置：把 CI/遠端 transport 當成日常本機 business execution plane。結果會增加大量與真正工程成果無關的中間狀態：workflow condition、runner label、排隊、checkout、artifact upload/download、Action success/failed 等。

對 Case 0003 這種需要固定 UL7、固定 workspace、同時跑多個本機工具、最後還要檢查實體圖像/地形/3D 成果的案例，GitHub-first 會讓「工具問題」與「transport 問題」混在一起。Action 綠燈也不代表 Street View 不是黑圖、Orthophoto 可視、DTM usable tiles > 0，或 Blender 成果正確。

### 新版：OpenWorker local-first business execution

新版 canonical 路徑：

```text
ChatGPT / local supervisor
→ OpenWorker 本機總控
→ durable jobs / agent slots / fixed host / canonical workspace
→ go-tool localexec capability registry
→ owning repo local CLI / service / script
→ workspace physical artifact + evidence
→ physical / semantic QC
```

這個改變把責任分開：

- OpenWorker 管「在哪台機器、哪個 workspace、哪個 durable job、哪個 agent slot、queue 是否阻塞」。
- go-tool 管「目前有哪些正式 capability，以及要呼叫哪個本機 handler」。
- owning tool 管「真正的工程/影像/3D 邏輯」。
- ChatGPT / QC 層只在實體成果與 evidence 足夠時才接受結果。

因此現在發現問題後，理想路徑變成：

```text
發現成果不對
→ 定位 owning capability
→ OpenWorker 本機提交/重跑
→ go-tool localexec
→ 直接看 canonical workspace 實體成果
→ 缺口回 owning repo 修
→ 再跑
```

而不是：

```text
發現成果不對
→ 先改 workflow / condition / runner
→ dispatch
→ 等 GitHub queue / runner
→ 看 Action log
→ 再猜是 transport 還是工具壞
→ 回本機修
```

### 新版對本案例的直接效果

1. **並行更直接**：Street View 與 Orthophoto 不互相依賴，OpenWorker 可直接分配不同 agent slot 同時跑，不需要建立兩條 GitHub workflow 再等待 runner 排程。
2. **固定機器更可靠**：UL7 是 OpenWorker persisted host authority，localexec 會再次驗證實際 `COMPUTERNAME`；不再靠 GitHub runner 搶單或複雜 label condition 當主要保證。
3. **queue 處理更簡單**：本機總控可直接看到 durable job/agent 狀態；若發現阻塞，應使用 OpenWorker 新版 one-call queue drain，而不是逐筆處理 GitHub workflow queue。
4. **成果直接落 canonical workspace**：Street View、Orthophoto、Terrain、Blender 等成果直接寫入 `D:\AI-Work\jobs\0003-YUJING-BRIDGE`，下游不需要先經 Action artifact 搬運才能繼續。
5. **錯誤定位更乾淨**：本機 handler 成功但實體成果失敗，直接修 owning tool；不必先排除 workflow/checkout/artifact transport 的干擾。
6. **business acceptance 更嚴格**：Action success 不再是 acceptance gate；PNG visibility、DTM usable tiles、SHA256、Blender render、SceneX screenshot 等 physical evidence 才是 gate。
7. **GitHub 回到正確角色**：GitHub 主要保留 code review、commit、CI、fallback、bootstrap、必要 evidence transport；不再要求大部分並行 business action 經 GitHub。

結論：新版不是單純把 workflow 換成 PowerShell，而是把 execution authority 從 GitHub Actions 移回 OpenWorker 本機總控，使 GitHub 從「主要執行平面」退回「代碼/CI/備援平面」。後續 Case 0003 新增 capability 時，除非 local execution 暫時不可行，否則不得重新把 GitHub workflow_dispatch 當 canonical business path。

## 已接受

### Step 1/2 — OpenWorker / go-tool control plane

已完成固定 UL7 host/workspace continuity、capability discovery 與 durable work state。早期 GitHub Action run/job IDs保留作歷史 provenance，但新版後續執行不再要求每個 business step 經 GitHub。

### Step 3 — geolocation

accepted state：

`D:\AI-Work\jobs\0003-YUJING-BRIDGE\geo\geolocation.json`

Street View / Orthophoto local handlers都只能讀此 accepted state，不得自行硬寫玉井橋座標。

## Step 4A — Street View：舊 acceptance 作廢，改走 localexec REAL rerun

舊 STATUS 曾把四向 headless PNG 標成 accepted；2026-08-18 依案例實際回報確認舊 producer 只驗證 PNG 存在/非空/hash，黑畫面仍可能被誤判，因此撤銷 acceptance。

Terrain owning repair：

- headless screenshot semantic visibility fail-closed：`027915e7e4ddf8384ab680cdb4a1f5105834fad6`
- tests sync：`d1c58f96e5a0a6ca3448c45af79732bf1e9af96a`

2026-08-18 新版本機路徑：

```text
OpenWorker durable job
→ go-tool gtr-local-exec
→ capability terrain.streetview.acquire
→ Terrain_To_DXF local CLI terrain-streetview-render
→ Chrome/Edge + ANGLE/SwiftShader WebGL
→ 0 / 90 / 180 / 270 四向 PNG
→ semantic visibility + SHA256
→ workspace/streetview/browser
```

go-tool local handler commits：

- Terrain local handlers：`987337a8c3390e4de29d891cd9d1001a0f7ff826`
- `gtr-local-exec` 加入 `TERRAIN_ROOT`：`e99cf37f20dc0255e3566e53364c65b31789acd0`
- local registry tests：`d43f6143a9892ef460b3d13dce110a83e37c6c4d`

接受條件：四張實體 PNG 都必須 decode、visibility PASS、SHA256/manifest 一致。舊 PNG 只能保存歷史 evidence。

## Step 4B — 正射影像 Orthophoto：正式 local_action

案例回報證明原工具鏈缺 orthophoto。已在 Terrain_To_DXF 補 NLSC `PHOTO2` bounded WMTS acquisition、JPEG decode、3x3 mosaic、tile/mosaic SHA256 provenance、semantic visibility fail-closed。

主要成果：

- CLI：`terrain-orthophoto-acquire`
- workspace：`orthophoto\nlsc-photo2\`
- bounded acquisition：預設 z19 / radius 1，禁止全臺大量 cache
- imagery 只作 visual/reference truth，不取代 DTM geometry truth

2026-08-18 go-tool 已改為 local-first：

- capability：`terrain.orthophoto.acquire`
- registry：`capabilities.d/terrain-orthophoto.yaml`
- `execution.mode: local_action`
- local-action registry commit：`15b7fbaf599d7746718c09c310221a447d330170`

正式路徑：

```text
OpenWorker durable job
→ go-tool gtr-local-exec
→ terrain.orthophoto.acquire
→ Terrain_To_DXF local CLI
→ NLSC PHOTO2 bounded tiles
→ JPEG decode + mosaic + visibility + SHA256
→ workspace/orthophoto/nlsc-photo2
```

## Step 4C — Street View + Orthophoto 本機並行

OpenWorker 已新增 Case 0003 本機並行提交入口：

`scripts/case0003_local_imagery_parallel.ps1`

commit：`28613a83407f8dab92e4ea9f7dc1485182250d04`

此入口一次向本機 OpenWorker `POST /v1/jobs` 提交兩個 durable jobs：

1. `terrain.streetview.acquire`
2. `terrain.orthophoto.acquire`

兩者：

- machine 固定 `DESKTOP-UL7V2VV`
- workspace 固定 `D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- 使用不同 lock，可由不同 agent slot 同時執行
- command 執行 `go run ./cmd/gtr-local-exec --claim ...`
- `TERRAIN_ROOT` 由本機 runtime/environment authority 提供
- `github_business_transport=false`

提交 receipt：

`workspace\evidence\case0003-local-imagery-parallel-submit.json`

個別 localexec 結果：

`workspace\evidence\case0003-*-localexec-result.json`

## Terrain / elevation AOI

DTM geometry truth 路線維持：

```text
D:\TaiwanDTM
  catalog\
  raw\
  extracted\
  normalized\
  cog\
```

既有 bootstrap evidence：`evidence/0005-terrain-aoi-and-dtm-bootstrap.md`。

DTM/AOI 後續也應逐步由 OpenWorker local jobs + go-tool local_action 取代 GitHub Action business transport；尚未 localize 的能力可以暫時 fallback，但文檔要明確標示 legacy/fallback，不得再把 GitHub transport 當 canonical architecture。

## 目前正確下一步

1. 在 UL7 確認 OpenWorker native service / agents online。
2. 確認 `GO_TOOL_ROOT`、`TERRAIN_ROOT` 是本機 authority，不在 Case 寫死工具 checkout 路徑。
3. 執行 `scripts/case0003_local_imagery_parallel.ps1`，一次提交 Street View + Orthophoto durable jobs。
4. 由 OpenWorker `/v1/jobs` 與 `/v1/cluster/agents` 觀察兩個 job 是否真正並行、由 UL7 agent slots 接單。
5. 驗證 Street View 四向 PNG semantic visibility / SHA256。
6. 驗證 PHOTO2 mosaic semantic visibility / tile + mosaic SHA256。
7. 只有兩個 local business jobs 都 PASS 才把 imagery gates 改回 `ACCEPTED`。
8. 接著把 `terrain.aoi.build`、consumer orchestration、Blender 等剩餘 Case 0003 能力依新版 local-first 模式逐步 localize。
9. SceneX → OS Artifact Registry → Delivery Revision → website 完整閉環。

任何新缺口仍依同一規則：案例暴露缺口 → 修 owning repo / go-tool local handler → OpenWorker local REAL rerun → physical artifact QC → append-only evidence。
