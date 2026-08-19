# Case 控制路径权威说明

更新时间：2026-08-19（Asia/Taipei）

## 唯一推荐路径

对已经进入 resident OpenWorker / Local Supervisor 架构的 Case，控制路径必须保持最短：

```text
ChatGPT / LLM
  -> 查询 go-tool-runtime 的 openworker.supervisor.control
  -> 对固定目标机发送一条 high-level short command
  -> go-tool :8848 Local Supervisor 接管
  -> OpenWorker :8787 保存 durable business state / append-only ledger
  -> 本机 worker / executor 并行执行
```

Canonical short commands：

```text
supervisor_status
case_status
case_work_status
case_bootstrap
case_continue
case_dispatch
queue_clear
```

Case 0005：

```text
machine: DESKTOP-ODAQN0D
operation: case_continue
case_id: 0005
```

## GitHub 的边界

GitHub 只允许在无法直接到达目标机 go-tool 时，作为一次性的 transient short-command transport。GitHub 一旦取得 local acceptance 必须结束，不能等待 Case 完成。

禁止：

```text
PR -> control workflow -> workflow_dispatch -> Case business control
GitHub Actions 作 Case status bus
GitHub Actions 作 Case business executor
GitHub artifact 作 Case 成果 authority
Git commit / workflow conclusion 代替 OpenWorker durable ledger
```

## Authority

```text
go-tool :8848 = command/control authority
OpenWorker :8787 = durable business-state / ledger authority
COMPUTERNAME = fixed-machine authority
```

没有 local acceptance、CaseWorklist 或 supervisor ledger 的直接证据，不得宣称 Case 已继续或完成。

机器可读主契约：`liuxb99/go-tool-runtime/capabilities.d/openworker-supervisor.yaml`。
