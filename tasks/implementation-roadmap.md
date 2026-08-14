# OpenWorker 工程版獨立分段開發 Roadmap

更新日期：2026-08-14

## 專案定位

OpenWorker 工程版是 AI 工程顧問公司的 AI 員工與自然語言操作層；AI-Engineering-OS 保持 Project / Job / Workflow / Artifact / Review / Delivery lifecycle 權威，專業 Engine 保持工程算法權威。

## 目前完成度

- E0：`IMPLEMENTED`
- E1 Capability Registry / Readiness：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E2 AI-Engineering-OS Bridge：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E3 Tool Facade + Persona Wiring：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E4 Direct Specialist Adapters：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E5 Digital Thread / Provenance：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6 RC Column Golden Job：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.1 Lifecycle Closure：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.2 Review / Approval / Delivery：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.3 OS-managed Calculation + Drawing + BIM RC Flow：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- E6.4 Public RC Flow API + E2E Verification Harness：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- H0 OpenWorker × DeepSeek Harness 架構研究/詳細設計：`IMPLEMENTED`
- H1 AgentRuntime seam / NativeRuntime：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`
- H2 Harness integration skeleton：`NOT_STARTED`
- H3 DeepSeekHarnessRuntime sidecar adapter：`NOT_STARTED`
- H4 Tool / Permission / Approval bridge：`NOT_STARTED`
- H5 Session / Resume bridge：`NOT_STARTED`
- H6 AI-Engineering-OS dynamic tools：`NOT_STARTED`
- H7 Runtime jobs / interrupt mapping：`NOT_STARTED`
- H8 RC Golden Job Native vs Harness A/B：`NOT_STARTED`
- H9 ComfyX long-running job validation：`NOT_STARTED`
- H10 Desktop packaging：`NOT_STARTED`
- H11 Default-runtime decision：`NOT_STARTED`
- E7 Media / Company Coworker：`NOT_STARTED`

## E6.3 / E6.4 架構

完整 RC Golden Path 以 AI-Engineering-OS `internal/rcflow` 為權威：

```text
Job
→ design-forge / rc-column
→ engsketch / generate
→ aibim / build
→ Calculation + Drawing + BIM/IFC Artifacts
→ Job review
```

OpenWorker 不自行重建上述 workflow，而是透過 public client API 呼叫：

```python
EngineeringOSFlowClient.execute_rc_column_flow(...)
```

正式 route 仍為：

`POST /api/v1/jobs/{id}/flows/rc-column`

E6.4 已移除 `managed_rcflow.py` 對 `EngineeringOSClient._object()` / `_required_id()` 的直接依賴。Agent Tool 與 verification harness 均使用同一 public flow contract。

## E6.4 可部署 E2E Verification

新增 CLI：

```text
openworker-engineering-e2e
```

預設真實驗證路徑：

```text
readiness
→ Project identity
→ create Job
→ OS RC Flow
→ Calculation + Drawing + IFC Artifact completeness
→ review
```

CLI 必須帶 `--confirm-side-effects` 才允許建立工程資料。

治理階段保持顯式：

- 沒有 `--reviewer`：停在 review。
- 有 `--reviewer`：逐 Artifact Review，要求 derived Approval Status = approved 且 Job = completed。
- `--publisher` 必須搭配 reviewer；Publish 後要求 Job = published。

因此 harness 能實際驗證：AI-Engineering-OS、Design Forge、EngSketch、AI-BIM-Forge、Artifact lifecycle，以及選配的 Review / Delivery；但「程式已存在」不等於「真實環境已跑通」。

## E6 系列目前閉環

```text
Engineering Coworker
→ OpenWorker Approval Gate
→ AI-Engineering-OS Job
→ OS RC Flow
   ├─ Calculation
   ├─ Engineering Drawing
   └─ BIM / IFC
→ OS Artifacts
→ review
→ Artifact Reviews
→ derived Approval Status
→ completed
→ Delivery Publish
→ checksum / manifest / website
→ published
```

## H0 / H1 DeepSeek Harness 開發線

架構權責固定為：

```text
OpenWorker Product Layer
        ↓
AgentRuntime seam
   ├─ NativeRuntime → existing TurnEngine
   └─ DeepSeekHarnessRuntime → future dsh sidecar
        ↓
OpenWorker Tool / Permission Gateway
        ↓
