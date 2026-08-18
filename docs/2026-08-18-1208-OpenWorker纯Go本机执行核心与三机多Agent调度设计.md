# OpenWorker 纯 Go 本机执行核心与三机多 Agent 调度设计

日期：2026-08-18
状态：P2 BATCH-2 IMPLEMENTED — CLUSTER JOB/AGENT/REMOTE-SUBMIT CONTRACT READY

## 1. 架构结论

OpenWorker 的 Python 层继续负责案例、WorkLedger、知识、审核与上层 orchestration；纯 Go `openworker-node.exe` 负责本机 durable execution 与三机 cluster observation/routing。GitHub Action 只保留 transport/CI/evidence。Action completed 永远不等于业务 succeeded。

## 2. P0 ~ P2 Batch-1 已完成摘要

已完成：SQLite durable queue、4 worker pool、Action `_work` worktree、resource locks、真实 process supervisor、timeout/cancel/process-tree kill、drain/retry/recover、Python adapter、durable ACK、Windows Service、build identity、job events、Case 0004 submit->ACK->exit、restart PID reconciliation、tool/GPU/capability inventory、15 秒 node lease、UL7/ODA/O87 service bootstrap、纯 Go Cluster Registry、peer heartbeat controller，以及 capability/load-aware route decision。

真实三机 self-hosted/network receipt 尚未取得，因此仍不宣称 REAL VERIFIED。

## 3. P2 Batch-2：AgentSlot durable authority

本批先修正一个结构性回归：先前 runtime 虽然有 worker slot 概念，但 `agent_slot` 没有完整保留在 SQLite job authority 中，cluster 无法可靠回答 A01/A02 正在跑谁。

提交：

- `f87c60d7`：`model.Job` 恢复 `agent_slot`；
- `2e747eda`：SQLite schema/migration/scan/retry/requeue/MarkRunning 全部持久化 `agent_slot`；
- `c5fd2d6e`：runtime 启动真实 process 时把 worker slot 写入 durable job。

现在 cluster_agents 不再只显示 `busy_workers=2`，而可以形成：

```text
node=UL7 slot=1 busy=true job_id=...
node=UL7 slot=2 busy=false
node=O87 slot=3 busy=true job_id=...
```

## 4. P2 Batch-2：Cluster Jobs / Agents 聚合

提交 `c6883aa8` 新增 `internal/cluster/jobs.go`。

新增能力：

```text
Jobs(limit)
Agents()
JobStatus(job_id)
Submit(cluster request)
JobCounts()
```

`cluster_jobs` 会从所有 lease-valid online nodes 抓 `/v1/jobs`，每笔 job 同时保留 `node_id + endpoint + durable Job`。

`cluster_agents` 根据每台 node 的 max_workers 与 job.agent_slot 建立 A01..Axx 状态，因此可以看到 worker slot 与真实 job 的对应关系。

`cluster job status` 会逐个 online node 查询指定 durable `job_id`，找到后返回该 job 所在 node 与 endpoint；不会根据 Action run 猜测任务位置。

## 5. P2 Batch-2：Remote Durable Submit

Cluster Submit 输入：

```json
{
  "job": {
    "job_id": "...",
    "dispatch_id": "...",
    "machine": "any",
    "command": "...",
    "cwd": "..."
  },
  "required_capabilities": ["bridge", "blender"]
}
```

流程：

```text
Registry.Select(machine, capabilities)
-> online lease only
-> fixed machine 不漂移 / machine=any 才自动选
-> POST selected-node /v1/jobs
-> selected node 自己做 CWD / COMPUTERNAME / durable idempotency 检查
-> cluster 必须收到 matching job_id + dispatch_id + accepted=true
-> 才返回 remote durable ACK
```

因此 Cluster scheduler 不绕过单节点的 fail-closed contract。

`0ee07129` 使用 `httptest` 覆盖 remote durable submit、job status 与 agent slot 聚合。

## 6. P2 Batch-2：本机也纳入 Registry

提交 `084829f1`：每个 node 启动 cluster controller 时会把自己的 local endpoint 一并加入 observation list，再加 configured peers。

这修正了一个潜在问题：如果 registry 只有 peers，`machine=any` 可能永远不会选到当前这台最空闲的机器。

对于 `0.0.0.0`/`::` listen，self-probe 自动使用 `127.0.0.1`，避免拿 wildcard address 当 client endpoint。

## 7. P2 Batch-2：Cluster API 扩充

提交 `1638d492` 新增：

```text
GET  /v1/cluster/jobs?limit=100
GET  /v1/cluster/jobs/{job_id}
GET  /v1/cluster/agents
POST /v1/cluster/jobs
```

