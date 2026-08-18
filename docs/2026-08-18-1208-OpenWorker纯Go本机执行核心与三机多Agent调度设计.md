# OpenWorker 纯 Go 本机执行核心与三机多 Agent 调度设计

日期：2026-08-18
状态：P0 BATCH-1 IMPLEMENTED — WAITING FOR SELF-HOSTED ACTION VERIFICATION

## 1. 结论

OpenWorker 不只在现有 Python server 上增加几个本机执行 API，而是新增一层**纯 Go Local Execution Core**。

最终分层：

```text
ChatGPT / Knowledge Graph / go-tool
                |
                v
     OpenWorker Python Control Plane
                |
                v
       OpenWorker Go Execution Core
                |
        Local Scheduler / Agent Host
          /          |          \
        UL7         ODA         O87
```

职责明确分离：

- Python：案例、WorkLedger、知识、业务流程、审核、Drive、上层 orchestration。
- Go：本机真实进程、durable queue、多 Agent slots、资源锁、heartbeat、timeout、cancel、drain、stale recovery、三机 node 状态与低延迟调度。
- GitHub Action：保留为入口/transport，不再承担长期执行器职责。
- go-tool：向大模型暴露 OpenWorker 能力，不实现 scheduler 本身。

## 2. 为什么要独立 Go 层

现有 OpenWorker 主体是 Python，已有 FastAPI、Agent、Worklist、工程流程、审计等大量能力，继续保留最合适。

但本机执行核心有不同要求：常驻 Windows service、高频 heartbeat、多子进程并发、process tree kill、可靠 timeout/cancel、独立 durable queue 与三机节点服务。因此 Go 层不是替代 OpenWorker，而是成为 OpenWorker 的**执行内核**。

## 3. 目标架构

```text
GitHub Action
   |
   | submit + durable ACK
   v
+----------------------------------+
| openworker-node.exe              |
| HTTP API                         |
| Durable Job Store                |
| Local Scheduler                  |
| Worker Pool                      |
| Resource Lock Manager            |
| Process Supervisor               |
| Heartbeat / Lease                |
| Node/Cluster Status              |
+----------------------------------+
      |       |       |       |
    A01     A02     A03     A04
```

V1 默认 `max_workers=4`。

## 4. 保留原 Action 工作目录语义

Go Core 不另外发明一套完全不同的执行根。原 canonical checkout 例如：

```text
D:\actions-runner\_work\openworker\openworker
```

多 Agent 后续采用同一 `_work` 根下独立 worktree：

```text
D:\actions-runner\_work\openworker\_agents\A01\openworker
D:\actions-runner\_work\openworker\_agents\A02\openworker
D:\actions-runner\_work\openworker\_agents\A03\openworker
D:\actions-runner\_work\openworker\_agents\A04\openworker
```

业务 workspace 仍保持既有路径，例如 `D:\AI-Work\jobs\0003-YUJING-BRIDGE`。程式码 checkout 与业务 workspace 分离。

## 5. GitHub Action 新职责

```text
queued -> runner accepted -> verify COMPUTERNAME -> submit to Go Core -> durable ACK -> completed
```

`Action completed` 只代表派工成功，不代表真实任务成功。

## 6. 三层状态

Dispatch：`queued/running/dispatched/completed/failed`。

Worker：`accepted/queued_local/starting/running/blocked/stale`。

Task：`running/producing_artifact/qc/succeeded/failed/timed_out/cancelled/retrying`。

## 7. 统一 Job ID

Action、Go Core、Python Control Plane、WorkLedger、artifact、QC receipt 共用 `job_id`；一次派工另有 `dispatch_id`。重复 `dispatch_id` 必须 idempotent。

## 8. Go Core durable store

V1 使用 SQLite + 纯 Go driver，不依赖外部数据库服务。

当前目录：

```text
go-runtime/
  cmd/openworker-node/
  internal/model/
  internal/store/
  internal/runtime/
  internal/api/
```

后续继续拆出 locks/cluster/receipts/worktree。

## 9. Process Supervisor

负责启动真实子进程、stdout/stderr、PID、heartbeat、timeout、cancel、Windows process tree kill、exit code 与 stale recovery。单一 process hang 只能占一个 slot。

## 10. Worker Pool

V1 为 4 个通用 worker slots。四个互不冲突任务必须可同时运行，第五个保持 `queued_local`。

## 11. Resource Lock

P1 补齐 workspace/tool/GPU/custom string locks。Git code 修改任务采用独立 Git worktree，禁止多个 agent 同时 checkout/reset 同一 working tree。

## 12. Queue / Cancel / Drain

目标能力：`submit/status/list/cancel/drain/retry/recover`。

