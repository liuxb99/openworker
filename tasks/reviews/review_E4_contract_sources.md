# E4 Contract Sources

本 Segment 的 Direct Specialist Adapter 僅依下列已核對來源建立，不自行補齊未公開契約：

- AI-CivilDesign-Forge README + `docs/TOOL-PROTOCOL.md` + `cmd/civilforge-tool/main.go`
- AI-EngSketch README + `cmd/draftforge-cli/`
- AI-BIM-Forge README canonical Public API
- KnowGraphGo README + `cmd/knowgraph/root.go`

重要決策：

- Design Forge 直接使用 `tool-protocol/1.0.0` machine-readable CLI。
- EngSketch 只開安全唯讀/驗證型 CLI operation allowlist。
- BIM Forge 不猜函式 signature，使用透明 `args` / `kwargs` forwarding。
- KnowGraphGo 的 `--dsn` / `--json` 依實際 root parser 放在 command 之前。
