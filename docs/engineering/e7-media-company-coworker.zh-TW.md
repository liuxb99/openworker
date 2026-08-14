# E7 Media / Company Coworker 開發進度

更新日期：2026-08-14

## 目標與固定邊界

E7 讓 OpenWorker 的 Media / Company Coworker 把工作轉成可保存、可交接、可執行、可驗證、可交付的產品流程，但不再造第二套平台。

固定邊界：

- 不新增第二套 Agent loop / Tool Registry / Scheduler / Connector layer / Artifact Registry。
- NativeRuntime 預設；Harness 只允許 explicit opt-in。
- canonical engineering / media authority 固定由 AI-Engineering-OS control plane 與既有 specialist engine 負責。
- send / publish / spend / purchase / commitment 必須保留既有 approval gate。
- Persona 模組只做產品 contract、lineage、handoff 與 result projection，不直接偷跑外部副作用。

## E7.1 — Media / Company built-in personas

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/builtin/media.md`、`company.md`、`tests/test_e7_builtin_personas.py`。

Media Coworker 負責媒體需求、grounding、script/prompt/production plan、specialist handoff、artifact QA 與 delivery package；Company Coworker 負責 research、proposal、project coordination、engineering/media handoff、status、delivery 與 follow-up。

## E7.2 — Declarative Task Package

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/task_package.py`、`tests/test_e7_task_packages.py`。

Contract：`PersonaTaskPackage / WorkStep / PackageKind(media|company) / ActionClass(local|canonical|external)`。

Fail-closed：canonical step 不得把 OpenWorker 當 execution authority；external step 必須 `requires_approval=True`；task package 只描述工作，不直接執行 tool/send/publish/scheduler。

## E7.3 — Persona-facing Product Contract

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/product_contract.py`、`tests/test_e7_product_contract.py`。

產品鏈：

```text
PersonaSession
→ PersonaTaskPackage
→ save to Project Workspace
→ canonical_handoffs()
→ external_approval_intents()
→ EvidenceRef
→ QA
→ delivery-ready envelope
```

Task package 保存：

```text
<ProjectRoot>/.openworker/persona-tasks/<persona>/<session_id>/<package_id>.json
```

canonical handoff 固定 `authority=AI-Engineering-OS`；external action 只保留 approval intent，`execution=not-performed`。Artifact 直接復用 AI-Engineering-OS Artifact Registry 與 `coworker.engineering.digital_thread.EvidenceRef`。

## E7.4 — Canonical Handoff Submission Adapter

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/submission.py`、`tests/test_e7_submission.py`。

`submit_product_plan()` 將 E7.3 plan 建立/顯式復用既有 AI-Engineering-OS canonical Job。Project ID 必須明確；Job reuse 必須 explicit，並驗證 project/persona/session/workspace/task-package lineage。

Job metadata 保存：

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

E7.4 不呼叫 `transition_job / publish_job / connector sender / scheduler create`。`collect_job_artifacts()` 只從 OS 回讀真實 Artifact，再透過既有 `os_artifact_ref()` 形成 evidence。`assess_delivery_readiness()` 要求 QA passed + 真實 artifact + canonical approval 全部成立，且仍固定 `publish_performed=false / external_send_performed=false`。

驗證：main CI `31790725031` 已 `pytest / gui-unit/typecheck / gui-e2e` 全部 success，因此 E7.4 可正式標 `MAIN CI VERIFIED`。

## E7.5 — Canonical Execution / Result Bridge

狀態：`IMPLEMENTED — MAIN CI / WIN11 VERIFICATION IN PROGRESS`

本批新增/修改：

```text
coworker/personas/execution_bridge.py
tests/test_e7_execution_bridge.py
coworker/engineering/tools.py
tests/test_engineering_tools.py
coworker/personas/__init__.py
.github/workflows/e7-media-company-personas-win11.yml
```

### 1. 不新增第二套 executor

E7.5 沒有在 persona 目錄直接呼叫 AI-Engineering-OS private HTTP route，也沒有直接啟 subprocess。它只產生現有 Tool Registry 可執行的 `CanonicalToolCall` descriptor：

```text
openworker.persona-canonical-tool-call/v1
```

Descriptor 固定輸出：

```text
authority = AI-Engineering-OS
requires_approval = true|false
execution = not-performed
```

所以真正執行仍經既有 OpenWorker Tool Registry / approval flow。

### 2. RC-column managed flow 正式進既有 engineering tool facade

