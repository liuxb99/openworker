# OpenWorker 工程版獨立分段開發 Roadmap

更新日期：2026-08-08

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
- E7 Media / Company Coworker：`NOT_STARTED`

## E6.3 架構修正

核對 AI-Engineering-OS `internal/rcflow` 後確認，正式系統已具備完整 RC 柱三段流程：

```text
Job
→ design-forge / rc-column
→ engsketch / generate
→ aibim / build
→ Calculation + Drawing + BIM/IFC Artifacts
→ Job review
```

因此正式 Golden Path 不再由 OpenWorker 自行逐一調三個 specialist，而是呼叫：

`POST /api/v1/jobs/{id}/flows/rc-column`

新增：

- `coworker/engineering/managed_rcflow.py`
- `coworker/engineering/managed_tools.py`
- `engineering_run_rc_column_flow`（`requires_approval=True`）
- Drawing / BIM Artifact completeness fail-closed
- OS Artifact → Job Digital Thread
- 永久 regression tests
- 中文規格 `docs/engineering/managed-rcflow.zh-TW.md`

E6/E6.1 的 direct Design Forge path 保留為低階 integration fixture；完整工程流程以 AI-Engineering-OS rcflow 為權威，避免 OpenWorker 形成第二套 Workflow Engine。

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
→ E6.2 Artifact Reviews
→ derived Approval Status
→ completed
→ Delivery Publish
→ checksum / manifest / website
→ published
```

## 目前 P0

1. E1～E6.3 尚待完整 checkout + dependencies 的 pytest / compileall / diff check。
2. 真實 AI-Engineering-OS + Design Forge + EngSketch + AI-BIM-Forge + filesystem delivery runtime E2E 尚未在目前環境執行。
3. `managed_rcflow.py` 第一版透過 package-internal client helpers 呼叫 route；後續應把 rcflow route 正式提升為 `EngineeringOSClient` public method，降低內部耦合。

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
- [x] permanent regression tests / 中文規格。
- [ ] full repository verification。
- [ ] real multi-repo runtime E2E。

## 下一階段

優先 E6.4：把 managed rcflow 正式收進 `EngineeringOSClient` public contract、補真實 runtime-friendly verification harness，然後再進 E7 Media / Company Coworker。
