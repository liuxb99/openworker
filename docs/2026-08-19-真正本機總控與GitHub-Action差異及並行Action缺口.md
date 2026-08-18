# 真正本機總控 vs GitHub Action：差異、目前缺口與「並行 Action」未真正成立的原因

日期：2026-08-19

## 1. 結論先行

目前系統已經具備不少「本機化」元件：

- go-tool-runtime 本機 HTTP：`:8848`
- OpenWorker 本機 Supervisor：`:8787`
- durable local-work queue / SQLite
- gtr-work-agent
- gtr-work-executor
- gtr-local-exec
- OpenWorker `max_workers=4`
- CaseWorklist / durable job / execution summary / explain

但這些元件目前還沒有組成真正的「本機總控並行 Action」。

真正的根因不是單一 bug，而是目前存在 **兩條互相重疊的本機執行路徑**，而且兩條都沒有完整實現總控並行：

1. **go-tool local-work queue 路徑**
   - `:8848 -> gtr-work-agent -> spool -> gtr-work-executor -> capability`
   - 目前安裝腳本只啟動 **1 個 agent + 1 個 executor**。
   - agent 一次 claim 一個 work，並且在該 work terminal 前不會再 claim 下一個。
   - executor 逐一掃描 claim，呼叫 `reg.Execute()` 時同步阻塞，單一 action 最長可佔用 45 分鐘。
   - 因此這條路徑本質上目前是 **單工 queue**，不是並行 Action supervisor。

2. **OpenWorker Case controller 路徑**
   - `Case controller -> OpenWorker child job -> Python run-step -> gtr-local-exec -> capability`
   - 這條路徑可以利用 OpenWorker 4-slot，同時跑多個 child job。
   - 但它直接啟動 `gtr-local-exec`，**繞過 :8848 durable local-work queue**。
   - 因此真正的「工具執行總控」並沒有集中在 go-tool local supervisor；OpenWorker 在管 process slot，而 go-tool queue 又是另一套單工狀態。

此外，Case controller 自身還有未實作的 fan-out：

- `image.comfyx.storyboard-real` 目前在 `_claim_inputs()` 直接 `NotImplementedError`
- `comfyx.production.video.real` 目前在 `_claim_inputs()` 直接 `NotImplementedError`
- `_dispatch_step()` 限制每個 step 只能有一個 `allowed_action`
- 因此即使 OpenWorker 有 4 slots，Case 0005 的角色圖、場景圖、shot video 也還不能被 controller materialize 成多個可並行 child job

所以目前看到的現象是合理的：

> 「有 4-slot，但沒有真正本機總控並行 Action。」

---

## 2. GitHub Action 與真正本機總控的本質差異

### 2.1 GitHub Action 模式

GitHub Action 是遠端 workflow scheduler。

典型流程：

```text
ChatGPT
  -> GitHub API / workflow_dispatch / push
  -> GitHub Actions scheduler
  -> self-hosted runner 接單
  -> runner 執行腳本
  -> artifact / commit / log 回傳
```

優點：

- 雲端容易觸發
- 有天然 workflow/job UI
- runner 可以平行跑不同 job
- 適合安裝、升級、修復、一次性 bootstrap

缺點：

- scheduler 在 GitHub，不是本機
- runner 是否接單受 labels / busy / workflow concurrency 影響
- 同一台機器的本機真實狀態需要再透過 workflow 查詢
- workflow 完成不代表業務成果真的完成
- 容易把「傳輸層成功」誤認為「Case 執行成功」
- 不適合成為長時間 Case business orchestration authority
- 每一次查狀態、kick、snapshot 都經 GitHub，延遲高而且容易造成重複 bootstrap / race

因此 GitHub Action 應只保留：

- 首次安裝
- 程式升級
- 緊急 repair
- 真的無本機直連時的一次性 transport

不應再負責：

- Case business execution
- Case status query
- Case kick
- Case snapshot
- Case artifact return
- 本機 action scheduling

---

### 2.2 真正本機總控模式

真正本機總控應該是：