P0 Batch-1 已实现：`submit/status/list/cancel/drain queued`。`drain all`、retry policy 与更完整 recover receipt 放到后续批次。

## 13. Heartbeat 与 stale recovery

running job 周期 heartbeat。Host restart 时旧 `starting/running` 不可假装成功，当前 Batch-1 会 fail-closed 标记 stale；后续再细化 PID 存活检查与 retry policy。

## 14. COMPUTERNAME 是最终机器权威

固定机器任务在 Go Core durable accept 前检查实际 hostname；不符 fail-closed。runner label 只做 GitHub 初步路由。

## 15. 三机 Cluster Registry

P2：UL7 / ODA / O87 各运行 `openworker-node.exe`，发布 node_id、computer_name、heartbeat、lease、worker slots、queue depth、capabilities 与资源状态。

## 16. 三机状态查询

目标接口：`openworker.cluster.status`、`openworker.cluster.jobs`、`openworker.node.status`、`openworker.job.status`。

## 17. Scheduler 路由

`machine=<fixed>` 只允许指定节点，离线时 fail-closed；只有 `machine=any` 才允许按 capability、free slots、queue depth、locks、GPU 可用性自动选择节点。

## 18. Python 与 Go 接口

Python 不直接管理 Windows PID，通过 Go Core HTTP API：

```text
POST /v1/jobs
GET  /v1/jobs/{job_id}
GET  /v1/jobs
POST /v1/jobs/{job_id}/cancel
POST /v1/queue/drain
GET  /v1/node/status
```

后续增加 retry/cluster API。

## 19. go-tool 边界

go-tool 只暴露能力，不实现 scheduler。后续暴露 `openworker.job.submit/status/cancel`、`openworker.queue.drain`、`openworker.cluster.status/jobs`。已知失败路径同步为负面工具知识。

## 20. P0 Batch-1 实作进度

### 已完成代码

提交：`9a528a3afa64d278d0d2dbc9268aa53e84dd06dc`

已加入：

- `go-runtime/go.mod`
- `cmd/openworker-node/main.go`
- `internal/model/job.go`
- `internal/store/store.go`
- `internal/runtime/manager.go`
- `internal/api/server.go`
- store/runtime tests

已实现：

- SQLite durable job store；
- WAL + busy timeout；
- job_id / dispatch_id idempotency；
- machine fail-closed；
- priority queue claim；
- 4 worker pool；
- shell command + cwd + env；
- stdout/stderr 持久化；
- PID；
- heartbeat；
- timeout；
- cancel；
- Windows `taskkill /T /F` process-tree kill；
- queued drain；
- stale startup recovery；
- `/healthz`；
- `/v1/node/status`；
- `/v1/jobs` submit/list；
- `/v1/jobs/{jobID}` status；
- `/v1/jobs/{jobID}/cancel`；
- `/v1/queue/drain?mode=queued`。

### 验证 workflow

提交：`990337c163c11324e5b9f73c40052ed6261738c2`

新增 `.github/workflows/openworker-go-runtime-p0.yml`，在原 self-hosted Windows Action workspace 执行：

1. 显示 COMPUTERNAME / GITHUB_WORKSPACE / PWD；
2. Go 1.23；
3. `go mod tidy`；
4. `go build ./cmd/openworker-node`；
5. `go test ./... -count=1 -v`；
6. 单独执行 `TestFourWorkersRunAndFifthQueues`。

当前状态：**代码已提交，真实 self-hosted Action 验证尚未取得 completed receipt，因此不得宣称 P0 已通过。**

## 21. P1

- Git worktree slot manager；
- workspace/tool/GPU locks；
- Python Control Plane adapter；
- GitHub Action submit bridge；
- 一条真实 case workflow 改成 submit -> ACK -> exit；
- go-tool capability metadata。

## 22. P2

- 三机 registry；
- heartbeat / lease；
- cluster status/jobs；
- node-to-node query；
- `machine=any` scheduler；
- capability-aware routing；
- cluster failover policy。

## 23. P0 验收铁律

必须真实验证：四任务并行、第五任务排队、hang 不阻塞其他 workers、timeout 回收 slot、cancel 终止 process tree、drain 一次清完 queued、重复 drain 安全、重复 dispatch 不重复执行、restart 恢复 queued、lost running 标 stale、cwd 保持 Action `_work` 相容、COMPUTERNAME 不符 fail-closed。

## 24. 最终目标

OpenWorker 从“GitHub Actions 驱动的本机执行”升级成“OpenWorker 自己拥有的三节点、多 Agent、可恢复、可观察、本机执行系统”。GitHub Actions 继续作为派工入口、CI 与证据通道，不再成为本机长任务调度核心。
