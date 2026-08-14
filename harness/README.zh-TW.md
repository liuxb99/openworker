# OpenWorker Harness Integration

狀態：H2 integration skeleton。

這個目錄是 OpenWorker 對 DeepSeek Harness 的整合層，不是 DeepSeek Harness upstream 的 vendor copy，也不是第二套 OpenWorker UI。

## H2 固定原則

1. DeepSeek Harness upstream 固定到 commit `47f943859bef60e4160492346772ded9b24f765a` / `0.1.0-rc.5`。
2. 第一優先復用官方 `@deepseek-ai/dsh-acp` 的 Agent Client Protocol JSON-RPC stdio 控制面。
3. ACP 只被視為 bootstrap/control transport，不被誤稱為完整 OpenWorker Runtime bridge。
4. OpenWorker 仍保留 `NativeRuntime` 為預設；H2 不會啟動或選用 Harness runtime。
5. OpenWorker Permission/Approval 與 AI-Engineering-OS 工程權威邊界不變。
6. 不直接修改 DeepSeek Harness core；缺口優先由 OpenWorker profile/plugin 補齊。

## ACP rc.5 已能提供

- fresh agent session；
- text prompt；
- committed assistant text；
- `session/cancel`；
- one-shot permission request/decision；
- 一個 stdio connection 管理多個 session。

## ACP rc.5 尚未提供 OpenWorker 所需的完整能力

- durable load/resume/replay；
- live reasoning / token delta；
- live tool activity / tool cards；
- plan/title/usage stream；
- per-session close；
- additional directories / MCP server injection；
- image/audio/embedded resource prompt。

因此後續 H3/H4/H5 不會單純把 ACP 等同 `DeepSeekHarnessRuntime`。預期形態是：

```text
OpenWorker DeepSeekHarnessRuntime
        │
        ├─ ACP stdio
        │    ├─ create/prompt/cancel
        │    └─ one-shot permission control
        │
        └─ OpenWorker Harness plugins
             ├─ live session/event bridge
             ├─ tool gateway bridge
             ├─ approval bridge
             └─ durable session/resume bridge
```

## H2 contract files

- `upstream-lock.json`：upstream commit/release/package pin。
- `src/protocol.ts`：transport capability contract；所有 ACP 缺口都必須顯式為 `false`。
- `src/health.ts`：版本與 health/capability report。
- `tests/contracts.test.mjs`：永久測試，防止未實作能力被誤宣稱為 supported。

## H2 驗證

```cmd
cd harness
npm install
npm test
```

H2 的成功只代表 integration contract/skeleton 可編譯、測試與版本 pin 正確；不代表 Harness agent 已能在 OpenWorker 內工作。
