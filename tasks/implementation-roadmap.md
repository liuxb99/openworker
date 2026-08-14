# OpenWorker 工程版獨立分段開發 Roadmap

更新日期：2026-08-14

## 專案定位

OpenWorker 工程版是 AI 工程顧問公司的 AI 員工與自然語言操作層；AI-Engineering-OS 保持 Project / Job / Workflow / Artifact / Review / Delivery lifecycle 權威，專業 Engine 保持工程算法權威。

## 目前完成度

- E0：`IMPLEMENTED`
- E1 Capability Registry / Readiness：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E2 AI-Engineering-OS Bridge：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E3 Tool Facade + Persona Wiring：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E4 Direct Specialist Adapters：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E5 Digital Thread / Provenance：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6 RC Column Golden Job：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.1 Lifecycle Closure：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.2 Review / Approval / Delivery：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.3 OS-managed Calculation + Drawing + BIM RC Flow：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.4 Public RC Flow API + E2E Verification Harness：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- H0 OpenWorker × DeepSeek Harness 架構研究/詳細設計：`IMPLEMENTED`
- H1 AgentRuntime seam / NativeRuntime：`VERIFIED — WIN11 LOCAL ACTION`
- H2 Harness integration skeleton / ACP-first contract：`VERIFIED — WIN11 LOCAL ACTION`
- H3 DeepSeekHarnessRuntime sidecar adapter：`VERIFIED — OFFICIAL ACP WIN11 LOCAL ACTION`
- H4 Tool / Permission / Approval bridge：`VERIFIED — WIN11 BRIDGE CONTRACT；H6 CONTEXT PRODUCER IMPLEMENTED`
- H5 Session / Resume bridge：`IMPLEMENTED — SESSION OWNERSHIP BOUNDARY；COMBINED REGRESSION PASS`
- H6 AI-Engineering-OS dynamic tools：`IMPLEMENTED — DYNAMIC TOOL GATEWAY；COMBINED REGRESSION PASS`
- H6.1 Harness Cordis tool adapter + context ingress：`IMPLEMENTED — WINDOWS FILE-URL FIX INCLUDED；OFFICIAL GATE RUNNING`
- H6.2 Official Harness consequential-tool Golden E2E：`IMPLEMENTED — WINDOWS FILE-URL FIX INCLUDED；OFFICIAL GATE RUNNING`
- H7 Runtime jobs / interrupt mapping：`IMPLEMENTED — MANAGED JOB/CANCEL REGRESSION PASS；WAITING FOR OFFICIAL WIN11 GATE`
- H8 RC Golden Job Native vs Harness A/B：`IMPLEMENTED — DETERMINISTIC VERIFY CLI/TESTS；REAL SAME-MACHINE EVIDENCE OPTIONAL INPUT PENDING`
- H9 ComfyX long-running job validation：`IMPLEMENTED — LONG-JOB VERIFY CLI/TESTS；REAL GPU JOB EVIDENCE OPTIONAL INPUT PENDING`
- H10 Desktop packaging：`IMPLEMENTED — PACKAGED HARNESS CAPABILITY/LAUNCH CONTRACT；WAITING FOR OFFICIAL WIN11 GATE`
- H11 Default-runtime decision：`IMPLEMENTED — DEFAULT POLICY + PROJECT WORKSPACE HOST；WAITING FOR OFFICIAL WIN11 GATE`
- Project Workspace Bootstrap / one-command Engineering Host：`IMPLEMENTED — FOCUSED CONTRACT PASS；OFFICIAL WIN11 GATE ADDED`
- E7 Media / Company Coworker：`NOT_STARTED`

## H0-H11 主線權責

```text
OpenWorker Product Layer
        ↓
AgentRuntime seam
   ├─ NativeRuntime → existing TurnEngine
   └─ EngineeringHarnessRuntime → ManagedDeepSeekHarnessRuntime
        ↓
OpenWorker Tool / Permission Gateway
        ↓
go-tool-runtime information/context authority
        ↓
AI-Engineering-OS canonical agent API
        ↓
Design Forge / EngSketch / BIM / Bridge / Terrain / ComfyX / ...
```

固定原則：

