# E4：Direct Specialist Adapters 中文規格

更新日期：2026-08-08

## 1. 定位

Direct Specialist Adapter 是 OpenWorker 對權威專業引擎的薄型直接入口，不取代 AI-Engineering-OS。

```text
Engineering Coworker
├─ AI-Engineering-OS：Project / Job / Workflow / Artifact / Approval / Delivery 權威
└─ Direct Specialist Adapters：readiness、capability、受控專業操作
```

原則：專業算法留在各權威 repo；OpenWorker 不維護第二套公式、繪圖、BIM 或知識推理實作。

## 2. 第一批四個權威引擎

### AI-CivilDesign-Forge

來源契約：`tool-protocol/1.0.0`。

正式 machine-readable CLI：

```text
civilforge-tool capabilities
civilforge-tool execute <request.json>
```

OpenWorker Adapter：`DesignForgeAdapter`。

能力：`structural`、`reporting`。

正式 operations：

- `capabilities`
- `execute`

`execute` 只接受 `payload.request` JSON object，寫入暫存 request.json 後，以 argv list 呼叫 CLI；不透過 shell。

### AI-EngSketch

來源契約：DraftForge CLI 與 immutable version workspace。

OpenWorker Adapter：`EngSketchAdapter`。

能力：`drawing`、`reporting`。

E4 第一批只開：

- `themes`
- `validate`
- `versions`

刻意不開 `patch apply`、`generate`、`render` 等會建立或改變成果的操作。後續若開放，必須經 Tool Facade 與 Approval 分類，不得以 generic CLI escape hatch 暴露。

### AI-BIM-Forge

來源契約：README 明定 canonical Python API：

- `build_ifc_model`
- `build_and_write_ifc`
- `reopen_and_audit`
- `get_element_quantities`

OpenWorker Adapter：`BIMForgeAdapter`。

能力：`bim_ifc`、`quantity`。

採 lazy import `aibim.api`；未安裝、API 缺失時 readiness 回報 unavailable/degraded，而不是假裝能力存在。

### KnowGraphGo

來源契約：嵌入式 Go Library + `knowgraph` CLI。

OpenWorker Adapter：`KnowGraphAdapter`。

能力：`knowledge_graph`。

E4 第一批只開：

- `check`
- `node_list`

必須配置 DSN；沒有 DSN 時明確 unavailable。`node_list` 強制 JSON 輸出。

## 3. 安全邊界

所有 CLI adapter：

- 使用 argv list。
- 不使用 `shell=True`。
- 不接受任意 command string。
- operation 使用 allowlist。
- timeout 明確設定。
- 非零 exit code 視為失敗。
- machine-readable 回應必須驗證 JSON。

Direct Adapter 的 descriptor 使用 `ApprovalPolicy.MUTATING`，但 E4 本身不是 Tool surface。真正暴露給 Agent 的 mutating operation 仍必須在後續 Tool Facade 明確標記 approval，不可因 adapter 可呼叫就自動成為 Agent 工具。

## 4. 與控制平面的責任邊界

Direct Adapter 不得：

- 自建 Project ID / Job ID。
- 修改 AI-Engineering-OS lifecycle。
- 直接替代 Job / Artifact / Delivery authority。
- 將專業引擎內部算法複製到 OpenWorker。

正式工程任務優先路徑仍是：

```text
Engineering Coworker
→ AI-Engineering-OS Job
→ 專業 Engine
→ Artifact / Review / Approval / Delivery
```

Direct Adapter 主要用於能力發現、診斷、預覽、受控專業操作與後續 Golden Job orchestration。

## 5. 驗證

永久測試：`tests/test_engineering_specialists.py`。

涵蓋：

- Design Forge Tool Protocol health / execute。
- 禁止任意 Design Forge operation。
- EngSketch allowlist。
- KnowGraphGo DSN fail-closed 與 JSON node list。
- BIM canonical API readiness / invoke。
- 四個 Adapter 可同時註冊至 `EngineeringAdapterRegistry`。

完整 repository pytest / compileall 尚需在已安裝 OpenWorker dependencies 的 checkout 執行。
