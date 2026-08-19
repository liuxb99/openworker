# OpenWorker 派工断点修复：QUEUE.CLEAR 后 stale work reference

时间：2026-08-19（Asia/Taipei）

## 结论

本轮定位到一个会造成“本机 slot 全空、Case 仍有 READY step，但 CASE.CONTINUE_BATCH 不再产生 durable work”的真实状态机断点。

断点位于 `go-runtime/internal/casecontroller/continue.go`：

1. Case controller 先读取 `.openworker/case-controller-last.json` 中的当前 `work_id`；
2. `QUEUE.CLEAR` 可以清掉 pending / claimed durable work；
3. controller snapshot 仍保留旧 `work_id`；
4. 下一次 `Continue()` 会 GET `/api/execution/local-work/<work_id>`；
5. queue 返回 HTTP 404 时，旧实现直接 return error；
6. 因此后面的 READY discovery → Action Mapper → deterministic work_id → durable submit 永远不会执行。

这会形成 stale controller reference 死锁。

## 修复

OpenWorker commit：`3fb94496be84e3954bd99bcefb4a595ce4766fb5`

修复规则：

- queue GET 404 被明确分类为 `durable work not found`；
- 若 worklist 中对应 step 仍为 `PENDING` / `READY`，允许把旧 controller ref 视为 queue maintenance 后的 stale reference；
- 先写 append-only ledger event：`go_stale_controller_work_ref_cleared`；
- 删除 stale `case-controller-last.json`；
- 继续进入原有 READY scan 与 Action Mapper；
- 使用原有 deterministic `executionID(case_id, step_id, action, revision)` 重新提交，因此不会创建随机重复 business identity；
- 若 step 已是 `FAILED` 或其他异常非可恢复状态，则仍 fail-closed，不自动重派；
- 500、连接失败、timeout 等非 404 错误仍 fail-closed。

## 回归测试

新增：`go-runtime/internal/casecontroller/continue_queue_clear_test.go`

覆盖：

1. stale controller work GET 404 后继续提交 READY step；
2. 重新提交必须走 deterministic work identity；
3. ledger 必须记录 stale-ref recovery；
4. FAILED step 的 missing work 不得自动重派。

## 部署/验收

本文件提交带 `[bootstrap-oda-node]`，用于触发现有 ODA resident OpenWorker 升级 workflow。

现有 workflow 会在 ODA：

- `go test ./... -count=1`；
- build `openworker-node.exe`；
- 安装/升级 `OpenWorkerNode`；
- 验证 running commit / target commit / VERIFIED；
- 验证 `127.0.0.1:8787/v1/cases/continue` route。

REAL 验收仍需随后取得：

1. ODA resident service 跑到包含本修复的 commit；
2. `CASE.CONTINUE_BATCH` 在 stale-ref 场景返回 accepted；
3. `:8848` 出现新的/恢复的 deterministic durable `work_id`；
4. Case ledger 出现 `go_stale_controller_work_ref_cleared`（仅 stale 场景）；
5. 随后出现 `go_step_dispatch_start` / `go_step_durable_accepted`；
6. 4-slot supervisor 正常 claim/executor。

在上述 REAL evidence 取得前，只能声明“源码断点已修复并触发部署”，不能声明 Case0005 业务成果已完成。
