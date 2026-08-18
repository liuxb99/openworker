# OpenWorker 纯 Go 本机执行核心与三机多 Agent 调度设计

日期：2026-08-18
状态：DESIGN LOCKED — READY FOR IMPLEMENTATION

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

但本机执行核心有不同要求：

1. 常驻 Windows service；
2. 高频 heartbeat；
3. 多子进程并发；
4. process tree kill；
5. timeout / cancel 必须可靠；
6. queue 与资源锁不能被某个 Python agent 卡住；
7. 三台电脑之间需要轻量、长期稳定、低资源占用的节点服务；
8. 后续可直接做成单 exe 部署。

因此 Go 层不是替代 OpenWorker，而是成为 OpenWorker 的**执行内核**。

## 3. 目标架构

```text
GitHub Action
   |
   | submit + durable ACK
   v
+----------------------------------+
| openworker-node.exe              |
|                                  |
| HTTP/RPC API                     |
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
      |       |       |       |
   process process process process
```

默认 V1：

```text
max_workers = 4
```

后续按机器能力动态调整。

## 4. 保留原 Action 工作目录语义

Go Core 不另外发明一套完全不同的执行根。

原 canonical checkout 例如：

```text
D:\actions-runner\_work\openworker\openworker
```

多 Agent 采用同一 `_work` 根下的独立 worktree：

```text
D:\actions-runner\_work\openworker\_agents\A01\openworker
D:\actions-runner\_work\openworker\_agents\A02\openworker
D:\actions-runner\_work\openworker\_agents\A03\openworker
D:\actions-runner\_work\openworker\_agents\A04\openworker
```

业务 workspace 仍保持原路径，例如：

```text
D:\AI-Work\jobs\0003-YUJING-BRIDGE
```

因此现有 scripts、PowerShell、Python、Go tools 仍可沿用 Action 路径习惯。

## 5. GitHub Action 的新职责

GitHub Action 以后只做：

```text
queued
-> runner accepted
-> verify COMPUTERNAME
-> submit to openworker-node.exe
-> receive durable ACK
-> publish dispatch receipt
-> completed
```

`Action completed` 只代表**派工成功**，不代表真实任务成功。

## 6. 三层状态模型

### 6.1 Dispatch status

```text
queued
running
dispatched
completed
failed
```

### 6.2 Worker status

```text
accepted
queued_local
starting
running
blocked
stale
```

### 6.3 Task status

```text
running
producing_artifact
qc
succeeded
failed
timed_out
cancelled
retrying
```

OpenWorker 查询时必须把三层状态同时返回。

## 7. 统一 Job ID

Action、Go Core、Python Control Plane、WorkLedger、artifact、QC receipt 共用同一 `job_id`。

例如：

```text
OWJ-20260818-001
```

另有一次派工的 `dispatch_id`：

```text
OWD-20260818-001
```

重复 `dispatch_id` 必须 idempotent，不得重复执行。

## 8. Go Core durable store

V1 使用纯 Go SQLite driver，避免依赖外部数据库服务。

建议目录：

```text
go-runtime/
  cmd/openworker-node/
  internal/jobstore/
  internal/scheduler/
  internal/worker/
  internal/process/
  internal/locks/
  internal/cluster/
  internal/api/
  internal/receipts/
```

SQLite 至少包含：

```text
jobs
job_events
worker_slots
resource_locks
node_state
cluster_nodes
```

### jobs 关键字段

```text
job_id
dispatch_id
machine
status
priority
command
args_json
cwd
workspace_root
created_at
accepted_at
started_at
finished_at
heartbeat_at
pid
exit_code
stdout_path
stderr_path
timeout_sec
resource_spec_json
lock_spec_json
retry_count
```

## 9. Process Supervisor

Go Core 必须真正拥有子进程生命周期。

至少做到：

- 启动进程；
- 捕获 stdout/stderr；
- 保存 PID；
- heartbeat；
- timeout；
- cancel；
- Windows process tree kill；
- exit code；
- crash/stale detection；
- receipt。

单一 process hang 只能占一个 slot，不得堵住整个 Host。

## 10. Worker Pool

V1：4 个通用 worker slots。

```text
A01
A02
A03
A04
```

四个互不冲突任务必须可真正同时运行。

第五个任务进入 `queued_local`，直到 slot 空出。

后续可扩展：

```text
general-agent x N
blender x N
comfyx x N
gpu-worker x N
```

## 11. Resource Lock

并行必须受控。

V1 至少支持：

- `workspace:<path>` exclusive lock；
- `tool:<name>` lock；
- `gpu:0`；
- `gpu:1`；
- 自定义字符串 lock。

同一个业务 workspace 的写任务不得同时修改同一份成果。

Git code 修改任务使用独立 Git worktree，避免多个 agent 同时 checkout/reset 同一 working tree。

## 12. Queue / Cancel / Drain

Go Core 必须原生提供：

```text
submit
status
list
cancel
drain
retry
recover
```

Drain 两种模式：

```text
drain queued
```

只清未执行任务。

