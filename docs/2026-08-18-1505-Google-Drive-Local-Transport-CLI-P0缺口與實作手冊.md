# OpenWorker P0：Google Drive Local Transport CLI 缺口與實作手冊

- 日期：2026-08-18
- 等級：P0 共用基礎設施缺口
- 適用：Case 0002 / 0003 / 0004 及所有需要 ChatGPT 實體成果審查的工作
- Authority：OpenWorker = 執行/進度/queue；go-tool = capability；Google Drive = 暫時 review exchange；WorkLedger = durable authority

## 1. 為什麼這不是 Case 0004 特例

Case 0004 已有 REAL overview：

`D:\AI-Work\jobs\0004-DWG-TO-3D\dwg\exports\default\visual-search\case0004-overview.png`

且 SHA256 已有 authority：

`5cee03340cbbcad51e412b46b85bda9dcaac22b193586b953bbfd5134039103e`

真正 blocker 不是 CAD 成果不存在，而是本機沒有一條統一、可由 OpenWorker 直接呼叫的：

```text
local artifact -> Google Drive -> receipt -> ChatGPT connector review
```

目前存在兩條不一致路線：

1. `ReviewCycle.handoff_to_drive_sync()`：只 copy 到 Google Drive Desktop 的同步資料夾，依賴 Desktop client 是否安裝、是否登入、是否同步完成。
2. `case0004_publish_overview_drive.ps1`：直接打 Drive API，但要求呼叫方事先提供短效 `OPENWORKER_GOOGLE_DRIVE_ACCESS_TOKEN`，案例腳本自己承擔 transport 與認證。

這會造成每個案例重複造 transport、token 過期、receipt schema 不一致、無法由 go-tool 統一查 capability。

因此定義為 OpenWorker P0 共用缺口：**Google Drive Local Transport CLI**。

## 2. 新版責任切分

```text
Case / CAD / Blender / ComfyX
        |
        v
OpenWorker durable job
        |
        v
openworker-drive / openworker drive
        |
        +-- OAuth refresh / access token lifecycle
        +-- upload / list / download / review publish
        +-- SHA256 + size + mime verification
        +-- canonical JSON receipt
        |
        v
Google Drive TEMP review folder
        |
        v
ChatGPT Google Drive connector
```

禁止：

- 每個 Case 自己寫 Google API transport。
- 把短效 access token 當 durable configuration。
- 用 GitHub Actions 當成果傳輸的 canonical queue。
- upload HTTP 200 就當 business step PASSED。
- receipt 不帶本機 SHA256 / Drive file id。

## 3. CLI V1

第一批必須完成：

```text
openworker-drive auth-check
openworker-drive upload <file> [--folder-id ID] [--name NAME] [--receipt PATH]
openworker-drive list [--folder-id ID] [--name NAME]
openworker-drive download <file-id> --output PATH
openworker-drive review-publish <file-or-directory> --work-code CODE [--folder-id ID] [--receipt PATH]
```

之後可再將相同 parser 掛入：

```text
openworker drive ...
```

V1 先以獨立 console script 保持最小改動與可測試性。

## 4. OAuth / Credential contract

認證優先順序：

1. `OPENWORKER_GOOGLE_DRIVE_ACCESS_TOKEN`
   - 只作 emergency / 已由外部安全流程提供的短效 token。
2. OAuth refresh credentials：
   - `OPENWORKER_GOOGLE_CLIENT_ID`
   - `OPENWORKER_GOOGLE_CLIENT_SECRET`
   - `OPENWORKER_GOOGLE_REFRESH_TOKEN`
   - CLI 自動向 Google OAuth token endpoint refresh access token。
3. `OPENWORKER_GOOGLE_CREDENTIALS_FILE`
   - JSON credential file；V1 支援 `authorized_user` 格式。

任何模式都不得把 access token / refresh token 寫進 receipt 或 stdout。

V1 fail-closed：沒有可用 credentials 就失敗，不 fallback 到未授權的 Google Drive Desktop copy。

## 5. Google Drive folder contract

預設 review folder：沿用 OpenWorker 既有 authority：

- Folder ID：`1A4BnZEcFe2WIhcperRd4QSpxoSUN_ARR`
- Folder Name：`OpenWorker-ChatGPT-Review-TEMP`

CLI 可用 `--folder-id` 覆蓋，或使用：

