# Case 0003 玉井橋 — Drive Review Gate Local-First

日期：2026-08-18

## 結論

Case 0003 的最終接受邊界已更正為：

```text
OpenWorker local REAL execution
→ physical artifact gates
→ AI-Engineering-OS Artifact Registry
→ OS Review / Approval
→ OS Delivery Revision
→ OpenWorker fresh mechanical verification
→ immutable review bundle
→ Google Drive review handoff
→ ChatGPT connector-grounded visual / semantic review
→ PASS / TUNE / FAIL
→ only PASS may accept the WorkLedger revision
```

Google Drive 只作為 ChatGPT 審查交換面，不是 business execution transport；OpenWorker / go-tool / owning local tools 仍是 consequential execution authority。

## 本輪發現的舊邏輯缺口

舊 `scripts/case0003_final_acceptance.py` 仍帶有 GitHub-first 時期的假設：

1. provenance 會寫入歷史 GitHub run IDs；
2. OS delivery path / delivery ID 有舊 hard-code；
3. mechanical checks 全 PASS 後直接 `accept_revision()`；
4. 隨後直接 `deliver_revision()`；
5. 因此 Drive / ChatGPT 實體成果審查並不是 acceptance 的必要前置 gate。

這與 2026-08-18 local-first 閉環不相容。舊檔保留作歷史遷移參考，但不可作為新版 final acceptance authority。

## 新 authority

### `scripts/case0003_prepare_drive_review.py`

commit: `6d8bba35e888688359cc71d1b4085638fe148619`

行為：

- 固定檢查 `DESKTOP-UL7V2VV` JobBinding authority；
- DTM SQLite `quick_check`；
- Terrain `terrain-context/v1` + `usable_tiles > 0`；
- Consumer `consumer-orchestration/v1`；
- Blender scene/render/evidence + PNG physical decode；
- SceneX workspace/evidence + 1280x720 screenshot + geometry diagnostics；
- OS Delivery receipt + manifest + checksum manifest + website；
- 所有新 WorkLedger artifact provenance 使用 local-first capability/transport，不再把舊 GitHub run 當 fresh provenance；
- 建立 fresh review revision；
- 建立 `openworker-review-bundle/v1`；
- handoff 到 bounded Google Drive Desktop review sync root；
- revision 狀態改為 `blocked / WAITING_DRIVE_REVIEW`；
- 不呼叫 `accept_revision()`；
- 不呼叫 `deliver_revision()`。

### `scripts/case0003_local_drive_review_prepare.ps1`

commit: `9a780c79bd3a23f94b58c9481d8ae1bff7714e45`

行為：

- 由 OpenWorker durable local job 執行 review prepare；
- 固定 UL7；
- 要求 OS Delivery receipt 已存在且 `ok=true`；
- 要求明確 `OPENWORKER_REVIEW_DRIVE_ROOT`；
- 同 stage 已 `accepted / queued_local / starting / running` 時 suppress duplicate submission；
- `github_business_transport=false`。

## Drive 上既有 Case 0003 結構驗證

既有 rework revision `rev_0851c5ab49ff459d83ee1cb6268ea8d3` 的 review folder 仍可由 connected Google Drive 找到。其 bundle 使用：

- `review-request.json`
- `manifest.json`
- `manifest.sha256`
- `artifacts/blender-render.png`
- `artifacts/scenex-browse.png`
- `artifacts/scenex-evidence.json`
- `artifacts/delivery-index.html`
- `artifacts/mechanical-acceptance.json`

新版沿用 `ReviewCycle` 的正式 schema 與 bundle 語意，但 **不繼承該舊 revision 的 artifact acceptance**。新 bundle 必須來自本次 UL7 canonical workspace physical artifacts。

## Duplicate-race repair

本輪也發現 `case0003_local_continue.ps1` 在 physical artifact 尚未落盤、stage job 已 queued/running 時可能重複提交 timestamp work IDs。

修正：

- controller v5 commit `3cf0870db3b43a3e9dddc87873328de7e1bce03c`
- imagery stage-idempotent commit `5faba8f6771bc37c10d3d55f85c038cd0f56f749`

現在 controller 會讀 `/v1/jobs?limit=1000`，將 `accepted / queued_local / starting / running` 視為 active stage，記錄 `suppressed_duplicate_submissions`；imagery submit 自己也會逐個 Street View / Orthophoto stage 去重。

## Acceptance rule

Case 0003 目前仍不得因 code path 完成而標記最终 ACCEPTED。

唯一有效順序：

```text
UL7 REAL artifacts
→ OS registry / approval / delivery
→ fresh mechanical review prepare
→ Drive publication observed by ChatGPT connector
→ ChatGPT physical visual/semantic review receipt
→ apply connector review
→ PASS 才 accept revision
```

TUNE 必須產生受 allowlist 約束的 tuning revision；FAIL / TOOL_GAP 必須回 owning repo 修正再 REAL rerun。
