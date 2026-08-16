# E6.2 Review / Approval / Delivery Closure

## 結論

AI-Engineering-OS 已經具備 Review 與 Delivery 權威服務。OpenWorker 不建立第二套 Approval 資料模型，只透過既有 API 操作。

## AI-Engineering-OS 權威規則

### Review

Review 綁定：Job、Artifact、Artifact Revision、Reviewer、Decision、Comment。Decision 為：

- `approved`
- `rejected`
- `rework`

`rejected` / `rework` 必須附 comment。

### Approval Status

Approval 是衍生結果：一個 Job 的每個最新 Artifact revision，都必須有最新且 revision 相符的 `approved` Review。全部成立後 `approved=true`，Review Service 會將 Job 從 `review` 推進到 `completed`。

### Delivery

`POST /api/v1/jobs/{id}/publish` 不是單純改狀態。AI-Engineering-OS 會：

1. 要求 Job 為 completed / published。
2. 再次執行 `RequireApproved()`。
3. 選取每個成果類別的最新 Artifact。
4. 驗證來源檔案存在且 SHA256 與 Artifact checksum 相符。
5. 建立 delivery manifest、checksum manifest、download index、README 與 website。
6. 原子切換正式交付目錄。
7. 建立 Delivery revision。
8. completed Job 轉為 published。

因此 OpenWorker 不應自行複製交付檔案或自行判定「已核准」。

## OpenWorker Bridge

新增讀取：

- `list_job_reviews(job_id)`
- `list_artifact_reviews(artifact_id)`
- `approval_status(job_id)`
- `list_deliveries(job_id)`
- `latest_delivery(job_id)`

新增 mutation：

- `submit_artifact_review(...)`
- `publish_job(...)`

Review decision 在 client 端先做 enum/comment fail-closed，再由 OS domain 做 Artifact/Job ownership 與 revision 驗證。

## Coworker Tool Boundary

唯讀 Tool 不需人工批准；以下 mutation Tool 必須走 OpenWorker Approval Gate：

- `engineering_submit_artifact_review`
- `engineering_publish_job`

這個 Approval Gate 是「允許 Agent 執行外部副作用」；AI-Engineering-OS 的 Approval Status 則是「工程成果是否已被正式審查核准」。兩者語義不同，不能混在一起。

## Golden Job

`run()` 只做到 review-ready，不自動核准。

`approve_for_delivery()` 需要顯式 reviewer，對本次 Golden Job 已註冊的每個 Artifact 提交 approved Review，然後要求 OS 回報 `approved=true` 且 Job 已轉 completed。

`publish()` 需要顯式 publisher，且只接受 completed + approved 的結果；真正的 checksum、delivery staging、website rebuild 與 published transition 全部由 AI-Engineering-OS 負責。

## 安全邊界

- 不自動替工程師作出 Review decision。
- 不用 OpenWorker metadata 假裝 Approval Status。
- 不繞過 AI-Engineering-OS `RequireApproved()`。
- 不自行建立 delivery path 或 manifest。
- 不把 `approved=true` 與 OpenWorker Tool Approval 視為同一件事。
