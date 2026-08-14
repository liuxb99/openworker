# OpenWorker × DeepSeek Harness H4 開發進度

更新日期：2026-08-14

狀態：`IMPLEMENTED — WIN11 BRIDGE REGRESSION PASS；OFFICIAL ACP H3/H4 GATE QUEUED`

## 本批目標

H4 將 DeepSeek Harness ACP 的 `session/request_permission` 接回 OpenWorker 既有 PermissionEngine / approver 治理層，但不虛構 ACP 沒有提供的工具資訊，也不提前實作 H5 durable session、H6 dynamic tool gateway 或 H7 jobs mapping。

## 上游限制與設計修正

DeepSeek Harness `0.1.0-rc.5` 的 ACP permission request 只傳：

```text
sessionId
toolCall.toolCallId
```

官方 ACP request 並沒有提供 OpenWorker PermissionEngine 判斷所需的：

```text
tool_name
arguments
metadata / risk context
```

因此 H4 禁止直接相信 ACP request 來做權限判斷。正式安全路徑改為：

```text
Harness tool call
→ OpenWorker Tool Gateway（H6 producer）
→ HarnessToolContextRegistry.register(callId → canonical tool context)
→ ACP session/request_permission(callId only)
→ HarnessPermissionBridge
→ registry.resolve(callId)
→ PermissionEngine.evaluate(tool_name, arguments, metadata)
→ existing OpenWorker approver（需要人工核准時）
→ ACP allow-once / reject-once / cancelled
```

若 call id 找不到 OpenWorker-owned canonical context，必須 fail closed 回 `cancelled`。

## 已完成代碼

### `coworker/runtimes/harness_permissions.py`

新增：

- `HarnessToolContext`
  - `tool_call_id`
  - `tool_name`
  - `arguments`
  - `metadata`

- `HarnessToolContextRegistry`
  - OpenWorker-owned process-local authoritative call-id registry。
  - `register()` / `resolve()` / `discard()` / `clear()`。
  - 空 call id 拒絕。
  - 重複 live call id 拒絕，不允許靜默覆蓋另一個 operation 的 policy context。

- `HarnessPermissionBridge`
  - 先用 call id 解析 canonical context。
  - 無 context → `cancelled`。
  - PermissionEngine 已允許 → ACP `allow-once`。
  - PermissionEngine hard deny → ACP `reject-once`。
  - `needs_user=True` → 呼叫 OpenWorker 既有 `Approver(PermissionRequest)`。
  - `ApprovalOutcome.ONCE` → allow-once。
  - `ALWAYS_TOOL` → 寫入 OpenWorker session tool allowlist，再對當次 ACP 回 allow-once。
  - `ALWAYS_COMMAND` → 寫入 OpenWorker session command allowlist，再對當次 ACP 回 allow-once。
  - `DENY` → reject-once。

ACP rc.5 wire 只提供 one-shot choice，因此「always」語義由 OpenWorker 自己的 session policy 記憶持有，不能假裝 ACP 本身有 durable grant。

### exports

`coworker/runtimes/__init__.py` 已導出：

```text
HarnessPermissionBridge
HarnessToolContext
HarnessToolContextRegistry
ToolContextResolver
```

## 永久測試

`tests/runtimes/test_harness_permissions.py` 已覆蓋：

1. registry register / resolve / discard。
2. duplicate call id fail-closed。
3. 缺 canonical context 時取消，不呼叫 approver。
4. read-only tool 自動允許，不呼叫 approver。
5. interactive shell 經既有 approver。
6. DISCUSS/read-only mode consequential call 直接拒絕，不讓人工 override hard policy。
7. ALWAYS_COMMAND 寫入既有 PermissionEngine session allowlist。
8. DENY → reject-once。
9. 真 ACP subprocess wire：server 發 `session/request_permission` → `AcpProcessClient` → `HarnessPermissionBridge` → `PermissionEngine` → existing approver。

## Win11 驗證證據

專用 workflow：

```text
AI-Engineering-OS/.github/workflows/openworker-harness-h3-official-win11.yml
runs-on: [self-hosted, Windows, X64]
```

Run #3：`31771808050`

在被較新 H4 registry Run 正常取消前已完成：

```text
OpenWorker install: PASS
compileall: PASS
H1/H3/H4 Python runtime regressions: PASS
H2 TypeScript contracts: PASS
official DeepSeek Harness checkout: PASS
exact upstream commit identity: PASS
```

Run #3 在 `pnpm install` 階段因新 commit 觸發同一 concurrency group 而取消，因此不能拿它宣稱 official ACP smoke 已通過。

最新 Run #4：`31771872273`

```text
OpenWorker ref: 1db845766bd067873cd77e7bf327a196a80368ff
DeepSeek Harness ref: 47f943859bef60e4160492346772ded9b24f765a
status: queued / pending self-hosted Win11 runner
```

Run #4 會重跑完整 H1/H2/H3/H4 gate，最後執行 pinned official Harness `initialize + session/new` smoke。

## H4 尚未宣稱完成的部分

H4 bridge contract 已存在，但真實 Harness tool permission E2E 還需要 H6 Tool Gateway 在 tool call 發生時把 `tool_name + arguments + metadata` 寫入 `HarnessToolContextRegistry`。因此目前不能宣稱：

- Harness 已可安全執行所有 OpenWorker tools。
- 官方 ACP permission request 本身包含完整工具資訊。
- H4 已完成 H6 dynamic tools。
- Harness runtime 已可成為 OpenWorker 預設 runtime。

## 下一批

若 Run #4 官方 ACP smoke 全綠：

- H3 升級為 `VERIFIED — OFFICIAL ACP WIN11 LOCAL ACTION`。
- H4 標記為 `VERIFIED — WIN11 BRIDGE CONTRACT；WAITING FOR H6 TOOL-CONTEXT E2E`。

下一個功能 Segment 進 H5/H6 前，優先順序為：

```text
H5：session ownership / durable resume boundary
H6：OpenWorker Tool Gateway + AI-Engineering-OS dynamic tools + HarnessToolContextRegistry producer
H7：jobs / interrupt / cancellation mapping
```

H6 完成後再做官方 Harness consequential-tool permission E2E，才能真正閉環 H4。
