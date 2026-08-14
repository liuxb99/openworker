# OpenWorker 工程版獨立分段開發 Roadmap

更新日期：2026-08-14

## 專案定位

OpenWorker 工程版是 AI 工程顧問公司的 AI 員工與自然語言操作層；go-tool-runtime 是 Project Workspace 的 Information / Context Authority；AI-Engineering-OS 保持 Project / Job / Tool / Artifact / Review / Delivery lifecycle 權威；DeepSeek Harness 是可替換 agent runtime；專業 Engine 保持工程算法權威。

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
- H3 DeepSeekHarnessRuntime sidecar adapter：`VERIFIED — OFFICIAL ACP WIN11 LOCAL ACTION`
- H4 Tool / Permission / Approval bridge：`VERIFIED — OFFICIAL H3-H11 WIN11 GATE`
- H5 Session / Resume bridge：`VERIFIED — OFFICIAL H3-H11 WIN11 GATE`
- H6 AI-Engineering-OS dynamic tools：`VERIFIED — OFFICIAL H3-H11 WIN11 GATE`
- H6.1 Harness Cordis tool adapter + context ingress：`VERIFIED — OFFICIAL H3-H11 WIN11 GATE`
- H6.2 Official Harness consequential-tool Golden E2E：`VERIFIED — OFFICIAL H3-H11 WIN11 GATE`
- H7 Runtime jobs / interrupt mapping：`VERIFIED — OFFICIAL H3-H11 WIN11 GATE`
- H8 RC Golden Job Native vs Harness A/B：`IMPLEMENTED / DETERMINISTIC VERIFIED — REAL SAME-MACHINE EVIDENCE PENDING`
- H9 ComfyX long-running job validation：`IMPLEMENTED / DETERMINISTIC VERIFIED — REAL GPU MP4 EVIDENCE PENDING`
- H10 Desktop packaging：`VERIFIED — OFFICIAL H3-H11 WIN11 GATE`
- H11 Default-runtime decision：`VERIFIED — OFFICIAL H3-H11 WIN11 GATE`
- Project Workspace Bootstrap / one-command Engineering Host：`VERIFIED — OFFICIAL H3-H11 WIN11 GATE`
- ProjectRoot CLI product smoke：`VERIFIED — OFFICIAL WIN11 GATE`
- E7 Media / Company Coworker：`IN PROGRESS — E7.1 BUILTIN PERSONAS IMPLEMENTED / PYTHON VERIFIED；WIN11 FOCUSED GATE PENDING`

## 正式權責鏈

```text
ProjectRoot
├─ AGENTS.md
├─ TASK.md
└─ inputs/
        ↓
OpenWorker persona / product surface
        ↓
NativeRuntime（產品預設）或 explicit Harness opt-in
        ↓
go-tool-runtime information/context（Harness engineering path）
        ↓
AI-Engineering-OS canonical tools
        ↓
professional domain engines
        ↓
Artifact Registry / Workspace Artifact Publisher
        ↓
deliverables / reports / evidence
```

固定原則：

1. go-tool-runtime 只負責 information/context，不執行工程 mutation。
2. OpenWorker 負責產品 lifecycle、permission、runtime jobs、persona 與 Harness composition，不建立第二套 Tool Registry。
3. DeepSeek Harness 負責 agent loop / ACP，不是工程 schema authority。
4. AI-Engineering-OS 是 canonical tool / job / artifact / delivery authority。
5. 專業 Engine 仍是 domain authority。
6. consequential publish/mutate 必須同時通過 OpenWorker approval 與 AI-Engineering-OS allow_* gate。
7. H11 維持 NativeRuntime 為產品預設；Harness 仍須 explicit opt-in，直到 H8/H9 REAL evidence 支持改變 default policy。

## Official H3-H11 + ProjectRoot CLI Win11 最終證據

### Harness / Workspace 主線

```text
Run: 31783857135
OpenWorker: 56265c07ea3b276bfcb8d930dbe6dad0151f15ef
DeepSeek Harness: 47f943859bef60e4160492346772ded9b24f765a
conclusion: success
```

### ProductRoot CLI 主線

```text
OpenWorker commit: d7fdff82b56e7a048d19a16041c9d134781d2d9e
OpenWorker CI: 31788214072 — pytest success / gui-unit success
AI-Engineering-OS official Win11: 31788465175 — success
```