1. OpenWorker 是產品/員工層：UX、connectors、scheduler、memory、approval、finished-work delivery。
2. DeepSeek Harness 是可替換 agent runtime，不是工程 schema authority。
3. go-tool-runtime 是 Project Workspace 的 Information / Context Authority；OpenWorker 不自行掃磁碟猜工具或環境。
4. AI-Engineering-OS 是工程 Tool/Recipe/Job/Artifact/Review/Digital Thread authority。
5. 不把 Harness 塞進 ProviderClient；它擁有 agent loop/session/jobs/runtime lifecycle。
6. NativeRuntime 不提前刪除，直到 H8/H9 真實 A/B 完成。
7. PermissionEngine 仍由 OpenWorker 掌權；publish/mutate 同時受 OpenWorker approval 與 AI-Engineering-OS allow_* safety gate 保護。
8. 不修改 ACP wire 來偷塞 OpenWorker 私有欄位；缺口用正式 Cordis/plugin seam 補。

## Project Workspace / one-command Host

本批已把「使用者只給一個 cwd」正式接進 Harness 主線，而不是另造 agent loop。

```text
cwd / ProjectRoot
→ go-tool-runtime /agent/start
→ AgentInformationPack + authority prompt
→ AI-Engineering-OS Project deterministic reuse
→ 每次 Host 執行建立新 Job
→ dynamic canonical tool discovery
→ OpenWorker PermissionBridge
→ ManagedDeepSeekHarnessRuntime
→ Workspace Artifact Publisher
→ deliverables / reports / evidence
```

主要檔案/測試：

```text
coworker/runtimes/tool_runtime_bootstrap.py
coworker/runtimes/engineering_harness_bootstrap.py
coworker/runtimes/engineering_scope.py
coworker/runtimes/engineering_host.py
coworker/runtimes/engineering_launch.py
tests/runtimes/test_tool_runtime_bootstrap.py
tests/runtimes/test_engineering_harness_bootstrap.py
tests/runtimes/test_engineering_scope.py
tests/runtimes/test_engineering_host.py
tests/runtimes/test_engineering_launch.py
```

安全/責任邊界：

- `ToolRuntimeBootstrapClient` 必須驗證 workspace identity 與 `information_authority=go-tool-runtime` / `execution_authority=AI-Engineering-OS` markers；不符就 fail closed。
- Project 使用 workspace identity deterministic reuse；Job 每次 Host 執行新建，避免 lineage 混線。
- packaged desktop 優先使用 H10 明確 Harness launch capability；若明確 configured command 壞掉則 fail closed；只有未配置 packaged command 時才允許 development fallback。
- Agent 不需要知道 Node/Harness、AI-Engineering-OS 或專業 Engine 的實際安裝路徑。

Focused contract 證據：

```text
OpenWorker run: 31775667217
focused-contract job: completed / success
涵蓋：Workspace information authority、managed Harness governance、H8-H11 non-regression、CLI import smoke
self-hosted Win11 job: waiting for runner
```

AI-Engineering-OS 已把上述 Workspace regression 正式加入 `OpenWorker Harness H3-H11 Official Win11`；最新 official gate 會以真正 pinned OpenWorker H11 product SHA 驗證，不再依賴 frozen verification branch。

## H3 已驗證

最終 Win11 證據：

```text
Run: 31771872273
DeepSeek Harness: 47f943859bef60e4160492346772ded9b24f765a
conclusion: success
```

已通過 deterministic runtime regression、H2 TypeScript contract、exact upstream pin、官方 Harness workspace install，以及：

```text
OpenWorker Python AcpProcessClient
→ official dsh ACP subprocess
→ initialize
→ session/new
```

## H4 權限治理

安全鏈：

```text
Harness tool call id
→ OpenWorker-owned HarnessToolContextRegistry
→ ACP session/request_permission
→ HarnessPermissionBridge
→ PermissionEngine
→ existing approver UX
→ allow-once / reject-once / cancelled
```

官方 ACP permission request 沒有完整 tool name/arguments，因此缺 context 一律 fail closed。

## H5 Session Ownership

```text
OpenWorker ConversationStore = durable product source of truth
Harness ACP session          = connection/process-local runtime context
```

Pinned ACP 尚無 load/list/resume/delete/fork，因此禁止用 prompt replay 假裝 durable resume。H5 tests 已隨 combined regression 通過；最終 VERIFIED 等 official H3-H11 Win11 gate 收斂後統一記錄。

