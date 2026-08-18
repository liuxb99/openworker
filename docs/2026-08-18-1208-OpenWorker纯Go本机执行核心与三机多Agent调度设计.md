# OpenWorker 纯 Go 本机执行核心与三机多 Agent 调度设计

日期：2026-08-18
状态：P1 BATCH-4 IMPLEMENTED — WAITING FOR O87 SERVICE + REAL-CASE VERIFICATION

## 1. 架构结论

OpenWorker 采用双层结构：Python 保留案例、WorkLedger、知识、审核、Drive 与上层 orchestration；纯 Go `openworker-node.exe` 成为本机执行内核，负责 durable queue、多 Agent slots、真实进程、资源锁、heartbeat、timeout、cancel、drain、retry/recover，以及后续三机 cluster。

GitHub Action 逐步退化为 transport：`runner accepted -> COMPUTERNAME -> submit -> durable ACK -> Action completed`。Action 完成不代表真实任务完成。

## 2. Action 工作目录兼容

canonical checkout 继续位于原 Action `_work`，例如 `D:\actions-runner\_work\openworker\openworker`。Git 修改型并行 Agent 使用同层 `_agents/Axx/<repo>` worktree；业务 workspace 继续保持 `D:\AI-Work\jobs\...`。

## 3. P0 已完成

核心提交 `9a528a3a`：SQLite durable store、4 worker pool、command/cwd/env、stdout/stderr、PID、heartbeat、timeout、cancel、Windows process-tree kill、queued drain、startup stale recovery、HTTP submit/status/list/cancel/drain、COMPUTERNAME fail-closed。

## 4. P1 Batch-1 已完成

- `00b4b786` / `8f10ef3a` / `7bff6416`：resource lock、schema、TryAcquire/Requeue/Release；
- `eca0c6c1`：Action-compatible Git worktree slots；
- `ebe99bea`：`scripts/submit_openworker_node.ps1`；
- `70a2f1fd`：P0-P1 self-hosted verification workflow。

等待锁的 job 会 requeue，不长期占 worker slot。`use_worktree=true` 时 `cwd/GITHUB_WORKSPACE` 会切到 `_agents/Axx/<repo>`。

## 5. P1 Batch-2 已完成

Python adapter：`2e37a322` 新增 `coworker/node_client.py`，支持 `node_status/submit/jobs/job_status/cancel/retry/drain`。

Retry/recover：`4e04d148` 只允许 `failed/timed_out/cancelled/stale` 显式 retry；`34bda54e` 验证 stale -> queued。

Drain all：`75e8cae4` 让 `queued/starting/running` 统一走 Cancel，running 会 context cancel + Windows process-tree kill + lock release；`e5f87923` 暴露 retry/drain API。

`03a7f112` 扩展 self-hosted 验证 workflow。

## 6. 当前 Go Node API

```text
GET  /healthz
GET  /v1/node/info
GET  /v1/node/status
POST /v1/jobs
GET  /v1/jobs
GET  /v1/jobs/{job_id}
GET  /v1/jobs/{job_id}/events
POST /v1/jobs/{job_id}/cancel
POST /v1/jobs/{job_id}/retry
POST /v1/queue/drain?mode=queued|all
```

统一 `job_id` 贯穿 Action、Go Core、Python Control Plane、WorkLedger、artifact、QC receipt；`dispatch_id` 负责派工幂等。

## 7. 当前调度铁律

- `COMPUTERNAME` 是固定机器最终权威；
- `machine=<fixed>` 不允许其他机器执行；
- `machine=any` 才允许未来 P2 自动路由；
- resource lock busy 必须 requeue；
- Git 修改型并行任务必须独立 worktree；
- restart 后未知 running 必须 stale，不能假成功；
- retry 必须显式；
- `drain queued` 与 `drain all` 必须分开；
- Action durable ACK 后即可结束；
- Action completed 永远不能直接当作业务 succeeded。

## 8. P1 Batch-3：真实 Case 0004 迁移样板

`ab157b7c` 新增 `scripts/case0004_worklist_state_local.ps1`，在真实 `D:\AI-Work\jobs\0004-DWG-TO-3D` 上执行现有 Worklist ensure/show，并把结果写入：

```text
D:\AI-Work\jobs\0004-DWG-TO-3D\.openworker\evidence\latest-worklist-state-node.json
```

`cff7b53f` 新增 `.github/workflows/case0004-o87-worklist-state-node.yml`：O87 runner 只检查 COMPUTERNAME + node health，submit real job，收到 durable ACK 后结束；真实工作继续由 Go Node 的独立 worktree/worker slot 执行。

旧 `matrix slot [1,2,3]` workflow 暂时保留作 A/B fallback。

## 9. P1 Batch-3：go-tool 接线

OpenWorker `5cc8b44d` 新增 O87 node control workflow，提供：

```text
node.status
job.status
job.cancel
job.retry
queue.drain queued|all
```

go-tool-runtime `8b2be98c` 新增：

```text
openworker.node.o87.control
openworker.case0004.worklist-state.node
```

Capability 描述已经写入负面知识：GitHub Action completed 只表示 dispatch/control workflow 完成，真实业务状态必须继续通过 durable `job_id` 查询。

## 10. P1 Batch-4：原生 Windows Service Host

本批不使用 NSSM，也不把普通 console exe 硬塞给 SCM。

新增/调整：

- `6cf96748`：把 node lifecycle 抽成可复用 `runNode(ctx,cfg)`；
- `d6e9b935`：`openworker-node.exe` 支持 console 与 `-service` 双模式；
- `f0518c7c`：Windows 专用 `service_windows.go`，使用 Go 原生 Windows Service Control Manager protocol；
- `d4813f94`：非 Windows `-service` fail-closed；
- `12c68ce0`：加入 `golang.org/x/sys/windows/svc` 依赖。

