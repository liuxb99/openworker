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
- H5 Session / Resume bridge：`IMPLEMENTED — SESSION OWNERSHIP BOUNDARY；COMBINED WIN11 REGRESSION PASS`
- H6 AI-Engineering-OS dynamic tools：`IMPLEMENTED — DYNAMIC TOOL GATEWAY；COMBINED WIN11 REGRESSION PASS`
- H6.1 Harness Cordis tool adapter + context ingress：`IMPLEMENTED — OFFICIAL PLUGIN SMOKE QUEUED`
- H6.2 Official Harness consequential-tool Golden E2E：`IMPLEMENTED — DETERMINISTIC WIN11 ACTION QUEUED`
- H7 Runtime jobs / interrupt mapping：`NOT_STARTED`
- H8 RC Golden Job Native vs Harness A/B：`NOT_STARTED`
- H9 ComfyX long-running job validation：`NOT_STARTED`
- H10 Desktop packaging：`NOT_STARTED`
- H11 Default-runtime decision：`NOT_STARTED`
- E7 Media / Company Coworker：`NOT_STARTED`

## H0-H11 主線權責

```text
OpenWorker Product Layer
        ↓
AgentRuntime seam
   ├─ NativeRuntime → existing TurnEngine
   └─ DeepSeekHarnessRuntime → dsh ACP / plugin runtime
        ↓
OpenWorker Tool / Permission Gateway
        ↓
AI-Engineering-OS canonical agent API
        ↓
Design Forge / EngSketch / BIM / Bridge / Terrain / ComfyX / ...
```

固定原則：

1. OpenWorker 是產品/員工層：UX、connectors、scheduler、memory、approval、finished-work delivery。
2. DeepSeek Harness 是可替換 agent runtime，不是工程 schema authority。
3. AI-Engineering-OS 是工程 Tool/Recipe/Job/Artifact/Review/Digital Thread authority。
4. 不把 Harness 塞進 ProviderClient；它擁有 agent loop/session/jobs/runtime lifecycle。
5. NativeRuntime 不提前刪除，直到 H8/H9 真實 A/B 完成。
6. PermissionEngine 初期仍由 OpenWorker 掌權。
7. 不修改 ACP wire 來偷塞 OpenWorker 私有欄位；缺口用正式 Cordis/plugin seam 補。

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

Pinned ACP 尚無 load/list/resume/delete/fork，因此禁止用 prompt replay 假裝 durable resume。H5 tests 已隨 H6 combined Win11 regression 通過；最終 VERIFIED 等目前 H6.2 official gate 收斂後統一記錄。

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

H6 Run `31772297067` 已取得 self-hosted Win11 runner，且 H1/H3/H4/H5/H6 Python regression 與 H2 contract 已 PASS；該舊 Run 的 official checkout 仍執行中，最終證據由更新後 H6.2 gate 接手。

## H6.1 Official Cordis Tool Plugin

官方 extension point已確認：

```text
ctx.tools.register(ToolDefinition)
tools/pre-execute → allow / deny / ask
```

新增：

```text
harness/upstream-plugin/openworker-engineering-tools.ts
coworker/runtimes/harness_context_ingress.py
tests/runtimes/test_harness_context_ingress.py
tests/runtimes/test_harness_official_tool_plugin_smoke.py
docs/engineering/deepseek-harness-h6-1-progress.zh-TW.md
```

安全規則：Cordis plugin 只把 `callId + exposed name + arguments` 送到 loopback side-channel；canonical id / side-effect / approval metadata 由 OpenWorker 自己重新查 AI-Engineering-OS catalog，不信任 plugin 自報 policy facts。

## H6.2 Deterministic Consequential Tool Golden E2E

官方 Harness 內建 `@deepseek-ai/dsh-llm-replay`，因此不用付費模型即可讓真正 agent loop產生 deterministic tool-call。

新增：

```text
tests/runtimes/test_harness_official_engineering_tool_e2e.py
docs/engineering/deepseek-harness-h6-2-progress.zh-TW.md
```

Golden chain：

```text
ACP prompt
→ official dsh-llm-replay
→ tool-call budget__calculate({amount:42})
→ official ToolRuntime
→ OpenWorker Cordis plugin
→ tools/pre-execute
→ localhost context ingress
→ H4 PermissionBridge / PermissionEngine / approver
→ ACP allow-once
→ canonical OS invoke
→ ToolResult
→ second replay model call
→ committed DONE
→ end_turn
```

最新 Win11 Action：

```text
Run: 31772905006
OpenWorker: 5e386d8ab01a139cca749582f3ad9eb83def96ee
DeepSeek Harness: 47f943859bef60e4160492346772ded9b24f765a
status: queued
runs-on: [self-hosted, Windows, X64]
```

在 Run 全綠前 H6.1/H6.2 都只標 IMPLEMENTED，不提前宣稱 VERIFIED。

## 下一批 H7

H6.2 全綠後進：

```text
Harness/OS long-running job identity
→ OpenWorker job UX
→ status polling / progress
→ request_interrupt
→ Harness session/cancel
→ AI-Engineering-OS job cancel
→ terminal state / artifact evidence
```

之後 H8 用同一台固定 runner 做 RC Golden Job NativeRuntime vs HarnessRuntime A/B，H9 再做 ComfyX 長任務。
