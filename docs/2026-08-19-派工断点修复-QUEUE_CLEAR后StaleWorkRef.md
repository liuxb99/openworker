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

## 2026-08-19 22:50 +08:00：ODA REAL 补充验证与第二层修复

本轮直接在 `DESKTOP-ODAQN0D` 绕过 GitHub Actions，以 localhost API 和本机 durable data 做最短路径重现。实际发现两个更具体的前置断点：

1. `OpenWorkerNode` Windows service 不存在，`127.0.0.1:8787` 没有 resident process，导致 `openworker supervisor status` 返回 502。
2. 沿用原 durable data dir `C:\ProgramData\OpenWorker\node` 启动 4-worker Go resident 后，旧 resident binary 又因不接受 `manifest_path` 而在 go-tool → OpenWorker HTTP boundary 返回 400。main source 已支持该 schema，升级 resident 后此 boundary 通过。

随后双次执行 Go OpenWorker `POST /v1/cluster/queue/drain?machine=DESKTOP-ODAQN0D&mode=all`；两次 node response 都为 `count=0`。再次执行 `case continue 0005` 时，旧 revision 14 durable work 已是 terminal `failed`，原逻辑会把 `0005-010` 标成 FAILED 并立即返回，仍阻止 revision 15 重新派工。

最小修复为：controller ref 读取 `revision`；只有当 terminal failed work 明确属于较旧 revision，且当前 worklist revision 已前进时，才清除 failed ref、把该 step 恢复为 PENDING 并按当前 revision 产生新的 deterministic work id。同 revision failed 仍保持 fail-closed，不会自动无限重试。新增 ledger event：`go_failed_controller_work_ref_cleared`。

REAL 结果：

- queue before：pending=0、claimed=0、active_slots=0、inflight=0；fresh claim slots=4、fresh executor slots=4。
- step_id：`0005-010`。
- new work_id：`case0005-0005-010-r000015-50dfa3ce`。
- durable accepted：2026-08-19T14:50:47.0049213Z（event 746，pending）。
- claimed：2026-08-19T14:50:47.2820832Z（event 747）。
- claim slot：`DESKTOP-ODAQN0D-pid-15416-slot-01`。
- executor started：2026-08-19T14:50:47.7817211Z（event 748）。
- executor slot：3；executor id：`DESKTOP-ODAQN0D-pid-18428-exec-slot-03`。
- queue after：pending=0、claimed=1、active_slots=1、inflight=1。
- Case ledger：`go_failed_controller_work_ref_cleared`、`go_step_dispatch_start`、`go_step_durable_accepted`。
- Case ledger path：`D:\AI-Work\jobs\0005-SNOW-WHITE\.openworker\case-supervisor-ledger.jsonl`。
- claim receipt：`C:\ProgramData\go-tool-runtime\work-agent\spool\case0005-0005-010-r000015-50dfa3ce.claim.json`。
- executor lock：`C:\ProgramData\go-tool-runtime\work-agent\spool\case0005-0005-010-r000015-50dfa3ce.exec.lock`。
- run path：`D:\AI-Work\jobs\0005-SNOW-WHITE\runs\case0005-0005-010-r000015-50dfa3ce`。
- Python controller used：false；GitHub Actions business execution used：false。

验证：`go test ./...` PASS；本机 build PASS；新版 resident 以 hidden detached process 运行，PID 4780、workers=4、data dir 仍为原 `C:\ProgramData\OpenWorker\node`。

尚存缺口：当前用户没有权限覆盖 `C:\ProgramData\OpenWorker\bin\openworker-node.exe`，因此 REAL 验证 binary 暂从用户 temp staging path 启动，但 durable SQLite/data dir 未改变。后续需用既有升级 authority 将同一修复 binary 正式写入 ProgramData，并建立或恢复自动启动机制；这不影响本轮已取得的 durable accepted/claimed/executor-started 证据。