服务名固定：

```text
OpenWorkerNode
```

SCM Stop/Shutdown 会 cancel node context，HTTP server graceful shutdown，再由 runtime 停 worker/process。

## 11. P1 Batch-4：Windows 安装/升级入口

提交 `87ce1151` 新增：

```text
scripts/install_openworker_node_service.ps1
```

行为：

```text
管理员权限检查
-> 停现有 OpenWorkerNode
-> 复制新版 openworker-node.exe
-> sc.exe create/config start=auto
-> 配置失败自动 restart
-> Start-Service
-> /healthz 自检
-> 输出 machine-readable install receipt
```

默认路径：

```text
C:\ProgramData\OpenWorker\bin\openworker-node.exe
C:\ProgramData\OpenWorker\node\openworker-node.sqlite3
```

默认：`127.0.0.1:8787`、4 workers。

## 12. P1 Batch-4：Build Identity / Node 自检

`bbe6e68a` 新增 `internal/buildinfo`，可通过 ldflags 写入：

```text
version
commit
build_time
```

`510438ee` 把 build identity 加到：

```text
GET /healthz
GET /v1/node/info
GET /v1/node/status
```

因此不只知道 node 在线，也能知道当前常驻服务到底跑的是哪一个 commit。

## 13. P1 Batch-4：Durable Job Event Ledger

`5d44736c` / `db50735f` 新增 job event 查询：

```text
GET /v1/jobs/{job_id}/events?limit=100
```

`69b26712` 补齐运行轨迹事件：

```text
running
succeeded
failed
timed_out
cancel_requested
cancelled
drained
retried
```

因此 cancel/drain/retry 不再只有“目前状态”，也能追出“为什么变成这个状态”。

`1f333dd4` 扩充 self-hosted 验证：失败 job 必须出现 durable `failed` event；retry 后执行 `drain all`，event ledger 必须出现 `drained`。

## 14. P1 Batch-4：O87 服务安装 workflow

提交 `2b2800b7` 新增：

```text
.github/workflows/bootstrap-openworker-node-o87.yml
```

它会在 `DESKTOP-O87PJNR`：

```text
Go build
-> ldflags 注入 GITHUB_SHA/build_time
-> install/upgrade OpenWorkerNode service
-> GET /v1/node/status
-> 验证 service build.commit == GITHUB_SHA
```

这会成为 O87 本机执行核心的 authority bootstrap。

## 15. P1 Batch-4：Case 0004 独立结果验证

提交 `ab7c830b` 新增：

```text
.github/workflows/case0004-o87-worklist-state-node-verify.yml
```

输入 durable `job_id` 后，它不会看原 dispatch Action 是否绿色，而是独立执行：

```text
GET /v1/jobs/{job_id}
-> 必须 status=succeeded
-> GET /v1/jobs/{job_id}/events
-> 检查本机 .openworker/evidence/latest-worklist-state-node.json
-> artifact.job_id 必须等于查询 job_id
-> artifact.machine 必须等于 O87
-> 形成 evidence/case0004/latest-node-worklist-state-result.json
-> commit/push GitHub
```

这样形成两条独立证据链：

```text
Dispatch receipt = Action 成功派工
Result receipt   = Go Node 真实完成 + 实体成果
```

## 16. 当前真实迁移状态

截至本文档更新：代码已完成，但仍未取得以下 REAL receipt，因此不宣称 VERIFIED：

1. O87 `OpenWorkerNode` service 的 Running + build.commit receipt；
2. Case 0004 新版 dispatch 的 durable ACK；
3. 对应 `job_id` 的 final `succeeded`；
4. durable event ledger；
5. 本机实体 `latest-worklist-state-node.json`；
6. GitHub `latest-node-worklist-state-result.json`。

当前结论：**P1 Batch-4 IMPLEMENTED，等待 O87 服务与真实案例验收。**

## 17. 下一批 P1

1. 更细的 restart recovery：PID 存活检查，而不是启动时一律 stale；
2. 把 service bootstrap 复制到 UL7 / ODA；
3. node capabilities / GPU / tool inventory；
4. 统一三机 node heartbeat/lease，为 P2 cluster registry 做准备；
5. 真实 Case 0004 跑通后，把同样 dispatch/result 分离模式复制到 Case 0002/0003。

## 18. P2：三机 Cluster

UL7 / ODA / O87 各运行 `openworker-node.exe`。下一阶段增加 registry heartbeat/lease、node capabilities、cluster status/jobs、node-to-node query、`machine=any` capability-aware scheduler、跨 node resource lease 与 failover policy。

目标：

```text
openworker.node.status
openworker.job.status
openworker.cluster.status
openworker.cluster.jobs
```

## 19. 验收铁律

真实验证必须覆盖：四任务并行、第五排队、同锁串行且不占死 worker、hang 不阻塞其他 workers、timeout 回收 slot、cancel 终止 process tree、drain queued、drain all、重复 drain、重复 dispatch 幂等、restart lost running -> recover/stale、stale 可显式 retry、Action `_work` worktree 语义、COMPUTERNAME fail-closed、Action durable ACK 后独立结束、Windows Service SCM stop/start/restart、build identity 对齐，以及真实 Case 在 Action 结束后继续由 Go Node 完成。

## 20. 最终目标

OpenWorker 从 GitHub Actions 驱动的单 runner 执行，升级为 OpenWorker 自己拥有的三节点、多 Agent、可并行、可恢复、可观察的本机执行系统。GitHub Actions 保留版本、入口、CI 与证据职责，不再成为长任务 scheduler。
