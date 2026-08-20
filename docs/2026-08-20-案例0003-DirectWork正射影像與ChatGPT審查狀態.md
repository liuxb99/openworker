# 案例 0003 玉井橋 — DirectWork 正射影像與 ChatGPT 審查狀態

- 日期：2026-08-20（Asia/Taipei）
- Case：`0003` / 玉井橋 / YUJING BRIDGE
- 固定機：`DESKTOP-UL7V2VV`
- 固定 workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- 新版總控 authority：`liuxb99/DirectWork`
- 方法 / Context 查詢層：`liuxb99/go-tool-runtime`
- 正射 owning repo：`liuxb99/Terrain_To_DXF`

## 1. 本輪執行原則

案例 3 後續固定採：

```text
新版密語 -> GitHub 僅傳輸 -> DirectWork durable work -> owning repo REAL executor -> artifact/evidence -> Drive -> ChatGPT review
```

GitHub Action 成功不代表 business 完成；DirectWork durable evidence 才是 execution authority。go-tool 只提供工具、方法、能力與 Context 查詢，不負責 business dispatch。

## 2. 本輪確認的缺口

### 缺口 A：DirectWork master 沒有 Case 0003 專用密語入口

DirectWork 目前已有 Case 0005 / 0006 密語 workflow，但 master tree 中沒有 Case 0003 專用密語 workflow。這導致案例 3 即使 orthophoto producer 已存在，也無法按新版主線直接由密語建立可追蹤 durable work。

### 缺口 B：DirectWork `docs/cases/` 沒有 Case 0003 案例 authority 文檔

目前 `docs/cases/` 原有 Case 0006，缺少 Case 0003，造成新版證據仍散落在舊 OpenWorker 文件與 owning repo operator workflow。

### 缺口 C：fresh REAL orthophoto 尚未取得 DirectWork durable receipt

目前不可宣告完成的項目：

- DirectWork `work_id`
- claimed/running/terminal event sequence
- slot / executor / pid
- exit code
- fresh orthophoto artifact path / size / SHA256
- producer commit / evidence receipt
- Drive exact revision identity
- ChatGPT 實圖 review receipt

## 3. 已補修內容

DirectWork 修補分支：

```text
case0003-directwork-orthophoto-20260820
```

已新增：

```text
.github/workflows/secret-case0003-orthophoto-ul7.yml
secret-requests/case0003-orthophoto-ul7.json
docs/cases/CASE0003-YUJING-BRIDGE.zh-TW.md
```

新版密語：

```text
CASE0003.ORTHOPHOTO.CONTINUE
```

密語 workflow 固定執行機：

```text
runs-on: [self-hosted, Windows, X64, UL7]
COMPUTERNAME == DESKTOP-UL7V2VV
```

其 GitHub job 只做 command transport；真正正射 business command 由：

```text
POST http://127.0.0.1:8787/v1/work
```

建立 DirectWork durable work 後執行。

## 4. go-tool 使用方式

密語 ingress 會先記錄：

```text
GET http://127.0.0.1:8848/health
GET http://127.0.0.1:8848/tools
```

結果寫入 secret receipt 的 `go_tool` 欄位，用來證明當下查詢層狀態。go-tool 不執行 orthophoto producer，避免再次混淆 authority。

## 5. REAL orthophoto producer

Owning repo：

```text
liuxb99/Terrain_To_DXF
```

既有 current producer：

```text
cmd/terrain-orthophoto-acquire
capability: terrain.orthophoto.acquire
provider: nlsc
layer: PHOTO2
zoom: 19
radius-tiles: 1
```

預期成果：

```text
D:\AI-Work\jobs\0003-YUJING-BRIDGE\orthophoto\nlsc-photo2\orthophoto-photo2-z19.jpg
D:\AI-Work\jobs\0003-YUJING-BRIDGE\orthophoto\nlsc-photo2\orthophoto-photo2-evidence.json
```

DirectWork command 必須：

1. 驗證 `geo\geolocation.json` 存在且 `ok=true`。
2. 拉取 current `Terrain_To_DXF/main`。
3. `go test ./...`。
4. build `terrain-orthophoto-acquire`。
5. 執行 NLSC PHOTO2 bounded acquire。
6. 驗 JPEG 非空。
7. 驗 evidence `ok=true`。
8. 驗 provider/layer。
9. 驗 JPEG SHA256 與 evidence `output_sha256` 完全一致。
10. 寫 DirectWork artifact receipt。

## 6. Durable PASS 判定

只有下列證據同時存在才可標示正射段 PASS：

```text
request_id
work_id
DirectWork status = succeeded
exit_code = 0
claimed/running/succeeded events
slot/executor/pid evidence
artifact path
artifact size > 0
artifact SHA256
producer_commit
provider = nlsc
layer = PHOTO2
bounded tile_count
evidence path
secret receipt path
```

GitHub workflow success 不可代替以上任何一項。

## 7. ChatGPT 審查 gate

正射 durable PASS 後才允許進：

```text
Drive verified publish
-> exact revision folder/file ID
-> ChatGPT 讀取該 exact revision 的實際影像
-> PASS / TUNE / FAIL
-> review receipt 回寫案例紀錄 / WorkLedger
```

只看檔名、metadata、SHA 或 workflow log，不算 ChatGPT 實圖審查。

## 8. 本輪目前 checkpoint

已完成：

- 找回 Case 0003 固定機與 workspace authority。
- 核對 Terrain_To_DXF current orthophoto producer。
- 核對 DirectWork / go-tool 權責邊界。
- 發現並補上 Case 0003 DirectWork 密語 ingress 程式碼。
- 補上 DirectWork Case 0003 案例文檔。
- 補上本 OpenWorker 狀態文檔，作歷史 authority 與新版 DirectWork 之間的 migration record。

尚未完成：

- 修補線尚未併入 DirectWork `master`，因此 `CASE0003.ORTHOPHOTO.CONTINUE` 尚未在 UL7 實機觸發。
- 尚未取得新的 DirectWork `work_id` / events / exit code / artifact receipt。
- 尚未取得 fresh REAL orthophoto durable PASS。
- 尚未 Drive verified publish。
- 尚未 ChatGPT 實圖審查。

## 9. 下一步

下一個操作不得退回舊 `operator-orthophoto-acquire.yml` 當 business authority。正確下一步是：

```text
DirectWork Case0003 修補線進 master
-> 更新 secret request request_id
-> 觸發 CASE0003.ORTHOPHOTO.CONTINUE
-> 讀 secret-results/case0003/<request_id>.json
-> 依 durable evidence 判定 PASS 或找 root cause
-> 若失敗，修 owning repo / ingress 最小缺口後重跑
-> PASS 後接 Drive + ChatGPT review
```

本文件之後每次執行都要追加：時間、request_id、work_id、狀態事件、slot/executor、exit code、artifact/SHA256、修補 commit、Drive receipt、ChatGPT review decision；不得只寫「成功/失敗」。
