# OpenWorker 纯 Go 本机执行核心与三机多 Agent 调度设计

日期：2026-08-18
状态：P1 BATCH-3 IMPLEMENTED — WAITING FOR SELF-HOSTED REAL-CASE VERIFICATION

## 1. 架构结论

OpenWorker 采用双层结构：Python 保留案例、WorkLedger、知识、审核、Drive 与上层 orchestration；纯 Go `openworker-node.exe` 成为本机执行内核，负责 durable queue、多 Agent slots、真实进程、资源锁、heartbeat、timeout、cancel、drain、retry/recover，以及后续三机 cluster。

GitHub Action 逐步退化为 transport：`runner accepted -> COMPUTERNAME -> submit -> durable ACK -> Action completed`。Action 完成不代表真实任务完成。

## 2. Action 工作目录兼容

canonical checkout 继续位于原 Action `_work`，例如 `D:\actions-runner\_work\openworker\openworker`。需要修改 Git 的并行 Agent 使用同层 `_agents/Axx/<repo>` worktree；业务 workspace 仍保持 `D:\AI-Work\jobs\...`。

## 3. 已完成 P0

核心提交 `9a528a3a`：SQLite durable store、4 worker pool、command/cwd/env、stdout/stderr、PID、heartbeat、timeout、cancel、Windows process-tree kill、queued drain、startup stale recovery、HTTP submit/status/list/cancel/drain、COMPUTERNAME fail-closed。

## 4. 已完成 P1 Batch-1

Resource locks + worktree + Action ACK bridge 已落地：

- `00b4b786` / `8f10ef3a` / `7bff6416`：resource lock、schema、scheduler TryAcquire/Requeue/Release；
- `eca0c6c1`：Action-compatible Git worktree slots；
- `ebe99bea`：`scripts/submit_openworker_node.ps1`；
- `70a2f1fd`：P0-P1 self-hosted verification workflow。

等待资源锁的任务会 requeue，不长期占 worker slot。`use_worktree=true` 时真实 `cwd/GITHUB_WORKSPACE` 切到 `_agents/Axx/<repo>`。

## 5. 已完成 P1 Batch-2：Python Control Plane adapter

提交 `2e37a322` 新增 `coworker/node_client.py`。Python 上层通过 Go Node API 调用：`node_status/submit/jobs/job_status/cancel/retry/drain`，不直接碰 Windows PID。

提交 `cbe15b5f` 新增 adapter contract test。

## 6. 已完成 P1 Batch-2：retry / recover

提交 `4e04d148` 增加显式 Retry：只有 `failed/timed_out/cancelled/stale` 可回到 `queued_local`；`running/starting/queued/succeeded` 不允许误 retry。Retry 清 PID、exit code、started/finished/heartbeat，并写 `retried` event。

提交 `34bda54e` 增加 stale -> retry -> queued test。

## 7. 已完成 P1 Batch-2：drain all

提交 `75e8cae4` 增加 `Manager.DrainAll()`：`queued/starting/running` 逐个走统一 `Cancel()`；running job 会触发 context cancel + Windows process-tree kill + resource lock release。

提交 `e5f87923` 扩充：

```text
POST /v1/jobs/{job_id}/retry
POST /v1/queue/drain?mode=queued
POST /v1/queue/drain?mode=all
```

## 8. P1 Batch-2 验证 workflow

提交 `03a7f112`：Go build、全部 Go tests、4 worker 并行、shared lock 串行、Python node_client contract、真实 node 启动、Action durable ACK、失败 job retry、drain all。

仍需 self-hosted runner completed receipt 才能宣称 VERIFIED。

## 9. 当前 Go Node API

```text
GET  /healthz
GET  /v1/node/status
POST /v1/jobs
GET  /v1/jobs
GET  /v1/jobs/{job_id}
POST /v1/jobs/{job_id}/cancel
POST /v1/jobs/{job_id}/retry
POST /v1/queue/drain?mode=queued|all
```

统一 `job_id` 贯穿 Action、Go Core、Python Control Plane、WorkLedger、artifact、QC receipt；`dispatch_id` 负责派工幂等。

## 10. 当前调度铁律

- `COMPUTERNAME` 是固定机器最终权威；
- `machine=<fixed>` 不允许其他机器执行；
- `machine=any` 才能在未来 P2 自动路由；
- resource lock busy 必须 requeue，不占死 worker；
- Git 修改型并行任务必须独立 worktree；
- restart 后未知 running 必须 stale，不能假成功；
- retry 必须显式；
- `drain queued` 与 `drain all` 语义分开；
- Action 收到 durable ACK 后即可结束，不等待真实任务结果。

## 11. P1 Batch-3：真实 Case 0004 迁移样板

### 11.1 本机真实工作脚本

提交 `ab157b7c` 新增：

```text
scripts/case0004_worklist_state_local.ps1
```

它在真实业务 workspace `D:\AI-Work\jobs\0004-DWG-TO-3D` 上执行现有 `case_worklist_action.py ensure/show`，验证 `case_id/workspace_root`，并把真实结果写入：

```text
D:\AI-Work\jobs\0004-DWG-TO-3D\.openworker\evidence\latest-worklist-state-node.json
```

