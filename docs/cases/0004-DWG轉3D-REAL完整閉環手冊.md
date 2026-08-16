# 案例 0004：使用者 DWG → 3D REAL 完整閉環手冊

> 主責位置：`liuxb99/openworker`
>
> 執行治理：`liuxb99/AI-Engineering-OS`
>
> DWG owning repo：`liuxb99/DWG_todo`（default branch：`master`）
>
> 指定 REAL 主機：`DESKTOP-O87PJNR`（O87）
>
> 更新時間：2026-08-16（Asia/Taipei）
>
> 狀態：`IMPLEMENTING / O87-ONLY ORCHESTRATION CONTRACT / WAITING FOR USER REAL DWG INPUT`
>
> 目標：使用者上傳一份真實 `.dwg` 後，由 `OpenWorker → AI-Engineering-OS → go-tool-runtime → DWG_todo/OpenCADStudio → Blender → AI-Engineering-OS Artifact Registry → Review → Delivery Revision` 完成真正 DWG→3D 閉環。不得以 fixture、假 3D wireframe、只產 JSON、只產 GLB、workflow 全 skip 或 renamed file 冒充完成。

---

## 0. 本案例執行原則

1. **所有 REAL 產品步驟固定只在 O87：`DESKTOP-O87PJNR` 執行。**
2. OpenWorker 是案例工作狀態與操作總控，不複製 DWG 產品邏輯。
3. AI-Engineering-OS 擁有 canonical Project / Job / workspace / Artifact Registry / Review / Delivery lifecycle。
4. `DWG_todo` 擁有 DWG 解析、樓層/構件辨識、配準、Building World Coordinates、GLB、native ACIS Solid3D DWG 等產品能力。
5. OpenWorker 只能透過正式 capability / go-tool / self-hosted Action 操作 owning repo，不得在 OpenWorker 寫第二套 DWG converter。
6. 使用最新正式提交；DWG_todo 使用 `master`，OpenWorker / OS / go-tool-runtime 使用各自最新正式主線。
7. 發現缺口時修真正 owning repo，再用同一條正式路徑重跑。
8. 任何 output 必須有 physical path、存在、非零、size、SHA256；需要 reopen 的格式必須真實 reopen。
9. GitHub Actions 非 O87 job、routing-only、skip job 不能算產品成功。
10. GitHub artifact quota 錯誤只屬 evidence-upload 問題，不能取代本機 physical product gate。

---

## 1. 全鏈

```text
User uploads REAL DWG
→ AI-Engineering-OS canonical Job Workspace
→ input/source.dwg
→ OpenWorker job binding / project knowledge
→ go-tool-runtime capability dispatch
→ DWG_todo raw DWG inspect / overview
→ repeated crop / story-region recognition
→ structural story design + review
→ materialize to job-scoped llmCAD
→ story anchors / registration
→ Building World Coordinates
→ production GLB
→ Blender 5.2 REAL reopen + render
→ native ACIS Solid3D DWG build
→ OpenCAD DwgReader reopen / 3DSOLID validation
→ canonical 3D outputs + evidence
→ AI-Engineering-OS Artifact Registry
→ Review current revisions
→ Delivery Revision
→ delivery package / website
```

案例的主要「3D 成果」至少要同時有：

- `building.glb`：供 Blender / downstream 3D consumer 使用；
- `building-3d.dwg`：真正 AC1032 native DWG，內含 ACIS `3DSOLID`，不是線框改副檔名；
- Blender reopen/render screenshot；
- manifest / inspect / SHA256 evidence。

---

## 2. O87 固定執行 contract

### 2.1 Assigned host

固定：

```text
CASE0004_ASSIGNED_HOST=DESKTOP-O87PJNR
```

OS/OpenWorker workflow 必須在產品步驟開始前驗證：

```text
COMPUTERNAME == DESKTOP-O87PJNR
OpenWorker JobBinding.assigned_host == DESKTOP-O87PJNR
```

任一不一致立即 fail closed。

### 2.2 Runner routing

本案例不採用 0002 那種「多個一般 self-hosted matrix slot 搶到後再 skip」作為常態方案。

正式方案優先：

```text
runs-on: [self-hosted, Windows, X64, O87]
```

並且仍保留 `COMPUTERNAME` 二次檢核。

如果目前 GitHub runner 尚未掛 `O87` 專屬 label，第一個 infrastructure gap 就是補專屬 label；在專屬 routing 完成前，不得靠反覆 rerun 抽 O87 宣稱穩定閉環。

---

## 3. Canonical OS workspace

建議固定工作區：

```text
D:\AI-Work\jobs\0004-DWG-TO-3D
```

