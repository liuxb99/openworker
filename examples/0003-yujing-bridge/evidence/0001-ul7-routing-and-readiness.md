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

## 嘗試 4 — 保留舊 run 後的新正式驗證

修復 G-0003-001 後產生 run：`31920174970`（run #9）。

觀察：

- 狀態為 `pending`；
- `jobs` 清單為空；
- 表示這個 run 尚未進到 job 建立/runner routing 階段；
- 前一個 run `31920136486` 仍有 8 個 jobs 全部 `queued`。

判定：仍未完成 Step 1。

## 發現缺口 G-0003-002 — 固定 concurrency group 讓新驗證卡在舊 queued run 後面

G-0003-001 把 `cancel-in-progress` 改為 `false` 後，雖然不再取消舊 run，但固定的：

`concurrency.group = case-0003-yujing-bridge-ul7`

會讓新 run `31920174970` 變成 `pending`，因為舊 run `31920136486` 仍佔著同一 group 且在等待 self-hosted runner。

這會造成另一種死鎖：歷史 queued run 不能完成，新修正後的 run 也不能建立 jobs，自然無法驗證修正。

### 正式修復

owning repo：`liuxb99/openworker`

修復：移除 Case 0003 workflow 的固定 `concurrency` block，讓每次正式驗證 run 都能獨立建立 jobs，不受歷史 queued run 阻塞。

修復 commit：`b0a059647ed0ebb8d314dcecbbaa397ef8126933`

### 修復後驗證

新正式 run：`31920291957`（run #10）。

此 run 已成功越過 `pending-with-no-jobs` 狀態並建立 8 個 `[self-hosted, Windows, X64]` jobs：

- `95099001501`
- `95099001512`
- `95099001542`
- `95099001553`
- `95099001573`
- `95099001578`
- `95099001581`
- `95099001620`

截至最近一次查詢，8 個 jobs 仍全部 `queued`，沒有 `runner_name`，因此 Step 1 readiness 仍未開始。

## 發現缺口 G-0003-003 — UL7 runner 可見性 / 註冊 / 在線狀態尚未成立

為排除 GitHub Actions 平台或 `[self-hosted, Windows, X64]` selector 本身故障，交叉檢查同一時間其他 owning repo 的成功 Windows jobs：

### go-tool-runtime 成功 runner 證據

- run `31920155725` / job `95098649210`：`DESKTOP-O87PJNR-R030`，machine `DESKTOP-O87PJNR`，成功完成 Win11 Local Verification。
- run `31920059493` / job `95098396799`：`DESKTOP-ODAQN0D-R002`，machine `DESKTOP-ODAQN0D`，成功完成 Win11 Local Verification。
- run `31919939848` / job `95098079885`：runner `DESKTOP-O87PJNR-R030`，labels 為 `[self-hosted, Windows, X64]`，success。
- run `31919459618` / job `95096822109`：runner `DESKTOP-ODAQN0D-R002`，labels 為 `[self-hosted, Windows, X64]`，success。

### AI-Engineering-OS 成功 runner 證據

- run `31919947413` / job `95098100854`：runner `DESKTOP-ODAQN0D-R003`，machine `DESKTOP-ODAQN0D`，成功完成 OpenWorker Win11 Baseline。

### Runner API 限制

嘗試直接呼叫 GitHub REST：

`GET /repos/liuxb99/go-tool-runtime/actions/runners?per_page=100`

回覆：`403 Resource not accessible by integration`。

因此目前 GitHub App 權限無法直接枚舉 self-hosted runner 清單，也無法從 REST endpoint 直接讀 UL7 的 online/busy 狀態。

### 判定

- GitHub Actions 平台正常；
- `[self-hosted, Windows, X64]` selector 正常；
- O87 / ODAQ runner 在同一時間窗有實際成功接單證據；
- 0003 run `31920291957` 仍完全沒有 runner 接單；
- 目前可取得的真實 job evidence 中尚未觀察到 `DESKTOP-UL7V2VV`。

因此 Step 1 當前 verdict：`BLOCKED`。

blocker：**UL7 self-hosted runner 對案例執行 repo 的可見性 / 註冊 / 在線狀態尚未被證明成立。**

這一點不能被誤寫成 `go-tool`、Blender、街景或 SceneX readiness 失敗，因為 UL7 尚未取得任何 job。

### 下一個修復 / 驗證動作

1. 優先找出 UL7 對應的實際 GitHub runner instance（預期 runner name 形如 `DESKTOP-UL7V2VV-Rxxx`，但不得猜具體 suffix）。
2. 驗證該 runner 是否有註冊到承載案例正式 execution 的 repo，且 labels 包含 `[self-hosted, Windows, X64]`。
3. 若 UL7 只註冊在其他 owning repo，應透過正式跨 repo execution/dispatch 能力讓案例由可見的 UL7 runner 執行，而不是改用 O87/ODAQ 代做。
4. UL7 runner 恢復可見後，重新執行 Case 0003 Step 1。
5. 只有拿到 `COMPUTERNAME=DESKTOP-UL7V2VV` 與實際 `RUNNER_NAME` 後，才進 `go-tool` / Blender readiness。

## 重跑驗收

下一個 gate：

1. run `31920291957` 或後續正式重跑的任一 `[self-hosted, Windows, X64]` job 被 runner 接單；
2. 必須留下 `COMPUTERNAME` / `RUNNER_NAME`；
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
- 不要用固定 concurrency group 去序列化可能長時間 queued 的 self-hosted case runs，否則新修正 run 會被歷史死 run 阻塞；
- runner 尚未接單時，不得把 queued/pending/cancelled 解讀成工具 readiness 失敗；
- 若其他同 selector runner 可成功接單，而指定主機始終不可見，應把問題收斂到該主機的 runner registration / online visibility，而不是繼續修改業務工具。
