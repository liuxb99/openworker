# OpenWorker × DeepSeek Harness 正式執行鏈缺口修復計畫

- 日期：2026-08-15
- 狀態：IMPLEMENTING
- 優先級：P0

## 1. 問題

OpenWorker 已有 EngineeringHarnessHost / EngineeringHarnessRuntime / ManagedDeepSeekHarnessRuntime / DeepSeek Harness ACP 正式能力，但案例 0002 現行 REAL V3 仍由 Python driver 直接呼叫 EngineeringOSMediaClient，沒有讓 DeepSeek Harness 成為主要 agent runtime。

因此目前雖然使用了 OpenWorker 的 JobBinding、go-tool bootstrap 與 engineering client，但不能證明「大模型 → OpenWorker → DeepSeek Harness → OS tools → Studio → ComfyX → REAL artifact」完整閉環。

## 2. 正式權威鏈

固定為：

使用者要求
→ OpenWorker EngineeringHarnessHost
→ go-tool-runtime information preflight/query
→ OpenWorker fixed host/workspace/job binding
→ DeepSeek Harness ACP session
→ Harness engineering tool gateway
→ OpenWorker permission + Mission Guard
→ AI-Engineering-OS Project/Job/tool execution
→ Comfyx-Studio story/Bible/shot/Director/ProductionQueue
→ ComfyX / ComfyUI / H3 REAL generation
→ evidence/QC/Final Assembly
→ OS Artifact Registry / Review / Delivery
→ OpenWorker Project Work Ledger

## 3. V3 的具體缺口

### GAP-HARNESS-0002-01 — Harness 被 Case driver 繞過

現行 `case0002_openworker_source_to_film.py` 自己完成 go-tool bootstrap、OS Job、source-to-film dispatch 與 terminal wait。它應降級為 deterministic regression/fallback，不再作為「OpenWorker agent REAL」的主要入口。

### GAP-HARNESS-0002-02 — 缺 Harness runtime evidence

REAL evidence 至少必須保存：

- runtime=engineering-harness
- ACP session_id
- Harness runtime_job_id
- Engineering OS project_id/job_id
- assigned_host/workspace
- go-tool session_id
- Harness tool call/evidence refs
- Studio queue_id
- ComfyX execution_id/prompt_id
- final artifact provenance

### GAP-HARNESS-0002-03 — Runtime 預設與 formal workflow 不一致

`RuntimeKind` 目前 Native 是產品預設；正式 Case 0002 必須明確走 EngineeringHarnessHost，而不能依賴隱式 default runtime。

### GAP-HARNESS-0002-04 — Harness 啟動環境沒有被 formal Action 驗證

Formal Action 必須 fail-closed 驗證 DeepSeek Harness root、Node、Cordis config/plugin、ACP initialize/session/new/session/prompt 與 engineering tool ingress。

### GAP-HARNESS-0002-05 — Project Knowledge 尚未記錄 Harness 事件

Project Work Ledger 必須記錄 Harness session/runtime job/tool call/failure/repair/terminal，否則 OpenWorker 回答「做到哪了」仍缺少真正 agent runtime 歷史。

## 4. 修復策略

### P0-A OpenWorker

1. 增加 Case/automation 可用的 non-interactive EngineeringHarnessHost 執行入口。
2. 保留 PermissionEngine；Action 模式只允許明確 allowlisted engineering capabilities 自動批准。
3. Harness runtime event 追加到 ProjectKnowledgeStore。
4. TURN_START/TURN_END/ERROR/INTERRUPTED/tool evidence 都寫 ledger。
5. Mission Guard 在 consequential tool call 前比對 project/job/host/workspace/stage。

### P0-B AI-Engineering-OS Case 0002

1. 新建 REAL V4 Harness workflow，不破壞 V3 regression。
2. 固定 `DESKTOP-ODAQN0D` + `D:\AI-Work\jobs\0002-ALADDIN`。
3. 啟動 go-tool、OS、Studio、ComfyX、ComfyUI 後，不再直接執行 source-to-film Python orchestration 作為 primary path。
4. 改執行 OpenWorker Engineering Harness CLI/runner，讓 DeepSeek Harness 自己透過 OS engineering tools 完成任務。
5. 保存 Harness + OS + Studio + ComfyX evidence。

### P0-C 驗證

必須證明：

1. go-tool preflight 在 OS execution 前。
2. Harness ACP session 真實建立。
3. Harness runtime job 與 OS Job 關聯。
4. Harness 真實取得 OS tool manifest。
5. source-to-film tool call 由 Harness 路徑發出，而不是 Case Python driver 偷跑。
6. H3 prompt/artifact provenance 對應 current prompt。
7. Project Knowledge 可回答 current stage、blocker、next action、latest runtime_job_id/prompt_id。

## 5. Python Case Driver 的新定位

保留 `case0002_openworker_source_to_film.py`，但定位改為：

- deterministic integration regression
- OS/Studio/ComfyX contract smoke
- Harness 故障時的診斷對照

它的成功不能再單獨代表「OpenWorker AI agent 案例完成」。

## 6. 完成標準

只有 REAL V4 evidence 同時存在以下鏈才可關閉缺口：

`go-tool session → OpenWorker binding → Harness ACP session → Harness runtime_job → OS job → Harness engineering tool call → Studio queue → ComfyX execution/prompt → current artifact → QC/final delivery → Project Work Ledger`

任何一段缺失都維持 IMPLEMENTING。