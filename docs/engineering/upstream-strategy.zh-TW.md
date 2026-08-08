# OpenWorker Fork 上游同步策略

## 一、目標

`liuxb99/openworker` 是 `andrewyng/openworker` 的 fork。工程化改造必須長期保留同步上游能力，不能因短期方便大量修改核心，最後變成無法升級的孤立版本。

## 二、核心原則

### 原則 1：新增優先，修改核心最後

優先新增：

- `coworker/engineering/`
- `coworker/personas/builtin/engineering.md`
- `docs/engineering/`
- `tests/test_engineering_*.py`

只有在 OpenWorker 現有擴充點確實不足時才修改共用核心。

### 原則 2：Persona / Tool / Adapter 優先

工程功能優先透過：

```text
Persona
→ Tool Factory
→ Engineering Adapter
→ Gateway / MCP / HTTP / CLI
```

而不是在 `engine.py`、session manager 或 connector core 中加入大量 `if engineering` 分支。

### 原則 3：上游檔案修改必須可解釋

若必須修改上游檔案，每一項修改都要回答：

- 為什麼不能用既有 extension point？
- 是否可以向 upstream 提通用 PR？
- 修改是否只是一個 hook，而不是工程業務邏輯？
- 未來 upstream 改版時是否容易重新套用？

## 三、建議分支

```text
main
  = 與 upstream 同步後、已驗證的穩定工程版

engineering-foundation
  = 工程整合基礎與目前 Draft PR

feature/engineering-*
  = 後續各 Adapter / Tool / Persona 功能

upstream-sync/YYYY-MM-DD
  = 上游同步與衝突處理分支
```

## 四、同步流程

建議定期執行：

```text
andrewyng/openworker main
        ↓ fetch / compare
建立 upstream-sync 分支
        ↓
先合併純上游變更
        ↓
處理與工程擴充的衝突
        ↓
跑 upstream tests
        ↓
跑 engineering tests
        ↓
確認 Engineering Persona / Adapter / Docs
        ↓
PR 回 main
```

## 五、禁止事項

- 不大規模 rename 上游 package。
- 不把工程 repo 程式碼直接 copy 進 `coworker/`。
- 不修改 OpenWorker 通用 Connector 使其只服務工程案例。
- 不在 core 裡寫固定本機 repo 路徑。
- 不在 core 裡維護工程公式或工程規則。
- 不刪除 upstream tests 來讓 fork 通過。

## 六、什麼功能適合回饋 upstream

若工程版開發過程發現以下需求具有通用性，可考慮做成乾淨的 upstream PR：

- 更穩定的 Persona extension hook。
- 通用 external-tool adapter interface。
- Capability readiness / health model。
- Tool-level approval metadata。
- 通用 artifact provenance UI。

工程專屬的 Design／BIM／Quantity／PCCES 契約則留在 fork。

## 七、完成判定

每次上游同步完成，至少驗證：

- OpenWorker 原本 Persona 正常。
- Engineering Coworker 正常載入。
- Engineering Adapter Registry 正常。
- upstream tests 未因工程修改失效。
- engineering tests 全部通過。
- `git diff` 中沒有不必要的大面積 upstream core 改動。

長期目標是讓工程版新增價值集中在 extension layer，而不是維護一份實質 forked core。