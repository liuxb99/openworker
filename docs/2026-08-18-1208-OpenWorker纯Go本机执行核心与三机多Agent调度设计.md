# OpenWorker 纯 Go 本机执行核心与三机多 Agent 调度设计

日期：2026-08-18
状态：P1 BATCH-2 IMPLEMENTED — WAITING FOR SELF-HOSTED ACTION VERIFICATION

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

## 5. P1 Batch-2：Python Control Plane adapter

提交 `2e37a322` 新增 `coworker/node_client.py`。Python 上层不再直接碰 Windows PID，而通过 Go Node API 调用：

```text
node_status
submit
jobs
job_status
cancel
retry
drain queued/all
```

提交 `cbe15b5f` 新增 adapter contract test，使用 `httpx.MockTransport` 验证 Python -> Go HTTP contract，不依赖真实 node。

## 6. P1 Batch-2：retry / recover

提交 `4e04d148` 在 durable store 增加显式 `Retry`：只有 `failed/timed_out/cancelled/stale` 可回到 `queued_local`；`running/starting/queued/succeeded` 不允许误 retry。Retry 会清 PID、exit code、started/finished/heartbeat，并写 `retried` event。

提交 `34bda54e` 增加 stale -> retry -> queued 的 store test。

Host 启动仍先把遗留 `starting/running` fail-closed 标成 `stale`；现在 operator/control plane 可以显式 retry，而不是偷偷把未知执行结果当成功。

## 7. P1 Batch-2：drain all

提交 `75e8cae4` 增加 `Manager.DrainAll()`：扫描 active jobs，对 `queued/starting/running` 逐个走统一 `Cancel()`；running job 因而会触发 context cancel + Windows process-tree kill + resource lock release。

这和旧 `DrainQueued()` 分开，避免 queued-only 管理动作意外杀掉运行任务。

提交 `e5f87923` 扩充 HTTP API：

```text
POST /v1/jobs/{job_id}/retry
POST /v1/queue/drain?mode=queued
POST /v1/queue/drain?mode=all
```

未知 drain mode fail-closed。

## 8. P1 Batch-2：验证 workflow

提交 `03a7f112` 更新 `.github/workflows/openworker-go-runtime-p0.yml`：

1. Go build；
2. 全部 Go tests；
3. 4 worker 并行 smoke；
4. shared resource lock 串行 smoke；
5. Python `node_client` contract test；
6. 启动真实 `openworker-node.exe`；
7. Action bridge durable ACK；
8. 提交一个真实失败 job；
9. `/retry` 必须重新进入 `queued_local`；
10. `/queue/drain?mode=all` 必须成功清理 active queue。

当前仍不得宣称 VERIFIED：需要 self-hosted runner 真正接单并产生 completed receipt。

## 9. 当前状态接口

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

统一 `job_id` 继续贯穿 Action、Go Core、Python Control Plane、WorkLedger、artifact、QC receipt；`dispatch_id` 负责派工幂等。

## 10. 当前调度铁律

- `COMPUTERNAME` 是固定机器最终权威；
- `machine=<fixed>` 不允许其他机器执行；
- `machine=any` 才能在未来 P2 做自动路由；
- resource lock busy 必须 requeue，不占死 worker；
- Git 修改型并行任务必须独立 worktree；
- restart 后未知 running 必须 stale，不能假成功；
- retry 必须显式；
- `drain queued` 与 `drain all` 语义必须分开；
- Action 收到 durable ACK 后即可结束，不等待真实任务结果。

## 11. 尚未完成的 P1

1. 选一条真实 case workflow 从长执行改成 `submit -> ACK -> exit`，形成迁移样板；
2. go-tool capability metadata：`openworker.job.submit/status/cancel/retry`、`openworker.queue.drain`、`openworker.node.status`；
3. Windows service 安装/升级入口；
4. running cancel/drain 的独立 durable receipt/event 查询 API；
5. 更细 PID 存活检测与 restart recover policy。

## 12. P2：三机 Cluster

UL7 / ODA / O87 各运行 `openworker-node.exe`。下一阶段增加 registry heartbeat/lease、node capabilities、cluster status/jobs、node-to-node query、`machine=any` capability-aware scheduler、跨 node 资源 lease 与 failover policy。

目标查询：

```text
openworker.node.status
openworker.job.status
openworker.cluster.status
openworker.cluster.jobs
```

## 13. 验收铁律

真实验证必须覆盖：四任务并行、第五排队、同锁串行且不占死 worker、hang 不阻塞其他 workers、timeout 回收 slot、cancel 终止 process tree、drain queued 一次清完 queued、drain all 终止 active、重复 drain 安全、重复 dispatch 不重复执行、restart lost running -> stale、stale 可显式 retry、worktree 保持 Action `_work` 语义、COMPUTERNAME 不符 fail-closed、Action durable ACK 后可独立结束。

## 14. 最终目标

OpenWorker 从 GitHub Actions 驱动的单 runner 执行，升级为 OpenWorker 自己拥有的三节点、多 Agent、可并行、可恢复、可观察的本机执行系统。GitHub Actions 保留版本、入口、CI 与证据职责，不再成为长任务 scheduler。