```text
ChatGPT / llama.cpp Coder
        |
        v
 go-tool :8848  <-- 唯一對外本機總控入口
        |
        +-- tool/method authority
        +-- Case supervisor API
        +-- durable action queue
        +-- parallel action scheduler
        +-- action claim / lease / heartbeat
        +-- capability registry
        +-- artifact list/download/publish
        |
        v
 OpenWorker :8787
        |
        +-- process/job execution truth
        +-- PID / timeout / cancel
        +-- local slot accounting
        +-- execution summary / explain
        |
        v
 allowlisted capability executors
        |
        +-- ComfyX
        +-- ComfyX-Studio
        +-- OpenMAIC
        +-- DWG / Blender / Engineering tools
```

真正本機總控應具備以下特徵：

1. **不依賴 GitHub scheduler 才能繼續工作**。
2. **同一台機器可同時執行多個 Action**。
3. Action 的 queue / claim / lease / heartbeat / terminal state 都在本機 durable storage。
4. 每個 Action 都有獨立 work_id / execution_id。
5. 本機總控知道目前：
   - queued
   - claimed
   - running
   - completed
   - failed
   - blocked
   - retryable
6. 本機總控知道每個 action 用掉多少 slot。
7. Case controller 只做 DAG / dependency / approval gate，不自己直接執行工具。
8. OpenWorker 只做 process execution kernel，不負責猜工具方法。
9. go-tool 是 tool/method authority，也是 action scheduling authority。
10. GitHub 不再是 status bus。

---

## 3. 為什麼目前「本機總控並行 Action」沒有真正成立

### 原因 A：gtr-work-agent 是單工 claim loop

目前 `gtr-work-agent` 的流程是：

```text
claim 1 work
  -> 寫 claim spool
  -> holdLeaseUntilTerminal()
  -> 等 result/error
  -> complete/fail
  -> 才回到下一次 claim
```

也就是：

```text
agent-1
  work-A ------------------------------ terminal
                                         |
                                         +--> 才 claim work-B
```

單一 agent 永遠只會有一個 inflight work。

目前安裝腳本只啟動 1 個 agent，所以每台機器的 local-work queue 最多只能同時 claim 1 個 action。

這是第一個直接造成「無法並行」的硬瓶頸。

---

### 原因 B：gtr-work-executor 本身也是同步單工

目前 executor：

```go
for _, claim := range entries {
    ctx, cancel := context.WithTimeout(... 45*time.Minute)
    res, execErr := reg.Execute(ctx, claim)
    ...
}
```

`reg.Execute()` 是同步阻塞。

如果第一個 capability 跑 20 分鐘，executor 就會卡 20 分鐘，後面的 claim 即使已經存在 spool 也不會開始。

所以即使未來把 agent 改成一次 claim 4 個 work，只要還只有一個同步 executor，最後仍是：

```text
claim-A -> execute 20 min
claim-B -> 等
claim-C -> 等
claim-D -> 等
```

因此 agent 與 executor 兩邊都必須一起改。

---

### 原因 C：安裝腳本只啟動一組 Agent / Executor

目前 Windows installer 只建立：

- `GoToolRuntime-LocalWorkQueue`
- `GoToolRuntime-LocalWorkAgent`
- `GoToolRuntime-LocalWorkExecutor`

也就是每台機器只有一組：

```text
1 queue
1 agent
1 executor
```

沒有：

```text
agent slot 1..4
executor slot 1..4
```

也沒有單一 process 內建 worker pool。

所以「max_workers=4」目前只存在於 OpenWorker execution kernel，不存在於 go-tool local-work supervisor。

---

### 原因 D：Case controller 目前繞過 :8848 queue

目前 Case controller 在 OpenWorker child job 裡直接執行：

```text
gtr-local-exec --claim xxx.json
```

這代表：

- OpenWorker job 有 durable truth
- 但 go-tool local-work queue 不知道這個 action 正在執行
- `:8848/api/execution/local-work` 看不到所有 Case action
- local-work queue 無法統一做 slot / retry / cancel / backpressure

因此現在其實是：

```text
OpenWorker supervisor = 一套 scheduler

go-tool local-work queue = 另一套 scheduler
```