AI-Engineering-OS authoritative engineering workflows
```

H1 已完成：

- `coworker/runtimes/base.py`：最小 `AgentRuntime` lifecycle protocol。
- `coworker/runtimes/native.py`：以 `TurnEngine` 為實作基底的 `NativeRuntime`。
- `coworker/runtimes/events.py`：沿用既有 OpenWorker `Event/EventType`，避免第二套 UI event contract。
- `coworker/runtimes/manager.py`：集中 runtime name/selection；H1 僅允許 native，Harness fail-closed。
- `coworker/runtimes/__init__.py`：正式 runtime package exports。
- `coworker/agent.py`：唯一正式建構點由 `TurnEngine(...)` 改為 `NativeRuntime(...)`，其餘 engine wiring 不變。
- `tests/runtimes/test_runtime_seam.py`：永久測試覆蓋 native compatibility、正式 build path、event identity、default selection、Harness fail-closed、unknown runtime rejection。

H1 明確不做：

- 不啟動 dsh。
- 不加入 Node/Harness dependency。
- 不改 Permission/Approval semantics。
- 不改 Session persistence。
- 不改 UI/WebSocket event schema。
- 不改 AI-Engineering-OS workflow。
- 不把 Harness 當 ProviderClient。

H1 驗證狀態：

```text
Git diff review: PASS（agent.py 僅 import + constructor switch）
Permanent regression tests: ADDED
GitHub Actions: BLOCKED / repository API currently reports 0 workflow runs
Full pytest / GUI / E2E: NOT YET EXECUTED
Status: IMPLEMENTED — WAITING FOR FULL VERIFICATION
```

下一個 Harness Segment：H2，建立 `harness/` integration skeleton、pin policy、versioned IPC protocol contract、health/capability schema與 TypeScript permanent tests；H2 不啟用正式 Harness agent loop。

## 目前 P0

1. E1～E6.4 尚待完整 checkout + dependencies 的 pytest / compileall / diff check。
2. 真實 AI-Engineering-OS + Design Forge + EngSketch + AI-BIM-Forge + filesystem delivery E2E 尚未在目前執行環境實際跑通。
3. 必須在部署機使用 `openworker-engineering-e2e --confirm-side-effects` 產生一次真實驗證證據，才可把 E6 系列升級為 `VERIFIED`。
4. H1 必須補一次完整 repository CI / pytest 證據，才能由 `IMPLEMENTED — WAITING FOR FULL VERIFICATION` 升為 `VERIFIED`。

## P1

- H2～H7：完成 Harness sidecar / tools / approval / session / jobs integration。
- H8～H9：以 RC Golden Job 與 ComfyX 長任務做 Native vs Harness 真實 A/B。
- Review / Delivery evidence 納入 Digital Thread 下一版。
- pcces-web / Quantity / Schedule / DWG/PDF 第二批 adapters。
- adapter config persistence / Digital Thread persistence。
- E7 Media / Company Coworker。

## E6 系列驗收

- [x] 計算 Artifact。
- [x] EngSketch drawing stage 納入 OS authoritative rcflow。
- [x] AI-BIM-Forge BIM/IFC stage 納入 OS authoritative rcflow。
- [x] Drawing/BIM Artifact completeness fail-closed。
- [x] Job review closure。
- [x] Artifact Review / derived approval / publish closure。
- [x] mutating Agent tools 均經 OpenWorker Approval Gate。
- [x] managed RC flow public client API。
- [x] deployable E2E verification harness。
- [x] E2E CLI side-effect confirmation gate。
- [x] permanent regression tests / 中文規格。
- [ ] full repository verification。
- [ ] real multi-repo runtime E2E verification evidence。

## H1 驗收

- [x] AgentRuntime seam 存在。
- [x] NativeRuntime 保留 TurnEngine 行為與相容性。
- [x] 正式 `build_engine()` 路徑改走 NativeRuntime。
- [x] runtime event contract 不分叉。
- [x] Harness 在未實作前 fail-closed。
- [x] 永久 regression tests 已加入。
- [x] 無 Harness runtime dependency / sidecar 偷渡進 H1。
- [ ] full pytest / GUI / E2E verification evidence。

## 下一階段

Harness 主線先進 H2 integration skeleton；原 E6.5 Verification Evidence / CI 仍保留為工程線 P0，兩者不得互相覆蓋或改變 AI-Engineering-OS 的工程權威。