`OPENWORKER_GOOGLE_DRIVE_REVIEW_FOLDER_ID`

上傳到 TEMP review exchange 不改變 WorkLedger durable authority。

## 6. Canonical receipt

單檔 upload 成功必須產生：

```json
{
  "schema": "openworker.google-drive-upload-receipt.v1",
  "status": "UPLOADED",
  "source_path": "...",
  "source_sha256": "...",
  "source_size": 123,
  "drive_file_id": "...",
  "drive_name": "...",
  "drive_mime_type": "image/png",
  "drive_size": "123",
  "drive_md5_checksum": "...",
  "drive_web_view_link": "...",
  "drive_parent_ids": ["..."],
  "openworker_job_id": "...",
  "openworker_agent_slot": "...",
  "published_at": "..."
}
```

驗收規則：

- local file 存在且非空；
- local SHA256 在 upload 前計算；
- Drive 回傳必須有 file id；
- 若 Drive 回傳 size，必須與 local size 一致；
- receipt atomic write；
- secrets 不得進 receipt。

## 7. review-publish contract

### 單檔

直接 upload，receipt 指向 Drive file。

### 目錄

V1 不依賴 Google Drive directory recursive API。先 deterministic 打包成 ZIP：

```text
source directory
-> deterministic inventory
-> ZIP
-> SHA256
-> upload
-> receipt
```

這樣 review bundle 有單一 immutable transport object，後續可再擴充 native folder upload。

## 8. go-tool capabilities

go-tool 應新增/更新：

```text
drive.auth.check
drive.file.upload
drive.file.list
drive.file.download
drive.review.publish
```

Canonical execution：OpenWorker local process / durable job。

GitHub Actions：只可作 CI / regression / emergency transport，不是 business scheduler。

Negative knowledge：

- 不要要求案例自己取得 access token。
- 不要用 `gh workflow run` 當 Drive upload 的正常入口。
- 不要用 Desktop sync folder 是否出現檔案作唯一 upload success authority。

## 9. 與既有 ReviewCycle 的整合

`ReviewCycle.build_bundle()`、review governance、WorkLedger 不重寫。

要改的是 transport boundary：

舊：

```text
ReviewCycle bundle -> handoff_to_drive_sync() -> local Desktop sync folder
```

新 canonical：

```text
ReviewCycle bundle -> drive.review.publish -> Drive API -> receipt
```

`handoff_to_drive_sync()` 暫保留作 legacy fallback，相容既有流程；不得再作新案例 canonical path。

## 10. Case 0004 驗證案例

補完 CLI 後第一個 REAL 驗證：

```text
openworker-drive upload \
  D:\AI-Work\jobs\0004-DWG-TO-3D\dwg\exports\default\visual-search\case0004-overview.png \
  --name case0004-overview.png \
  --receipt D:\AI-Work\jobs\0004-DWG-TO-3D\receipts\case0004-overview-drive-handoff.json
```

必須驗證：

1. source SHA256 = `5cee03340...4039103e`
2. Drive connector 能找到 `case0004-overview.png`
3. ChatGPT 能取得實體 PNG 做 multimodal review
4. receipt 有 Drive file id + source SHA256
5. 才進入 `0004-045 cad.build_story_index`

## 11. V1 實作批次

本批：

- 新增 `coworker/google_drive_transport.py`
- 新增 `coworker/google_drive_cli.py`
- 新增 `openworker-drive` console entrypoint
- OAuth refresh / authorized_user credential file
- upload / list / download / review-publish
- atomic receipt
- 單元測試：credential resolution、receipt secret hygiene、upload size validation、directory ZIP

下一批：

- go-tool capability 登記
- OpenWorker durable action wrapper
- Case 0004 REAL upload
- 讓 `ReviewCycle` canonical transport 切到 Drive API

## 12. 完成定義

P0 缺口只有在以下都成立才算 CLOSED：

```text
CLI 可用
+ OAuth 可自動 refresh
+ upload/list/download 可用
+ receipt 可追溯
+ go-tool 可發現 capability
+ OpenWorker 可直接 durable dispatch
+ Case0004 REAL overview 可被 ChatGPT connector 看見
```

僅寫腳本、僅 HTTP request 成功、僅 GitHub Action 可跑，都不能算 P0 CLOSED。
