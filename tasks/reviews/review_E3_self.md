# E3 Self Review — Engineering Tool Facade + Persona Wiring

日期：2026-08-08

## 結論

狀態：`IMPLEMENTED — WAITING FOR FULL VERIFICATION`

E3 已完成 Production Code、永久 regression tests、Persona wiring、Approval metadata 與中文規格；尚未在完整 OpenWorker checkout + dependencies 環境執行全量 pytest / compileall，因此不得標記 VERIFIED。

## Review 範圍

- `coworker/engineering/tools.py`
- `coworker/catalog.py`
- `coworker/personas/builtin/engineering.md`
- `coworker/engineering/__init__.py`
- `tests/test_engineering_tools.py`
- `tests/test_engineering_persona_wiring.py`
- `docs/engineering/engineering-tool-facade.zh-TW.md`
- `tasks/implementation-roadmap.md`

## 架構檢查

- PASS：沿用 Persona manifest → Catalog → Agent.tool_factory → ToolRegistry。
- PASS：未修改 `engine.py` 加 engineering 特例。
- PASS：Project / Job lifecycle 仍由 AI-Engineering-OS 權威實作。
- PASS：Tool Facade 不直接寫 SQLite、不產生 ID、不複製工程公式。
- PASS：read tools 不要求 approval。
- PASS：`engineering_create_job` 標記 `requires_approval=True`。
- PASS：沿用既有 `RiskClass.EXTERNAL`，沒有新增 fork-only 風險類型。

## 自我複審發現與修正

### E3-R1 — RiskClass 名稱錯誤

初版 Catalog 曾使用不存在的 `RiskClass.WRITE_REMOTE`。

根因：把概念上的 remote write 誤當作 OpenWorker 已存在 enum。

修正：改用上游既有 `RiskClass.EXTERNAL`；Tool metadata 的 `requires_approval=True` 與 `risk.classify()` 行為保持一致。

狀態：CLOSED。

## 永久測試覆蓋

- stable tool names
- readiness summary
- read tools approval=false
- create job approval=true
- Project / Job delegation
- metadata JSON object validation
- unavailable control plane stops module discovery
- Catalog `engineering_os` capability
- Engineering persona manifest wiring
- external risk summary

## 尚待完整驗證

```text
python -m compileall coworker tests
pytest -q tests/test_engineering_adapters.py \
          tests/test_engineering_os_bridge.py \
          tests/test_engineering_os_transport.py \
          tests/test_engineering_tools.py \
          tests/test_engineering_persona_wiring.py
git diff --check engineering-e2-os-bridge...engineering-e3-tool-facade
```

目前 ChatGPT Python 執行環境未安裝 OpenWorker 的 `aisuite` dependency，因此沒有以不完整環境假造 pytest 成功證據。
