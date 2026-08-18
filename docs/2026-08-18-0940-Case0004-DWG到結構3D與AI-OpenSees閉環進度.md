# Case 0004 — DWG 到結構 3D 與 AI-OpenSees 閉環進度

日期：2026-08-18
狀態：IMPLEMENTING / O87 EXECUTION GATE WAITING

## 1. 固定案例權威

- Case：0004
- Workspace：`D:\AI-Work\jobs\0004-DWG-TO-3D`
- Assigned host：`DESKTOP-O87PJNR`
- OpenWorker durable manifest：`case-worklists/0004.json`
- 原始 DWG SHA256：`aaadbd84e8a5b2e1b0b8f54c16901a69085c7501aeec602929fd994f3192f5b6`

## 2. 已完成的視覺搜尋與 Story Region 定位

真實 DWG 已完成 OpenCAD Model Space inspect / candidate region / bounded visual review。

經重新解碼實際圖片後，真正可作樓層平面候選的是 Round 2：

- review tile：`c-mid-left`
- source preview：`candidate-overview.png`
- source preview SHA256：`5cee03340cbbcad51e412b46b85bda9dcaac22b193586b953bbfd5134039103e`
- pixel crop：`[0,533,200,133]`

前一輪 Round 3 / Round 4 的 central/right crop 偏移到表格／文字區，不再作 Story Region authority。

OpenCAD `project()` 已確認使用：

- 10 px margin
- X/Y 等比例 fit
- Y 軸反轉

已新增 deterministic pixel crop → Model Space transform，Case 0004 候選 bounds：

```text
minX = 44443.2512
minY = 44319.7138
maxX = 58261.7808
maxY = 53992.6846
```

該 bounds 目前只標記為 `candidate`，必須先通過真實 `cad.query_bounds` probe 才能執行 `cad.set_story_region`。

## 3. Story Region 真實 probe

DWG_todo 已新增 Case 0004 O87 Story Region probe workflow。

舊做法使用：

```yaml
runs-on: [self-hosted, Windows, X64, O87]
```

已依 2026-08-18 最新 OpenWorker 路由策略改為：

```yaml
runs-on: [self-hosted, Windows, X64]
```

配合 matrix candidate + `COMPUTERNAME == DESKTOP-O87PJNR` + workspace lock。

原因：固定機器權威應由實體 computer name 決定，不再依賴自訂 runner label 是否正確掛載。

Probe acceptance：

1. 只在 `DESKTOP-O87PJNR` 執行。
2. 使用既有 `dwg/agent-cad-state.json`。
3. build 最新 `dwg-editor` + OpenCAD。
4. 真跑 `cad.query_bounds`。
5. candidate region `entity_count >= 20`。
6. 回寫 `review-tmp/case0004/story-region-probe.json`。

截至本文件更新時，該 receipt 尚未回寫，所以不可把 Story Region 宣告 confirmed。

## 4. 柱候選與 Story Design

最新版 `cad.design_story_structure` 明確要求至少兩個經模型視覺確認的 OpenCAD column handles。

因此已新增 read-only shortlist 能力：

- `cmd/dwg-column-shortlist`
- 輸入：`cad.query_bounds` 真實 entities
- 輸出：候選 handle / bounds / section-like geometry ranking
- authority：固定 `none`

此工具只縮小人工／模型視覺審查範圍，不會把任意矩形自動升格為柱。

`story-region-probe.json` 一旦回寫，Case 0004 column-shortlist workflow 會自動產生：

`review-tmp/case0004/column-shortlist.json`

後續：

`confirmed column handles → cad.design_story_structure → Column Authority → Column Graph → Primary Beam → Floor Bay → Secondary Beam → design.json + design.png`

## 5. AI-OpenSees 整合邊界

已確認不能直接把單層 `design_story_structure` 的柱心模型送進 AI-OpenSees。

單層 story design 中柱位置可能以 same-story zero-height member 作暫時 authority；真正 3D 柱必須在多樓層 registration 後，由 `MaterializeColumnAuthority` 把相鄰 story placements 連成上下節點：

`column-link-<lower>-<upper>`

因此 AI-OpenSees canonical gate 固定在：

`Story registration confirmed → Stage 08 V1 structural authority → AI-OpenSees validation → Stage 11 structural 3D`

而不是單層 Story Design 後立即驗證。