## H6 Dynamic Engineering Tools

不複製 OS schema，直接動態使用：

```text
GET /api/v1/ai/tools/mcp
→ exposed MCP-safe name + raw inputSchema
→ annotations.canonical_tool_id / side_effect / job scope
→ HarnessEngineeringToolGateway
→ HarnessToolContextRegistry
→ H4 permission gate
→ POST /api/v1/ai/tools/{canonical_id}/invoke
```

主要檔案：

```text
coworker/runtimes/harness_engineering_tools.py
tests/runtimes/test_harness_engineering_tools.py
docs/engineering/deepseek-harness-h6-progress.zh-TW.md
```

## H6.1 / H6.2 Windows Cordis 修正

官方 Cordis plugin 的 `name` 最終交給 Node ESM loader。Windows `C:/...` 會被當成未知 `c:` URL scheme，因此 plugin module 必須使用 `Path.resolve().as_uri()` 形成 `file:///C:/...`。

最新工程分支：

```text
engineering-h11-workspace-bootstrap
OpenWorker HEAD: 7dbe94de654c2b761d8d64dea5025ea38aef2092
51352c5b...：official plugin smoke 改 file URL
7dbe94de...：H6.2 deterministic E2E config 同步改 file URL
```

這兩個修正都保留既有 Cordis/plugin authority，不修改 DeepSeek Harness upstream。

## H7 Runtime Jobs / Interrupt

已完成 managed Harness runtime job lifecycle 與 cancellation mapping：

```text
Harness turn
→ OpenWorker runtime job identity
→ status/progress
→ request_interrupt
→ ACP/session cancellation first
→ AI-Engineering-OS job cancellation when scoped
→ terminal state
```

H7 不是第二套 OS Job Registry；AI-Engineering-OS Job 仍是工程 execution identity，OpenWorker runtime job 只服務 UI/agent runtime lifecycle。

## H8 / H9 Verification

H8 已具備 NativeRuntime vs HarnessRuntime RC Golden compare CLI/tests；H9 已具備 ComfyX long-running job / non-empty MP4 evidence verifier。正式 workflow 將真實 project/job IDs 設為 `workflow_dispatch` optional inputs；沒有 supplied IDs 時不假造 REAL evidence。

因此目前正確狀態是「code implemented，deterministic contracts ready；REAL same-machine/GPU evidence 仍需獨立 supplied job」。

## H10 / H11

H10 已完成 packaged Harness capability / desktop resource contract。H11 已完成 runtime default policy 與 Project Workspace Engineering Host composition。one-command CLI 優先採 packaged capability，避免把 Node/Harness path 暴露給 Agent。

## 最新官方 Win11 Gate

AI-Engineering-OS workflow：

```text
.github/workflows/openworker-harness-h3-official-win11.yml
```

已正式增加：

```text
Project Workspace bootstrap and one-command host regressions
```

同一條 official gate 現在必須同時通過：

```text
H1-H7 runtime regressions
Project Workspace bootstrap / scope / host / launch
H6.2 managed RC non-regression
H8-H11 packaging/default policy
H2 TypeScript contracts
pinned official DeepSeek Harness
ACP smoke
Cordis plugin smoke
H6.2 deterministic official tool Golden E2E
```

最新 AI-Engineering-OS run：`31781354830`，目前等待 self-hosted Win11 runner。只有這條最新 official gate 全綠，才把 H5-H7/H10-H11 由 IMPLEMENTED 升成 VERIFIED。

## 下一批

1. 追 `31781354830` 到 Win11 runner 接單；有 failure 就沿真實 log 修，不繞過。
2. official gate 全綠後，校正 H5/H6.1/H6.2/H7/H10/H11 為 VERIFIED，保留 H8/H9 REAL hardware evidence 與 deterministic code verification 的區別。
3. 把 Project Workspace contract 回寫 AI-Engineering-OS：`AGENTS.md` 是唯一 tiny bootstrap usage guide；動態 information 來自 go-tool-runtime，不在專案內複製 tool registry。
4. 接 E7 前先跑一次真正 `openworker-engineering` 從 ProjectRoot 啟動、透過 Workspace Artifact Publisher 交付成果的 product-level smoke。
