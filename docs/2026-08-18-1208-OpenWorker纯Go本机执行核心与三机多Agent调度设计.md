# OpenWorker 纯 Go 本机执行核心与三机多 Agent 调度设计

日期：2026-08-18
状态：P2 BATCH-3 IMPLEMENTED — ADVERTISE / FORWARDED CONTROL / DURABLE CLUSTER LEDGER READY, WAITING FOR REAL THREE-NODE CONNECTIVITY

## 1. 架构结论

OpenWorker Python 层继续负责案例、WorkLedger、知识、审核与上层 orchestration；纯 Go `openworker-node.exe` 负责本机 durable execution、三机 observation/routing 与 cluster control。GitHub Action 只保留 transport/CI/evidence。Action completed、cluster durable ACK、task succeeded 三者必须严格区分。

## 2. P0 ~ P2 Batch-2 已完成摘要

已完成 SQLite durable queue、4 worker pool、Action `_work` worktree、resource locks、process supervisor、timeout/cancel/process-tree kill、drain/retry/recover、Python adapter、durable ACK、Windows Service、build identity、job event ledger、restart PID reconciliation、tool/GPU/capability inventory、15 秒 node lease、UL7/ODA/O87 bootstrap、Cluster Registry、capability/load route、cluster_jobs、cluster_agents、agent_slot durable authority、remote durable submit、cluster job status，以及 go-tool `openworker.cluster.control`。

真实三机 network receipt 仍未取得，因此不宣称 REAL VERIFIED。

## 3. P2 Batch-3：Listen / Advertise / Peers 正式分层

本批解决先前最大的网络语义缺口：`127.0.0.1:8787` 只能代表本机 listen，不能当作别人可访问我的地址。

提交：

- `8e063909`：`openworker-node.exe` 新增 `-advertise`；
- `f6fcb768`：nodeConfig 正式分成 `Listen / Advertise / Peers`；
- `93f16e8c`：peer Probe 会读取 node status 的 `advertise_endpoint`，Registry 保存权威对外 endpoint；
- `2eb68b41`：Windows Service installer 支持 `-Advertise` 并持久写入 SCM binPath；
- `da34aa50`：self observation 仍走本机 listen/loopback，不绕 advertise；对外 registry endpoint 则使用 advertise。

环境变量也支持：

```text
OPENWORKER_NODE_ADVERTISE
OPENWORKER_CLUSTER_PEERS
```

默认仍保持 loopback，不为了 cluster 自动暴露所有网卡。只有显式配置稳定 LAN/Tailscale endpoint 后才进入跨机模式。

## 4. Node Status 网络权威

`GET /healthz`、`GET /v1/node/info`、`GET /v1/node/status` 现在都发布：

```text
machine
advertise_endpoint
heartbeat_at
lease_until
build
inventory
```

Peer 可以通过一个 bootstrap/source endpoint 首次探测，然后改用 node 自己声明的 advertise endpoint 做后续 remote submit/control。

## 5. P2 Batch-3：Durable Cluster Dispatch Ledger

提交 `dfde0edd` 新增：

```text
go-runtime/internal/store/cluster_ledger.go
```

新增 durable tables：

```text
cluster_dispatches
cluster_control_events
```

每次 cluster remote submit 成功取得 matching durable ACK 后，记录：

```text
job_id
dispatch_id
requested_machine
selected_node_id
selected_machine
endpoint
required_capabilities
accepted_at
created_at
```

控制操作也会记录：

```text
submit / submit_failed
cancel / cancel_failed
retry / retry_failed
drain.queued / drain.all / drain_failed
```

这形成 cluster routing history，但它不取代 selected node 自己的 final job/event ledger。

`dc3b34ba` 增加 durable dispatch/control ledger round-trip test。

## 6. P2 Batch-3：跨节点 Cancel / Retry / Drain 转发

提交 `77d9ca9d` 扩充 Cluster Controller：

```text
JobAction(job_id, cancel|retry)
Drain(machine, queued|all)
```

Job cancel/retry 流程：

```text
cluster JobStatus(job_id)
-> 找出当前 online owning node
-> POST owning-node /v1/jobs/{job_id}/cancel|retry
-> 回传 node_id/machine/endpoint/response
-> cluster_control_events durable 记录
```

Cluster drain 明确禁止模糊 destructive intent：

```text
machine=<fixed node/machine>
或
machine=all
```

不接受用 `machine=any` 表达清队列意图，避免随机挑一台机器清错队列。

`e5a57361` 测试 remote submit + status + cancel + retry + drain forwarding。

## 7. P2 Batch-3：Cluster API 扩充

提交 `dfbd13c3` 后，Cluster API 包含：

