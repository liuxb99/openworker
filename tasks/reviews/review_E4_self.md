# E4 Self Review — Direct Specialist Adapters

日期：2026-08-08

## 結論

狀態：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

E4 第一批四個 Direct Specialist Adapters 已完成，架構邊界符合 OpenWorker 薄整合原則，未修改 `engine.py`，未複製專業算法。

## 審查依據

- AI-CivilDesign-Forge `docs/TOOL-PROTOCOL.md`：`tool-protocol/1.0.0`、capabilities / execute envelope。
- AI-CivilDesign-Forge `cmd/civilforge-tool/main.go`：實際 CLI 為 `capabilities` 與 `execute <request.json>`。
- AI-EngSketch README：DraftForge CLI、版本化 workspace、validate/themes/versions。
- AI-BIM-Forge README：canonical `aibim.api` 函式名稱。
- KnowGraphGo `cmd/knowgraph/root.go`：`--dsn` / `--json` 為 command 前的 top-level flags。

## Self-review 發現與修正

### P0-1 KnowGraphGo global flag 位置錯誤 — 已修正

初版依 README 範例組成 `knowgraph check --dsn ...` / command 後置 global flags。直接讀 `root.go` 後確認 Go `flag.Parse()` 在 dispatch 前執行，正式 usage 為：

```text
knowgraph [--dsn <path>] [--json] <command> ...
```

已修為：

```text
knowgraph --dsn <dsn> check
knowgraph --dsn <dsn> --json node list --ns <namespace>
```

並更新永久測試固定 argv contract。

### P0-2 BIM Forge 參數 signature 被過度假設 — 已修正

README 只支持 canonical 函式名稱，未在所讀來源內支持「全部 kwargs」的具體 signature。初版 Adapter 曾把 payload 直接當 kwargs。

已改為透明 `args: []` + `kwargs: {}` forwarding：

```text
func(*args, **kwargs)
```

OpenWorker 不再自行發明 BIM API signature。

## 安全檢查

- subprocess 使用 argv list。
- `shell=False`。
- operation allowlist。
- 無 generic command escape hatch。
- Design Forge request 使用 tempfile JSON。
- KnowGraphGo 無 DSN fail-closed。
- BIM API lazy import；未安裝時 health unavailable。
- Direct Adapter 未自動暴露成 Agent mutating tools。

## 驗證限制

永久測試已提交：`tests/test_engineering_specialists.py`。

目前 ChatGPT 執行環境仍缺完整 OpenWorker runtime dependencies（前段已確認 `aisuite` 缺失），因此沒有宣稱完整 pytest / compileall 已通過。

完成閘門仍缺：

```text
pytest
python -m compileall coworker
 git diff --check
```

須在完整 checkout + dependencies 環境執行後才能標記 `VERIFIED`。
