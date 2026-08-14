# E7 Media / Company Coworker 開發進度

更新日期：2026-08-14

## 目標

E7 的目標不是再造一套 Agent 平台，而是讓 OpenWorker 的 Media Coworker / Company Coworker 可以把使用者工作轉成可保存、可交接、可驗證、可交付的產品流程，同時沿用既有 Runtime、Tool Registry、Scheduler、Connector 與 Artifact Registry。

固定邊界：

- 不新增第二套 Agent loop。
- 不新增第二套 Tool Registry。
- 不新增第二套 Scheduler。
- 不新增第二套 Connector layer。
- 不新增第二套 Artifact Registry。
- NativeRuntime 仍是預設 runtime。
- Harness 仍是 explicit opt-in。
- 發送、發布、付款、購買、對外承諾等 consequential action 必須保留 approval gate。
- 工程與媒體專業執行必須交給 AI-Engineering-OS / specialist engine，不讓 persona 自稱 canonical execution authority。

## E7.1 — Media / Company built-in personas

狀態：`IMPLEMENTED / PYTHON VERIFIED；WIN11 FOCUSED GATE PENDING`

已建立：

- `coworker/personas/builtin/media.md`
- `coworker/personas/builtin/company.md`
- `tests/test_e7_builtin_personas.py`

Media Coworker 負責媒體任務的需求整理、資料 grounding、腳本 / prompt / production plan、專業媒體能力交接、artifact QA 與 delivery package。

Company Coworker 負責研究、提案、project coordination、engineering/media handoff、status update、delivery 與 follow-up。

兩者都是 persona product surface，不包含第二套 tool/runtime implementation。

## E7.2 — Declarative Task Package

狀態：`IMPLEMENTED — CI / WIN11 VERIFICATION IN PROGRESS`

核心檔案：

- `coworker/personas/task_package.py`
- `tests/test_e7_task_packages.py`

主要 contract：

```text
openworker.persona-task-package/v1
PersonaTaskPackage
WorkStep
PackageKind: media | company
ActionClass: local | canonical | external
```

安全 invariants：

- canonical step 不得把 OpenWorker 當下游 execution authority。
- external step 沒有 `requires_approval=True` 直接 fail closed。
- external send/publish 只有在使用者明確提供 target 時才出現在 package。
- task package 只描述工作，不直接執行 tool、send、publish 或 scheduler。

## E7.3 — Persona-facing Product Contract

狀態：`IMPLEMENTED — VERIFICATION IN PROGRESS`

本批新增：

- `coworker/personas/product_contract.py`
- `tests/test_e7_product_contract.py`
- `coworker/personas/__init__.py` 公開 product contract API
- E7 focused Win11 workflow 擴充 E7.3 gate

### 1. Persona Session

`PersonaSession` 將 Media / Company persona 與既有 session / Project Workspace identity 綁定：

```text
persona
session_id
workspace_id
```

產品入口接受 `media` / `company` 字串並正規化成既有 `PackageKind`。session / workspace / package ID 僅接受安全 workspace identifier，避免 path traversal。

### 2. Task Package 保存到 Project Workspace

`save_task_package()` 將 declarative package 保存到：

```text
<ProjectRoot>/.openworker/persona-tasks/<persona>/<session_id>/<package_id>.json
```

schema：

```text
openworker.persona-workspace-task/v1
```

寫入採同目錄 temporary file + replace；保存動作不會 enqueue job、不會執行 agent、不會呼叫外部 connector。

### 3. Canonical Handoff

`canonical_handoffs()` 將所有 `ActionClass.CANONICAL` step 映射成：

```text
openworker.persona-canonical-handoff/v1
```

固定：

```text
authority = AI-Engineering-OS
runtime_policy = NativeRuntime default; Harness explicit opt-in
execution = descriptor-only
```

其中：

- Company engineering handoff → `AI-Engineering-OS`
- Company media handoff → `AI-Engineering-OS` control plane → specialist media engine
- Media produce → `AI-Engineering-OS` control plane → specialist media engine

`source_authority` 保留原 task package 所描述的 specialist authority，方便后續 routing / audit，但 canonical control-plane authority 不改。

### 4. External Approval Intent

`external_approval_intents()` 不執行 send / publish，只把 external step 轉成 approval metadata：

```text
requires_approval = true
execution = not-performed
```

真正 send / publish 仍必須走現有 connector + PermissionEngine / approval flow。

### 5. ArtifactRef / QA / Delivery

E7.3 不新增 Artifact Registry，直接復用：

```text
coworker.engineering.digital_thread.EvidenceRef
AI-Engineering-OS Artifact Registry
Workspace Artifact Publisher
```

`DeliveryEvidence` schema：

```text
openworker.persona-delivery-evidence/v1
```

Fail-closed 規則：

- `delivery_ready=True` 必須先 `QAStatus.PASSED`。
- QA passed 必須至少有一個真實 artifact reference。
- `EvidenceKind.ARTIFACT` 必須有 checksum lineage。
- delivery envelope 永遠不把「準備好交付」偽裝成「已對外發送」，因此輸出固定 `external_delivery_performed=false`。

### 6. Product Plan

`build_product_plan()` 完成：

```text
Media / Company persona session
→ create PersonaTaskPackage
→ save to Project Workspace
→ canonical_handoffs()
→ external_approval_intents()
→ downstream AI-Engineering-OS / specialist execution
→ EvidenceRef
→ QA
→ delivery-ready envelope
```

schema：

```text
openworker.persona-product-plan/v1
```

bindings 明確指向既有系統：

```text
scheduler  -> coworker.automation
connectors -> coworker.connectors
artifacts  -> AI-Engineering-OS Artifact Registry / Workspace Artifact Publisher
```

所以 E7.3 沒有新增第二套 scheduler / connector / artifact registry。

## 驗證

E7 focused Win11 workflow 現在會同時執行：

```text
tests/test_e7_builtin_personas.py
tests/test_e7_task_packages.py
tests/test_e7_product_contract.py
```

並額外 smoke：

- Media / Company PersonaRegistry 可載入。
- `PersonaSession(persona='media', ...)` 可正規化。
- Media canonical handoff authority 必須是 `AI-Engineering-OS`。
- task-package / product-contract modules 可在 Win11 安裝後 import。

先前 focused run `31789585432` 長時間停在 queued，不算 VERIFIED。後續 push 因 workflow 的 `cancel-in-progress: true` 可能取消舊 run；只以最新 E7 focused run 的實際 conclusion 作最終證據。

容器側直接 clone GitHub 因執行環境 DNS 無法解析 `github.com`，因此沒有把該失敗誤記為 test failure 或 verification evidence。

## 下一批 E7.4

E7.3 contract 全綠後，下一批應接「canonical handoff submission adapter」，但仍只組合既有 `EngineeringOSClient`：

```text
PersonaProductPlan
→ resolve existing Project
→ create/reuse canonical AI-Engineering-OS Job according to product policy
→ attach task-package path / persona/session metadata
→ execute selected canonical flow through existing tools
→ read real artifacts
→ convert with existing EvidenceRef helpers
→ QA / review / delivery readiness
```

E7.4 不直接做 external send/publish；即使 downstream delivery 已 ready，對外動作仍需現有 approval / connector gate。