`31788465175` 已通過 Project Workspace bootstrap/Host/CLI product regression、ACP、Cordis plugin 與 H6.2 deterministic official E2E。

## Windows 真機修正閉環

- Cordis / Node ESM：official plugin smoke、H6.2 E2E、production EngineeringHarnessHost、official Cordis include 均使用 `Path.resolve().as_uri()`。
- loopback context ingress：auth reject 時只 drain bounded Content-Length body，再回 JSON 401；維持 auth-before-parse、body-size limit 與 policy-field smuggling rejection。`31783857135` / `31788465175` 已驗證。

## Project Workspace / one-command Host

已完成：

```text
ToolRuntimeBootstrapClient
EngineeringOSScopeClient
EngineeringHarnessRuntime
EngineeringHarnessHost
packaged_process_config
openworker-engineering CLI
```

安全 contract：workspace identity 必須與 AgentInformationPack 一致；Project deterministic reuse、Job 每次 run 新建；Agent 不掃磁碟、不猜 Node/Harness/engine path；publish capability 預設關閉；consequential call 仍需 OpenWorker approval + AI-Engineering-OS authorization。

## E7 Media / Company Coworker

### E7.1 — Built-in persona product surfaces

本批已新增：

```text
coworker/personas/builtin/media.md
coworker/personas/builtin/company.md
tests/test_e7_builtin_personas.py
.github/workflows/e7-media-company-personas-win11.yml
```

Media Coworker 定位：研究、腳本、prompt、圖片/影片/音訊、ComfyX/其他 specialist media workflow、artifact QA 與 delivery package 的協調層。

Company Coworker 定位：機會研究、proposal、project kickoff、engineering/media coordination、status brief、client update、delivery checklist 與 follow-up 的跨職能協調層。

兩者都只復用既有：

```text
PersonaRegistry
OpenWorker Native/Harness runtime policy
connectors / messaging / scheduler
engineering_os facade
AI-Engineering-OS canonical tools
Workspace Artifact Publisher
professional engines
```

不得：

```text
新增第二套 agent loop
auto-copy static tool registry
掃描任意磁碟猜工具路徑
把 draft 當成已發送/已發布
未經 approval 自動發送、發布、購買、付款或承諾
假造 image/video/upload/delivery artifact
```

E7 persona registry regression 已驗證：Media/Company 都是 builtin、knowledge/deliverable workspace、messaging/connectors enabled，並包含 `engineering_os` vetted capability。

Python CI：

```text
OpenWorker run: 31789065761
pytest: completed / success
gui-unit/typecheck: completed / success
```

Focused Win11：

```text
Workflow: E7 Media Company Personas Win11
Run: 31789065928
status: queued / waiting for self-hosted Windows runner
```

在 `31789065928` 全綠前 E7.1 不提前標 Win11 VERIFIED。

### H11 runtime boundary 對 E7 的影響

E7 不強制 Harness。H11 policy 保持：

```text
DEFAULT_RUNTIME = NativeRuntime
Harness = explicit opt-in + packaged launch capability required
```

所以 Media / Company Coworker 在一般產品使用中走既有 NativeRuntime；需要 Harness 且部署已 opt-in 時才走已驗證 Harness path。專業工程/媒體能力仍由 `engineering_os` / AI-Engineering-OS 動態調用，不在 persona 內複製工具實作。

### E7.2 — 下一批

下一批不是造新 runtime，而是補「產品任務包」：

```text
Media task package
→ brief / inputs
→ production plan / prompt pack
→ canonical media execution request
→ ArtifactRef / QA / delivery package

Company task package
→ request / evidence
→ research / proposal / work package
→ engineering/media handoff when needed
→ delivery/follow-up plan
```

並把 scheduler/connectors 的既有行為接入 persona-level product contract：draft 與 external send/publish 嚴格分離，所有 consequential action 繼續沿既有 approval boundary。

## H8 / H9 REAL evidence

H8/H9 deterministic verifier code 與 workflow contract 已完成；REAL evidence 仍需 supplied 真實 ID。沒有真實 IDs 時保持 skipped，不生成假 evidence。

## 本階段結論

Project Workspace / go-tool-runtime / OpenWorker / official DeepSeek Harness / AI-Engineering-OS / Workspace Artifact Publisher 的代碼主線已完成並通過 Win11 acceptance。E7 已正式開始，第一批 persona 產品入口已實作並通過 Python regression；下一步是 Win11 focused gate + E7.2 任務包，而不是重寫底層 runtime。