這是架構重疊，而不是真正「本機總控」。

真正架構應該統一成：

```text
Case controller
   -> go-tool durable action queue
       -> parallel local action workers
           -> OpenWorker durable process job
               -> capability executor
```

或採反向分工：

```text
go-tool :8848 = DAG/action scheduler
OpenWorker :8787 = process kernel
```

不能讓 controller 再直接 `gtr-local-exec`。

---

### 原因 E：Case 0005 fan-out 還沒有 materialize

Case 0005 設計上本來有可並行區段：

```text
0005-027 approval
    |
    +-- 0005-030 character masters
    +-- 0005-040 scene concepts
                |
                v
             0005-050 join
```

以及：

```text
0005-057 approval
    |
    +-- shot-001 video
    +-- shot-002 video
    +-- shot-003 video
    +-- ...
                |
                v
             0005-070 join
```

但目前 controller 的 `_claim_inputs()` 對：

- `image.comfyx.storyboard-real`
- `comfyx.production.video.real`

仍直接回 `NotImplementedError`。

也就是 DAG 雖然寫了 fan-out 概念，真正的 per-asset / per-shot durable work items 還沒有 materialize。

所以目前根本沒有足夠多的獨立 action 可以餵給 4-slot。

---

### 原因 F：step 模型仍偏「一步一 action」

目前 `_dispatch_step()` 要求：

```text
len(step.allowed_actions) == 1
```

這個限制本身不是錯；單一步驟只允許一種 capability 反而容易驗證。

真正的缺口是：

> 一個 fan-out step 應該 materialize 成多個「同 capability、不同 inputs、不同 work_id」的 child action。

例如：

```text
0005-030
  -> 0005-030/character/snow-white
  -> 0005-030/character/queen
  -> 0005-030/character/huntsman
  -> 0005-030/character/dwarf-01
```

每個都是獨立 durable action，才能真正平行。

不是把 `allowed_actions` 改成很多 action 就算平行。

---

## 4. 正確的真正本機總控並行架構

### 4.1 單一機器

```text
                         +--------------------+
ChatGPT / Local LLM ---> | go-tool :8848      |
                         | Local Supervisor   |
                         +---------+----------+
                                   |
                      durable action queue
                                   |
                  +----------------+----------------+
                  |                |                |
              worker-1         worker-2         worker-3 ... worker-N
                  |                |                |
                  v                v                v
             OpenWorker        OpenWorker       OpenWorker
             child job         child job        child job
                  |                |                |
                  v                v                v
             capability       capability      capability
```

其中：

- N 預設 = OpenWorker `max_workers`
- ODA 目前目標 N = 4
- 每個 worker 可同時持有一個 action lease
- 每個 action 獨立 heartbeat
- 每個 action terminal 後立刻釋放 slot
- queue 本身不阻塞其他 work

---

### 4.2 Case DAG

Case controller 不再執行工具，只做：

1. 讀 Worklist
2. 找 ready steps
3. materialize fan-out child actions
4. 提交至 go-tool local supervisor
5. 收集 durable action terminal evidence
6. 更新 Worklist
7. materialize downstream
8. approval gate 停住等待人

因此 controller 是 orchestration authority，不是 executor。

---

## 5. 並行 Action 的必要資料模型

每個 action 至少需要：

```json
{
  "work_id": "case0005-030-character-snow-white-...",
  "case_id": "0005",
  "step_id": "0005-030",
  "parent_step_id": "0005-030",
  "fanout_key": "character:snow-white",
  "assigned_host": "DESKTOP-ODAQN0D",
  "capability_id": "image.comfyx.storyboard-real",
  "inputs": {},
  "priority": 80,
  "status": "queued",
  "slot_cost": 1,
  "claimed_by": "",
  "lease_token": "",
  "lease_until": "",
  "attempt": 0
}
```

並且需要：

- unique `(work_id)`
- unique fan-out identity
- idempotent submit
- per-action lease
- stale lease requeue
- terminal result immutable
- fail/retry policy
- slot_cost
- optional resource locks

---

## 6. 本次實作方向

