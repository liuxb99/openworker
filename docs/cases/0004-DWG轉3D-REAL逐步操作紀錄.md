# 案例 0004：DWG → 3D REAL 逐步操作紀錄 / 未來手冊原稿

> 案例主責：`liuxb99/openworker`  
> OS 治理：`liuxb99/AI-Engineering-OS`  
> 工具資訊平面：`liuxb99/go-tool-runtime`  
> CAD owning repo：`liuxb99/DWG_todo`  
> 固定 REAL 主機：`DESKTOP-O87PJNR`（O87）  
> 開始時間：2026-08-16（Asia/Taipei）  
> 狀態：`IMPLEMENTING / REAL USER DWG RECEIVED / TOOL-GAP-DRIVEN CLOSURE`

---

## 0. 這份文件怎麼使用

這不是只寫「做到哪裡」的摘要，而是案例完成後要整理成正式操作手冊的原始紀錄。

**從現在開始，每一步都必須記：**

```text
Step / 時間
目的
OpenWorker 當下已知狀態
OpenWorker 為什麼選這個下一步
go-tool-runtime 查詢內容
查到的 capability / owning repo / workflow / ref
normalized inputs
workspace_root / assigned_host
GitHub Action run id / job id / runner
產品輸出 physical path
size / SHA256 / schema / revision
OpenWorker 對輸出的判讀
驗收 PASS / FAIL / BLOCKED
若 FAIL：真正 owning repo / root cause / 修復 commit
修復後同一路徑 rerun evidence
下一步
```

不得只記「成功」；也不得把 fixture、skip、metadata-only、artifact upload 成功當產品成功。

案例原則：

```text
OpenWorker 真正做專案
→ 不知道工具就查 go-tool-runtime
→ 使用 owning repo 正式 Action
→ 看真實輸出再決定下一步
→ 工具有缺口就修真正 owning repo
→ 回同一份真 DWG / 同一 workspace / 同一 O87 路徑重跑
→ 直到 OS Artifact / Review / Delivery 閉環
```

---

# Part A — 真實輸入接收

## Step A-001｜2026-08-16｜使用者提供兩份真實 DWG

### 使用者輸入

本次對話收到：

```text
378建照圖(核准版) (1)(1).dwg
S1-1140926(1).dwg
```

這兩份均為使用者真實上傳，不是 repository fixture。

### Physical input gate

#### Input 1

```text
filename: 378建照圖(核准版) (1)(1).dwg
DWG header: AC1018
size: 1,435,765 bytes
SHA256: 1ce944040d1001cd06ef15c7f8fc815bcf68cf196c3bffc22de61cd8f15d0fd6
basic gate: PASS
```

`AC1018` 對應較舊 DWG 格式。保留為第二份 REAL compatibility / regression case，不與主案例 geometry 混合。

#### Input 2 — Case 0004 主輸入

```text
filename: S1-1140926(1).dwg
DWG header: AC1032
size: 1,385,583 bytes
SHA256: aaadbd84e8a5b2e1b0b8f54c16901a69085c7501aeec602929fd994f3192f5b6
basic gate: PASS
role: PRIMARY REAL SOURCE
```

選它作主案例的原因：

1. 是真實使用者檔案；
2. header 為 `AC1032`，與 Case 0004 native Building 3D DWG 最終 delivery target 一致；
3. 先用一份 source 完整閉環，避免兩份圖的 geometry / story / provenance 被混用；
4. 第一份保留作閉環後的第二檔案相容性回歸。

### Canonical Case 0004 目標位置

```text
workspace_root = D:\AI-Work\jobs\0004-DWG-TO-3D
assigned_host  = DESKTOP-O87PJNR
canonical source = D:\AI-Work\jobs\0004-DWG-TO-3D\input\source.dwg
```

此時只代表 ChatGPT 會話已收到 binary；**尚未宣稱檔案已 materialize 到 O87**。

### Step 結果

```text
REAL USER INPUT RECEIVED = PASS
O87 CANONICAL MATERIALIZATION = PENDING
```

---

# Part B — OpenWorker 先查 go tool，不靠模型記憶

## Step B-001｜查詢 go-tool-runtime 使用規範

OpenWorker/操作者先讀 `go-tool-runtime/SKILL.md`，確認正式操作模式：

```text
LLM / OpenWorker
→ query go-tool-runtime
→ obtain capability / owning repo / workflow / inputs / runner / evidence
→ dispatch owning repo Action
→ self-hosted tool executes REAL work
→ inspect run/jobs/logs/physical artifacts
→ validate
```

重要邊界：go-tool-runtime 是資訊/Action guidance plane，不取代 `DWG_todo` 做 CAD。

### 判讀

Case 0004 不應建立一個硬編碼巨型 driver 幫模型假裝做完所有 CAD 判斷；OpenWorker 應逐步查工具、看結果、再決定下一步。

---

## Step B-002｜查 `dwg.cad.execute` 主入口

查到：

```text
repo: liuxb99/DWG_todo
workflow: .github/workflows/operator-dwg-cad.yml
ref: master
inputs:
  method
  params_json
  workspace_root
  assigned_host
```

舊 `0003_dwg.cad.execute_ZH.md` 文件只列到 generic：

```text
cad.build_3d
cad.export_glb
cad.validate_3d
```

但後續 capability guides / `config.yaml` 已存在：

```text
cad.design_story_structure
cad.materialize_story_structure
cad.set_story_anchor
cad.list_story_anchors
cad.register_stories
cad.validate_story_registration
cad.list_story_registrations
cad.build_building_3d
cad.export_building_glb
cad.validate_building_3d
cad.build_building_dwg
cad.export_building_dwg
cad.validate_building_dwg
```