鏡像/展示區：

```text
D:\AI-Example\0004
```

使用者上傳 DWG 被 OS 接收後，canonical input 固定 materialize 為：

```text
D:\AI-Work\jobs\0004-DWG-TO-3D\input\source.dwg
```

### Input gate

必須驗證：

- 副檔名 `.dwg`；
- physical file exists；
- size > 0；
- SHA256 可計算；
- canonical path 位於 Case 0004 workspace；
- 不允許 `..` traversal / workspace escape；
- 原始檔必須保留 immutable provenance，不直接覆寫。

OpenWorker ProjectKnowledge 要記錄：

- source path；
- source size / SHA256；
- OS Project / Job ID；
- assigned host；
- current stage / blocker / next action。

---

## 4. Owning repo：DWG_todo 現有能力

截至 2026-08-16 最新檢查，DWG_todo 已有以下主線能力：

### 4.1 Building-level 3D

正式 built-in methods：

```text
cad.list_story_registrations
cad.build_building_3d
cad.export_building_glb
cad.validate_building_3d
```

已驗證過的產品鏈：

```text
Story Region
→ reviewed story materialization
→ Story Anchor
→ Story Registration
→ Building World Coordinates
→ production GLB
→ Blender 5.2 reopen
→ headless render PNG
→ physical SHA256 evidence
```

歷史 REAL Blender gate：

```text
Run 31929000434
Runner DESKTOP-UL7V2VV-R002
Blender 5.2.0 LTS
```

該 run 證明產品 GLB 可被 Blender 真實 import/render，但 **案例 0004 必須在 O87 用使用者真實 DWG 重新完成一次**，不能直接借用舊 fixture evidence。

### 4.2 Native 3D DWG

正式 built-in methods：

```text
cad.build_building_dwg
cad.export_building_dwg
cad.validate_building_dwg
```

正式 native path：

```text
Building World Coordinates
→ opencad-3d-dwg-build/v1
→ OpenCADStudio --build-3d-dwg
→ acadrust primitives::build_box
→ ACIS Solid3D SAT
→ DwgWriter AC1032
→ physical .dwg
→ DwgReader + OpenCAD inspect reopen
→ 3DSOLID / layer count / SHA256 validation
```

結構 layer：

```text
primary beam   → S-BEAM-PRIMARY
secondary beam → S-BEAM-SECONDARY
column support → S-COL
```

不得把 3D DXF / GLB 改名成 `.dwg`。

---

## 5. 歷史 native REAL gate 與案例 0004 判讀

歷史 workflow：

```text
DWG Building 3D DWG REAL
Run 31929525959
Job 95122140673
Runner DESKTOP-UL7V2VV-R002
```

結果：`completed / failure`。

已通過：

- Go/Rust toolchain；
- built-in bridge unit checks；
- OpenCADStudio native writer release build；
- native writer Rust tests（7/7）；

真正失敗點：REAL manifest 被 Rust 端解析時出現 schema mismatch：

```text
missing field `x` at line 18 column 7
```

因此該 run **不能算 native 3D DWG REAL VERIFIED**。

之後 DWG_todo `master` 已有更多 Building DWG / column / beam authority commits；案例 0004 不沿用舊 run 判定，必須以最新 master 在 O87 重跑並取得實體 DWG reopen PASS。

---

## 6. Step A：使用者 DWG → OS Input

輸入：使用者上傳的一份真實工程 `.dwg`。

驗收：

```text
input/source.dwg exists
size > 0
SHA256 recorded
OS Project/Job exists
OpenWorker JobBinding exists
assigned_host = DESKTOP-O87PJNR
```

若尚未有真實 DWG，本案例停在 `WAITING_FOR_REAL_DWG_INPUT`，不得用 synthetic fixture 升級為案例完成。

---

## 7. Step B：Raw DWG inspection / visual understanding

OpenWorker 透過 go-tool-runtime 調用 DWG_todo 的正式 operator，對 canonical `input/source.dwg` 做：

- native open / inspect；
- drawing overview；
- layer/entity inventory；
- repeated crop / visual regions；
- story/floor candidate recognition；
- structural handles / provenance。

每個識別結果必須能追溯到原始 DWG handle / layer / crop evidence。

不允許大模型直接憑截圖猜完整棟 geometry。

---

## 8. Step C：Story Design → reviewed materialization

對每一樓層：

1. 產生結構 Story Design；
2. 柱、主梁、次梁等 section 需保存 authority/provenance；
3. review 通過後才 materialize；
4. materialize 到 job-scoped llmCAD authoritative state；
5. 未 review / stale revision 不得進 Building assembly。

