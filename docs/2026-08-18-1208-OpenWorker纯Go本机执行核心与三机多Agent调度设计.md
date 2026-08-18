# OpenWorker 纯 Go 本机执行核心与三机多 Agent 调度设计

日期：2026-08-18
状态：P1 BATCH-5 IMPLEMENTED — ENTERING P2 CLUSTER PREP

## 1. 架构结论

OpenWorker 继续采用双层结构：Python 保留案例、WorkLedger、知识、审核、Drive 与上层 orchestration；纯 Go `openworker-node.exe` 作为本机执行内核，负责 durable queue、多 Agent slots、真实进程、资源锁、heartbeat、timeout、cancel、drain、retry/recover，以及三机节点状态。

GitHub Action 继续退化为 transport：`runner accepted -> COMPUTERNAME -> submit -> durable ACK -> Action completed`。Action completed 永远不等于业务 succeeded。

## 2. 当前 Go Node API

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

`job_id` 贯穿 Action、Go Core、Python Control Plane、WorkLedger、artifact、QC receipt；`dispatch_id` 负责派工幂等。

## 3. P0 ~ P1 Batch-4 已完成摘要

已完成：SQLite durable store、4 worker pool、Action `_work` worktree slots、resource locks、真实 process supervisor、heartbeat/timeout/cancel、Windows process-tree kill、queued/all drain、显式 retry、Python node adapter、Action durable ACK bridge、原生 Windows Service、build identity、durable job event ledger，以及 Case 0004 O87 `submit -> ACK -> exit` + 独立 result verify 样板。

O87 service bootstrap 与真实 Case 0004 仍需 self-hosted REAL receipt，因此未宣称真实验收完成。

## 4. P1 Batch-5：Restart PID 存活恢复

旧逻辑在 Host 启动时把所有 `starting/running` 一律标 stale，无法分辨旧 PID 是否仍活着。

本批新增：

- `68f91006`：Windows 使用 `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` + `GetExitCodeProcess` 检查 PID 是否 `STILL_ACTIVE`；
- `ff9c8b0d`：非 Windows 使用 signal 0 做存活探测；
- `2458a1be`：Store 增加 `ActiveJobs()` 与 `MarkStale(job_id,detail)`；
- `12721533`：Host startup recovery 改为逐 job reconciliation；
- `2c57529f`：验证遗留 active job 在 startup 被标 stale 并写 durable event。

当前 fail-closed policy：

```text
读取 starting/running
-> 检查 PID
-> PID 已死：直接 stale
-> PID 仍活：先 kill 整个 orphan process tree
-> stale
-> durable stale event 记录 pid/alive/处理结果
-> 只有显式 retry 才能重新执行
```

这样避免服务重启后“旧进程还活着 + 新 retry 又跑一份”的双执行风险。

## 5. P1 Batch-5：Node Capability / Tool / GPU Inventory

提交 `ea07e3e5` 新增 `internal/inventory`。

`GET /v1/node/info` 与 `/v1/node/status` 现在可以发布：

```text
capabilities
installed tool availability/path
gpu index/name/memory
collected_at
```

默认 tool probe：

```text
git
go
python
powershell
blender
nvidia-smi
```

GPU inventory 使用 `nvidia-smi --query-gpu=index,name,memory.total`；没有 NVIDIA 环境时返回空 GPU list，不伪造资源。

`b6030628` 增加 capability normalization test。

## 6. P1 Batch-5：Heartbeat / Lease Contract

提交 `0673bf21` 扩充 `/healthz` 与 `/v1/node/status`：

```text
node_id
heartbeat_at
lease_seconds = 15
lease_until
```

P2 Registry 后续只要定期抓 node status，即可按 `lease_until` 判断节点是否仍可调度。超过 lease 的节点必须视为 unavailable，不允许继续派 `machine=any` 新任务。

目前 lease 是 node response contract，还没有中央 Registry 持久化，这是下一阶段 P2 的工作。

## 7. P1 Batch-5：Service Capability 配置

提交：

- `81d29a7c`：nodeConfig 支持 `Capabilities`；
- `c4dc97fe`：`openworker-node.exe -capabilities`；
- `be79d2ed`：Windows service installer 支持 `-Capabilities`，并持久写入 SCM `binPath`。

