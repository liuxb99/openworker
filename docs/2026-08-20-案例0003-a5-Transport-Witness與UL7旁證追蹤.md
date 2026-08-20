# 案例0003 — a5 Transport Witness 與 UL7 旁證追蹤

- 日期：2026-08-20（Asia/Taipei）
- Case：0003 / 玉井橋 / YUJING BRIDGE
- 固定機：DESKTOP-UL7V2VV
- runner label：UL7
- workspace：D:\AI-Work\jobs\0003-YUJING-BRIDGE
- 密語：CASE0003.ORTHOPHOTO.CONTINUE
- current request：case0003-orthophoto-20260820-a5

## 1. 已有 REAL authority
request a2 已取得 DirectWork durable evidence：work_id=dw-20260820T072026-2b13548d00bf965a；accepted PASS；claimed PASS（slot=4 / DESKTOP-UL7V2VV）；running PASS（pid=21080）；terminal failed；exit_code=1。因此歷史上已證明 GitHub short transport → UL7 → DirectWork /v1/work → durable queue → claim → slot → executor 真實成立，a2 不可描述為 DirectWork 沒接案。

## 2. a3 / a4 transport 缺口
a3 已部署 self-diagnosing payload，失敗應帶回 stage/error/workspace_exists/geo_exists/tool_root/producer_commit/stdout/stderr，但 fresh receipt 未觀察到。a4 request-only retrigger 亦未觀察到 fresh receipt。因此 GAP-0003-TRANSPORT-01 定義為：request 已落 master，但無 fresh evidence 證明 UL7 workflow runner 已開始。此 gap 位於 transport/runner-start 層，與 a2 business exit=1 不同。

## 3. a5 transport witness
DirectWork 已新增 .github/workflows/case0003-transport-witness-ul7.yml，正式落 master commit 5dec37d5a5836c3409d60dd4b2b9d110bce1d6c4；同一 atomic commit 將 request 更新為 case0003-orthophoto-20260820-a5。witness 只在 UL7 runner 開始時寫 transport-results/case0003/case0003-orthophoto-20260820-a5.json，business_execution=false，不執行正射業務。

2026-08-20 本輪再次讀取後：transport witness 仍為 404 / NOT OBSERVED；secret-results/case0003/case0003-orthophoto-20260820-a5.json 亦為 404 / NOT OBSERVED。此證據只能證明「尚未觀察到」，不能單獨宣告 UL7 offline 或 workflow failure。

## 4. ODA→UL7 runner inventory 旁證
為避免 UL7 自證在線，go-tool-runtime 已部署 .github/workflows/case0003-query-ul7-runner-inventory-oda.yml，由 DESKTOP-ODAQN0D / ODA runner 查 http://127.0.0.1:8848/api/information/runners/current，預期寫 evidence/case0003/ul7-runner-inventory-from-oda.json。

第一輪 trigger 後 evidence 未觀察到。本輪已確認 workflow 與 request trigger 檔均存在 main，並再次以 request-only 方式重觸發：

- trigger file：case-requests/case0003-query-ul7-runner-inventory.txt
- a2 trigger commit：1e69d9bb720ca54f0c9923165929eb1322c90bae
- trigger content：case0003 query UL7 runner inventory from ODA 2026-08-20 a2

重觸發後立即檢查，evidence 仍為 NOT OBSERVED。這表示目前不只 UL7 witness 沒回來，連 ODA 旁證工作也尚未形成 durable Git receipt；因此新的疑點提升為「self-hosted Actions transport/runner availability 可能是跨機器共通問題」，但在取得 runner inventory 或 GitHub runner authority 前仍不得把它寫成已證實故障。

## 5. go-tool 8848 負面知識
127.0.0.1:8848 是新版 per-machine local-work queue-only profile；codebase/git/knowledge/actions disabled 是允許且預期。不得再把 /tools disabled 當完整 go-tool query runtime 故障，也不得因此重裝 queue runtime。本案 ODA 旁證使用的是 /api/information/runners/current information endpoint。

## 6. 最新 acceptance matrix
```text
a2 DirectWork ingress              PASS
a2 durable queue                   PASS
a2 claim / slot                    PASS (slot 4)
a2 executor                        PASS (pid 21080)
a2 business                        FAIL (exit 1)
a3 self-diagnosing payload         DEPLOYED
a3 receipt                         NOT OBSERVED
a4 retrigger                       SENT
a4 receipt                         NOT OBSERVED
a5 transport witness               DEPLOYED
a5 transport receipt               NOT OBSERVED (fresh recheck)
a5 business receipt                NOT OBSERVED (fresh recheck)
ODA→UL7 inventory query workflow   DEPLOYED
ODA inventory query a1             NOT OBSERVED
ODA inventory query a2 retrigger   SENT (commit 1e69d9bb...)
ODA inventory receipt              NOT OBSERVED (immediate recheck)
Cross-machine transport suspicion  OPEN / NOT YET PROVEN
Fresh DirectWork work_id           PENDING
Fresh PHOTO2 JPEG                  NOT PROVEN
Artifact size/SHA256               NOT PROVEN
NLSC PHOTO2 evidence               NOT PROVEN
Drive verified publish             NOT STARTED
ChatGPT exact-image visual QA      NOT STARTED
```

## 7. 缺口與補齊策略
GAP-0003-TRANSPORT-01 保持 OPEN。現在不得再改正射 producer，因為 fresh runner-start 尚未證明。下一個有效 authority 必須至少滿足其一：

1. UL7 transport witness 出現；
2. ODA runner inventory receipt 出現並明確給出 UL7 online/offline/absent；
3. GitHub runner inventory / runner service authority 提供 fresh 可核對狀態。

若 ODA inventory 顯示 UL7 offline/absent，先修 runner availability/label/service；若 UL7 online 但 witness 不出現，修 workflow routing/trigger；若 witness 出現但 business receipt 不出現，修 secret workflow→DirectWork ingress；若 business receipt failed，直接依 self-diagnosing stage/error/stdout/stderr 補最小 business gap；若 succeeded，驗收 work_id/events/slot/pid/exit=0/tool_root/producer_commit/JPEG path-size-SHA256/provider=nlsc/layer=PHOTO2/tile_count。

只有 fresh orthophoto durable PASS 後才可 Drive publish；只有 ChatGPT 取得 exact JPEG 並實際看圖後才可記 visual QA PASS/TUNE/FAIL。
