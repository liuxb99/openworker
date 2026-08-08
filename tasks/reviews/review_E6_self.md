# E6 自我 Code Review — RC Column Golden Job

日期：2026-08-08

## 結論

E6 v1 已達到「第一條真實 production call path 的 Golden Job fixture」邊界，但尚未達到完整工程 lifecycle E2E。狀態維持 `IMPLEMENTED — WAITING FOR FULL VERIFICATION`。

## 核對來源

1. AI-CivilDesign-Forge Tool Protocol：`forge.rc-column`、version `1.0.0`、nested `arguments.input`、`status=succeeded/failed`、`data.design_ok`、Artifact contract。
2. RC Column input schema：必要幾何、材料與內力欄位。
3. AI-Engineering-OS bridge：目前公開 readiness / project / job create/read；沒有在 OpenWorker bridge 中發現 transition / artifact registration / review / approval / delivery methods。
4. E5 Digital Thread：外部權威 identity reference graph。

## 已修正/避免的問題

### 1. 不把 `design_ok=false` 當 protocol failure

Tool Protocol 明定工程檢核結果與通訊狀態分離，因此 Golden Job 只要求 `status=succeeded`；工程結果原樣保留。

### 2. 不偽造後半段 E2E

Roadmap 舊文字期待 Design → EngSketch → BIM → Review → Approval → Delivery，但現有穩定契約不足。E6 v1 明確縮到可由來源支持的 Job → RC Design → Artifact Evidence。

### 3. Side-effect 前先 fail-closed

輸入、project identity、OS readiness、Design Forge readiness 均在 create_job 前檢查，避免已知不可執行時先留下 Job。

### 4. Artifact 必須有完整性證據

直接使用 E5 `design_forge_artifact_ref()`，缺 path/SHA256/media type 會拒絕進 Digital Thread。

## 已知限制

- Design Forge 在 Job 建立後失敗時，目前沒有 OS cancel/archive compensation API 可由 bridge 呼叫；因此會留下 draft Job。這是下一輪 lifecycle bridge 應解決的 P0，而不是在 OpenWorker 私自改資料。
- 尚未執行完整 checkout pytest / compileall。
- 尚未做真實 AI-Engineering-OS + civilforge-tool runtime E2E。

## Reviewer 評分

- 架構邊界：24/25
- 契約忠實度：24/25
- Fail-closed / 安全性：23/25
- 測試與驗證：19/25
- 總分：90/100

扣分主要來自環境尚未做 full runtime verification，以及 Job 建立後 specialist failure 尚無 authoritative compensation endpoint。
