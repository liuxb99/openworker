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
- H1 AgentRuntime seam / NativeRuntime：`VERIFIED — WIN11 LOCAL ACTION`
- H2 Harness integration skeleton / ACP-first contract：`VERIFIED — WIN11 LOCAL ACTION`
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

## H1 Win11 本機 Action 驗證

本專案 Harness 主線以 Windows 11 self-hosted GitHub Actions 作為正式驗證，不以 GitHub-hosted Ubuntu 取代本機證據。

候選版：

```text
OpenWorker ref: c1d325d15ac15ba34bcd14b744ffc185ca497cb4
AI-Engineering-OS workflow: openworker-win11-verify.yml
Run: 31758376818
Runner: DESKTOP-ODAQN0D-R002 / DESKTOP-ODAQN0D
Windows: 10.0.26200.8655 (Windows 11)
Python: 3.14.6
compileall: PASS
H1 runtime seam regression: 6 passed / 0 failed
Full Python suite: 1247 passed / 12 failed / 2 skipped
```

H1 前基線：

```text
OpenWorker ref: 468d58104b4b6f3dfa69cbdf098d078c8cc74b05
AI-Engineering-OS workflow: openworker-win11-baseline.yml
Run: 31758614434
Runner: DESKTOP-O87PJNR-R003 / DESKTOP-O87PJNR
Windows: 10.0.26200.8655 (Windows 11)
Python: 3.14.5
compileall: PASS
Full Python suite: 1241 passed / 12 failed / 2 skipped
```

差分結論：

- H1 新增 6 個 permanent tests，全部通過。
- H1 前後完整 Python suite 的失敗數都是 12，且失敗測試名稱逐項相同。
- 候選版沒有新增 full-suite failure；passed 數正好增加 6。
- 現存 12 個 failure 屬 H1 前既有 Win11/Python 3.14/NetworkService 測試基線，不得算成 H1 regression；仍需在獨立維護 Segment 修正。
- 兩次 A/B 被不同 Win11 runner 接單，因此未宣稱「同一硬體」結果；後續 H8/H9 性能與行為 A/B 必須固定 machine label，禁止 runner 漂移。

現存 Win11 baseline failure 類別包括：symlink privilege、Windows ACL/0600 語義、workspace rename file lock、PowerShell `pwd` 呈現、RelayHub/Slack timing、UI refresh timing，以及既有 engineering E2E `draft`/`review` fixture 狀態。這些在 H1 前基線已同樣存在。

H1 狀態：

```text
Git diff review: PASS
Permanent regression tests: PASS 6/6
Win11 compileall: PASS
Win11 full-suite differential regression: PASS（0 new failures）
Status: VERIFIED — WIN11 LOCAL ACTION
```

## H2 Harness integration skeleton / ACP-first contract

H2 研究確認 DeepSeek Harness `master` 在 2026-08-13 已發布 public `0.1.0-rc.5`，其中 `@deepseek-ai/dsh-acp` 提供 Agent Client Protocol JSON-RPC stdio automation server。

H2 upstream pin：

```text
Repository: deepseek-ai/deepseek-harness
Commit: 47f943859bef60e4160492346772ded9b24f765a
Release: 0.1.0-rc.5
CLI package: @deepseek-ai/dsh 0.1.0-rc.5
ACP package: @deepseek-ai/dsh-acp 0.1.0-rc.5
```

H2 採用原則：

- 官方 ACP 優先承擔 fresh session / text prompt / committed answer / cancel / one-shot permission 控制。
- 不再自行重造已存在的 JSON-RPC stdio bootstrap protocol。
- ACP 不是完整 Runtime bridge：官方 rc.5 尚不提供 durable load/resume/replay、live reasoning/tool events、plan/title/usage、per-session close、額外 directory/MCP injection 或 multimodal prompt。
- 因此 H3～H5 仍須用 OpenWorker-specific Harness plugin bridge 補足 session/event/tool lifecycle，不能把 ACP 直接等同 `DeepSeekHarnessRuntime`。

H2 新增：

```text
harness/upstream-lock.json
harness/package.json
harness/tsconfig.json
harness/src/protocol.ts
harness/src/health.ts
harness/tests/contracts.test.mjs
harness/README.zh-TW.md
```

H2 capability contract 特別把 ACP 未支援能力顯式標成 `false`，防止後續程式或文件在未實作前誤宣稱 resume/replay/live tool events 已可用。

H2 Win11 驗證：

```text
OpenWorker ref: b679ca670de2afed3c7de760900c70c3e1b8ebcd
AI-Engineering-OS workflow: openworker-harness-h2-win11.yml
Run: 31759166471
Runner: DESKTOP-O87PJNR-R003 / DESKTOP-O87PJNR
Windows: 10.0.26200.8655 (Windows 11)
Python: 3.14.5
Node: v24.19.0
npm: 11.17.0
OpenWorker compileall: PASS
H1 runtime regression: 6 passed / 0 failed
npm install: PASS / 0 vulnerabilities
TypeScript build: PASS
H2 contract tests: 4 passed / 0 failed
Status: VERIFIED — WIN11 LOCAL ACTION
```

H2 明確沒有宣稱：

- 真實 dsh process 已由 OpenWorker 啟動。
- Harness 已可取代 NativeRuntime。
- ACP 已有 OpenWorker 所需全部事件與 durable session 能力。
- OpenWorker PermissionEngine 已經接到 Harness tool pipeline。

下一個 Harness Segment：H3，實作真實 Harness/ACP process lifecycle adapter，先完成 process spawn/stdio JSON-RPC initialize/session-new/prompt/cancel/health/shutdown smoke；NativeRuntime 仍為預設，H3 不提前做完整 tool/approval/session bridge。

## 目前 P0

1. E1～E6.4 尚待完整工程 runtime E2E 與 evidence 閉環；不能因 H1/H2 已 VERIFIED 而升級 E 系列狀態。
2. 真實 AI-Engineering-OS + Design Forge + EngSketch + AI-BIM-Forge + filesystem delivery E2E 尚需依工程線驗證規格補證據。
3. OpenWorker Win11 full suite 現存 12 個 pre-H1 baseline failures，應另開維護 Segment 修復，不阻擋已證實零新增失敗的 H1/H2。
4. 後續 Harness A/B Action 必須固定 runner/machine label，避免兩台 Win11 runner 漂移造成性能比較失真。

## P1

- H3～H7：完成 Harness sidecar / tools / approval / session / jobs integration。
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
- [x] Windows 11 self-hosted Action compileall。
- [x] H1 permanent tests 6/6。
- [x] pre-H1 vs H1 full Python suite 差分：0 new failures。

## H2 驗收

- [x] upstream commit/release 精確 pin。
- [x] ACP-first control-plane decision documented。
- [x] ACP 未支援能力 fail-closed / explicit false。
- [x] versioned OpenWorker Harness bridge contract。
- [x] health/capability schema。
- [x] TypeScript strict build。
- [x] permanent contract tests 4/4。
- [x] H1 regression 6/6 retained。
- [x] Windows 11 self-hosted Action evidence。
- [x] 不啟用 Harness runtime、不改 Native default。

## 下一階段

Harness 主線進 H3 DeepSeekHarnessRuntime sidecar/ACP adapter；原 E6.5 Verification Evidence / CI 仍保留為工程線 P0，兩者不得互相覆蓋或改變 AI-Engineering-OS 的工程權威。