### Phase 1：go-tool local supervisor 先真正並行

修改：

1. `gtr-work-agent`
   - 不再 claim 一個後整個 process 等 terminal
   - 改成 worker pool / slot pool
   - 同一 agent 可維持 N 個 inflight leases
   - 每個 inflight work 獨立 heartbeat

2. `gtr-work-executor`
   - 不再同步逐檔執行
   - 改 bounded worker pool
   - 預設 `--workers=4`
   - 每個 claim 只能被一個 executor slot 擁有
   - 增加 `.running`/ownership lock，避免兩個 worker 重複跑同 claim

3. installer
   - 寫入 `max_parallel_actions`
   - ODA 預設 4
   - agent/executor 都以同一 parallel setting 啟動
   - authority receipt 明確記錄 parallel slots

### Phase 2：Case controller 不再直跑 gtr-local-exec

修改：

- controller 將 action 提交至 `:8848/api/execution/local-work`
- 等待/監看 local-work durable terminal result
- 不再 `subprocess.run(gtr-local-exec)`

這樣 go-tool 才是唯一 action supervisor。

### Phase 3：Case 0005 真正 fan-out

實作：

- 0005-030：按 character asset materialize 多個 child action
- 0005-040：按 scene asset materialize 多個 child action
- 0005-060：按 approved shot materialize 多個 video child action
- parent step 只在所有 child action terminal + evidence 通過後才 PASSED
- 任一 child 失敗時保留已成功結果，只 retry 失敗 child

### Phase 4：總控觀測

`:8848` 應回報：

- max_parallel_actions
- active_slots
- free_slots
- inflight actions
- queued actions
- per-action elapsed
- per-action lease
- per-action OpenWorker child job
- completed / failed / blocked summary

---

## 7. 驗收標準

真正「本機總控並行 Action」完成，不能只看程式碼存在，必須用真實案例驗證：

### 驗收 A：4 個 synthetic allowlisted actions

在 ODA 一次提交 4 個獨立 action：

```text
A
B
C
D
```

必須同時看到：

```text
active_slots = 4
```

而不是 A 完才 B。

### 驗收 B：Case 0005 image fan-out

至少 character + scene 兩組同時執行，並且有不同 work_id / execution_id / heartbeat / evidence。

### 驗收 C：Case 0005 shot video fan-out

若有 4 個以上 shot：

- 同時最多 4 個 RUNNING
- 第 5 個保持 QUEUED
- 任一完成後第 5 個自動補入

### 驗收 D：故障隔離

其中一個 action 故意失敗：

- 其他 3 個不能被 cancel
- 其他成功 evidence 保留
- 只重試失敗 child

### 驗收 E：GitHub 完全不參與 business execution

Case 執行過程中：

```text
github_action_used_for_business_execution = false
```

且 status / action scheduling / artifact handoff 都可由本機總控完成。

---

## 8. 最終權威分工

### go-tool-runtime

負責：

- 工具方法權威
- capability registry
- durable local action queue
- parallel action scheduling
- action lease / heartbeat / retry
- Case supervisor API
- artifact access / publish

### OpenWorker

負責：

- 真實 process execution
- PID
- timeout
- cancel
- resource lock
- execution summary
- explain
- process/job truth

### Case controller

負責：

- DAG
- dependencies
- fan-out / join
- approval gate
- acceptance evidence
- Worklist transition

### GitHub

只負責：

- source control
- 首裝 / 升級 / repair 的可選 transport

**不再負責 Case business execution。**

---

## 9. 本次最重要的修正原則

> 不再靠「多開 GitHub Action job」假裝本機並行。

> 不再靠「OpenWorker 有 4 個 worker」就宣稱 go-tool 已經是本機總控。

> 真正的並行必須發生在本機 durable action supervisor：同一台機器、同一個 queue authority、同一個本機總控，同時存在多個獨立 inflight action。

> Case fan-out 必須 materialize 成多個 durable child action，而不是一個 step 裡面自己 serial loop。

這份文檔完成後，下一批代碼就按 Phase 1 → Phase 2 → Phase 3 的順序實作。