### 發現缺口 GTR-0001

```text
類型: AI-facing information drift
owning repo: liuxb99/go-tool-runtime
影響: OpenWorker 查主入口手冊時會得到過期 method family，可能錯過正式 Building 3D / native DWG 工具
```

這不是 DWG_todo 業務缺口，而是 go tool 資訊平面漂移。

---

## Step B-003｜逐項核對 DWG capability guides

已核對：

```text
0004 dwg.cad.3d
0005 dwg.cad.visual-search
0006 dwg.cad.story-design
0007 dwg.cad.story-materialize
0008 dwg.cad.story-registration
0009 dwg.cad.building-3d
0010 dwg.cad.building-dwg
```

其中完整主線已明確：

```text
cad.open_dwg
→ get_model_extents
→ render_png / candidate regions / query_bounds
→ set_story_region
→ design_story_structure
→ human/LLM visual review design.png
→ materialize_story_structure approved=true
→ set_story_anchor
→ register_stories
→ validate_story_registration
→ build/export/validate Building GLB
→ Blender REAL reopen/render
→ export/validate native Building DWG
```

### config.yaml authority

`go-tool-runtime/config.yaml` 的 `dwg.cad.execute` capability registry 已包含完整 family，並明確把：

```text
workspace_root
assigned_host
```

列為 canonical required inputs。

所以本次 root cause 是「guide 漂移」，不是 registry 缺能力。

---

## Step B-004｜修復 GTR-0001

修復 repo：

```text
liuxb99/go-tool-runtime
branch: main
```

修復內容：

- 把 `0003 dwg.cad.execute` 主入口更新成完整 method family；
- 明確指到 0004～0010 method-specific guides；
- 加入 OpenWorker 標準專案循環；
- 明確禁止跳過 Story review / registration；
- 加入 Building GLB / Blender / native ACIS Solid3D DWG evidence contract；
- 明確要求工具/參數不確定時重新查 go tool，不靠模型記憶猜。

修復 commit：

```text
c8e0f59576d1d722f973e6202528761e9ef7e7c7
```

### Step 結果

```text
GTR-0001 = FIXED
```

後續仍需 Win11 / runtime query gate 驗證此 commit 被實際 runtime 讀到；不能只因 Markdown commit 存在就宣稱 runtime LIVE 已更新。

---

# Part C — 真實檔案進 O87 workspace

## Step C-001｜確認目前缺口

ChatGPT 會話已持有真實 DWG binary，但 Case 0004 的權威 source 必須在：

```text
D:\AI-Work\jobs\0004-DWG-TO-3D\input\source.dwg
```

而且必須由 OS/OpenWorker 建立：

```text
Project / Job
JobBinding
workspace_root
assigned_host=DESKTOP-O87PJNR
immutable source provenance
```

目前尚未找到已證明可將「外部使用者上傳 binary」安全 materialize 到 assigned O87 canonical workspace 的正式 OpenWorker/OS intake capability。

### 目前狀態

```text
BLOCKER: OW/OS INPUT MATERIALIZATION CONTRACT NOT YET VERIFIED
```

這是下一個要查清楚的工具/平台缺口。若現有能力存在就使用；若不存在，應補在真正擁有 input/workspace lifecycle 的 OpenWorker/AI-Engineering-OS，而不是塞進 DWG_todo。

---

# Part D — 後續每一個 REAL Step 的固定紀錄模板

以下模板每跑一個工具就追加一節，不覆蓋歷史。

## Step X-XXX｜<時間>｜<目的>

### OpenWorker 當下狀態

```text
stage:
accepted evidence:
blocked evidence:
current revision:
next_action_before_query:
```

### go-tool 查詢

```text
query:
capability:
repo:
workflow:
ref:
method:
canonical params:
success criteria:
```

### Dispatch

```text
workspace_root:
assigned_host:
normalized inputs:
run_id:
job_id:
runner:
runner COMPUTERNAME:
```

### Physical outputs

```text
path:
size:
SHA256:
schema/version:
revision:
```

### OpenWorker 判讀

```text
what was observed:
why accepted/rejected:
```

### 結果

```text
PASS / FAIL / BLOCKED
```

### 若 FAIL

```text
root cause:
owning repo:
fix commit:
rerun id:
```

### 下一步

```text
...
```

---

# 最終閉環清單

只有下列全部變成實際有 evidence 的 PASS，案例 0004 才能標 `REAL CLOSED`：

```text
[PASS] 使用者真 DWG received + SHA256
[ ] OS Project / Job / workspace / JobBinding
[ ] source.dwg materialized on O87 + hash equals uploaded source
[ ] go-tool runtime query returns current full DWG tool family
[ ] cad.open_dwg REAL
[ ] raw Model Space overview PNG
[ ] candidate regions / repeated visual windows
[ ] confirmed real Story Regions
[ ] query_bounds real handles/geometry
[ ] confirmed real column handles
[ ] real Story Design JSON/PNG
[ ] OpenWorker visual review decision recorded
[ ] approved materialization
[ ] anchors selected from real evidence
[ ] story registration + residual validation
[ ] Building World Coordinates
[ ] production building.glb
[ ] Blender 5.2 REAL reopen
[ ] Blender REAL render PNG
[ ] native AC1032 ACIS Solid3D building-3d.dwg
[ ] OpenCAD/DwgReader reopen
[ ] 3DSOLID/layer count validation
[ ] second validate/reopen
[ ] OS Artifact Registry current revisions
[ ] Review approval
[ ] Delivery Revision
[ ] final delivery package / website
```

任何一格如果只能以 fixture/mock/skip/metadata 佐證，仍維持未完成。
