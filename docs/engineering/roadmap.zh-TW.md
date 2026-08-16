# OpenWorker 工程顧問版開發 Roadmap

## E0：文件與架構基線

目標：先把責任邊界、專案盤點、能力分類與整合方向定清楚。

完成標準：

- Engineering Coworker Persona 存在。
- Engineering Adapter 基礎存在。
- 中文總覽、Repo 盤點、架構、整合策略、Roadmap、上游同步策略完成。
- 不修改 OpenWorker 核心工程算法。

狀態：IN PROGRESS。

## E1：Engineering Capability Registry

目標：讓 OpenWorker 能知道「有哪些工程能力、由誰提供、目前是否可用」。

應完成：

- 統一 Capability schema。
- Adapter Registry。
- Health Check。
- Readiness 狀態。
- Engine version。
- Transport type。
- Approval level。
- Capability discovery Tool。

驗收：Engineering Coworker 能列出所有已設定 Engine，並清楚區分 VERIFIED、IMPLEMENTED、DOCUMENTATION_ONLY、BLOCKED。

## E2：AI-Engineering-OS Tool Bridge

目標：先接工程控制平面，而不是一次直接接十個 repo。

應完成：

- Project／Job 查詢與建立。
- Workflow 查詢與觸發。
- Artifact 查詢。
- Review／Approval request。
- Delivery 查詢與發布。
- Gateway health/version。

驗收：OpenWorker 可完成「建立 Job → 執行既有 Workflow → 顯示 Artifact → 送審」的最小閉環。

## E3：核心專業能力直連

依成熟度逐步加入：

第一組：

- KnowGraphGo
- AI-CivilDesign-Forge
- AI-EngSketch

第二組：

- AI-BIM-Forge
- DWG_todo
- go-pdf-drawing-reconstructor

第三組：

- pcces-web
- AI-CivilQuantity
- AI-CivilSchedule

規則：若 AI-Engineering-OS 已提供相同能力，OpenWorker 預設走 OS；直連只作特定高階 Tool、開發、測試或 OS 尚未提供的能力。

## E4：Engineering Digital Thread

目標：讓 OpenWorker 不只知道「生成了一個檔案」，而是知道整條工程證據鏈。

需支援：

- Project ID
- Job ID
- Task／Workflow ID
- Source Artifact Revision
- Engine／Version
- Knowledge Snapshot
- Calculation Trace
- Evidence
- Artifact Revision
- Checksum
- Review／Approval
- Delivery Revision

驗收：任一正式成果可從 OpenWorker 反查到來源輸入、計算引擎、版本、證據與批准狀態。

## E5：完整工程 Coworker Workflow

Golden Flow：

```text
使用者提交 PDF / DWG
→ 建立 Job
→ 重建 Engineering IR / ESM
→ Knowledge Query
→ 設計計算
→ 工程圖
→ BIM
→ Quantity
→ PCCES
→ Schedule
→ Review
→ Approval
→ Delivery Website / ZIP / Manifest
```

驗收：至少一條 Golden Job 完整走通，而且任何正式工程結果都不由 LLM 自行計算。

## E6：工程成果展示與媒體

整合：

- SceneX
- ComfyX
- Comfyx-Studio
- Bernini／FramePack 系列

用途：成果 2D／3D 展示、施工動畫、工程解說影片、簡報媒體。

媒體 Pipeline 是 Delivery 的衍生層，不得改寫工程計算權威結果。

## E7：公司級 Coworker

在工程能力穩定後，才擴充：

- GitHub 開發管理
- OpenCode／Coding Agent 管理
- Telegram 遠端控制
- 公司 SOP／Handbook
- 客戶資料與文件
- 自動排程與定期工作

此階段可參考 `opencode-manager`、`opencode-telegram-bot`、`AI-Company-Handbook`、`one-person-company` 等 repo，但與 Engineering Coworker 保持 Persona／權限隔離。

## 開發順序鐵律

1. 文件與 Contract 先行。
2. 先接 AI-Engineering-OS，再逐一接專業 Engine。
3. 每新增一個 Adapter 必須同時完成 health、version、capability、錯誤處理、測試與中文文檔。
4. 不因 repo 存在就宣稱 capability 可用。
5. 不允許 LLM fallback 產生看似正式的工程計算。
6. 正式發布必須經 Approval。
7. 每一大批修改完成後做完整返工循環再 Commit／PR。
