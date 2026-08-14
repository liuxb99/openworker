# E7 Media / Company Coworker 開發進度

更新日期：2026-08-14

## 目標與固定邊界

E7 讓 OpenWorker 的 Media / Company Coworker 把工作轉成可保存、可交接、可執行、可驗證、可交付的產品流程，但不再造第二套平台。

固定邊界：

- 不新增第二套 Agent loop / Tool Registry / Scheduler / Connector layer / Artifact Registry。
- NativeRuntime 預設；Harness 只允許 explicit opt-in。
- canonical engineering / media Job authority 固定由 AI-Engineering-OS control plane 管理；ComfyX 等 specialist engine 只擁有自己的專業執行契約。
- send / publish / spend / purchase / commitment 必須保留既有 approval gate。
- Persona 模組只做產品 contract、lineage、handoff 與 result projection，不直接偷跑外部副作用。

## E7.1 — Media / Company built-in personas

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/builtin/media.md`、`company.md`、`tests/test_e7_builtin_personas.py`。

## E7.2 — Declarative Task Package

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/task_package.py`、`tests/test_e7_task_packages.py`。

Contract：`PersonaTaskPackage / WorkStep / PackageKind(media|company) / ActionClass(local|canonical|external)`。canonical step 不得把 OpenWorker 當 execution authority；external step 必須 `requires_approval=True`。

