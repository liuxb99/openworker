# E7 Media / Company Coworker 開發進度

更新日期：2026-08-14

## 目標

E7 的目標不是再造一套 Agent 平台，而是讓 OpenWorker 的 Media Coworker / Company Coworker 可以把使用者工作轉成可保存、可交接、可驗證、可交付的產品流程，同時沿用既有 Runtime、Tool Registry、Scheduler、Connector、AI-Engineering-OS Job/Review/Delivery 與 Artifact Registry。

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

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/builtin/media.md`、`company.md`、`tests/test_e7_builtin_personas.py`。

Media Coworker 負責媒體需求整理、grounding、腳本 / prompt / production plan、專業媒體能力交接、artifact QA 與 delivery package。Company Coworker 負責研究、提案、project coordination、engineering/media handoff、status update、delivery 與 follow-up。兩者都是 persona product surface，不包含第二套 tool/runtime implementation。

## E7.2 — Declarative Task Package

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/task_package.py`、`tests/test_e7_task_packages.py`。

主要 contract：

```text
openworker.persona-task-package/v1
PersonaTaskPackage
WorkStep
PackageKind: media | company
ActionClass: local | canonical | external
```

安全 invariants：canonical step 不得把 OpenWorker 當下游 execution authority；external step 沒有 `requires_approval=True` 直接 fail closed；external send/publish 只有明確 target 才出現在 package；task package 只描述工作，不執行 tool、send、publish 或 scheduler。

