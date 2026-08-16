# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`IMPLEMENTING / UL7 VERIFIED / STEP 2 GO-TOOL CAPABILITY CLOSURE`

## Canonical execution contract

- 固定主機：`DESKTOP-UL7V2VV`
- canonical workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- case mirror：`D:\AI-Example\0003`
- canonical input：`location_text = 臺南市玉井橋`
- REAL / consequential work：一律由本機 self-hosted GitHub Action 執行
- OpenWorker persisted JobBinding / workspace 是 host/workspace authority；Action labels / matrix 只負責 transport fan-out。

## 已確認

1. UL7 並非 offline。
   - cross-repo readiness run：`31921072421`
   - UL7 job：`95100919549` / `readiness (4)`
   - runner：`DESKTOP-UL7V2VV-R002`
   - machine：`DESKTOP-UL7V2VV`
   - identity gate：`CASE0003_UL7_IDENTITY_PASS`

2. 舊的「UL7 runner offline/unavailable」結論已被上述 REAL evidence 取代。

3. run `31921072421` 的真正失敗點不是 runner，而是直接從外層 workflow checkout private `liuxb99/go-tool-runtime`：
   - `actions/checkout@v4`
   - error：`Repository not found`
   - 原因：該 workflow 的 `GITHUB_TOKEN` 僅有自身 repo scope，不能當成跨 private repo 的正式 operator credential。

4. go-tool-runtime 最新設計已經解決這類 credential / dispatch 問題：
   - `auth_mode: auto`
   - priority：local shared credential DB → GitHub App → `GITHUB_TOKEN`
   - shared DB：`C:\ProgramData\go-tool-runtime\runtime.db`
   - key：`GH_TOKEN`
   - capability registry / readiness / dispatch / run/jobs/artifacts query 已正式實作。

因此 Case 0003 不再用案例 workflow 自己 checkout/build 每個 private owning repo；正式路徑改成：

`OpenWorker state/binding → UL7 上既有 go-tool-runtime → capability discovery/schema/readiness → go-tool formal dispatch → owning repo Operator Action → go-tool run/jobs/artifacts query → OpenWorker ledger/evidence`

## 目前真正缺口

### G-0003-004 — Case workflow 繞過 go-tool formal operator layer

舊 CASE-0003 probe 自己 checkout `go-tool-runtime`，導致 private repo credential scope failure。這是 orchestration 層錯誤，不是 runner availability 問題。

**修正方向：** Case 0003 只負責 bootstrap / state / evidence；工具執行全部透過 UL7 上 go-tool-runtime 正式 capability provider。

### G-0003-005 — Street View / geolocation 最新能力尚未完整暴露為 go-tool capabilities

`Terrain_To_DXF` main 已具有 Street View provider-neutral metadata、Google metadata lookup、snapshot、route scan、headless browser renderer、highest-resolution acquisition policy、master tile acquisition、native-resolution panorama stitch 與 checksum evidence。

目前 go-tool `config.yaml` 已正式註冊 `terrain.dxf.generate`，但尚未看到上述 Street View / location acquisition 對應的 production capability entries。

這代表 Case 0003 Step 2 的第一個產品缺口是：

`owning repo capability exists → go-tool capability registry / Operator contract 尚未完整暴露`

修復後必須由 UL7 本機 Action 重新執行 Step 2 discovery/readiness，不能只用 unit test 宣稱完成。

## 下一步

1. 查 `Terrain_To_DXF` 最新 operator workflows / CLI contract，找出 Street View / location / terrain source 的 canonical inputs 與 artifact evidence。
2. 若已有 Operator workflow：直接在 go-tool registry 正式註冊並補測試。
3. 若只有 library/CLI/Golden：在 `Terrain_To_DXF` 補 typed `workflow_dispatch` Operator workflow，禁止任意 shell input，輸出固定到 runner temp / canonical workspace materialization contract。
4. go-tool 補 capability entry + schema/readiness/evidence contract。
5. 由 UL7 上 go-tool formal dispatch 真正執行：
   - capability discovery
   - detail/schema
   - readiness / queue preflight
   - dispatch
   - run/jobs/artifacts query
6. 將 REAL run/job/runner/artifact/hash/缺口/修復/重跑全部寫入 `evidence/0002-capability-discovery.md`。
7. Step 2 PASS 後進 Step 3：僅以 `臺南市玉井橋` 做正式位置解析，不硬編座標。
