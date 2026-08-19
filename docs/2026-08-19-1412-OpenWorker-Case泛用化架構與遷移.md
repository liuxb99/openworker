# OpenWorker Case 泛用化架構與遷移

更新時間：2026-08-19 14:12 +08:00

## 問題

OpenWorker Go control plane 雖已支援 Case 0004 / 0005，但先前仍存在兩種硬編碼：

1. `supportedCaseID()` 將 0004 / 0005 當成核心白名單。
2. `controlcli.caseConfig()` 直接 switch Case ID，寫死 assigned host / workspace / manifest / spec。

這會導致每增加 Case 0006、0007……都必須修改 Go 核心，與「單一泛用 Go 主控」目標衝突。

## 已完成

### 1. Bootstrap 改為 manifest/spec authority

Commit：`cfb82ca27a3393a52721eac846e0fcedf7d13106`

Case Engine 不再以 0004 / 0005 白名單判斷合法性，只做：

- case_id 字元/path safety 驗證；
- worklist `case_id` 必須與 request 一致；
- worklist `assigned_host` 必須與執行機器一致；
- worklist `workspace_root` 必須一致；
- revision > 0；
- dependency graph 合法；
- spec `case_id` 必須一致。

真正 Case authority 是 manifest/spec，不是 Go switch。

### 2. CLI 改為 manifest-driven discovery

Commit：`30041542041d197b262eebb7233f7ce3d785ca2a`

`openworker case status/bootstrap/continue <CASE_ID>` 現在動態讀：

- `case-worklists/<CASE_ID>.json`
- `case-specs/<CASE_ID>.json`

並由 worklist 取得：

- `assigned_host`
- `workspace_root`
- `revision`

CLI 不再寫死 0004 / 0005 的 machine/workspace。

因此新增 Case 時，只要新增合法 worklist/spec，CLI 與 bootstrap 即可識別。

## 下一層泛用化

`mapStepInputs()` 目前仍有 Case step-specific mapping。這層不應改成任意 JSON 透傳，否則會失去 fail-closed、安全路徑檢查與 capability contract。

正確架構為 Action Mapper Registry：

`Case manifest step`
→ `allowed_actions[0]`
→ `Action Mapper Registry`
→ bounded / validated inputs
→ durable local-work queue

核心只認 action/capability，不認 Case ID。

例如：

- `comfyx-studio.director.preproduction` mapper
- `comfyx-studio.storyboard.plan` mapper
- `presentation.openmaic` mapper
- `openworker.case.publish-artifacts` mapper
- `openworker.review.await-drive` mapper
- `cad.build_story_index` mapper

如果 Case 0006 復用既有 capability，只新增 worklist/spec，不需改 Go Case Engine。
只有全新 capability/input contract 才需要新增 mapper。

## 不採用方案

不把 worklist 內 arbitrary `inputs` 直接透傳給 executor；避免 Case JSON 變成任意 command ingress。

不依 Case ID switch 決定機器、workspace、controller。

不再新增 `case0006_*`、`case0007_*` Python controller。

## 最終目標

`openworker.exe`
→ generic Case Registry
→ generic dependency/reconciliation engine
→ Action Mapper Registry
→ generic fanout/join coordinator
→ `:8848` durable queue
→ leaf capability

Case 是資料；Go Engine 是泛用狀態機。