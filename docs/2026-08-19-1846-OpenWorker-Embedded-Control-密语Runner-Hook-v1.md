# OpenWorker Embedded Control「密語」Runner Hook v1

> 日期時間：2026-08-19 18:46 +08:00（Asia/Taipei）
> 狀態：IMPLEMENTED — REAL RUNNER HOOK INSTALL/SMOKE PENDING
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

## 9. 已完成實作

2026-08-19 18:46 +08:00 後已完成並合併至 `main`：

1. `scripts/openworker-job-started-hook.ps1`
   - 無 `OPENWORKER_CONTROL`：passthrough / exit 0。
   - 有密語：解析 JSON、驗證 schema / request_id / command / machine / max_parallel。
   - allowlist：`CASE.STATUS`、`CASE.CONTINUE_BATCH`、`SUPERVISOR.STATUS`、`QUEUE.CLEAR`。
   - 未知命令 fail-closed。
   - 合法後呼叫既有 `invoke-openworker-control-envelope-v1.ps1`。
2. `scripts/openworker-job-started.cmd`
   - Windows runner 的固定 Job Hook entrypoint。
3. `scripts/install-openworker-runner-hook.ps1`
   - 安裝 hook 到 `C:\ProgramData\OpenWorker\hooks`。
   - 寫入 runner `.env`：`ACTIONS_RUNNER_HOOK_JOB_STARTED=...`。
   - 明確回報 `restart_required=true`。
4. `.github/workflows/smoke-openworker-embedded-control.yml`
   - 無密語 passthrough smoke。
   - `CASE.STATUS` 認得密語 smoke。
5. PR #70 已合併，merge commit：`f33be5819196d7371a87a2942f6a5c2448f19789`。

## 10. REAL 測試紀錄

### 10.1 安裝前 smoke 設計

為避免直接修改 ODA 常駐 runner 後才發現 parser/dispatcher 有問題，先把 smoke workflow 改成直接在 ODA self-hosted job 中呼叫 hook 腳本：

- Test A：移除 `OPENWORKER_CONTROL`，預期 hook exit 0，普通 workflow body 繼續。
- Test B：設 `CASE.STATUS` Control Envelope，預期 hook 將密語送入 OpenWorker，成功後 workflow body 繼續。

### 10.2 觸發結果

建立 PR #71：`test: trigger OpenWorker embedded hook smoke`。

觸發提交：

- `01ca06c3cb34cc5c8cd90647944f6c0d2afd2317`
- 再次 synchronize：`015815b2ed8610def3fd3e60def4475aeb42587e`

兩次查詢均沒有取得對應的 GitHub workflow run；commit combined status 只有 `CodeRabbit: pending`，沒有 smoke workflow status。

因此目前**不能宣稱 ODA smoke 成功，也不能宣稱 Hook 失敗**。能確認的是：測試尚未真正進入 ODA runner，阻塞點仍在 GitHub Actions workflow trigger / scheduling / connector visibility 層。

### 10.3 目前 REAL 狀態

```text
中文規格                  COMPLETE
Control Envelope v1        COMPLETE
Job Hook parser/validator  COMPLETE
Windows hook entrypoint    COMPLETE
一次性 installer           COMPLETE
Smoke workflow             COMPLETE
合併 main                  COMPLETE
腳本級 ODA smoke           NOT YET EXECUTED / NO RUN EVIDENCE
Runner .env 安裝           NOT YET DONE
Runner restart             NOT YET DONE
自動密語攔截 REAL 驗證     NOT YET DONE
Case0005 4-slot REAL 驗證   NOT YET DONE
```

## 11. 下一個合法驗證步驟

1. 先讓 ODA self-hosted smoke workflow 真正取得 runner execution slot；
2. 確認直接 hook smoke 的 passthrough / recognized-secret 都成功；
3. 再執行 `install-openworker-runner-hook.ps1` 寫入 runner `.env`；
4. 重啟 runner service；
5. 再跑一個 workflow，這次**不在 steps 裡呼叫 hook**，只夾帶 `OPENWORKER_CONTROL`；
6. 在 `Set up runner` / hook log 證明 `ACTIONS_RUNNER_HOOK_JOB_STARTED` 自動攔截；
7. 最後用 `CASE.CONTINUE_BATCH` 驗證 Case0005，不重複 active work，並在合法 fanout 時觀察 4-slot。

## 12. 結論

這個設計正式把使用者提出的概念固定為：

> **GitHub Action 只是正常 Action；`OPENWORKER_CONTROL` 是夾帶密語；self-hosted runner Job Hook 是統一攔截器；OpenWorker 是唯一解讀並執行密語的總控。**

目前設計與代碼已完成；REAL runner hook 自動攔截仍需取得 ODA runner 真實執行證據後才算閉環。