## 6. Stage 08 V1 structural authority

DWG_todo Stage 08 已存在正式 authority：

- `structural-line-model.json`
- `column-authority.json`
- `v1-building-skeleton.json`

`structural-line-model.json` 為 registration 後 Building World Coordinates 下的 V1 structural skeleton，包含真正跨層柱、主梁與必要次梁。

Stage 11 已把它當作主要幾何權威，再建立：

- `building-assembly.json`
- `structural-solid-model.json`
- `opencad-3d-dwg-build.json`
- `artifacts/dwg/<project>-3d.dwg`

## 7. structural-line-model → AI-OpenSees bridge

已新增 deterministic `structural-line-model/v1 → MCT` bridge。

原則：

- 保留 node XYZ。
- 保留 member node-I / node-J topology。
- 保留已有 material / section name。
- 缺材料或 section 時只寫 `UNSPECIFIED`，不猜工程資料。
- 缺節點、duplicate id、非有限座標、same node topology、零幾何長度全部 fail-closed。

此 MCT 再交給最新 `AI-OpenSees/main` C++ `ai-opensees validate`。

## 8. Production AI-OpenSees gate

DWG_todo 已新增：

`.github/workflows/case-0004-o87-ai-opensees-production.yml`

Production gate：

1. computer-name routing 到 `DESKTOP-O87PJNR`。
2. 在 Case 0004 workspace 尋找唯一 Stage 08 `structural-line-model.json`。
3. 要求 sibling `v1-building-skeleton.json` 存在。
4. structural-line-model → MCT。
5. clone 最新 `liuxb99/AI-OpenSees main`。
6. 現場 CMake build 正式 C++ `ai-opensees.exe`。
7. 執行 `ai-opensees validate`。
8. 要求 `format=mct`、`status=complete`、nodes/elements 非空。
9. 回寫 `review-tmp/case0004/ai-opensees-production-validation.json`。

只有此 gate PASS 才允許 Case 0004 進 Stage 11 3D。

## 9. 3D 與截圖最終驗收

完整 acceptance 不以「檔案存在」為完成：

```text
Story Region confirmed
→ Story Design reviewed
→ materialize stories
→ Story anchors / registration confirmed
→ Stage 08 structural-line-model/v1
→ AI-OpenSees topology PASS
→ Stage 11 Building structural 3D
→ production GLB
→ Blender 5.2 REAL reopen
→ perspective render PNG
→ native AC1032 ACIS Solid3D DWG
→ OpenCAD DwgReader reopen / second validation
→ OS Artifact Registry
→ Drive Review Bundle
→ ChatGPT visual review receipt
→ approved Delivery Revision
```

Blender PNG 為硬性驗收成果，至少需要一張整體透視圖；建議再保留正立面／側立面或局部樓層視角。

## 10. OpenWorker durable Worklist

`case-worklists/0004.json` 已存在完整 0004 主線，workspace 與 assigned host 正確。

已新增：

`.github/workflows/case0004-sync-worklist-win11.yml`

用最新版 computer-name routing 把 manifest 同步到：

`D:\AI-Work\jobs\0004-DWG-TO-3D\.openworker\case-worklist.json`

並預計回寫：

`evidence/case0004/latest-worklist-sync.json`

截至本文件更新時，該 authority 尚未回寫。

## 11. 目前唯一外部執行阻塞

目前多條新 self-hosted workflow 都尚未產生 machine authority receipt：

- Story Region probe
- Case 0004 Worklist sync
- source overview metadata authority
- structural bridge run authority

因此目前最合理的執行層判斷是：O87 self-hosted runner 尚未完成接單／執行。

在 receipt 出現以前，不把任何新 REAL gate 誤算成成功。

## 12. 下一個 canonical step

一旦 O87 runner 可執行：

1. `0004-050`：Story Region probe。
2. 取得 `story-region-probe.json`。
3. 生成 `column-shortlist.json`。
4. 模型視覺確認 column handles。
5. `cad.set_story_region`。
6. `cad.design_story_structure`。
7. 逐層 materialize + registration。
8. Stage 08 structural authority。
9. production AI-OpenSees validation。
10. Stage 11 3D / Blender render / Solid3D DWG。

不得重新從全 DWG visual search 開始，除非 probe 證明目前 `c-mid-left` Model Space bounds 不成立。