## E7.3 — Persona-facing Product Contract

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/product_contract.py`、`tests/test_e7_product_contract.py`。

```text
PersonaSession
→ PersonaTaskPackage
→ Project Workspace
→ canonical_handoffs()
→ external_approval_intents()
→ EvidenceRef
→ QA
→ delivery-ready envelope
```

Artifact 直接復用 AI-Engineering-OS Artifact Registry 與 `coworker.engineering.digital_thread.EvidenceRef`。

## E7.4 — Canonical Handoff Submission Adapter

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

核心：`coworker/personas/submission.py`、`tests/test_e7_submission.py`。

`submit_product_plan()` 建立/顯式復用既有 AI-Engineering-OS canonical Job，保存 persona/session/workspace/task-package/runtime-policy lineage；不呼叫 publish、connector sender 或 scheduler。

Main CI `31790725031`：`pytest / gui-unit/typecheck / gui-e2e` 全部 success。

## E7.5 — Canonical Execution / Result Bridge

狀態：`IMPLEMENTED；MAIN CI REGRESSION 已修；最新整體 CI 隨 E7.6 再驗證；WIN11 FOCUSED GATE PENDING`

核心：

```text
coworker/personas/execution_bridge.py
coworker/engineering/tools.py
tests/test_e7_execution_bridge.py
tests/test_engineering_tools.py
```

E7.5 不新增 executor。Persona 只建立既有 Tool Registry 可執行的 `CanonicalToolCall` descriptor；RC-column 仍委派 AI-Engineering-OS authoritative flow。

`read_canonical_result()` 只回讀 canonical Job/Artifact/Review/approval，並透過既有 `os_job_ref()` / `os_artifact_ref()` 建 evidence。任何 job/project/persona/session/task-package/review identity 衝突都 fail closed；result 永遠不宣稱已 publish/send。

先前 main CI `31791707602` 唯一失敗是舊 `test_engineering_persona_wiring.py` 的固定工具名單漏列 `engineering_execute_rc_column_flow`；實際 pytest 為 `1368 passed / 1 failed / 4 skipped`，GUI jobs success。該 wiring regression 已更新，不是 execution bridge 邏輯故障。

## E7.6 — Authoritative Media Canonical Submit Facade

狀態：`IMPLEMENTED — MAIN CI / WIN11 VERIFICATION IN PROGRESS`

本批新增/修改：

```text
coworker/engineering/media_tools.py
coworker/catalog.py
coworker/personas/execution_bridge.py
tests/test_e7_media_facade.py
tests/test_e7_execution_bridge.py
tests/test_engineering_persona_wiring.py
.github/workflows/e7-media-company-personas-win11.yml
```

### 1. Authoritative submit contract 已確認

直接以 ComfyX repo 現有 `cmd/comfyx-tool/main.go` 為權威來源，不猜 HTTP endpoint、不新增 `comfyx-submit` 假 CLI。

ComfyX 正式協議：

```text
protocol_version = ai-tool-protocol/1.0.0
tool_id          = comfyx.minimax_h3.generate
```

官方 tool 已自行負責：

```text
Desktop-first runtime discovery
→ live capability probe
→ MiniMax H3 canonical prompt build
→ ComfyUI submission
→ wait/poll
→ history
→ artifact extraction
→ prompt_id + artifacts + history
```

五模式由同一 tool 的真實參數決定：無 reference、first frame、last frame、first+last frame、Ref2VA reference assets。OpenWorker 不複製這些 workflow 規則。

### 2. 新增薄協議 adapter：ComfyXToolClient

`coworker.engineering.media_tools.ComfyXToolClient` 只做：

```text
建立 ai-tool-protocol request JSON
→ comfyx-tool execute <request.json>
→ 驗證 protocol_version
→ 驗證 request_id
→ 驗證 tool_id
→ 驗證 status == succeeded
→ 驗證 data.prompt_id / mode / runtime / required_nodes
→ 保留 history / artifacts / warnings
```

允許參數完全按 ComfyX authoritative H3 schema 白名單；未知參數直接拒絕。Media generation facade 明確拒絕 `compile_only=true`，避免把「只編譯驗證」誤報成已生成。

回傳 envelope：

```text
openworker.comfyx-h3-result/v1
authority = ComfyX
prompt_id
mode
runtime
required_nodes
history
artifacts
publish_performed = false
external_send_performed = false
```

這裡的 `authority=ComfyX` 只代表 specialist execution result 的來源；canonical Project/Job/Artifact governance 仍由 AI-Engineering-OS 負責。

### 3. 不新增第二套 Tool Registry

Media persona 原本就使用既有 `engineering_os` catalog capability。本批只把：

```text
engineering_generate_minimax_h3
```

加入 `_engineering_os()` 已有工具集合：

```text
engineering_os_tools()
+ managed_engineering_tools()
+ managed_media_tools()
```

沒有新增 `media_registry`、`media_scheduler`、第二個 agent loop 或 connector layer。

Managed tool metadata：

```text
category = engineering
capabilities = write, engineering, media, video, generation
requires_approval = true
```

生成完成仍不等於 publish/send。

### 4. Persona media submission 現在能產生真實 canonical tool descriptor

E7.5 原先的 `media_submit_tool_call()` 因未確認 authoritative submit surface 而 fail-closed；E7.6 查清 ComfyX contract 後，現在輸出：

```text
tool_name = engineering_generate_minimax_h3
arguments = verified media payload
requires_approval = true
authority = AI-Engineering-OS
execution = not-performed
```

`CanonicalToolCall` 仍只是既有 Tool Registry 的 invocation descriptor，persona 自己沒有直接 subprocess 執行權。

### 5. Regression coverage

`tests/test_e7_media_facade.py` 鎖定：

- request 必須使用 `ai-tool-protocol/1.0.0`。
- tool id 必須為 `comfyx.minimax_h3.generate`。
- prompt_id / mode / runtime / required_nodes / artifacts / history 必須保留。
- unknown argument 在 subprocess 前就 fail closed。
- `compile_only=true` 不可冒充 generation。
- response protocol/request/tool identity mismatch 必須拒絕。
- managed media tool 仍 `requires_approval=True`。
- result 不得宣稱 publish/send。

`tests/test_e7_execution_bridge.py` 已改為要求 Media submission 指向真實 `engineering_generate_minimax_h3` facade；`tests/test_engineering_persona_wiring.py` 也鎖定它與既有 engineering tools 共用同一個 catalog expansion。

### 6. Win11 focused gate

`.github/workflows/e7-media-company-personas-win11.yml` 已加入：

```text
coworker/engineering/media_tools.py
coworker/catalog.py
tests/test_engineering_persona_wiring.py
tests/test_e7_media_facade.py
```

並在 compile / pytest / smoke 三層檢查 Media descriptor、managed tool 與 approval metadata。

## CI / Win11 驗證狀態

截至本次文檔更新：

```text
E7.1～E7.3 main CI: 31790204795 → ALL SUCCESS
E7.4 main CI:       31790725031 → ALL SUCCESS
E7.6 main CI:       31793729770 → IN PROGRESS
E7.6 focused Win11: 31793729801 → QUEUED
```

Focused Win11 若只是 self-hosted runner 未接單，不視為代碼失敗；只在 job 真正執行後依測試 conclusion 判定。

## 下一批 E7.7 — ComfyX Result → Canonical Artifact/Evidence Sync

E7.6 已打通真實 specialist submit facade，但 ComfyX 回傳的 `artifacts/history/prompt_id` 還不能直接取代 AI-Engineering-OS Artifact Registry。

下一批應補最薄的 canonical result sync：

```text
PersonaJobSubmission.job_id
+ ComfyXH3Result(prompt_id/history/artifacts)
→ 驗證真實本地輸出 / checksum / media type
→ existing EngineeringOSClient.register_artifact(...)
→ canonical Job metadata / execution evidence lineage
→ existing list_job_artifacts / reviews / approval
→ E7.5 read_canonical_result()
→ E7.4 assess_delivery_readiness()
```

原則：

- 不新增 Artifact Registry。
- 不把 ComfyX artifact list 當成已完成的 canonical delivery。
- prompt_id 必須綁回既有 PersonaJobSubmission / AI-Engineering-OS Job lineage。
- 真實媒體檔必須非空、格式/校驗值可驗證後才登記。
- publish/send 仍走既有 approval / connector 邊界。
