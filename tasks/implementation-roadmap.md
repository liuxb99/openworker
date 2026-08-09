# OpenWorker 工程版獨立分段開發 Roadmap

更新日期：2026-08-09

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

## 目前 P0

1. E1～E6.4 尚待完整 checkout + dependencies 的 pytest / compileall / diff check。
2. 真實 AI-Engineering-OS + Design Forge + EngSketch + AI-BIM-Forge + filesystem delivery E2E 尚未在目前執行環境實際跑通。
3. 必須在部署機使用 `openworker-engineering-e2e --confirm-side-effects` 產生一次真實驗證證據，才可把 E6 系列升級為 `VERIFIED`。

## P1

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

## 下一階段

在進 E7 前，優先執行 E6.5 Verification Evidence / CI：讓 E6.4 harness 的真實執行結果能保存成 machine-readable evidence，並建立可重複的驗證入口；真實環境跑通後再把對應 Segment 升級為 VERIFIED。
