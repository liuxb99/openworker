# 案例 0003 玉井橋 — DirectWork a2 REAL 失敗證據

- 日期：2026-08-20（Asia/Taipei）
- request_id：`case0003-orthophoto-20260820-a2`
- work_id：`dw-20260820T072026-2b13548d00bf965a`
- machine：`DESKTOP-UL7V2VV`
- workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`

## Durable evidence

```text
accepted  2026-08-20T07:20:26.1289004Z
aimed/claimed slot=4 machine=DESKTOP-UL7V2VV  2026-08-20T07:20:26.3720696Z
running slot=4 pid=21080  2026-08-20T07:20:26.5216167Z
failed exit status 1  2026-08-20T07:20:26.5739251Z
```

Terminal：`status=failed`、`exit_code=1`。

因此 Case 0003 目前已證明：DirectWork ingress、durable queue、claim、slot、executor REAL 可用；失敗發生在 business command 內部早期，不再把問題歸因於「runner 不接案」。

## 新缺口

### GAP-0003-DW-05

secret receipt 有 work metadata 與事件，但失敗時 `artifact_text` 為空，stdout/stderr 只有 UL7 本機路徑，導致 root cause 尚不能由 receipt 直接取得。已在 DirectWork master 補 diagnostic workflow 讀取該 work logs。

### GAP-0003-GOTOOL-01

a2 當下 go-tool：HTTP endpoint 可達，但 `/health` body 為 `status=down`，codebase/git disabled/unhealthy，`/projects` 為空。這代表 go-tool process 存活但 query capability 未正常啟用，需獨立修復；不可拿此狀態推翻 DirectWork durable PASS。

## 當前判定

```text
DirectWork ingress       PASS
queue/claim/slot         PASS
executor start           PASS
business command         FAIL exit=1
fresh orthophoto         NOT PROVEN
Drive publish            NOT STARTED
ChatGPT image review     NOT STARTED
go-tool query layer      DEGRADED/DOWN
```

## 下一步

1. 取回 a2 stdout/stderr。
2. 依第一個 fail-closed error 修 workspace/geo/local Terrain_To_DXF checkout 或 owning repo。
3. 修 go-tool disabled/down。
4. 用新 request_id 重跑，保留 a2 immutable history。
5. fresh orthophoto durable PASS 後才做 Drive + ChatGPT exact-image review。
