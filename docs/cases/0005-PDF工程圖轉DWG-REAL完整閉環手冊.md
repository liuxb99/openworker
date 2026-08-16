# Case 0005：PDF 工程圖 → Native DWG REAL 完整閉環手冊

更新日期：2026-08-16
主責位置：`liuxb99/openworker`
狀態：`IMPLEMENTING / WAITING REAL ACTION VERIFICATION`

## 1. 案例目標

使用者提供一份真實工程 PDF 圖檔，只給 OpenWorker/go-tool-runtime：

```text
goal = PDF 工程圖轉 DWG
input = engineering_pdf[source]
```

系統必須自行透過 Tool Graph 找出 owning capabilities、authority gate、runner、輸入輸出與驗證方式，最後取得可重新開啟且通過 native fidelity 驗證的非空 DWG。

禁止把 PDF 當 raster image 直接包進 DWG 假裝完成；目標是 evidence-backed EngineeringDrawingIR → approved authority → Native DWG production。

## 2. 正式責任分工

```text
go-pdf-drawing-reconstructor
= PDF evidence / vector inspection / EngineeringDrawingIR candidate

AI-Engineering-OS
= Artifact Registry / Review / approval evidence / authority transition

DWG_todo
= Approved EngineeringDrawingIR → production model → Native DWG → reopen/native fidelity

go-tool-runtime
= capability registry / Tool Graph plan / Action dispatch

KnowGraphGo
= capability/evidence graph / explain / execution learning

OpenWorker
= case workspace / goal / plan execution / durable case state / delivery manual
```

## 3. Tool Graph 目標路線

```text
engineering_pdf[source]
→ pdf.drawing.reconstruct
→ engineering_drawing_ir[candidate]
→ OS Artifact Registry
→ OS Review decision
→ engineering.review.evidence.export
→ engineering_ir_approval_evidence[validated]
→ engineering.review.approve
→ engineering_drawing_ir[approved]
→ dwg.cad.execute
→ native_dwg[validated]
→ reopen/native fidelity PASS
→ execution evidence → KnowGraphGo
```

## 4. 已完成的 executable capabilities

### 4.1 `pdf.drawing.reconstruct`

Owner：`liuxb99/go-pdf-drawing-reconstructor`

輸入：`engineering_pdf[source]`

輸出：

- `engineering_drawing_ir[candidate]`
- `cad_exchange_dxf[candidate]`

### 4.2 `engineering.review.evidence.export`

Owner：`liuxb99/AI-Engineering-OS`

從 OS SQLite authoritative stores 讀取：

- Artifact Registry `artifacts`
- Review Store `artifact_reviews`

只允許 exact artifact revision 的最新 review 仍為 `approved` 時輸出：

`engineering-ir-approval-evidence/v1`

後續 rework/reject 會撤銷可輸出性；歷史 revision approval 不可沿用。

### 4.3 `engineering.review.approve`

Owner：`liuxb99/AI-Engineering-OS`

只有 SHA256 + artifact revision + review ID/reviewer/decision 全部綁定的 approval evidence 才能把 candidate IR materialize 成 approved IR。

### 4.4 `dwg.cad.execute`

Owner：`liuxb99/DWG_todo`

復用既有 production chain：

```text
dwg-ir-import
→ dwg-materialize
→ Rust dwg_semantic_writer
→ Native DWG
→ reopen raw extractor
→ native semantics
→ native fidelity signature
```

## 5. REAL 驗收

Case 0005 只有同時具備以下證據才可改成 `CLOSED / REAL VERIFIED`：

- 真實使用者 PDF 的 path / size / SHA256；
- fresh Tool Graph plan；
- PDF reconstruction run/job/runner；
- candidate EngineeringDrawingIR 非空 + SHA256；
- OS Artifact Registry ID/revision；
- OS Review ID/reviewer/decision；
- approval evidence SHA-bound；
- approved EngineeringDrawingIR 非空 + SHA256；
- DWG production run/job/runner；
- Native DWG 非空 + SHA256；
- independent reopen PASS；
- native fidelity PASS；
- all-skipped = false；
- execution evidence 已寫入 KnowGraphGo。

## 6. 目前 CI 狀態

第五批 DWG operator commit：

`cafef2df19e145ca4e60217bd3fc2e5afaafb2ba`

CI Run：`31941945232`。最新檢查時仍在 full CI，已完成 native binary build/verify，尚未 terminal。

第五批 OS authority operator commit：

`c20fe890cf758d8804764c7a60a47d83cfb3cde0`

Local Verification Run：`31942018040`。最新檢查時 `os-local-verification` 仍 pending。

第六批新增 OS approval exporter：

- `a3910c01` exporter core
- `0da72734` exact-revision/latest-review regressions
- `7b73b9a4` SQLite CLI
- `fa0a01ba` Action operator

第六批 go-tool registry：

- `b0c7d14d` register `engineering.review.evidence.export`

## 7. 下一個 REAL 接續點

1. 追最新 CI terminal；失敗即修 owning repo。
2. 建立 Case 0005 OpenWorker workspace/job。
3. 將工程 PDF 放入 workspace input 並記錄 SHA256。
4. fresh go-tool-runtime Tool Graph plan。
5. 執行 `pdf.drawing.reconstruct`。
6. candidate IR 註冊 OS Artifact Registry。
7. 取得正式 Review decision。
8. 執行 approval evidence export。
9. 執行 authority transition。
10. 執行 Native DWG production。
11. reopen/native fidelity 驗證。
12. execution evidence 回寫 KnowGraphGo。

在第 10～12 步取得真實證據以前，本手冊不得標 `CLOSED`。
