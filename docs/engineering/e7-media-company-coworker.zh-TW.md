# E7 Media / Company Coworker 開發進度

更新日期：2026-08-14

## 目標與固定邊界

E7 讓 OpenWorker 的 Media / Company Coworker 把工作轉成可保存、可交接、可執行、可驗證、可交付的產品流程，但不再造第二套平台。

固定邊界：

- 不新增第二套 Agent loop / Tool Registry / Scheduler / Connector layer / Artifact Registry。
- NativeRuntime 預設；Harness 只允許 explicit opt-in。
- canonical engineering / media Job authority 固定由 AI-Engineering-OS control plane 管理；ComfyX 等 specialist engine 只擁有自己的專業執行契約。
- send / publish / spend / purchase / commitment 必須保留既有 approval gate。
- Persona 模組只做產品 contract、lineage、handoff、evidence sync 與 result projection，不直接偷跑外部副作用。

## E7.1～E7.4

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

已完成 Media/Company built-in personas、declarative Task Package、Persona Product Contract、canonical AI-Engineering-OS Job submission/reuse 與 delivery assessment。E7.4 main CI `31790725031` 全綠。

## E7.5 — Canonical Execution / Result Bridge

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

Persona 只建立既有 Tool Registry 可執行的 `CanonicalToolCall` descriptor；RC-column 委派 AI-Engineering-OS authoritative flow。`read_canonical_result()` 只回讀 canonical Job/Artifact/Review/approval，任何 lineage 衝突 fail closed，且永遠不宣稱已 publish/send。

E7.5 曾有一個舊 wiring 固定名單漏列新 tool 的 regression，已修正；最新 E7.6 main CI 已完整覆蓋並全綠。

## E7.6 — Authoritative Media Canonical Submit Facade

狀態：`IMPLEMENTED / MAIN CI VERIFIED；WIN11 FOCUSED GATE PENDING`

權威來源固定為 ComfyX `cmd/comfyx-tool/main.go`：

```text
protocol_version = ai-tool-protocol/1.0.0
tool_id          = comfyx.minimax_h3.generate
```

OpenWorker 的 `ComfyXToolClient` 只做 protocol adapter 與 fail-closed response validation；Desktop runtime discovery、MiniMax H3 五模式 prompt build、ComfyUI submission/poll、history 與 artifact extraction 全部仍由 ComfyX 負責。

Media persona 經既有 `engineering_os` catalog capability 使用 `engineering_generate_minimax_h3`，沒有新增第二套 registry/scheduler。生成 tool `requires_approval=True`，結果保留 `prompt_id/history/artifacts` 且固定 `publish_performed=false / external_send_performed=false`。

驗證：main CI `31793729770` 已 completed / success，`pytest + gui-unit/typecheck + gui-e2e` 全部 success。Focused Win11 `31793729801` 仍 queued，屬 self-hosted runner routing/availability 狀態，不是測試失敗。

## E7.7 — ComfyX Result → Canonical Artifact/Evidence Sync

狀態：`IMPLEMENTED — MAIN CI / WIN11 VERIFICATION IN PROGRESS；REAL COMFYX URI GAP IDENTIFIED`

本批新增/修改：

```text
coworker/personas/media_evidence.py
tests/test_e7_media_evidence.py
coworker/personas/__init__.py
.github/workflows/e7-media-company-personas-win11.yml
```

### 1. Canonical Artifact Registry sync 已建立

新增：

```text
sync_comfyx_media_evidence(writer, PersonaJobSubmission, ComfyX result)
```

它只接受 E7.6 的 authoritative specialist result：

```text
authority = ComfyX
tool_id = comfyx.minimax_h3.generate
request_id = non-empty
prompt_id = non-empty
artifacts = non-empty array
```

然後先重新讀取 AI-Engineering-OS canonical Job，核對：

```text
job.id == submission.job_id
job.project_id == submission.project_id
persona lineage
persona_session_id lineage
task_package_path lineage
```

任何 identity 衝突都在 Artifact Registry mutation 前 fail closed。

### 2. 真實本地 artifact 驗證後才登記

E7.7 不相信副檔名。若 artifact 是 MP4：

```text
explicit durable local uri/path
→ file exists
→ existing inspect_mp4() ISO-BMFF validation
→ SHA-256 streaming checksum
→ EngineeringOSClient.register_artifact(...)
```

Canonical registration 固定綁定：

