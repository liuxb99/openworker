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
- H5 Session / Resume bridge：`IMPLEMENTED — SESSION OWNERSHIP BOUNDARY；WIN11 GATE QUEUED`
- H6 AI-Engineering-OS dynamic tools：`IMPLEMENTED — DYNAMIC TOOL GATEWAY；WIN11 GATE QUEUED`
- H6.1 Harness tool adapter / consequential permission E2E：`NOT_STARTED`
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

## H3 已驗證

最終 Win11 證據：

```text
Run: 31771872273
DeepSeek Harness: 47f943859bef60e4160492346772ded9b24f765a
conclusion: success
```

已通過 deterministic runtime regression、H2 TypeScript contract、exact upstream pin、官方 Harness workspace install，以及真實：

```text
OpenWorker Python AcpProcessClient
→ official dsh ACP subprocess
→ initialize
→ session/new
```

因此 H3 已從 implemented/queued 升級為 VERIFIED。

## H4 權限治理

正式安全鏈：

```text
Harness tool call id
→ OpenWorker-owned HarnessToolContextRegistry
→ session/request_permission
→ HarnessPermissionBridge
→ PermissionEngine
→ existing approver UX
→ allow-once / reject-once / cancelled
```

官方 ACP permission request 沒有完整 tool name/arguments，因此缺 context 一律 fail closed。H6 已提供正式 context producer。

## H5 Session Ownership

OpenWorker durable conversation 與 Harness ACP ephemeral session 必須分離：

```text
OpenWorker ConversationStore = durable product source of truth
Harness ACP session          = connection/process-local runtime context
```

Pinned ACP 尚無 load/list/resume/delete/fork，因此 H5 禁止用 prompt replay 假裝 durable resume。

## H6 Dynamic Engineering Tools

H6 不複製 OS schema，直接動態使用 AI-Engineering-OS：

```text
GET /api/v1/ai/tools/mcp
→ exposed MCP-safe name + inputSchema
→ annotations.canonical_tool_id / side_effect / job scope
→ HarnessEngineeringToolGateway
→ HarnessToolContextRegistry
→ H4 permission gate
→ POST /api/v1/ai/tools/{canonical_id}/invoke
```

新增：

```text
coworker/runtimes/harness_engineering_tools.py
tests/runtimes/test_harness_engineering_tools.py
docs/engineering/deepseek-harness-h6-progress.zh-TW.md
```

H6 Win11 Run：`31772297067`，目前等待 self-hosted runner。

## 下一批 H6.1

Pinned ACP 沒有 client-side dynamic tool registration control plane，因此真正 full E2E 不能只改 Python ACP client。下一批需要建立 Harness plugin/tool adapter：

```text
AI-Engineering-OS dynamic catalog
→ Harness plugin tool registration
→ real Harness tool call
→ OpenWorker canonical call context
→ consequential permission request
→ OpenWorker approval
→ real OS invoke
→ Harness tool result
```

H6.1 完成後才進 H7 jobs/cancellation 與 H8 RC Golden Job A/B。