## E7.3 — Persona-facing Product Contract

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/product_contract.py`、`tests/test_e7_product_contract.py`。

產品鏈：

```text
Media / Company persona session
→ PersonaTaskPackage
→ save to Project Workspace
→ canonical_handoffs()
→ external_approval_intents()
→ AI-Engineering-OS / specialist execution
→ EvidenceRef
→ QA
→ delivery-ready envelope
```

Task package 保存到：

```text
<ProjectRoot>/.openworker/persona-tasks/<persona>/<session_id>/<package_id>.json
```

`canonical_handoffs()` 固定 `authority = AI-Engineering-OS`，並保留 `runtime_policy = NativeRuntime default; Harness explicit opt-in`。external action 只輸出 approval intent：`requires_approval=true / execution=not-performed`。Artifact/QA 直接復用 `coworker.engineering.digital_thread.EvidenceRef`、AI-Engineering-OS Artifact Registry 與 Workspace Artifact Publisher。

Fail-closed：`delivery_ready=True` 必須先 QA passed；QA passed 必須至少有一個真實 artifact reference；Artifact evidence 必須有 checksum lineage；delivery envelope 固定 `external_delivery_performed=false`。

## E7.4 — Canonical Handoff Submission Adapter

狀態：`IMPLEMENTED — CI / WIN11 VERIFICATION IN PROGRESS`

本批新增：

```text
coworker/personas/submission.py
tests/test_e7_submission.py
coworker/personas/__init__.py  公開 E7.4 API
E7 focused Win11 workflow 擴充 E7.4 gate
```

### 1. PersonaProductPlan → canonical Job

`submit_product_plan()` 現在把 E7.3 `PersonaProductPlan` 提交到既有 `EngineeringOSClient`。

固定規則：

```text
Project ID 必須明確提供，不猜測
沒有 existing_job_id → client.create_job(...)
有 existing_job_id → client.get_job(...) + identity/metadata 驗證後才 reuse
canonical authority = AI-Engineering-OS
```

新建 Job 會附上 lineage metadata：

```text
source = openworker-e7-persona
persona
persona_session_id
workspace_id
task_package_path
product_plan_schema
handoff_capabilities
runtime_policy = NativeRuntime default; Harness explicit opt-in
```

expected deliverables 直接由既有 canonical handoff 的 `expected_artifacts` 彙整，不建立第二份 deliverable schema。

### 2. Job reuse 必須 explicit + fail closed

E7.4 不自動搜尋「看起來像同一個」Job。只有呼叫者明確提供 `existing_job_id` 才 reuse，而且必須驗證：

```text
job.project_id == requested project_id
persona metadata 不衝突
persona_session_id 不衝突
workspace_id 不衝突
task_package_path 不衝突
```

任何 identity/lineage mismatch 都拋 `SubmissionContractError`，不靜默改綁。

### 3. Submission 不等於執行 / 發布

`submit_product_plan()` 只建立或復用 canonical Job。它刻意不呼叫：

```text
transition_job
publish_job
connector sender
scheduler create
```

所以 E7.4 不會在 persona 層形成第二套工程 executor。後續專業 flow 仍由 AI-Engineering-OS 現有 tool/job layer 與 specialist engine 執行；需要 Harness 時仍必須 explicit opt-in。

### 4. 真實 Artifact → Existing EvidenceRef

`collect_job_artifacts()` 只讀：

```text
EngineeringOSClient.list_job_artifacts(job_id)
```

然後使用既有：

```text
coworker.engineering.digital_thread.os_artifact_ref(...)
```

轉成 EvidenceRef。缺 id/checksum/uri/media_type 等 canonical artifact 必要欄位時 fail closed，不生成假 artifact identity。

### 5. QA + canonical approval → delivery readiness

`assess_delivery_readiness()` 合併兩個獨立條件：

```text
Persona QA
+
AI-Engineering-OS approval_status(job_id)
```

只有以下全部成立才 `delivery_ready=True`：

```text
qa_passed == true
至少一個真實 canonical ArtifactRef
approval_status.approved == true
```

即使 ready，也只輸出：

```text
openworker.persona-delivery-assessment/v1
publish_performed = false
external_send_performed = false
```

因此「已通過 QA / 已被 canonical review 批准 / 已準備交付」不會被誤表示成「已發送或已發布」。真正 publish/send 仍走既有 approval + connector / AI-Engineering-OS publish gate。

### 6. E7.4 regression

`tests/test_e7_submission.py` 已鎖定：

- 新建 canonical Job 必須保留 persona/session/workspace/task-package lineage。
- Media handoff capabilities 必須進 canonical Job metadata。
- 沒有 canonical handoff 的純 local Company package 不可提交成假的 engineering Job。
- reuse 必須 explicit，且不同 project / session lineage 必須拒絕。
- Artifact 必須從 AI-Engineering-OS 真實 artifact payload 轉成既有 EvidenceRef。
- QA passed 但 canonical approval 未過 → `delivery_ready=false`。
- QA + canonical approval 都過 → 才 `delivery_ready=true`。
- QA passed 但零 artifact → fail closed。
- E7.4 永遠不呼叫 `publish_job`。

## 驗證證據

上一批 E7.1～E7.3 所在 main CI：

```text
Run: 31790204795
pytest:  success
gui-unit/typecheck: success
gui-e2e: success
```

因此 E7.1～E7.3 現可標 `MAIN CI VERIFIED`。

Focused Win11：舊 run `31790166327` 在 E7.4 push 前仍長時間 `queued`，沒有被 self-hosted Windows runner 接單，因此不能算 VERIFIED。E7 workflow 使用 `cancel-in-progress: true`；後續 E7.4 push 會讓舊 queued run 被新 run 取代。最終只以最新包含 `tests/test_e7_submission.py` 的 focused Win11 run conclusion 作 E7.4 Win11 證據。

## 下一批 E7.5

E7.4 全綠後，下一批應做「canonical execution/result bridge」，但仍不建立第二套 executor：

```text
PersonaJobSubmission
→ 使用既有 AI-Engineering-OS tool/facade 選擇 canonical flow
→ existing runtime job/status/cancel
→ specialist engine execution
→ read canonical Job/Artifact/Review state
→ EvidenceRef / QA / delivery assessment
```

E7.5 重點是把「已建立 canonical Job」接到既有 tool facade 的真正 flow invocation 與 job status，而不是在 persona 模組自己實作工程/媒體執行。外部 send/publish 仍留在既有 approval gate。
