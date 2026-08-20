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

本輪再次讀取後：transport witness 仍為 404 / NOT OBSERVED；secret-results/case0003/case0003-orthophoto-20260820-a5.json 亦為 404 / NOT OBSERVED。此證據只能證明「尚未觀察到」，不能單獨宣告 UL7 offline 或 workflow failure。

## 4. ODA→UL7 runner inventory 旁證
為避免 UL7 自證在線，go-tool-runtime 已部署 .github/workflows/case0003-query-ul7-runner-inventory-oda.yml，由 DESKTOP-ODAQN0D / ODA runner查 http://127.0.0.1:8848/api/information/runners/current，預期寫 evidence/case0003/ul7-runner-inventory-from-oda.json。

第一輪與 a2 request-only retrigger（commit 1e69d9bb720ca54f0c9923165929eb1322c90bae）後，evidence 仍未觀察到。因此這條 ODA 旁證目前不能提供 UL7 fresh online/offline authority。

## 5. O87 fresh authority：否定「所有 runner 都掛」
2026-08-20 15:42（Asia/Taipei），DirectWork 已有 fresh O87 self-hosted runner 回傳的 Case0006 remote-admission receipt，commit 241b58b0cc4d340da6eaf1e1e335564204546085。該 receipt 明確記錄：observer=DESKTOP-O87PJNR、target=DESKTOP-ODAQN0D、remote work_id=dw-20260820T074210-48814d97fcd6d9ee、accepted→claimed(slot=4)→running(pid=2824)→succeeded、exit_code=0。

因此「所有 self-hosted runners 都停止消費新 job」已被 fresh evidence 否定。至少 O87 在 a5 之後仍能取得 job，且能跨機把 durable work 送進另一台 DirectWork 並完成。

## 6. 新缺口修補：O87→UL7 LAN service probe
為直接區分 UL7 主機/服務問題與 UL7 GitHub runner 問題，DirectWork 新增：

.github/workflows/case0003-o87-probe-ul7-services.yml

request：case0003-o87-probe-ul7-services-20260820-r01

該 workflow 固定 runs-on=[self-hosted, Windows, X64, O87]，由已具 fresh authority 的 DESKTOP-O87PJNR 對 DESKTOP-UL7V2VV 做 DNS 與 query-only probes：

- http://DESKTOP-UL7V2VV:8787/health
- http://DESKTOP-UL7V2VV:8787/v1/node/status
- http://DESKTOP-UL7V2VV:8848/health
- http://DESKTOP-UL7V2VV:8848/api/information/runners/current

結果預定寫回：diagnostics/case0003/case0003-o87-probe-ul7-services-20260820-r01.json。

部署 commits：workflow=e4f5c82e1e065b15767e3e70778df7fe6b267438；request=889ad67c342a158198f7900a0174da27f0ab2244。merge 前 compare 為 ahead=2 / behind=0，已 force=false fast-forward 到 DirectWork master。立即 fresh recheck 時 diagnostics receipt 尚未觀察到，因此只能記 DEPLOYED / RECEIPT PENDING。

## 7. go-tool 8848 負面知識
127.0.0.1:8848 是新版 per-machine local-work queue-only profile；codebase/git/knowledge/actions disabled 是允許且預期。不得再把 /tools disabled 當完整 go-tool query runtime 故障，也不得因此重裝 queue runtime。本案 runner 旁證使用 /api/information/runners/current information endpoint。

## 8. 最新 acceptance matrix
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
a5 transport receipt               NOT OBSERVED
a5 business receipt                NOT OBSERVED
ODA→UL7 inventory query            RETRIGGERED / NO RECEIPT
O87 self-hosted runner              FRESH PASS (15:42 +08)
O87 remote DirectWork admission     PASS (work_id dw-20260820T074210-48814d97fcd6d9ee)
O87→UL7 LAN service probe           DEPLOYED / RECEIPT PENDING
Fresh DirectWork work_id            PENDING
Fresh PHOTO2 JPEG                   NOT PROVEN
Artifact size/SHA256                NOT PROVEN
NLSC PHOTO2 evidence                NOT PROVEN
Drive verified publish              NOT STARTED
ChatGPT exact-image visual QA       NOT STARTED
```

## 9. 缺口與補齊策略
GAP-0003-TRANSPORT-01 保持 OPEN，但 scope 已縮小：GitHub repo 本身持續更新、O87 self-hosted runner fresh PASS，所以不再把「整個 self-hosted Actions 都停擺」當主假設。

下一個 authority 以 O87→UL7 probe 為優先：若 DNS/8787/8848 全部不可達，先修 UL7 host/network/service；若 8787/8848 可達但 UL7 witness 不出現，收斂到 UL7 GitHub runner service / label / workflow assignment；若 a5 business receipt出現，直接依 self-diagnosing stage/error/stdout/stderr 補 business gap。

只有 fresh orthophoto durable PASS 後才可 Drive publish；只有 ChatGPT 取得 exact JPEG 並實際看圖後才可記 visual QA PASS/TUNE/FAIL。
