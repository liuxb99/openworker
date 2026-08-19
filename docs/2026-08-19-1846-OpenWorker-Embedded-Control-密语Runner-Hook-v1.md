# OpenWorker Embedded Control「密語」Runner Hook v1

> 日期時間：2026-08-19 18:46 +08:00（Asia/Taipei）
> 狀態：DESIGN → IMPLEMENTATION
> Repo：`liuxb99/openworker`
> 目標機器：`DESKTOP-ODAQN0D`

## 1. 核心想法

GitHub Action 不需要理解 OpenWorker 業務語意，也不需要每一支 workflow 都加入一套 `if/switch/PowerShell` 控制邏輯。

只約定一個 GitHub 合法的「夾帶欄位」：

```yaml
env:
  OPENWORKER_CONTROL: >-
    {"schema":"openworker.control-envelope.v1","request_id":"demo-001","command":"CASE.CONTINUE_BATCH","machine":"DESKTOP-ODAQN0D","case_id":"0005","policy":{"max_parallel":4,"join":"case-defined","fail_closed":true}}
```

GitHub 對 `OPENWORKER_CONTROL` 只視為普通環境變數字串，不理解其中的 Case / command / fanout 語意。

真正理解密語的是 self-hosted runner 上的 OpenWorker Job Hook。

## 2. 一次安裝、所有 workflow 共用

GitHub self-hosted runner 官方支援：

```text
ACTIONS_RUNNER_HOOK_JOB_STARTED=<absolute path>
```

當 job 已分配給 runner、但 workflow steps 尚未開始時，runner 會自動執行這個本機 hook。

因此只需在每台受控 runner 安裝一次：

```text
ACTIONS_RUNNER_HOOK_JOB_STARTED=C:\ProgramData\OpenWorker\hooks\openworker-job-started.cmd
```

之後所有跑到這台 runner 的 workflow 都自動經過同一個 hook。

## 3. 密語規則

### 3.1 沒有密語

若 job 沒有：

```text
OPENWORKER_CONTROL
```

Hook 必須：

```text
exit 0
```

不得改變原 workflow 行為。

### 3.2 有密語

Hook 讀取 `OPENWORKER_CONTROL`，解析為 `openworker.control-envelope.v1`，再交給本機 OpenWorker。

```text
GitHub job
  ↓
ACTIONS_RUNNER_HOOK_JOB_STARTED
  ↓
OPENWORKER_CONTROL ?
  ├─ 無 → exit 0 → 原 GitHub job 照常執行
  └─ 有
      ↓
   validate envelope
      ↓
   OpenWorker control dispatcher
      ↓
   Case Engine / supervisor
      ↓
   go-tool durable queue
      ↓
   最多 4 個本機 claim/executor slots
```

## 4. 責任邊界

### GitHub Action

只負責：

- 正常 workflow 執行；
- 可選擇夾帶 `OPENWORKER_CONTROL` 字串。

GitHub Action 不負責：

- 解釋 `CASE.CONTINUE_BATCH`；
- 判斷 READY step；
- Case dependency；
- fanout / join；
- capability 選擇；
- durable queue；
- 本機 4-slot 排程。

### Runner Hook

只負責：

- 判斷有無密語；
- 基本 schema / JSON 驗證；
- 將 Control Envelope 交給 OpenWorker；
- 回傳 OpenWorker dispatcher 的 exit code。

Hook 不允許自行執行任意 CMD / PowerShell business payload。

### OpenWorker

負責：

- allowlist command；
- machine / case 驗證；
- reconcile；
- READY discovery；
- dependency legality；
- fanout / join；
- leaf blocker；
- idempotency；
- business control authority。

### go-tool-runtime

負責：

- durable local-work queue；
- claim；
- executor；
- capability execution；
- execution evidence；
- 4 claim slots + 4 executor slots。

## 5. 第一版允許命令

```text
CASE.STATUS
CASE.CONTINUE_BATCH
SUPERVISOR.STATUS
QUEUE.CLEAR
```

任何未知命令：

