# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-16 Asia/Taipei

狀態：`EXECUTING / UL7 ROUTING / MANUAL-EVOLVING / GAP-FIX-CLOSURE / OS WEBSITE DELIVERY REQUIRED`

## 任務

固定由 UL7（Windows `DESKTOP-UL7V2VV`）執行 consequential work：

`臺南市玉井橋 → 真實位置解析 → 真實街景/地形參考 → Blender 3D 場景 → SceneX 匯入 → SceneX REAL 瀏覽 → OS Artifact Registry → Delivery Revision → delivery/website/index.html`

## 文檔即操作手冊

本案例每一步都必須詳實記錄，文檔不是事後摘要，而是後續大模型直接照著執行的正式操作手冊。

每一步至少記錄：

- canonical input；
- tool / capability / workflow；
- owning repo 與 SHA；
- run id / job id / runner / COMPUTERNAME；
- 正式輸入與輸出摘要；
- artifact path / size / mtime / SHA256；
- PASS / FAIL / BLOCKED 依據；
- 缺口與根因；
- 修復 repo / commit / tests；
- 修復後同一步 REAL rerun；
- 最終 accepted 操作方式。

不得只寫「完成」或「失敗」。

## 缺口修復規則

案例執行時若發現正式能力缺口：

1. 先保存原始失敗 evidence；
2. 確認真正 owning repo；
3. 將缺口寫入 STATUS / evidence；
4. 直接補真正 owning repo 的缺口；
5. tests / build / CI 驗證；
6. 使用最新 commit 回到原失敗案例 Step；
7. 固定由 UL7 REAL 重跑；
8. PASS 後把正確操作與修復經驗寫回 README，形成後續手冊。

不得用案例特例、舊 commit、人工替代或臨時 script 掩蓋正式能力缺口。

## 固定執行邊界

- 本案例只允許 UL7（`DESKTOP-UL7V2VV`）執行 consequential case steps。
- routing workflow 可由 `[self-hosted, Windows, X64]` runner 接單；非 UL7 主機必須 clean skip。
- 不 fallback 到其他電腦產生成果。
- 案例 workflow：`.github/workflows/case-0003-yujing-bridge-ul7.yml`。

## OS 最終交付規則

- SceneX 可瀏覽只是中間驗收 gate。
- accepted artifacts 必須進 OS Artifact Registry。
- 必須建立 Delivery Revision。
- 最終 physical delivery 必須有：`delivery/website/index.html`。
- 成果網站必須展示/索引玉井橋真實位置、街景/地形 provenance、Blender 場景、SceneX REAL captures、QC、artifact hashes、execution provenance。

## 已完成

- canonical 案例入口已建立於 `examples/0003-yujing-bridge/`。
- 已定義 REAL 完成標準與 OS 成果網站交付規則。
- 已修正 UL7 routing：UL7 正式 Windows 主機為 `DESKTOP-UL7V2VV`，不使用不存在的 `UL7` label。
- routing workflow head：`22379efa04b55020508d2a3aced418714af0bdc6`。
- run `31919992683` 的 8 個 route jobs 最終均 cancelled，未取得 runner identity。
- 後續最新 route run `31920050536` 已建立 8 個 `[self-hosted, Windows, X64]` jobs；最近一次查詢仍全部 queued。
- 已把「每一步詳實記錄 → 文檔演進成手冊 → 缺口即修 owning repo → 同一步 REAL 重跑」寫入 canonical README。

## 目前 gate

Step 1 — UL7 runner identity / readiness。

最新 run：`31920050536`

最近一次 jobs：

- `95098375481`
- `95098375482`
- `95098375483`
- `95098375512`
- `95098375525`
- `95098375540`
- `95098375542`
- `95098375581`

最近一次查詢全部為 `queued`，尚未取得 runner name / COMPUTERNAME，因此尚未進 go-tool / Blender readiness。

## 下一個執行點

1. 追 `31920050536` 是否有 runner 接單。
2. 非 `DESKTOP-UL7V2VV` clean skip；UL7 取得 runner identity。
3. 記錄 go-tool / Blender / SceneX / OS delivery readiness。
4. 查正式 capabilities / schema / readiness。
5. 以 `臺南市玉井橋` 做 geocoding。
6. 每推進一個 Step 就立即更新 STATUS / evidence / README 的 accepted 操作方式。
7. 任一步發現缺口，就依缺口修復閉環補真正 owning repo，然後由 UL7 回到該 Step REAL 重跑。

## 尚未完成

- UL7 runner identity / readiness。
- go-tool / Blender / SceneX / OS delivery readiness。
- 玉井橋 canonical geolocation。
- street-view physical images。
- terrain/AOI physical data。
- `.blend` / SceneX exchange artifacts。
- Blender QC。
- SceneX REAL browse evidence。
- OS Artifact Registry。
- Delivery Revision。
- `delivery/website/index.html`。
