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
- ProjectRoot CLI product smoke：`IMPLEMENTED — CI IN PROGRESS`
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

## Official H3-H11 Win11 最終證據

最新完成 run：

```text
AI-Engineering-OS workflow: OpenWorker Harness H3-H11 Official Win11
Run: 31783857135
OpenWorker: 56265c07ea3b276bfcb8d930dbe6dad0151f15ef
DeepSeek Harness: 47f943859bef60e4160492346772ded9b24f765a
conclusion: success
```

同一次 self-hosted Win11 run 已全部通過：

```text
H1-H7 runtime regressions
Project Workspace bootstrap / scope / Host / production plugin URI / launch
H6.2 managed RC Golden non-regression
H8-H11 deterministic packaging/default policy regressions
H2 TypeScript contracts
pinned official DeepSeek Harness checkout/install
ACP initialize + session/new smoke
Cordis dynamic engineering tool plugin smoke
H6.2 deterministic consequential-tool Golden E2E
```

H8/H9 REAL evidence steps本次依設計 skipped，因為沒有 supplied real project/job IDs；這不等於 verifier code 未完成，也不把 deterministic evidence 假冒成 real hardware evidence。

## Windows 真機修正閉環

### 1. Cordis plugin module specifier

Windows Node ESM loader 不接受裸 `C:/...` module specifier。現在三層都統一使用 `Path.resolve().as_uri()`：

```text
official plugin smoke
H6.2 deterministic E2E
production EngineeringHarnessHost
```

### 2. loopback context ingress WinError 10053

Win11 run `31782095019` 暴露：無 Authorization 的 POST 在 request body 未被 drain 時，Windows 可把連線視為 WSAECONNABORTED / WinError 10053，而不是讓 client 穩定收到 401。

`HarnessContextIngressServer` 現在在 auth reject 時只 drain bounded Content-Length body，再回傳 JSON error；維持 auth-before-parse 與 body-size 上限，不放寬 policy。此修正已包含於成功的 `56265c07...` official gate。

### 3. H6.2 Cordis include

H6.2 deterministic config 的 official Cordis include path 也改成 file URL，避免 Windows `c:` scheme 解讀問題。成功 run `31783857135` 已證實 include + plugin + agent loop 一起成立。

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

- cwd/workspace identity 必須與 AgentInformationPack 回報一致。
- prompt 必須帶 `information_authority=go-tool-runtime` 與 `execution_authority=AI-Engineering-OS`。
- Project 依 workspace deterministic reuse；Job 每次 run 新建。
- packaged Harness capability 明確配置但不可用時 fail closed。
- Agent 不掃磁碟、不猜 Node/Harness/engine path。
- publish capability 預設關閉，需 explicit enable；每個 consequential call 仍需 approval。

## ProductRoot CLI product smoke

新增永久 regression：

```text
tests/runtimes/test_engineering_cli_product_smoke.py
OpenWorker commit: d7fdff82b56e7a048d19a16041c9d134781d2d9e
```

此測試直接執行真正 `openworker-engineering` CLI composition root，使用 loopback authority contract servers 與既有 deterministic ACP fixture，驗證：

```text
TASK.md fallback
→ AI-Engineering-OS Project create/reuse contract
→ per-run Job create
→ canonical tool catalog discovery
→ go-tool-runtime /agent/start
→ authority prompt
→ managed Harness turn
→ /agent/finish success
```

這個 smoke 不宣稱 REAL Publisher evidence；真實 `workspace.publish_artifact` ownership/SHA/path sandbox 已由 AI-Engineering-OS Workspace Artifact Publisher Win11 run `31780534951` 獨立驗證。

目前 OpenWorker CI run `31788214072` 正在驗證 `d7fdff82...`；通過後會把此 test 加入 AI-Engineering-OS official Win11 gate。

## H8 / H9 REAL evidence

H8/H9 deterministic verifier code 與 workflow contract 已完成，但 real evidence 必須 supplied 真實 ID：

```text
H8: 同機 NativeRuntime vs HarnessRuntime RC Golden project/job IDs
H9: 真實 ComfyX GPU job + non-empty MP4 artifact
```

沒有真實 IDs 時保持 skipped，不生成假 evidence。

## 下一批

1. 收 `31788214072` ProductRoot CLI smoke 的 Python CI 結果；失敗就沿真實 traceback 修。
2. CI 綠後，把 `d7fdff82...` pin 到 AI-Engineering-OS official Win11，將 CLI product smoke 納入同一 gate。
3. official Win11 CLI smoke 綠後，Project Workspace / Harness 主線代碼正式完成。
4. H8/H9 REAL hardware evidence 作獨立驗證線，不阻塞 deterministic code release。
5. 再進 E7 Media / Company Coworker，不另造第二套 Agent loop / Tool Registry / Artifact Registry。
