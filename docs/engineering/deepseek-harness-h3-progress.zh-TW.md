# OpenWorker × DeepSeek Harness H3 開發進度

更新日期：2026-08-14

狀態：`IMPLEMENTED — WIN11 LOCAL ACTION QUEUED`

## 本批目標

H3 將 H2 已確認的官方 ACP JSON-RPC stdio control plane，落成 OpenWorker 可使用的真 subprocess runtime adapter；本批不提前實作 H4 permission/approval bridge、H5 durable session/resume、H6 OS dynamic tools 或 H7 jobs mapping。

## 已完成代碼

### `coworker/runtimes/harness.py`

新增：

- `HarnessProcessConfig`
  - 明確 command / cwd / env / startup timeout / request timeout。
  - 正式環境以 `OPENWORKER_HARNESS_COMMAND` 注入啟動命令。
  - Windows 可用 JSON string array 避免 quoting 問題。
  - 未設定 command 時 fail closed，不猜本機 Harness 路徑。

- `AcpProcessClient`
  - `asyncio.create_subprocess_exec()` 啟動 sidecar。
  - stdin/stdout 使用 newline-delimited JSON-RPC 2.0。
  - 支援 `initialize`、`session/new`、`session/prompt`、`session/cancel`。
  - 接收 `session/update` committed assistant text。
  - 接收 `session/request_permission`，H3 固定回 `cancelled`，避免繞過 OpenWorker PermissionEngine。
  - stderr 與 process exit 會轉為結構化 runtime error。
  - shutdown 先 EOF，超時再 terminate / kill，避免 orphan sidecar。

- `DeepSeekHarnessRuntime`
  - 將 ACP fresh session / prompt / committed message / cancel 映射到既有 OpenWorker `Event/EventType`。
  - `request_interrupt()` 映射 `session/cancel`。
  - `health()` 明確區分 H3 已有與未有能力。
  - `retry()`、`resume()`、steering、runtime model switch 在 H3 顯式 fail closed。
  - NativeRuntime 仍是正式預設；Harness 尚未進 product selector。

### exports

`coworker/runtimes/__init__.py` 已導出 H3 runtime、ACP client/config/error 型別。

## 永久測試

新增：

```text
tests/runtimes/fixtures/mock_acp_server.py
tests/runtimes/test_harness_runtime.py
```

測試不是直接 mock method，而是實際啟動獨立 Python subprocess，以 stdin/stdout NDJSON JSON-RPC 驗證 process boundary：

```text
spawn
→ initialize
→ session/new
→ session/prompt
→ session/update
→ OpenWorker assistant event
→ session/cancel
→ interrupted event
→ graceful shutdown
```

另驗證 H3 capability health 與 unsupported features fail closed。

## 與官方 DeepSeek Harness rc.5 對齊

本批依 upstream pin：

```text
repo: deepseek-ai/deepseek-harness
commit: 47f943859bef60e4160492346772ded9b24f765a
release: 0.1.0-rc.5
ACP SDK family: @agentclientprotocol/sdk 0.25.1
```

官方 ACP 本身的限制仍成立：fresh sessions only、committed answers only、無 durable load/resume/replay、無 live reasoning/tool activity/plan/title/usage、無 per-session close。因此 H3 只聲稱 process/ACP adapter，不聲稱完整 Harness runtime 已取代 NativeRuntime。

## Win11 本機 Action

驗證 workflow 已更新為：

```text
AI-Engineering-OS/.github/workflows/openworker-harness-h2-win11.yml
workflow name: OpenWorker Harness H3 Win11
OpenWorker tested ref: 823203d023fefad4b171f24a42a15bd68beb1d33
Run: 31767195843
runs-on: [self-hosted, Windows, X64]
```

預定 gate：

1. Runner identity / Windows / Python / Node。
2. OpenWorker editable install。
3. `compileall coworker tests/runtimes`。
4. H1 runtime seam regression。
5. H3 ACP subprocess runtime regression。
6. H2 TypeScript build + contract tests。

目前 Run 31767195843 為 `queued`。查詢同時可見 AI-Engineering-OS 有多個其他 self-hosted workflows 正在執行，因此此時不修改 runner routing，也不把排隊誤判成 H3 workflow failure。

## 尚未完成 / 下一批

H3 尚缺一項最高價值證據：用 **官方 pinned DeepSeek Harness ACP composition** 做無模型呼叫的真實 `initialize + session/new` smoke。官方 upstream 已證明這條路徑不需要真 API call，只需讓 DeepSeek adapter 啟動；OpenWorker 下一批應把該 smoke 納入 Win11 Action，確認 Python ACP client 能直接對官方 dsh sidecar 互通，而不只對 deterministic fixture。

H3 完成後才進 H4：

```text
Harness session/request_permission
→ OpenWorker PermissionEngine
→ existing approval UX
→ allow-once / reject-once
→ ACP permission response
```

H4 之前禁止自動 allow consequential tool calls。
