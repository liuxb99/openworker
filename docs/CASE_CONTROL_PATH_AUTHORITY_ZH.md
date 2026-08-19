# Case 控制路径权威说明

更新时间：2026-08-19（Asia/Taipei）

## 唯一推荐架构

新版 Case 主控 authority 是 **Go 版 OpenWorker**，canonical executable：

`C:\ProgramData\OpenWorker\bin\openworker.exe`

相容入口：

`C:\ProgramData\OpenWorker\bin\openworkerctl.exe`

正确链路：

```text
ChatGPT / LLM
  -> 高阶短命令
  -> （无法直达时）GitHub transient short-command transport
  -> ODA openworker.exe / openworkerctl.exe
  -> OpenWorker Go Case Engine / Local Supervisor
  -> go-tool-runtime :8848 durable queue / tool execution control plane
  -> resident OpenWorker :8787 node / durable ledger
  -> 4 claim workers + 4 executor slots 并行执行
```

因此：

- `openworker.exe` = 新版 Go 主控 / Case controller authority
- `openworkerctl.exe` = compatibility CLI / 短命令入口
- `go-tool-runtime :8848` = durable queue、工具能力、execution control plane，不是 Case 主控本体
- `OpenWorker :8787` = resident node / durable Case ledger authority
- `COMPUTERNAME` = fixed-machine authority

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

## GitHub 的正确边界

GitHub 可以在 ChatGPT 无法直接到达目标机时，作为**短命令瞬时 transport**：

```text
ChatGPT
  -> command-requests/oda.json
  -> short-lived GitHub Action
  -> ODA openworkerctl/openworker.exe
  -> local acceptance
  -> command-results/oda/<request_id>/final.json
  -> ChatGPT read-back
```

GitHub Action 一旦拿到本机 acceptance 就必须结束。

允许：

- `case_status`
- `case_continue`
- `case_bootstrap`
- `queue_clear`
- 安装、升级、修复 control-plane

禁止：

- GitHub Action 做 Case business execution
- GitHub Action 等待整个 Case 完成
- GitHub artifact 作为业务成果 authority
- GitHub workflow 状态代替 OpenWorker durable ledger
- PR -> control PR -> 多层 workflow 编排普通 Case 短命令
- legacy Python controller 作为 Go-native Case controller

## Case 0005 当前特别规则

当前已存在 durable business work：

`case0005-0005-010-r000014-17b8b780`

因此在它 terminal 前：

- **不得再发新的 `case_continue`**
- 只能发 `case_status` / `case_work_status` 查询
- terminal completed 后由 Go Case Engine reconciliation 决定下一 ready step

没有 local acceptance、CaseWorklist、durable work 或 append-only ledger 的直接证据，不得宣称 Case 已继续或完成。