原有：

```text
GET /v1/cluster/status
GET /v1/cluster/capabilities
GET /v1/cluster/route
```

`cluster.status` 现在同时附带 cluster job counts。

部分 peer 查询失败时允许返回已有结果并带 `partial_error`；所有 online peer 都不可查询时才 fail，避免一台离线拖垮整个 cluster observation。

## 8. P2 Batch-2：Python Control Plane

提交 `d138c314` 扩充 `coworker/node_client.py`：

```text
cluster_status
cluster_capabilities
cluster_jobs
cluster_agents
cluster_job_status
cluster_route
cluster_submit
```

`8569e309` 扩充 Python contract test。

因此 Python 上层案例/WorkLedger 不需要自己拼 cluster HTTP。

## 9. P2 Batch-2：go-tool Cluster Capability

OpenWorker 提交 `c88b6ef8` 新增：

```text
.github/workflows/openworker-cluster-control-o87.yml
```

作为现阶段 cluster Action transport，提供：

```text
status
capabilities
jobs
agents
job.status
route
submit
```

go-tool-runtime 提交 `c364eb83` 新增：

```text
openworker.cluster.control
```

负面知识明确写入：

- Action completed 只代表 cluster transport 完成；
- submit success 只代表 selected node 已 durable ACK；
- 真实业务成功仍必须继续查 cluster `job.status`；
- expired lease / network unreachable 节点不可继续派工；
- fixed machine 不得因为其他机器空闲而漂移。

## 10. 当前 Cluster API

```text
GET  /v1/cluster/status
GET  /v1/cluster/capabilities
GET  /v1/cluster/route
GET  /v1/cluster/jobs
GET  /v1/cluster/jobs/{job_id}
GET  /v1/cluster/agents
POST /v1/cluster/jobs
```

单节点 API 继续保留，不被 cluster layer 取代。

## 11. 目前仍存在的真实网络缺口

remote durable submit **代码合约已完成**，但当前三机 Windows Service 默认仍主要使用：

```text
127.0.0.1:8787
```

这只允许本机访问，不能据此宣称 UL7/ODA/O87 已经互相可达。

下一步必须先确定安全且稳定的三机 endpoint，例如绑定各机 Tailscale/LAN address，并取得：

```text
UL7 -> ODA /v1/node/status
UL7 -> O87 /v1/node/status
ODA -> UL7 ...
O87 -> UL7 ...
```

的真实 receipt，才可以宣称 remote submit REAL 可用。

当前 `-peers` / service installer `-Peers` 已支持持久化 endpoint，但 endpoint 本身仍需真实机器配置与验证。

## 12. 当前调度铁律

- COMPUTERNAME 是 fixed machine 最终 authority；
- fixed machine 永不自动漂移；
- machine=any 才允许 capability/load routing；
- expired lease 绝不接新任务；
- cluster submit 必须取得 selected node durable ACK；
- agent slot 必须从 durable job authority 读取；
- Action ACK、cluster ACK、task succeeded 是三件不同的事；
- peer failure 不可拖死其他在线节点；
- stale job 仍只能显式 retry。

## 13. 尚未完成的 P2

1. 三机真实可达 endpoint 配置与 firewall/Tailscale 验证；
2. remote durable submit REAL 三机 smoke；
3. cluster cancel/retry/drain 直接按 job 所在 node 转发；
4. shared durable cluster history / dispatch routing ledger；
5. endpoint discovery/config receipt；
6. go-tool 不依赖单一 O87 authority 的多节点 fallback；
7. Case 0002/0003/0004 真正改成 cluster-aware dispatch。

## 14. 下一批 P2

优先补：

```text
cluster dispatch ledger
cluster job cancel/retry
remote drain
endpoint/advertise contract
three-node connectivity verification workflow
```

然后才把真实案例从 fixed node dispatch 逐步升级到 `machine=any + capability`；固定机器案例仍保持 fixed，不为了“cluster 化”而强行漂移。

## 15. 验收铁律

持续验证多 worker、resource lock、timeout/cancel/drain、dispatch 幂等、restart PID recovery、SCM service、inventory/lease。P2 额外必须覆盖：agent_slot 权威、job 聚合、peer partial failure、expired node 不路由、fixed machine 不漂移、remote ACK id 一致，以及三机真实 network reachability。

## 16. 最终目标

OpenWorker 成为自己拥有的三节点、多 Agent、可并行、可恢复、可观察、可按 capability 选择执行节点的本机优先系统。GitHub Actions 只保留版本、入口、CI 与证据通道，不再承担长任务 scheduler。