结果记录 `OPENWORKER_JOB_ID / OPENWORKER_AGENT_SLOT / OPENWORKER_MACHINE`，所以成果可追到具体 Go Node job 与 agent slot。

### 11.2 新版真实案例 workflow

提交 `cff7b53f` 新增：

```text
.github/workflows/case0004-o87-worklist-state-node.yml
```

新版流程：

```text
GitHub runner O87
-> COMPUTERNAME == DESKTOP-O87PJNR
-> GET openworker-node /healthz
-> submit real Case 0004 job
-> durable ACK
-> receipt 写入业务 workspace .openworker/dispatch/
-> Action 结束
-> Go Node 独立 worktree + workspace/tool locks 继续真实执行
```

关键差异：

- 不再使用旧版 `matrix slot [1,2,3]` 抢 runner；
- Action timeout 缩为 5 分钟，仅承担 dispatch；
- 真实工作 timeout 由 Go Node job 自己管理；
- 使用 `workspace:D:\AI-Work\jobs\0004-DWG-TO-3D` 与 `tool:case-worklist` locks；
- `use_worktree=true`，并锁定当前 `GITHUB_SHA`；
- dispatch receipt 在业务 workspace 持久存在，Action 结束后仍可查询；
- 旧 workflow 暂时保留，作为 A/B fallback，不直接破坏现有案例路径。

## 12. P1 Batch-3：O87 Go Node 控制入口

提交 `5cc8b44d` 新增：

```text
.github/workflows/openworker-node-control-o87.yml
```

提供轻量 control plane：

```text
node.status
job.status
job.cancel
job.retry
queue.drain queued|all
```

workflow 只允许 O87 路由，最终仍以 `COMPUTERNAME=DESKTOP-O87PJNR` fail-closed。结果写 machine-readable JSON artifact：

```text
openworker-node-control-<run_id>
```

这使 go-tool 可以通过既有 GitHub Action transport 查询/控制本机 persistent node，而不是让大模型直接猜本机状态。

## 13. P1 Batch-3：go-tool capability metadata

`liuxb99/go-tool-runtime` 提交 `8b2be98c` 新增：

```text
capabilities.d/openworker-node-o87.yaml
```

新增两项 capability：

```text
openworker.node.o87.control
openworker.case0004.worklist-state.node
```

其中 `openworker.node.o87.control` 暴露 `node.status/job.status/job.cancel/job.retry/queue.drain`；Case 0004 capability 则只负责 durable dispatch。

Capability 描述已加入负面工具知识：

> GitHub Action completed 只代表 dispatch/control workflow 完成，不能当作 OpenWorker job succeeded；真实结果必须继续用 durable `job_id` 查询 `job.status`。

这条规则用于防止大模型重复把 Action 成功误判为业务任务成功。

## 14. 当前真实迁移状态

代码与 metadata 已完成，但截至本批文档更新时，尚未取得：

1. O87 上 `openworker-node.exe` 常驻服务已启动的权威 receipt；
2. `case0004-o87-worklist-state-node.yml` 的真实 durable ACK；
3. 对应 `job_id` 最终 `succeeded`；
4. `.openworker/evidence/latest-worklist-state-node.json` 实体成果。

因此当前结论仍是：**P1 Batch-3 IMPLEMENTED，不宣称 REAL VERIFIED。**

## 15. 尚未完成的 P1

1. Windows service 安装/升级入口，使 `openworker-node.exe` 真正常驻；
2. 在 O87 跑通 Case 0004 新版 workflow，取得 durable ACK + final job status + local evidence；
3. running cancel/drain 独立 durable receipt/event 查询 API；
4. 更细 PID 存活检测与 restart recover policy；
5. 把同一模式逐步复制到 UL7 / ODA，而不是继续增加 matrix 抢 runner。

## 16. P2：三机 Cluster

UL7 / ODA / O87 各运行 `openworker-node.exe`。下一阶段增加 registry heartbeat/lease、node capabilities、cluster status/jobs、node-to-node query、`machine=any` capability-aware scheduler、跨 node 资源 lease 与 failover policy。

目标查询：

```text
openworker.node.status
openworker.job.status
openworker.cluster.status
openworker.cluster.jobs
```

## 17. 验收铁律

真实验证必须覆盖：四任务并行、第五排队、同锁串行且不占死 worker、hang 不阻塞其他 workers、timeout 回收 slot、cancel 终止 process tree、drain queued 一次清完 queued、drain all 终止 active、重复 drain 安全、重复 dispatch 不重复执行、restart lost running -> stale、stale 可显式 retry、worktree 保持 Action `_work` 语义、COMPUTERNAME 不符 fail-closed、Action durable ACK 后可独立结束，以及真实 Case workflow 在 Action 结束后仍由 Go Node 完成。

## 18. 最终目标

OpenWorker 从 GitHub Actions 驱动的单 runner 执行，升级为 OpenWorker 自己拥有的三节点、多 Agent、可并行、可恢复、可观察的本机执行系统。GitHub Actions 保留版本、入口、CI 与证据职责，不再成为长任务 scheduler。
