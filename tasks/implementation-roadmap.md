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
- E7 Media / Company Coworker：`NOT_STARTED`

## 正式權責鏈

```text
ProjectRoot
├─ AGENTS.md
├─ TASK.md
└─ inputs/
        ↓
openworker-engineering
        ↓
EngineeringHarnessHost
        ↓
go-tool-runtime /agent/start
        ↓
AgentInformationPack
        ↓
ManagedDeepSeekHarnessRuntime
        ↓
OpenWorker PermissionEngine
        ↓
AI-Engineering-OS canonical tools
        ↓
Artifact Registry / Workspace Artifact Publisher
        ↓
deliverables / reports / evidence
```

固定原則：

1. go-tool-runtime 只負責 information/context，不執行工程 mutation。
2. OpenWorker 負責產品 lifecycle、permission、runtime jobs、Harness composition，不建立第二套 Tool Registry。
3. DeepSeek Harness 負責 agent loop / ACP，不是工程 schema authority。
4. AI-Engineering-OS 是 canonical tool / job / artifact / delivery authority。
5. 專業 Engine 仍是 domain authority。
6. consequential publish/mutate 必須同時通過 OpenWorker approval 與 AI-Engineering-OS allow_* gate。
7. NativeRuntime 不因 Harness 驗證完成而提前刪除；H8/H9 REAL A/B evidence 仍保留。

## Official H3-H11 + ProjectRoot CLI Win11 最終證據

### Harness / Workspace 主線

```text
Run: 31783857135
OpenWorker: 56265c07ea3b276bfcb8d930dbe6dad0151f15ef
DeepSeek Harness: 47f943859bef60e4160492346772ded9b24f765a
conclusion: success
```

此 run 已驗證 H1-H7、Project Workspace bootstrap/scope/Host/launch、H6.2 managed RC、H8-H11 deterministic regression、TypeScript、official Harness install、ACP、Cordis plugin 與 H6.2 deterministic consequential-tool E2E。

### ProductRoot CLI 主線

```text
OpenWorker commit: d7fdff82b56e7a048d19a16041c9d134781d2d9e
OpenWorker CI: 31788214072 — pytest success / gui-unit success
AI-Engineering-OS official Win11: 31788465175 — success
```

`31788465175` 明確包含：

```text
Project Workspace bootstrap, Host, and CLI product regressions — success
Official ACP initialize and session-new smoke — success
Official Harness Cordis Engineering tool plugin smoke — success
H6.2 deterministic official Harness engineering tool Golden E2E — success
```

因此 `openworker-engineering` 真正 CLI composition root 已完成 Windows acceptance，不再只是 Host/unit contract。

## Windows 真機修正閉環

### Cordis / Node ESM file URL

Windows Node ESM 不接受裸 `C:/...` module specifier。official plugin smoke、H6.2 E2E、production EngineeringHarnessHost、official Cordis include 均已統一使用 `Path.resolve().as_uri()`。

### loopback context ingress WinError 10053

舊 Win11 run `31782095019` 暴露 auth reject 時 unread request body 可能造成 WSAECONNABORTED / WinError 10053。現在 `HarnessContextIngressServer` 在拒絕未授權 request 時只 drain bounded Content-Length body，再回 JSON 401；仍維持 auth-before-parse、body-size limit 與 policy-field smuggling rejection。成功 run `31783857135` / `31788465175` 已驗證。

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

安全 contract：

- workspace identity 必須與 AgentInformationPack 一致。
- bootstrap prompt 必須含 information / execution authority markers。
- Project deterministic reuse；Job 每次 run 新建。
- packaged Harness 明確配置但不可用時 fail closed。
- Agent 不掃磁碟、不猜 Node/Harness/engine path。
- publish capability 預設關閉；consequential call 仍需 OpenWorker approval + AI-Engineering-OS authorization。

## ProductRoot CLI product smoke

永久 regression：

```text
tests/runtimes/test_engineering_cli_product_smoke.py
```

直接執行真正 `openworker-engineering` CLI composition root，驗證：

```text
TASK.md fallback
→ Project create/reuse contract
→ per-run Job create
→ canonical tool catalog discovery
→ go-tool-runtime /agent/start
→ authority prompt
→ managed Harness turn
→ go-tool-runtime /agent/finish success
```

此 smoke 不冒充 REAL Publisher evidence。真實 `workspace.publish_artifact` ownership/SHA/path sandbox 已由 AI-Engineering-OS Workspace Artifact Publisher Win11 run `31780534951` 獨立驗證。

## H8 / H9 REAL evidence

H8/H9 deterministic verifier code 與 workflow contract 已完成；REAL evidence 仍需 supplied 真實 ID：

```text
H8: 同機 NativeRuntime vs HarnessRuntime RC Golden project/job IDs
H9: 真實 ComfyX GPU job + non-empty MP4 artifact
```

沒有真實 IDs 時保持 skipped，不生成假 evidence。

## 本階段結論

Project Workspace / go-tool-runtime / OpenWorker / official DeepSeek Harness / AI-Engineering-OS / Workspace Artifact Publisher 的代碼主線已完成並通過 Win11 acceptance。

本階段沒有剩餘 production code blocker。後續工作分成兩條獨立線：

1. H8/H9 REAL hardware evidence 補齊，不改變 deterministic code 已完成的狀態。
2. 進 E7 Media / Company Coworker，沿用既有 authority/Host/Tool/Artifact 架構，不新增第二套 Agent loop / Tool Registry / Artifact Registry。
