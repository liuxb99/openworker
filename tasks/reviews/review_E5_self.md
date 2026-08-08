# E5 Self Review — Digital Thread / Artifact Provenance

日期：2026-08-08

## 範圍

本次只審查 E5：

- `coworker/engineering/digital_thread.py`
- `coworker/engineering/__init__.py`
- `tests/test_engineering_digital_thread.py`
- `docs/engineering/digital-thread.zh-TW.md`
- `tasks/implementation-roadmap.md`

不審查 E6 Golden Job，也不把 E6 功能混入本 Segment。

## 權威契約來源

1. AI-Engineering-OS `internal/job/job.go`
   - Job ID / Project ID / revision / status / working_dir / delivery_dir。
2. AI-Engineering-OS `internal/artifact/artifact.go`
   - Artifact ID / revision / URI / media_type / checksum / source_run_id。
3. AI-CivilDesign-Forge `docs/ARTIFACT-CONTRACT.md`
   - Artifact / CalculationRun / semantic_id / SHA256 / engine/formula versions。
4. AI-EngSketch `internal/version/manifest.go`
   - version / parent / checksum / SVG SHA256 / PNG SHA256。
5. AI-BIM-Forge `src/aibim/tool_protocol.py`
   - ArtifactRef ID / type / path / SHA256。

## Review 結果

### P0/P1 修正

初版 `design_forge_artifact_ref()` 將 Forge 的 `sha256`、`path`、`media_type` 視為 optional，但 Forge Artifact Contract 把它們列為必要欄位。已修正為 fail-closed。

初版 `engsketch_version_refs()` 允許主 manifest checksum 缺失。Version manifest 本身有 checksum 欄位，Digital Thread 若沒有版本完整性證據就不應把該 version 視為正式 reference，因此已修正為必要欄位。

### 架構邊界

PASS：

- 沒有建立第二套 Artifact Store。
- 沒有重新計算 SHA256。
- 沒有將 path 當 Artifact identity。
- 沒有從流程假設自動生成 provenance link。
- 相同 external identity 發生不同內容時 fail-closed。
- source systems 的 schema 保持權威，OpenWorker 只保存引用。
- 沒有修改 `engine.py`。

### Determinism

PASS by code review：

- refs 依 key 排序。
- links 依 source / relation / target 排序。
- serialization schema version 固定為 `openworker-digital-thread/1.0.0`。
- 重複加入完全相同 EvidenceRef 為 idempotent。

### 永久測試

已新增 `tests/test_engineering_digital_thread.py`，涵蓋：

- OS Job / Artifact mapping。
- Design Forge trace/version metadata。
- Design Forge integrity fail-closed。
- EngSketch version / SVG / PNG evidence。
- EngSketch checksum fail-closed。
- BIM ArtifactRef mapping。
- provenance traversal。
- deterministic serialization。
- identity conflict。
- unknown endpoint。
- idempotency。

## 尚未完成的驗證

目前 ChatGPT 執行環境未取得完整 OpenWorker checkout + dependencies，因此沒有聲稱：

- full `pytest`
- `python -m compileall`
- repository-level import integration
- `git diff --check`

E5 狀態維持：

```text
IMPLEMENTED — WAITING FOR FULL VERIFICATION
```

## 下一 Segment

E6 Golden Job 才開始把 E2/E3/E4/E5 組成真正 RC 柱端到端流程。E5 本身只負責可追溯契約，不應提前實作假的 orchestration。
