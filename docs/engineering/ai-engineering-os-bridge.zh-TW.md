# OpenWorker → AI-Engineering-OS Bridge 規格

更新日期：2026-08-08

## 一、定位

本 Bridge 是 OpenWorker 工程版與 `AI-Engineering-OS` 之間的控制平面連接層。

```text
Engineering Coworker
        ↓
Engineering Tool Facade
        ↓
EngineeringOSClient
        ↓ HTTP
AI-Engineering-OS
        ↓
Project / Job / Workflow / Artifact / Delivery
        ↓
專業 Engineering Engines
```

Bridge 不實作設計公式、BIM、數量、預算或排程演算法，也不在 OpenWorker 建立第二套 Job 狀態機。

## 二、權威 API

依 `AI-Engineering-OS/internal/httpapi/server.go` 現有正式路由，E2 使用：

```text
GET  /healthz
GET  /readyz
GET  /api/v1/system/modules
GET  /api/v1/projects
GET  /api/v1/projects/{id}
GET  /api/v1/jobs
GET  /api/v1/projects/{id}/jobs
GET  /api/v1/jobs/{id}
POST /api/v1/jobs
```

E2 不自行發明 `/version` 或 `/capabilities` endpoint。

### Version

目前使用 `/api/v1/system/modules` 回傳的 `schema_version` 作為控制平面契約版本資訊。

### Capabilities

由 `modules.lock.yaml` 的 module id 映射為 OpenWorker 的 `EngineeringCapability`。未知 module 不推測、不自動賦予能力。

## 三、Job 建立契約

`POST /api/v1/jobs` 完全遵循 AI-Engineering-OS 既有 `job.CreateInput`：

```json
{
  "project_id": "project-...",
  "code": "J001",
  "name": "RC Column Design",
  "user_request": "Design an RC column",
  "expected_deliverables": ["calculation", "drawing", "ifc"],
  "priority": "high",
  "metadata": {
    "source": "openworker"
  }
}
```

OpenWorker 不建立另一套 Job ID、Revision、Status 或 Working/Delivery Folder 規則。

## 四、Transport 原則

Production transport 使用 Python 標準庫 `urllib`，不增加第三方 HTTP dependency。

Transport 可注入，因此永久測試不需要真的啟動 AI-Engineering-OS。

錯誤必須分類：

```text
EngineeringOSTimeoutError
EngineeringOSTransportError
EngineeringOSHTTPError
EngineeringOSContractError
```

其中：

- timeout 不得偽裝成 HTTP 500。
- connection failure 不得偽裝成 readiness failure。
- HTTP 4xx/5xx 保留遠端 `error` 與 `message`。
- 非法 JSON、缺少 `items`、module shape 錯誤必須 fail closed。

## 五、Health / Readiness

`health()` 與 `readiness()` 正規化為 E1 `HealthReport`。

```text
/healthz status=ok       → READY
/readyz status=ready     → READY
/readyz HTTP 503         → UNAVAILABLE
未知 status              → DEGRADED
transport / contract fail→ UNAVAILABLE（health probe）
```

調度層後續必須以 readiness 決定是否允許建立或執行工程 Job。

## 六、安全邊界

- Project ID / Job ID 不允許 `/`、`?`、`#`，避免 path injection。
- 必填文字欄位先 trim，再拒絕空字串。
- 不把遠端錯誤吞掉後回傳假成功。
- 不在 Bridge 自動 retry mutating `POST`，避免重複建立 Job。
- 不在 Bridge 自動替使用者批准正式工程成果。

## 七、E2 完成標準

- [x] stdlib HTTP transport。
- [x] injectable transport。
- [x] health / readiness。
- [x] schema version / module capabilities。
- [x] list/get Projects。
- [x] list/get Jobs。
- [x] create Job。
- [x] timeout / transport / HTTP / contract error 分類。
- [x] 永久 regression tests。
- [x] 不修改 OpenWorker core runtime。

完整 repository pytest / import / lint 尚需在完整 checkout 環境通過後，才可由 `IMPLEMENTED — WAITING FOR FULL VERIFICATION` 升級為 `VERIFIED`。
