# Google Drive → 固定機器 Ingress 缺口與 REAL 驗證

日期：2026-08-18

狀態：**IMPLEMENTED — DRIVE INGRESS CODE GREEN / ODA CREDENTIAL PROVISIONING BLOCKED**

## 目的

為固定機器工作建立一個通用、fail-closed 的外部 source transport primitive：

```text
Google Drive raw file
→ fixed machine authority
→ authenticated Drive API alt=media
→ expected size + SHA-256
→ temp download
→ atomic local publish
→ durable ingress receipt
```

本能力不限定工程規範；案例只用來做 REAL 驗證。Transport layer 不解包、不改寫來源內容。

## 本批新增能力

### 1. `coworker/drive_ingress.py`

新增：

- `GoogleDriveRawDownloadClient`
- `DriveIngressReceipt`
- `ingress_drive_file_atomic`
- `write_ingress_receipt`

安全規則：

- `expected_sha256` 必須是 64 位 hex。
- `expected_size_bytes` 必須為正值。
- download 寫入 unique temp file。
- download byte count、temp size、temp SHA 全部必須一致。
- publish 使用同 volume atomic/hard-link semantics；destination 已存在時不覆寫。
- destination 已存在且 SHA/size 相同：idempotent PASS。
- destination 已存在但 identity 不同：fail-closed。
- final file 再驗 SHA/size。
- receipt 不保存 OAuth token。

### 2. `scripts/download_drive_file_atomic.py`

通用 CLI contract：

```text
--file-id
--destination
--expected-sha256
--expected-size-bytes
--receipt
--machine-id
--request-id
--run-id
```

### 3. Credential resolution

`GoogleDriveRawDownloadClient.from_environment()` 目前依序嘗試：

```text
OPENWORKER_GOOGLE_DRIVE_ACCESS_TOKEN
→ machine-local SecretStore google_drive / google_drive:* profile
→ existing Google ADC fallback
```

不把 credential value 寫進 log、request 或 receipt。

### 4. 固定 ODA workflow

`.github/workflows/external-source-drive-ingress-oda.yml`

固定 scheduler：

```yaml
runs-on: [self-hosted, Windows, X64, ODA]
```

再 fail-closed：

```text
COMPUTERNAME == DESKTOP-ODAQN0D
```

允許 destination / receipt 只位於：

`D:\AI-Work\knowledge\`

request：

`external-source-ingress-requests/oda.json`

## Targeted tests

`tests/test_drive_ingress.py` 已覆蓋：

1. initial publish PASS。
2. same identity replay idempotent PASS。
3. wrong downloaded bytes / SHA reject。
4. wrong size reject。
5. conflicting destination reject且原 bytes 不變。
6. machine-local `SecretStore` Google Drive profile fallback。

ODA REAL runs 中 targeted gate 已實際達到 **6 passed**。

## 本次 REAL source

KnowGraphGo engineering standards immutable source bundle：

```text
Google Drive file id = 1tDuIxI_bTd19o3qK48OBePzfiESSo5DN
filename             = knowgraph-standards-source-bundle-deterministic.zip
size                 = 1,719,409 bytes
sha256               = 9bd159e9dc625efd35fd48f13da724d35dc83458557661255d9063406287a702
target               = D:\AI-Work\knowledge\standards\knowgraph-standards-source-bundle-deterministic.zip
```

Drive file 本身已由 connected Google Drive 實際建立；問題不是 file identity 或 upload。

## REAL run 1 — Actions secret 缺口

Run：`32069844110`

固定 ODA machine authority：PASS。

Targeted tests：`5 passed`。

REAL download step：FAIL。

直接原因：

```text
OPENWORKER_GOOGLE_DRIVE_ACCESS_TOKEN unavailable
```

結論：workflow 裡引用 secret 不等於 repository 已配置該 secret。

## REAL run 2 — NetworkService credential scope

Run：`32070110999`

固定 ODA authority：PASS。

Targeted tests：`6 passed`。

credential diagnostic：

```text
env_present=false
local_profiles=0
local_unexpired=0
```

Google ADC：不存在。

REAL download：FAIL。

結論：GitHub self-hosted runner 以 `NetworkService` identity 執行；它自己的 OpenWorker SecretStore 沒有 Google Drive profile。

## REAL run 3 — 使用者 SecretStore bounded probe

Run：`32070519847`

固定 ODA authority：PASS。

Targeted tests：`6 passed in 0.22s`。

user-scoped bounded metadata probe：

```json
{
  "inspected_secret_files": 0,
  "readable_active_drive_stores": 0,
  "ambiguous": false
}
```

因此不是「找到 profile 但 ACL 擋住」；標準 `%APPDATA%\coworker\secrets.json` 路線上沒有可供 runner 復用的 user Drive profile。

REAL download：因 env/local/ADC 三層均無 credential 而 FAIL。

## 修正後 fail-closed preflight

workflow 已新增 credential preflight。在 source download 前先解析 credential；若不可用，直接輸出：

`DRIVE_INGRESS_CREDENTIAL_UNAVAILABLE`

並停止，不再執行無意義的 media GET，也不把 Google ADC traceback 當成 source corruption。

## 對「本機服務」的實體核對

目前 `openworker/main` 可實體取得的 local-authority 主線是：

- `bootstrap-o87-local-authority.yml`：把權威版本 snapshot 到 `%ProgramData%\go-tool-runtime\work-agent\authorities`。
- `engineering-local-source-ingress-win11.yml`：仍由 GitHub self-hosted runner 執行 fixed-host ingress。

目前 main **沒有可直接取用的 `worker_service/` 常駐 daemon 實作**。因此不能假設已存在另一個以互動使用者 identity 執行、可直接復用 Google OAuth 的本機服務。

這個結論只描述目前 main 的可取用實作，不否定未來補 service executor 的方向。

## 現在真正的 owning gap

程式、request contract、fixed-machine routing、SHA/size/atomic publish、receipt、targeted tests 都已完成。

唯一未通過的 REAL gate 是：

**讓 assigned ODA execution identity 取得一個合法 Google Drive OAuth credential。**

可接受的 closure 方式只有下列任一條：

```text
A. 配置 repository/environment Actions secret OPENWORKER_GOOGLE_DRIVE_ACCESS_TOKEN
B. 在 ODA runner identity 的 OpenWorker SecretStore 配置 google_drive profile
C. 在 ODA runner identity 配置有效 Google ADC
D. 改用另一個已驗證、無需 Google OAuth 的 immutable binary transport
```

不接受：

- 再掃桌面 DriveFS。
- 把 opaque ChatGPT Library ID 當 Drive fileId。
- 在 repo / log / request 明文保存 OAuth token。
- 未拿到 canonical file SHA PASS 就宣稱 source 已交付。

## 下一個驗收條件

只有出現以下 terminal evidence 才把 Drive ingress 標為 `REAL PASS`：

```text
EXTERNAL_SOURCE_DRIVE_INGRESS_PASS
machine=DESKTOP-ODAQN0D
file_id=1tDuIxI_bTd19o3qK48OBePzfiESSo5DN
sha256=9bd159e9dc625efd35fd48f13da724d35dc83458557661255d9063406287a702
bytes=1719409
```

之後才進 KnowGraphGo：

```text
standardmd -bundle
→ 13/13 source verify
→ GraphData
→ SQLite
→ every-ID re-query
→ receipt 1.1 identity_bound=true
→ immutable revision
→ current.json
```