```text
project_id = PersonaJobSubmission.project_id
job_id = PersonaJobSubmission.job_id
kind = animation_video (MP4)
media_type = video/mp4
checksum = actual local SHA-256
source_run_id = ComfyX prompt_id
```

因此 `prompt_id` 已能成為 specialist execution → canonical Artifact 的 durable lineage，而不是只停留在 OpenWorker 回傳 JSON。

同一 local path + checksum 在單次 sync 中會去重；AI-Engineering-OS 回傳的 artifact 再透過既有 `os_artifact_ref()` 轉為 `EvidenceRef`。沒有新增 Artifact Registry。

### 3. Result envelope

成功 sync 後回傳：

```text
openworker.persona-media-evidence-sync/v1
authority = AI-Engineering-OS
media_authority = ComfyX
submission
prompt_id
request_id
artifacts = canonical EvidenceRef[]
publish_performed = false
external_send_performed = false
```

所以 E7.7 仍然只是 evidence registration，不會 publish、send，也不建立第二個 Job。

### 4. 找到一個真正的跨 repo 缺口：ComfyX artifact 尚未提供 durable local URI

檢查 ComfyX `internal/comfyui/artifact/artifact.go` 後確認，現在 H3 artifact contract 是：

```text
node_id
kind
filename
subfolder
type
url = /view?filename=...&subfolder=...&type=...
```

它沒有 local `uri/path`，也沒有 checksum。`/view?...` 是 ComfyUI runtime view URL，不等於 AI-Engineering-OS 可持久驗證的 local Artifact URI。

因此 E7.7 **刻意不猜** `ComfyUI/output/...`、不從 Desktop 安裝路徑反推、不把 `/view` 偽裝成本地檔案。現有真實 E7.6 H3 result 進 E7.7 時會 fail closed，直到 ComfyX authoritative result 補出 durable artifact location。

這個 gap 很重要：如果在 OpenWorker 端猜 output path，兩台電腦、Desktop 安裝位置、custom output directory 或 remote runtime 都會讓 lineage/checksum 失真。

### 5. Regression coverage

`tests/test_e7_media_evidence.py` 已鎖定：

- 真實 local MP4 經 ISO-BMFF 驗證與 SHA-256 後才 register。
- register 必須綁既有 project_id/job_id。
- `source_run_id` 必須等於 ComfyX prompt_id。
- identical local path + checksum 去重。
- 只有 filename/subfolder `/view` 的 current ComfyX artifact 必須 fail closed，不猜路徑。
- remote URL 不會被下載或當成本地 evidence。
- truncated/non-MP4 在 registry mutation 前拒絕。
- canonical Job session lineage mismatch 在 registry mutation 前拒絕。
- 非 media submission 不可 sync media evidence。
- sync result 永遠不宣稱 publish/send。

Focused Win11 workflow 已納入 `media_evidence.py`、`test_e7_media_evidence.py` 與 smoke import。

## CI / Win11 驗證狀態

```text
E7.1～E7.3 main CI: 31790204795 → ALL SUCCESS
E7.4 main CI:       31790725031 → ALL SUCCESS
E7.6 main CI:       31793729770 → ALL SUCCESS
E7.6 focused Win11: 31793729801 → QUEUED (runner not assigned)
E7.7 main CI:       triggered by current commits; verification pending
E7.7 focused Win11: triggered by current commits; verification pending
```

Queued self-hosted Windows job 不視為代碼失敗；只在 runner 真正接單後依 conclusion 判定。

## 下一批 E7.8 — ComfyX Durable Artifact Location Contract

目前阻止「真實 H3 → canonical Artifact Registry」閉環的最小缺口已縮到 ComfyX artifact contract。

下一批應直接在 ComfyX domain authority 補：

```text
comfyx.minimax_h3.generate
→ artifact extraction
→ resolve output through authoritative ComfyUI runtime/output contract
→ durable local uri/path when runtime is local
→ optional size/checksum metadata
→ preserve existing filename/subfolder/type/url
```

然後 OpenWorker E7.7 直接消費該 authoritative URI：

```text
ComfyX durable artifact URI
→ E7.7 local format/checksum verification
→ AI-Engineering-OS register_artifact
→ E7.5 read_canonical_result
→ E7.4 assess_delivery_readiness
```

原則仍是：路徑解析屬於 ComfyX/runtime domain，不搬到 Persona；remote runtime 若沒有可驗證 durable URI，就保持 fail closed，不偽造本地 evidence。
