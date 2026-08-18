# OpenWorker 纯 Go 本机执行核心与三机多 Agent 调度设计

日期：2026-08-18
状态：P2 BATCH-1 IMPLEMENTED — CLUSTER OBSERVATION / ROUTING CONTRACT READY

## 1. 架构结论

OpenWorker 继续采用双层结构：Python 保留案例、WorkLedger、知识、审核、Drive 与上层 orchestration；纯 Go `openworker-node.exe` 是本机执行与三机状态核心。GitHub Action 只负责 transport / CI / evidence，Action completed 永远不等于业务 succeeded。

## 2. P0 ~ P1 已完成摘要

已完成 SQLite durable queue、4 worker pool、Action `_work` worktree、resource locks、真实 process supervisor、heartbeat/timeout/cancel、process-tree kill、drain queued/all、retry/recover、Python adapter、durable ACK、原生 Windows Service、build identity、durable events、Case 0004 submit->ACK->exit 样板、restart PID reconciliation、tool/GPU/capability inventory、15 秒 node lease，以及 UL7/ODA/O87 service bootstrap。

真实三机 self-hosted receipt 仍待取得，因此没有把 IMPLEMENTED 写成 REAL VERIFIED。

## 3. P2 Batch-1：纯 Go Cluster Registry

提交 `06f487ea` 新增 `go-runtime/internal/cluster/registry.go`。

Registry 节点模型包含：

```text
node_id
machine
endpoint
online
heartbeat_at
lease_until
max/busy/free workers
queued_jobs
capabilities
inventory
build
last_error
```

Registry 不把“曾经在线”误当成“现在在线”。每次读取 Nodes 时都按当前时间重新判断 `lease_until`；lease 过期节点自动视为 offline。

## 4. P2 Batch-1：Capability-aware Route Selection

Registry 新增 `Select(machine, requiredCapabilities)`：

```text
固定 machine
  -> 只允许该 machine/node_id
machine=any
  -> online lease
  -> capability 全部满足
  -> free_workers 较多优先
  -> 同 free_workers 时 queued_jobs 较少优先
```

没有合格节点时 fail-closed 返回 `no online compatible node`，不会随便把任务丢给错误机器。

提交 `4240fd23` 增加测试，覆盖：

- expired lease 节点不能被调度；
- capability 不匹配不能被调度；
- `machine=any` 优先 free worker 较多节点。

## 5. P2 Batch-1：Heartbeat Controller

提交 `41e2fe0a` 新增 cluster Controller。

每个 OpenWorker Node 可以配置多个 peer endpoint，每 5 秒抓取：

```text
GET <peer>/v1/node/status
```

抓取成功则更新 heartbeat/lease/capability/load；抓取失败保留节点身份并标 offline/error。三台机器不需要同时永远在线，离线节点只是失去 lease，不会破坏其他节点执行。

当前实现是轻量 peer-observation registry，不做复杂共识协议；符合三台个人工作机不同时间上线的实际情况。

## 6. P2 Batch-1：Node Cluster 配置

提交：

- `4a59edf9`：node lifecycle 接入 cluster Controller；
- `84dbd2a9`：新增 `openworker-node.exe -peers`；
- `93962d5c`：Windows service installer 支持 `-Peers`，持久写入 SCM binPath。

也可使用：

```text
OPENWORKER_CLUSTER_PEERS
```

因此 cluster peer 配置与 capability 一样，不依赖一次性的 Action 环境变量。

## 7. P2 Batch-1：Cluster API

提交 `13b52676` 新增：

```text
GET /v1/cluster/status
GET /v1/cluster/capabilities
GET /v1/cluster/route?machine=any&capabilities=bridge,blender
```

`cluster.status` 返回 observed nodes、online/offline 数量与时间；`cluster.capabilities` 返回每节点 capability；`cluster.route` 只做路由决策，不直接执行任务，便于先观察/验证 scheduler 判断。

## 8. 当前 Go Node API

```text
GET  /healthz
GET  /v1/node/info
GET  /v1/node/status
GET  /v1/cluster/status
GET  /v1/cluster/capabilities
GET  /v1/cluster/route
POST /v1/jobs
GET  /v1/jobs
GET  /v1/jobs/{job_id}
GET  /v1/jobs/{job_id}/events
POST /v1/jobs/{job_id}/cancel
POST /v1/jobs/{job_id}/retry
POST /v1/queue/drain?mode=queued|all
```

## 9. 三机目标拓扑

```text
UL7 :8787 -> case0003,bridge,blender,scenex,engineering,drive-review
ODA :8787 -> case0002,comfyx,minimax-h3,video,storyboard,presentation
O87 :8787 -> case0004,dwg,story-index,engineering
```

每台 Node 的 `-peers` 指向另外可达节点 endpoint。某台关机后 lease 过期，其他节点仍可看到它 offline，并停止向它做 `machine=any` 路由。

## 10. 当前调度铁律

- COMPUTERNAME 仍是固定机器最终权威；
- capability 只是可执行能力，不替代机器身份；
- fixed machine 不自动漂移；
- `machine=any` 才允许 cluster route；
- expired lease 绝不能接新任务；
- route 目前只返回 selected node，不跨机偷偷 submit；
- Action durable ACK 与真实 job succeeded 分离；
- restart orphan PID 必须先处理再 stale；
- stale 只能显式 retry。

## 11. 尚未完成的 P2

1. `cluster_jobs`：聚合三机 job 状态；
2. `cluster_agents`：发布每个 worker slot 当前 job；
3. cluster route -> remote durable submit；
4. 跨节点 job_id / dispatch_id 幂等；
5. endpoint discovery/配置 receipt；
6. go-tool capability：`openworker.cluster.status/jobs/capabilities/route`；
7. 三机真实网络可达性、lease 过期、恢复上线 REAL 验证；
8. shared cluster durable history。当前 registry 是运行期观察层，不假装成已经完成的中央持久库。

## 12. 下一批 P2

下一批优先补：

```text
cluster_jobs
cluster_agents
remote submit
cluster job status
```

并把 cluster 查询/路由能力同步给 go-tool。等三机 service endpoint REAL 可达后，再决定 shared durable registry authority 的最终持久化位置，不提前引入复杂数据库或共识系统。

## 13. 验收铁律

持续覆盖：多 worker 并行、resource lock、timeout/cancel/drain、dispatch 幂等、restart PID recovery、Action `_work`、COMPUTERNAME、SCM service、build identity、inventory、lease；P2 新增必须验证 expired node 不路由、capability 不匹配不路由、fixed machine 不漂移、machine=any 才自动选节点、peer failure 不拖死本机执行。

## 14. 最终目标

OpenWorker 从 GitHub Actions 驱动的单 runner 执行，升级为自己拥有的三节点、多 Agent、可并行、可恢复、可观察、本机优先的执行系统。GitHub Actions 保留版本、入口、CI 与证据通道，不再承担长任务 scheduler。
