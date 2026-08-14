# OpenWorker × DeepSeek Harness H3 開發進度

更新日期：2026-08-14

狀態：`IMPLEMENTED — OFFICIAL ACP WIN11 ACTION QUEUED`

## 本批目標

H3 將 H2 已確認的官方 ACP JSON-RPC stdio control plane，落成 OpenWorker 可使用的真 subprocess runtime adapter；本批不提前實作 H4 permission/approval bridge、H5 durable session/resume、H6 OS dynamic tools 或 H7 jobs mapping。

本次追加的重點不是再寫一個 fixture，而是把 OpenWorker Python ACP client 直接對上 **官方 pinned DeepSeek Harness 0.1.0-rc.5 source composition**，驗證最小真實互通：

```text
OpenWorker AcpProcessClient
→ node + tsx
→ official dsh acp-demo composition
→ JSON-RPC initialize
→ JSON-RPC session/new
→ fresh Harness agent/session created
→ graceful shutdown
```

這條 smoke 不送 `session/prompt`，因此不呼叫模型；只驗證 process、Loader、Cordis composition、ACP framing、protocol negotiation 與 session factory 的真互通。

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

既有 deterministic process boundary 測試：

```text
tests/runtimes/fixtures/mock_acp_server.py
tests/runtimes/test_harness_runtime.py
```

實際啟動獨立 Python subprocess，以 stdin/stdout NDJSON JSON-RPC 驗證：

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

本次新增官方互通 smoke：

```text
tests/runtimes/test_harness_official_acp_smoke.py
```

測試會讀取 `DSH_HARNESS_ROOT`，確認官方 source bin / cordis.yml / root tsconfig 存在，並依 upstream `resolveExampleLaunch()` 的 source-mode 規則設定：

```text
TSX_TSCONFIG_PATH=<deepseek-harness>/tsconfig.json
node --import tsx packages/examples/acp-demo/src/bin.ts --config examples/acp-agent/cordis.yml
```

環境固定：

```text
DEEPSEEK_API_KEY=sk-dummy-for-boot
DSH_PERMISSION_MODE=danger-full-access
DSH_HOME=<isolated temp>/.dsh
DSH_AGENTS_HOME=<isolated temp>/.agents
```

Dummy key 只讓 DeepSeek adapter 通過啟動檢核；本 smoke 不進 model call。

## 與官方 DeepSeek Harness rc.5 對齊

Upstream pin：

```text
repo: deepseek-ai/deepseek-harness
commit: 47f943859bef60e4160492346772ded9b24f765a
release: 0.1.0-rc.5
ACP SDK family: @agentclientprotocol/sdk 0.25.1
pnpm: 11.7.0
```

官方 source launcher 明確使用 `TSX_TSCONFIG_PATH` 讓 `tsx` 依 root tsconfig paths 解析 workspace packages；OpenWorker 官方 smoke 已照這個 contract 實作，不自行猜 module resolution。

官方 ACP 本身限制仍成立：fresh sessions only、committed answers only、無 durable load/resume/replay、無 live reasoning/tool activity/plan/title/usage、無 per-session close。因此 H3 只聲稱 process/ACP adapter，不聲稱完整 Harness runtime 已取代 NativeRuntime。

## Win11 本機 Action

### 舊 H2/H3 workflow 問題

原本使用：

```text
AI-Engineering-OS/.github/workflows/openworker-harness-h2-win11.yml
```

它過去在 `AI-Engineering-OS main` 每次 push 都會觸發。當 OS 同時大量開發時，Harness run 會被無關 push 反覆建立、取消或重排，這屬於 trigger/concurrency 噪音，不是 self-hosted runner routing 問題。

已修正為只在該 workflow 檔自身修改時觸發；`runs-on` 仍保持：

```text
[self-hosted, Windows, X64]
```

沒有重新加入複雜 machine 判斷。

### 專用 H3 官方互通 workflow

新增：

```text
AI-Engineering-OS/.github/workflows/openworker-harness-h3-official-win11.yml
workflow: OpenWorker Harness H3 Official Win11
run: 31767728540
OpenWorker ref: 1870dfbf87dd598c361f5b63b7fdaa158adcef52
DeepSeek Harness ref: 47f943859bef60e4160492346772ded9b24f765a
runs-on: [self-hosted, Windows, X64]
```

Gate：

1. Runner identity / Windows / Python / Node / npm。
2. checkout OpenWorker H3 exact ref。
3. OpenWorker editable install。
4. `compileall coworker tests/runtimes`。
5. H1 + H3 deterministic runtime regressions。
6. H2 TypeScript build + contract tests。
7. checkout official DeepSeek Harness exact pinned commit。
8. `git rev-parse HEAD` 強制比對 pin。
9. `pnpm@11.7.0 install --frozen-lockfile --ignore-scripts`。
10. OpenWorker Python client 對官方 dsh ACP 執行 `initialize + session/new`。

目前專用 Run `31767728540` 已成功建立，狀態為 `queued`，尚未取得 self-hosted runner。因此目前仍不把 H3 標成 VERIFIED。

## H3 完成條件

只有以下全部成立才升級：

- [x] OpenWorker 真 subprocess ACP adapter 已實作。
- [x] deterministic subprocess regression 已加入。
- [x] official pinned Harness interoperability smoke 已加入。
- [x] Win11 專用 workflow 已建立且不受無關 OS push 觸發。
- [ ] Win11 deterministic H3 tests PASS。
- [ ] Win11 H2 contract tests PASS。
- [ ] Win11 exact upstream checkout PASS。
- [ ] Win11 official `initialize + session/new` PASS。
- [ ] 無 orphan sidecar / stdout protocol pollution。

## H3 後下一階段：H4

H3 驗證完成後才正式接：

```text
Harness session/request_permission
→ OpenWorker PermissionEngine
→ existing approval UX
→ allow-once / reject-once
→ ACP permission response
```

H4 之前禁止自動 allow consequential tool calls，也禁止把 Harness 設成 OpenWorker 預設 runtime。