因此 capability 不依赖临时 Action 环境变量；服务重启后仍保留节点角色。

## 8. 三机 Service Bootstrap

### O87

`96bd056c` 更新 O87 bootstrap：

```text
COMPUTERNAME = DESKTOP-O87PJNR
capabilities = case0004,dwg,story-index,engineering
```

并验证 `lease_until`、build commit 与 `dwg` capability。

### UL7

`d9749c97` 新增：

```text
.github/workflows/bootstrap-openworker-node-ul7.yml
```

固定：

```text
COMPUTERNAME = DESKTOP-UL7V2VV
capabilities = case0003,bridge,blender,scenex,engineering,drive-review
```

### ODA

`8b20d520` 新增：

```text
.github/workflows/bootstrap-openworker-node-oda.yml
```

当前固定检查：

```text
COMPUTERNAME = DESKTOP-ODAQN0D
capabilities = case0002,comfyx,minimax-h3,video,storyboard,presentation
```

该 hostname 必须由真实 ODA self-hosted run receipt 再确认；若实际 COMPUTERNAME 不同，workflow 会 fail-closed，不会静默在错误机器安装服务。

## 9. 当前三机目标状态

```text
UL7  -> OpenWorkerNode :8787 -> bridge/blender/scenex/engineering
ODA  -> OpenWorkerNode :8787 -> comfyx/minimax-h3/video/storyboard
O87  -> OpenWorkerNode :8787 -> dwg/story-index/engineering
```

每台默认 4 worker slots；实际并行能力仍由 resource locks / GPU locks / workspace locks 限制，不把“4 workers”误解为“所有 GPU 任务都可以四份同时跑”。

## 10. 当前恢复铁律

- service restart 不可直接重跑旧 active job；
- PID 存活必须先处理 orphan process；
- 旧 active job 最终进入 stale；
- stale 必须显式 retry；
- retry 保留同一 durable `job_id`；
- event ledger 必须记录 recovery 原因；
- 固定机器最后权威仍是 COMPUTERNAME；
- capability 是调度条件，不是机器身份替代品。

## 11. 当前真实验收状态

代码层已经进入三节点准备，但以下仍需 REAL self-hosted receipt：

1. O87 OpenWorkerNode service 安装/升级 + inventory/lease；
2. UL7 OpenWorkerNode service 安装/升级 + inventory/lease；
3. ODA OpenWorkerNode service 安装/升级 + COMPUTERNAME 最终确认；
4. Case 0004 durable ACK -> job succeeded -> event ledger -> local artifact -> GitHub result receipt；
5. restart 时真实 orphan PID recovery 行为。

因此本批状态是：**IMPLEMENTED，尚未宣称三机 REAL VERIFIED。**

## 12. 下一阶段 P2：Cluster Registry

下一批开始建立中央 cluster authority：

```text
cluster_nodes
cluster_agents
cluster_capabilities
cluster_jobs
```

每个 node 以 heartbeat/lease 更新：

```text
node_id
computer_name
endpoint
build.commit
heartbeat_at
lease_until
workers busy/free
capabilities
tools
gpus
queue depth
```

目标 API / go-tool：

```text
openworker.cluster.status
openworker.cluster.jobs
openworker.cluster.capabilities
```

之后才允许 `machine=any` 根据 online lease + capability + free slots + resource/GPU availability 自动选机器。固定 machine job 不参与自动漂移。

## 13. 验收铁律

必须持续覆盖：四任务并行、第五排队、同锁串行、不占死 worker、timeout、process-tree cancel、drain queued/all、dispatch 幂等、restart PID recovery、stale 显式 retry、Action `_work` worktree、COMPUTERNAME fail-closed、Windows SCM service、build identity、inventory、lease，以及真实 Case 在 Action 结束后由 Go Node 独立完成。

## 14. 最终目标

OpenWorker 从 GitHub Actions 驱动的单 runner 执行，升级为 OpenWorker 自己拥有的三节点、多 Agent、可并行、可恢复、可观察、本机优先的执行系统。GitHub Actions 只保留版本、入口、CI 与证据通道，不再承担长任务 scheduler。