原本 `EngineeringOSFlowClient.execute_rc_column_flow()` 已存在，但沒有掛進 `engineering_os_tools()`。

本批新增既有 registry 內的工具：

```text
engineering_execute_rc_column_flow(job_id, column)
```

它委派到：

```text
EngineeringOSFlowClient.execute_rc_column_flow(...)
POST /api/v1/jobs/{job_id}/flows/rc-column
```

Tool metadata：

```text
category = engineering
capabilities = write, engineering, job, flow
requires_approval = true
```

這不是第二套 flow implementation；business workflow 仍由 AI-Engineering-OS authoritative endpoint 負責。

### 3. Persona submission → existing tool invocation

`rc_column_tool_call()` 要求 `PersonaJobSubmission.handoff_capabilities` 包含 `engineering`，然後只建立：

```text
tool_name = engineering_execute_rc_column_flow
arguments.job_id = submission.job_id
arguments.column = caller input
requires_approval = true
```

若 submission 沒有 engineering capability，直接 `UnsupportedCanonicalFlowError`。

### 4. Canonical result snapshot

`read_canonical_result()` 只從既有 control plane 回讀：

```text
get_job(job_id)
list_job_artifacts(job_id)
list_job_reviews(job_id)
approval_status(job_id)
```

並建立：

```text
openworker.persona-canonical-result/v1
```

其中 Job/Artifact identity 直接使用既有 `os_job_ref()` / `os_artifact_ref()`。它會再次核對：

```text
job.id == PersonaJobSubmission.job_id
job.project_id == PersonaJobSubmission.project_id
persona/session/task_package lineage 不衝突
review.job_id 不得跨 Job
approval.approved 必須是真正 boolean
```

任何 evidence/lineage 不一致都 fail closed。

Result snapshot 即使 approved，也固定：

```text
publish_performed = false
external_send_performed = false
```

### 5. Media submit 缺口不偽造

目前 OpenWorker 已有 `ComfyXCLIClient.status/cancel()` 作為既有媒體長任務控制面，但在本 repo 尚未找到已註冊於 canonical Tool Registry 的 ComfyX `submit` tool，也沒有公開的 `EngineeringOSFlowClient.execute_media_*()`。

因此 E7.5 的 `media_submit_tool_call()` 目前刻意：

```text
UnsupportedCanonicalFlowError
```

而不是自行猜 endpoint 或直接 subprocess submit。這是明確的 fail-closed 缺口，不是假完成。

### 6. Regression

`tests/test_e7_execution_bridge.py` 已鎖定：

- RC-column descriptor 必須指向現有 tool facade。
- canonical flow tool 必須保留 approval metadata。
- 非 engineering submission 不可執行 engineering flow。
- media submit 在真實 canonical tool 尚未接入前必須 fail closed。
- canonical result 必須回讀真實 Job/Artifact/Review/approval identity。
- session lineage mismatch、cross-job review、非 boolean approval 必須拒絕。
- result snapshot 永遠不宣稱已 publish/send。

`tests/test_engineering_tools.py` 同步驗證 `engineering_execute_rc_column_flow` 已進同一個既有 Tool Registry，且 `requires_approval=True`。

## CI / Win11 驗證狀態

已確認：

```text
E7.1～E7.3 main CI: 31790204795 → ALL SUCCESS
E7.4 main CI:       31790725031 → ALL SUCCESS
```

E7.4 focused Win11 `31790673063` 在 E7.5 push 前仍停在 queued/pending，沒有 self-hosted Windows runner 接單，因此不能標 Win11 VERIFIED。E7 focused workflow 使用 `cancel-in-progress: true`，E7.5 push 後只以最新包含 `test_e7_execution_bridge.py` 的 run 為準。

## 下一批 E7.6

下一批直接補目前最明確的產品缺口：**Media canonical submit facade**。

目標：

```text
Media PersonaJobSubmission
→ existing ComfyX / AI-Engineering-OS submit surface
→ OpenWorker existing Tool Registry tool
→ approval metadata / NativeRuntime-Harness policy
→ prompt/execution id 回寫 canonical Job lineage
→ existing comfyx.job.status / job.cancel
→ AI-Engineering-OS Artifact Registry
→ E7.5 read_canonical_result()
→ QA / delivery assessment
```

實作原則：先從 ComfyX / AI-Engineering-OS 現有真實 submit API/CLI contract 取得 authoritative schema，再做最薄 adapter；不自行設計另一套 media scheduler、job model 或 artifact registry。
