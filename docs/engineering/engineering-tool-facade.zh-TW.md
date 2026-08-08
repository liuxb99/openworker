# Engineering Tool Facade 與 Persona 掛載規格

## 一、目的

E3 將 E2 的 `EngineeringOSClient` 從 Python Client 提升為 OpenWorker 模型真正可呼叫的 Tool surface。

正式資料流：

```text
Engineering Coworker
        ↓ Persona tools
Catalog: engineering_os
        ↓
engineering_os_tools()
        ↓
EngineeringOSClient
        ↓ HTTP
AI-Engineering-OS
        ↓
Project / Job / Workflow / Artifact / Delivery
```

OpenWorker 只負責 AI 員工、工具暴露、Permission 與 Approval；Project／Job 業務規則仍由 AI-Engineering-OS 決定。

## 二、掛載方式

本功能沿用 OpenWorker 原生擴充鏈：

```text
coworker/personas/builtin/engineering.md
        ↓ tools: [ ..., engineering_os ]
coworker/personas/manifest.py
        ↓ catalog.expand(...)
coworker/catalog.py
        ↓ engineering_os capability
coworker/engineering/tools.py
        ↓ concrete callables
ToolRegistry
        ↓
TurnEngine / PermissionEngine
```

因此不需要在 `engine.py` 加入 `if engineering` 分支。

## 三、正式工具

### 唯讀工具

- `engineering_system_readiness`
- `engineering_list_projects`
- `engineering_get_project`
- `engineering_list_jobs`
- `engineering_get_job`

上述工具：

```text
risk_level = low
requires_approval = false
```

### 狀態變更工具

- `engineering_create_job`

此工具會在 AI-Engineering-OS 建立正式 Job，因此：

```text
category = engineering
risk_level = medium
requires_approval = true
```

OpenWorker 既有 `risk.classify()` 會將 `requires_approval=True` 的未知內建名稱歸類為 `RiskClass.EXTERNAL`，由既有 Permission / Approval 機制處理。

## 四、建立 Job 契約

Tool 輸入：

```text
project_id            required
code                  required
name                  required
user_request          required
expected_deliverables optional
priority              low | normal | high | urgent
metadata_json         optional JSON object string
```

Tool 不重新驗證 AI-Engineering-OS 的完整 Domain Rule，只做模型輸入層必要的 JSON shape 防護，再交由 `EngineeringOSClient.create_job()` 與 AI-Engineering-OS 正式 API 驗證。

## 五、Readiness 行為

`engineering_system_readiness` 先查：

```text
/healthz
/readyz
```

只有 health 與 readiness 都為 ready 時，才進一步讀取：

```text
/api/v1/system/modules
→ schema_version
→ configured capabilities
```

若控制平面未 ready，不繼續做 module discovery，避免把 unavailable 系統誤包裝成能力正常。

## 六、安全邊界

禁止：

- Tool 直接寫 SQLite。
- Tool 自行產生 Project / Job ID。
- Tool 自行模擬 Job lifecycle。
- Tool 繞過 AI-Engineering-OS API。
- Tool 把 `create_job` 標成 read-only。
- Persona 因為自己是 Engineering Coworker 就取得特殊繞過 Permission 的權限。

允許：

- 唯讀查詢直接執行。
- 外部狀態變更走 OpenWorker 標準 Approval。
- 專業演算法仍交由 AI-Engineering-OS 所調用的專業 Engines。

## 七、永久測試

E3 新增：

```text
tests/test_engineering_tools.py
tests/test_engineering_persona_wiring.py
```

覆蓋：

- 穩定 Tool 名稱。
- readiness summary。
- 唯讀工具無 approval。
- create_job 必須 approval。
- Project / Job delegate 行為。
- metadata JSON fail-closed。
- unavailable 時不得繼續 module discovery。
- `engineering_os` 必須是正式 catalog capability。
- Engineering persona manifest 必須宣告 `engineering_os`。
- capability risk summary 必須含 `EXTERNAL`。

## 八、完成狀態

E3 程式、永久測試與中文規格已落地。

在完整 repository checkout 執行 pytest / compileall / diff check 前，狀態維持：

```text
IMPLEMENTED — WAITING FOR FULL VERIFICATION
```
