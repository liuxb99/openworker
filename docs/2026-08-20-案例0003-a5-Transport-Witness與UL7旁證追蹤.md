# 案例0003 — a5 Transport Witness 與 UL7 旁證追蹤

- 日期：2026-08-20（Asia/Taipei）
- Case：0003 / 玉井橋 / YUJING BRIDGE
- 固定機：DESKTOP-UL7V2VV
- runner label：UL7
- workspace：D:\AI-Work\jobs\0003-YUJING-BRIDGE
- 密語：CASE0003.ORTHOPHOTO.CONTINUE
- current request：case0003-orthophoto-20260820-a5

## 1. 已有 REAL authority

request a2 的 DirectWork durable evidence 已確認：

- work_id：dw-20260820T072026-2b13548d00bf965a
- accepted：PASS
- claimed：PASS，slot=4 / DESKTOP-UL7V2VV
- running：PASS，pid=21080
- terminal：failed
- exit_code：1

因此 a2 已證明 GitHub short transport → UL7 → DirectWork /v1/work → durable queue → claim → slot → executor 的鏈路歷史上真實成立。a2 不可描述為「DirectWork 沒接案」。

## 2. a3 / a4 transport 缺口

a3 已部署 self-diagnosing payload，失敗時應帶回 stage/error/workspace_exists/geo_exists/tool_root/producer_commit/stdout/stderr；但 fresh a3 receipt 未觀察到。

a4 以 request-only 方式再次觸發，fresh a4 receipt 仍未觀察到。

因此新增 GAP-0003-TRANSPORT-01：request 已落 master，但沒有 fresh evidence 證明 UL7 workflow runner 已開始執行。這個 gap 位於 transport/runner-start 層，與 a2 business exit=1 不同。

## 3. a5 修補

DirectWork 已新增獨立 transport witness：

.github/workflows/case0003-transport-witness-ul7.yml

正式落 master commit：

5dec37d5a5836c3409d60dd4b2b9d110bce1d6c4

同一 atomic commit 也把 request 更新為：

case0003-orthophoto-20260820-a5

witness 只在 UL7 runner 開始時寫：

transport-results/case0003/case0003-orthophoto-20260820-a5.json

其內容包含 request_id、runner_name、computer_name、github_run_id、head_sha、observed_at，並明確標註 business_execution=false。它不執行正射 business work，只證明 transport/runner-start。

截至本紀錄，a5 transport witness 與 DirectWork business receipt 均尚未觀察到，因此狀態只能寫：

A5 DEPLOYED / TRANSPORT WITNESS NOT YET OBSERVED / BUSINESS RECEIPT NOT YET OBSERVED

不能宣告 success，也不能宣告 failure。

## 4. UL7 旁證查詢

為避免要求 UL7 自己證明自己在線，go-tool-runtime 已新增 Case0003 專用 ODA 旁證流程：

.github/workflows/case0003-query-ul7-runner-inventory-oda.yml

由 DESKTOP-ODAQN0D / ODA runner 查：

http://127.0.0.1:8848/api/information/runners/current

並把 UL7 match 與完整 inventory 寫回：

evidence/case0003/ul7-runner-inventory-from-oda.json

workflow + trigger 已 fast-forward 進 go-tool-runtime main，trigger commit：

3548fde9cf4b75f839ef969e3d6ed1e4c52e6ca5

截至本紀錄，該旁證 receipt 尚未觀察到。

## 5. go-tool 8848 負面知識

127.0.0.1:8848 是新版 per-machine local-work queue-only profile；codebase/git/knowledge/actions disabled 是允許且預期的設定。不得再把 8848 /tools disabled 當作完整 go-tool query runtime 故障，也不得因此重裝 queue runtime。

此處真正使用的是 runner inventory information endpoint，而不是把 /tools 當 query health authority。

## 6. 最新 acceptance matrix

```text
a2 DirectWork ingress           PASS
a2 durable queue                PASS
a2 claim / slot                 PASS (slot 4)
a2 executor                     PASS (pid 21080)
a2 business                     FAIL (exit 1)
a3 self-diagnosing payload      DEPLOYED
a3 receipt                      NOT OBSERVED
a4 retrigger                    SENT
a4 receipt                      NOT OBSERVED
a5 transport witness            DEPLOYED
a5 transport receipt            NOT OBSERVED
a5 business receipt             NOT OBSERVED
ODA→UL7 runner inventory query  DEPLOYED
ODA inventory receipt           NOT OBSERVED
Fresh DirectWork work_id        PENDING
Fresh PHOTO2 JPEG               NOT PROVEN
Artifact size/SHA256            NOT PROVEN
NLSC PHOTO2 evidence            NOT PROVEN
Drive verified publish          NOT STARTED
ChatGPT exact-image visual QA   NOT STARTED
```

## 7. 下一步 gate

優先讀三個 fresh evidence：

1. DirectWork transport-results/case0003/case0003-orthophoto-20260820-a5.json
2. DirectWork secret-results/case0003/case0003-orthophoto-20260820-a5.json
3. go-tool-runtime evidence/case0003/ul7-runner-inventory-from-oda.json

判斷規則：

- ODA inventory 顯示 UL7 offline/absent → 先修 runner availability/label/service，不碰正射 producer。
- ODA inventory 顯示 UL7 online，但 a5 witness 不出現 → 修 workflow routing/trigger/runner assignment。
- a5 witness 出現但 business receipt 不出現 → transport PASS，修 secret workflow/DirectWork ingress。
- business receipt failed → 直接按 self-diagnosing stage/error/stdout/stderr 補最小缺口。
- business receipt succeeded → 驗收 work_id/events/slot/pid/exit=0/tool_root/producer_commit/JPEG path-size-SHA256/provider=nlsc/layer=PHOTO2/tile_count。

只有 fresh orthophoto durable PASS 後才可 Drive publish；只有 ChatGPT 讀到 exact JPEG 並實際看圖後才可記 visual QA PASS/TUNE/FAIL。
