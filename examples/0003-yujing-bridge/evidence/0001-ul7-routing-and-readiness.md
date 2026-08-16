# 0003 / Step 1 — UL7 routing 與 readiness 詳實紀錄

更新日期：2026-08-16 Asia/Taipei

## 目的

本步驟只驗證案例 0003 是否能由固定執行主機 UL7（Windows `DESKTOP-UL7V2VV`）透過 GitHub self-hosted Action 正式接單，並在 UL7 上查驗既有 `go-tool` 與 `blender` readiness。

canonical input：

- `location_text = 臺南市玉井橋`
- `delivery_case = 0003`
- `assigned_host = DESKTOP-UL7V2VV`

本步驟尚未執行 geocoding、street-view、terrain、Blender 建模或 SceneX。

## 嘗試 1 — 錯把 UL7 簡稱當 runner label

workflow 最初使用：

`runs-on: [self-hosted, Windows, X64, UL7]`

正式 run：`31919878274`

觀察：

- job：`95097918048`
- job name：`UL7 case probe`
- 狀態長時間 `queued`
- 未取得 `runner_name`
- 未產生 readiness log

判定：FAIL。

根因：`UL7` 是使用者對該電腦的簡稱，不是已證明存在的 GitHub runner label。案例不應猜 runner label。

修正：workflow 改為一般 `[self-hosted, Windows, X64]` candidate routing，接單後以 Windows `COMPUTERNAME == DESKTOP-UL7V2VV` 判定唯一可執行主機；其他主機 clean skip。

修正 commit：`22379efa04b55020508d2a3aced418714af0bdc6`

## 嘗試 2 — 以 COMPUTERNAME 固定 UL7

正式 run：`31919992683`

建立 8 個 route slots：

- `95098221494`
- `95098221466`
- `95098221545`
- `95098221522`
- `95098221442`
- `95098221441`
- `95098221453`
- `95098221458`

所有 job 初始 selector：

`[self-hosted, Windows, X64]`

預期：任何 Windows self-hosted runner 可先取得候選 job；非 `DESKTOP-UL7V2VV` 只執行 routing 判斷並 clean skip；UL7 繼續 readiness。

結果：8 個 jobs 最終皆 `cancelled`，未取得 runner identity、未執行 routing log。

判定：FAIL，但不是 UL7 readiness FAIL，因為 job 根本尚未到 runner。

## 嘗試 3 — OS 成果網站文檔更新後的 run

正式 run：`31920050536`

8 個 jobs：

- `95098375481`
- `95098375482`
- `95098375483`
- `95098375512`
- `95098375525`
- `95098375540`
- `95098375542`
- `95098375581`

結果：8 個 jobs 最終再次全部 `cancelled`，仍未取得 runner identity。

## 發現缺口 G-0003-001 — 手冊更新會取消正在等待 runner 的正式案例 run

當時 workflow 同時具備：

- `push.paths` 包含 `examples/0003-yujing-bridge/**`
- `concurrency.group = case-0003-yujing-bridge-ul7`
- `cancel-in-progress: true`

因此每次依規則更新案例手冊、STATUS 或 evidence，本身就會再觸發同一案例 workflow；新的 run 會取消前一個仍在等 runner 的正式 run。

這與「每一步都要詳實記錄文檔」互相衝突：記錄證據的動作反而破壞被記錄的執行。

### 正式修復

owning repo：`liuxb99/openworker`

workflow：`.github/workflows/case-0003-yujing-bridge-ul7.yml`

修復內容：

1. 移除 `examples/0003-yujing-bridge/**` 的自動 push trigger；
2. 保留 `workflow_dispatch`；
3. workflow 自身修改仍可觸發一次正式驗證；
4. `cancel-in-progress` 改為 `false`；
5. 文檔後續可持續更新而不再自動取消等待 UL7 的正式 run。

修復 commit：`0956ca74f796e66eb974ca91f25ee0229f54ab3c`

## 重跑驗收

修復 workflow 的 commit 會觸發新的 Case 0003 run。下一個 gate：

1. 新 run 不得因後續文檔 commit 被取消；
2. 任一 `[self-hosted, Windows, X64]` runner 接單後，必須留下 `COMPUTERNAME` / `RUNNER_NAME`；
3. 非 UL7 必須只 clean skip；
4. `DESKTOP-UL7V2VV` 接單時，才執行 `go-tool` / `blender` readiness；
5. readiness PASS 後才進 Step 2 capability discovery。

## 可重用操作手冊結論

未來固定某台 Windows self-hosted 主機，但沒有專用 GitHub label 時：

- 不要把人類簡稱直接當 runner label；
- 先用 `[self-hosted, Windows, X64]` routing；
- 在第一個 step 讀 `COMPUTERNAME`；
- 只有 canonical hostname 命中的 candidate 才執行 consequential steps；
- 文檔/evidence 更新不得設計成會取消正在執行或等待的正式案例 run；
- runner 尚未接單時，不得把 queued/cancelled 解讀成工具 readiness 失敗。