```text
drain all
```

清 queued，并 cancel running。

重复 drain 必须安全，且 receipt 必须列出实际处理的 job IDs。

## 13. Heartbeat 与 stale recovery

每个 node 与 running job 都有 heartbeat。

Host restart 后：

- `queued_local`：保留，重新排程；
- `running` 且 PID 已不存在：标记 `stale`；
- stale 是否 retry 由 policy 决定；
- 禁止把 lost process 标为 succeeded。

## 14. COMPUTERNAME 是机器最终权威

固定机器任务示例：

```text
machine=UL7
computer_name=DESKTOP-UL7V2VV
```

真正执行前 Go Core 必须读取本机 COMPUTERNAME。

不符：fail-closed。

runner label 只是 GitHub 初步路由，不是最终机器权威。

## 15. 三机 Cluster Registry

每台运行自己的：

```text
openworker-node.exe
```

例如：

```text
UL7 -> DESKTOP-UL7V2VV
ODA -> configured ODA host
O87 -> DESKTOP-O87PJNR
```

节点持续发布：

```text
node_id
computer_name
last_heartbeat
lease_until
max_workers
busy_workers
queued_jobs
capabilities
resources
```

lease 过期即视为 unavailable。

## 16. 三机状态查询

必须支持：

```text
openworker.cluster.status
openworker.cluster.jobs
openworker.node.status
openworker.job.status
```

返回至少包含：

```text
UL7 ONLINE 4/8 busy
ODA ONLINE 2/6 busy
O87 OFFLINE last_seen=...
```

以及每个 job：

```text
job_id
node
agent_slot
pid
status
heartbeat_age
workspace
tool
```

## 17. Scheduler 路由

### 固定机器

```text
machine=UL7
```

只允许 UL7。

UL7 offline / unavailable 时直接 blocked/fail-closed，不可擅自换机。

### 任意机器

```text
machine=any
```

才允许依据：

- capability；
- free slots；
- queue depth；
- resource locks；
- GPU availability；

选择机器。

## 18. Python 与 Go 的接口

Python Control Plane 不直接管理 Windows PID。

Python 通过 Go Core API 操作：

```text
POST /v1/jobs
GET  /v1/jobs/{job_id}
GET  /v1/jobs
POST /v1/jobs/{job_id}/cancel
POST /v1/queue/drain
POST /v1/jobs/{job_id}/retry
GET  /v1/node/status
GET  /v1/cluster/status
GET  /v1/cluster/jobs
```

Go Core 返回 durable receipt；Python 再映射进 WorkLedger / Case Worklist / knowledge layer。

## 19. go-tool 边界

go-tool 只暴露能力给大模型：

```text
openworker.job.submit
openworker.job.status
openworker.job.cancel
openworker.queue.drain
openworker.cluster.status
openworker.cluster.jobs
```

已知失败的派工方法、错误工具组合、不可重试条件，可写入 go-tool 的负面工具知识，避免模型重复失败。

## 20. 第一批 P0 实作

先实现单机 Go Core，不同时展开三机调度：

1. 新建 `go-runtime` Go module；
2. `openworker-node.exe`；
3. SQLite durable job store；
4. max_workers=4；
5. submit/status/list/cancel/drain；
6. command/cwd/env 执行；
7. stdout/stderr 持久化；
8. timeout；
9. process tree cancel；
10. heartbeat；
11. stale recovery；
12. dispatch idempotency；
13. COMPUTERNAME authority；
14. HTTP API；
15. receipts。

## 21. 第二批 P1

1. Git worktree slot manager；
2. workspace/tool/GPU locks；
3. Python Control Plane adapter；
4. GitHub Action submit bridge；
5. 一条真实 case workflow 从长执行改成 submit -> ACK -> exit；
6. go-tool capability metadata。

## 22. 第三批 P2

1. 三机 registry；
2. heartbeat / lease；
3. cluster status/jobs；
4. node-to-node query；
5. `machine=any` scheduler；
6. capability-aware routing；
7. cluster failover policy。

## 23. P0 验收铁律

P0 不接受“API 返回 200”作为完成。

必须真实验证：

1. 四个 shell job 实际时间重叠；
2. 第五个 job 在 slots 满时维持 queued；
3. 一个 hang job 不影响其他三个继续完成；
4. timeout 能回收 slot；
5. cancel 能终止 process tree；
6. drain 一次清完 queued；
7. 重复 drain 安全；
8. 重复 dispatch_id 不产生第二份执行；
9. Host restart 后 queued job 能恢复；
10. lost running process 被标记 stale；
11. cwd 可保持在 Action `_work` 相容目录；
12. COMPUTERNAME 不符时 fail-closed。

## 24. 最终目标

OpenWorker 从：

```text
GitHub Actions 驱动的本机执行
```

升级为：

```text
OpenWorker 自己拥有的三节点、多 Agent、可恢复、可观察、本机执行系统
```

GitHub Actions 继续存在，但只作为版本控制生态中的派工入口和 CI/证据通道，不再成为本机长任务调度的核心。