最新 DWG_todo master 已持續補：

- recognized column section dimensions；
- column section provenance；
- primary beam explicit design result；
- secondary beam explicit design result。

案例 0004 要用實際上傳圖驗證這些能力，而不是只跑 fixture。

---

## 9. Step D：跨樓層配準 → Building World Coordinates

要求：

- reference story 明確；
- shared anchors；
- non-reference story registration；
- RMS / max residual 可追溯；
- local → world geometry provenance 不漂移；
- story Z/elevation 有限且一致。

若樓層無法可信配準，fail closed，不生成整棟 3D。

---

## 10. Step E：Production GLB → Blender 5.2 REAL

調用：

```text
cad.build_building_3d
cad.export_building_glb
cad.validate_building_3d
```

O87 必須真實執行 Blender 5.2：

```text
bpy.ops.import_scene.gltf
mesh_object_count >= 1
world bounding box valid
headless render succeeds
render PNG exists and size > 0
```

記錄：

- GLB path / size / SHA256；
- building manifest；
- Blender version；
- reopen report；
- render PNG path / size / SHA256；
- world bounds。

---

## 11. Step F：Native ACIS Solid3D DWG REAL

調用：

```text
cad.build_building_dwg
cad.export_building_dwg
cad.validate_building_dwg
```

正式 acceptance：

1. `.dwg` physical file exists / non-zero；
2. target version AC1032；
3. representation = solid；
4. DwgReader reopen 成功；
5. expected structural operations 均 reopen；
6. `3DSOLID` count 與 solid operation count 一致；
7. layer entity counts 一致；
8. second validate/reopen 仍 PASS；
9. DWG / manifest / inspect / evidence 均記 SHA256。

這一步成功後，才能宣稱「DWG 真的轉成 native 3D DWG」。

---

## 12. Step G：AI-Engineering-OS Artifact Registry

至少註冊：

```text
source-dwg
building-world-model / manifest
building-glb
blender-reopen-report
blender-render-png
building-native-3d-dwg
native-dwg-inspect
native-dwg-validation-evidence
```

每個 artifact 至少具有：

- ProjectID / JobID / ComponentID / Kind / Revision；
- canonical path；
- size / SHA256；
- provenance / producing execution；
- current revision semantics。

---

## 13. Step H：Review / Delivery

Review 僅針對 `(component_id, kind)` 的 latest current revision 做 approval gate；歷史 rejected/rework revision 保留，但不得阻塞已取代的新 approved revision。

Delivery 前至少要求：

- source DWG provenance PASS；
- Blender 3D visual evidence PASS；
- native 3D DWG reopen PASS；
- current artifacts approved；
- 建立 Delivery Revision。

最終 delivery package 至少包含：

```text
source/source.dwg
3d/building.glb
3d/building-3d.dwg
evidence/blender-render.png
evidence/blender-reopen.json
evidence/native-dwg-inspect.json
evidence/native-dwg-validation.json
delivery/website/index.html
```

---

## 14. 案例 0004 完成定義

只有以下全部完成才能標記 `REAL CLOSED`：

- 使用者真實 DWG 已由 OS canonical workspace 接收；
- 全部 consequential work 在 O87 執行；
- raw DWG 真實 open/inspect；
- 真實樓層/構件辨識與 review/materialize；
- 多樓層配準與 Building World Coordinates；
- production GLB；
- Blender 5.2 REAL reopen/render；
- native ACIS Solid3D DWG；
- DwgReader/OpenCAD second reopen + 3DSOLID/layer validation；
- OS Artifact Registry；
- Review current revisions；
- Delivery Revision；
- 最終 delivery package / website。

任何 fixture-only、mock、skip-only、metadata-only 都不得算案例完成。

---

## 15. 當前下一步

1. 在 AI-Engineering-OS 建 `case-0004` O87-only workflow/driver，沿用案例 0003 的 `OpenWorker JobBinding + ProjectKnowledge + OS lifecycle + go-tool dispatch` 正式架構。
2. workflow routing 固定 O87，優先使用專屬 runner label `O87`，並保留 `COMPUTERNAME=DESKTOP-O87PJNR` 二次 fail-closed gate。
3. canonical workspace 建立 `input/source.dwg` upload/materialization contract。
4. 接 `dwg.cad.building-dwg` 及 DWG_todo 既有 CAD operator capabilities。
5. 使用一份使用者真實 `.dwg` 啟動 Case 0004 REAL；第一個產品缺口在哪就修哪個 owning repo。
6. 每完成一批，把 run/job/commit/artifact/SHA256/blocker/next step 更新回本手冊。