```text
GET  /v1/cluster/status
GET  /v1/cluster/capabilities
GET  /v1/cluster/route
GET  /v1/cluster/jobs
GET  /v1/cluster/jobs/{job_id}
GET  /v1/cluster/agents
POST /v1/cluster/jobs
POST /v1/cluster/jobs/{job_id}/cancel
POST /v1/cluster/jobs/{job_id}/retry
POST /v1/cluster/queue/drain?machine=<node|all>&mode=queued|all
GET  /v1/cluster/dispatches
GET  /v1/cluster/dispatches/{job_id}
GET  /v1/cluster/control-events
```

Cluster submit 成功后必须先写 durable `cluster_dispatches`；失败 submit/control 也会进入 control ledger。

## 8. P2 Batch-3：Python Control Plane 与 go-tool 同步

`d581a5f0` 扩充 `coworker/node_client.py`：

```text
cluster_job_cancel
cluster_job_retry
cluster_drain
cluster_dispatches
cluster_dispatch
cluster_control_events
```

OpenWorker `fe55b501` 扩充 O87 cluster transport workflow；go-tool-runtime `ffd6b3d2` 更新 `openworker.cluster.control`，新增：

```text
job.cancel
job.retry
queue.drain
dispatches
dispatch
control.events
```

负面知识明确写入：cluster dispatch ledger 只证明“曾在某 node durable ACK”，不能据此宣称业务成功；真正结果仍查 owning node job/event ledger。

## 9. P2 Batch-3：三机 Service 网络配置入口

UL7 / ODA / O87 三条 bootstrap workflow 都新增：

```text
listen
advertise
peers
```

提交：

- `05b5337e` UL7；
- `667b5140` ODA；
- `d0f46790` O87。

因此可选择：

```text
listen = 某机 Tailscale/LAN IP:8787 或显式 0.0.0.0:8787
advertise = http://稳定可达名称或 IP:8787
peers = 另外两台 advertise URLs
```

默认 `listen=127.0.0.1:8787` 保留安全本机模式。

## 10. P2 Batch-3：三机 Connectivity REAL 验证入口

提交 `0f4ba8c7` 新增：

```text
.github/workflows/openworker-cluster-connectivity-verify.yml
```

输入：

```text
ul7_endpoint
oda_endpoint
o87_endpoint
```

然后分别在 UL7 / ODA / O87 self-hosted runner 上执行真实 HTTP 探测，每台都必须访问三组 `/v1/node/status`，并检查：

```text
endpoint -> expected COMPUTERNAME
advertise_endpoint == supplied endpoint
```

O87 authority 额外等待 heartbeat convergence 后要求：

```text
cluster.status online_count >= 3
```

只有这条 workflow 真正完成，才能声称三机 direct HTTP connectivity 成立。

注意：ODA 当前 COMPUTERNAME 仍使用 `DESKTOP-ODAQN0D` fail-closed；真实 receipt 若显示不同名称，必须先修正 authority，不允许静默通过。

## 11. 当前真实状态

代码层已经具备：

```text
listen/advertise/peers
peer registry
cluster route
remote durable submit
cluster jobs/agents
cluster cancel/retry/drain
durable cluster dispatch/control ledger
go-tool/Python cluster control
three-node connectivity verifier
```

但截至本文档更新，尚未取得 UL7/ODA/O87 三机 network REAL receipt。因此：

**P2 Batch-3 = IMPLEMENTED，不等于 REAL CONNECTED。**

尤其不能因为本机 `cluster.status` 可调用，就宣称另外两台已可达。

## 12. 当前调度铁律

- COMPUTERNAME 是 fixed machine 最终 authority；
- fixed machine 永不自动漂移；
- `machine=any` 只用于非 destructive route/submit；
- expired lease 不接新任务；
- advertise endpoint 必须来自 node 自己 status；
- self health 不依赖 advertise 网络；
- remote submit 必须 matching durable ACK；
- cluster cancel/retry 必须先定位 owning node；
- drain 必须显式 node 或 all；
- dispatch ledger != final result ledger；
- Action completed != job succeeded。

## 13. 下一批 P2

下一批优先补：

```text
cluster endpoint/config durable receipt
connectivity status/history
remote operation retry/backoff
cluster authority fallback（不再只依赖 O87 transport）
cluster dispatch_id 跨 authority 去重/冲突验证
```

等真实三机 endpoint 确认后，再把 Case 0002/0003/0004 中适合 `machine=any + capability` 的步骤迁过去；明确 fixed-machine 的业务步骤仍保持 fixed。

## 14. 验收铁律

持续覆盖 multi-worker、resource lock、timeout/cancel/drain、restart PID recovery、SCM service、inventory/lease、agent_slot、job 聚合、remote ACK；P2 Batch-3 新增必须验证 advertise endpoint、三机双向 reachability、cluster forwarded cancel/retry/drain、durable dispatch ledger、peer offline/lease expiry，以及重新上线后的 registry convergence。

## 15. 最终目标

OpenWorker 成为自己拥有的三节点、多 Agent、可并行、可恢复、可观察、可按 capability 选择执行节点的本机优先系统。GitHub Actions 保留版本、入口、CI 与证据通道，不再承担长任务 scheduler。