```text
REJECT / non-zero exit
```

不得猜測。

## 6. CASE.CONTINUE_BATCH 語意

密語：

```json
{
  "schema": "openworker.control-envelope.v1",
  "request_id": "case0005-batch-001",
  "command": "CASE.CONTINUE_BATCH",
  "machine": "DESKTOP-ODAQN0D",
  "case_id": "0005",
  "policy": {
    "max_parallel": 4,
    "join": "case-defined",
    "fail_closed": true
  }
}
```

OpenWorker 收到後：

1. reconcile 目前 durable state；
2. 若 current work 仍 pending / claimed / running，不重複提交；
3. 找出合法 READY step；
4. 若 Case 定義允許 fanout，由 Case Engine 建立 child works；
5. 投遞 go-tool durable queue；
6. 本機 supervisor 最多 4 路並行；
7. join / acceptance / blocker 仍由 Case authority 判斷。

`max_parallel=4` 是上限，不代表一定要同時有四件合法 work。

## 7. 安全原則

- 密語不是 shell script。
- 禁止任意 PowerShell / CMD / executable path。
- `command` 必須 allowlist。
- `machine` 必須與 runner 實機一致。
- `request_id` 必須合法且可供 idempotency 使用。
- `max_parallel` 固定 1..4。
- `fail_closed` 預設 true。
- Hook 只呼叫固定 OpenWorker dispatcher。
- OpenWorker / go-tool 才有 business authority。

## 8. 為什麼比修改每支 Action 好

舊模式：

```text
workflow A → 自己寫 case_continue 邏輯
workflow B → 自己寫 status 邏輯
workflow C → 自己寫 queue 邏輯
```

容易產生不同版本的判斷式與 PowerShell。

新模式：

```text
所有 workflow
   ↓
同一個 Runner Hook
   ↓
同一個 OpenWorker Control Envelope
   ↓
同一個 OpenWorker authority
```

以後新增 OpenWorker 命令主要改 OpenWorker allowlist / dispatcher，不需要把 business logic 複製到每支 workflow。

## 9. 實作範圍

本批開發：

1. `openworker-job-started-hook.ps1`：讀 `OPENWORKER_CONTROL`；無密語直接 exit 0；有密語則驗證與 dispatch。
2. `openworker-job-started.cmd`：Windows runner hook 穩定入口。
3. `install-openworker-runner-hook.ps1`：一次性安裝到 `C:\ProgramData\OpenWorker\hooks`，設定 runner `.env` 的 `ACTIONS_RUNNER_HOOK_JOB_STARTED`。
4. 使用既有 `invoke-openworker-control-envelope-v1.ps1` 作為固定 dispatcher。
5. smoke workflow：只夾帶 `OPENWORKER_CONTROL`，不寫 OpenWorker business dispatch step，用來驗證 runner hook 是否真的攔截到密語。

## 10. 驗收

### A. 無密語

普通 workflow 在 ODA runner 上執行，Hook 不應改變結果。

### B. 認得密語

`CASE.STATUS` 或 `CASE.CONTINUE_BATCH` 被 Hook 捕獲並送到 OpenWorker，log 應在 `Set up runner` 階段看到 hook 執行證據。

### C. 不認得密語

未知 command 必須 fail-closed，workflow 不得繼續假裝成功。

### D. Case0005

以 `CASE.CONTINUE_BATCH` 驗證：

- 若 0005-010 仍 active，不重複 business work；
- 若已 terminal，OpenWorker reconcile 後只派合法 READY work；
- fanout 到達時才驗證多 work / 4-slot；
- 狀態回報需包含 supervisor / queue / blocker 證據。

## 11. 結論

這個設計正式把使用者提出的概念固定為：

> **GitHub Action 只是正常 Action；`OPENWORKER_CONTROL` 是夾帶密語；self-hosted runner Job Hook 是統一攔截器；OpenWorker 是唯一解讀並執行密語的總控。**

如此可做到「一次安裝 Hook，之後 workflow 只需要夾帶資料，不再各自維護 OpenWorker business logic」。
