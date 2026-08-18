# 0003 臺南市玉井橋 — STATUS

更新時間：2026-08-18 Asia/Taipei

狀態：`IMPLEMENTING / GEO ACCEPTED / IMAGERY v3+v2 STRICT REAL QC REQUIRED / TERRAIN+CONSUMER+BLENDER+SCENEX LOCALIZED / OS+DRIVE REVIEW LOOP LOCALIZED / UL7 REAL REQUIRED`

## 1. Canonical authority

- Host：`DESKTOP-UL7V2VV`
- Workspace：`D:\AI-Work\jobs\0003-YUJING-BRIDGE`
- Input：`臺南市玉井橋`
- OpenWorker：本機總控、durable queue、agent slots、host/workspace/JobBinding authority。
- go-tool-runtime：capability discovery + `localexec`。
- owning repos：真正 imagery / terrain / Blender / SceneX / OS logic authority。
- GitHub Actions：CI / fallback / bootstrap / historical evidence；不是 canonical business execution plane。

Canonical flow：

```text
OpenWorker local controller
→ go-tool localexec
→ physical workspace artifacts
→ strict QC
→ OS Registry / Review / Delivery
→ immutable Drive review ZIP
→ ChatGPT connector PASS/TUNE/FAIL/TOOL_GAP
→ WorkLedger accept / deliver
```

## 2. Acceptance boundary

目前 whole-case 歷史上只有 GEO 可稱 ACCEPTED：

`D:\AI-Work\jobs\0003-YUJING-BRIDGE\geo\geolocation.json`

Street View / Orthophoto 的 code、localexec、semantic visibility、SHA、GEO binding、workspace-boundary、stage WorkLedger history contract 已補；**但尚未由 UL7 跑出最新版 v3/v2 fresh imagery，因此仍不得稱 REAL ACCEPTED。**

Whole Case 更不得稱 ACCEPTED/DELIVERED，必須等 OS Delivery + Google Drive/ChatGPT connector review PASS + reviewed-delivery finalizer。

## 3. Canonical auto entrypoint

`scripts/case0003_local_continue_auto.ps1`

目前 root-resolution schema：`openworker/case0003-root-resolution/v6`。

順序：

```text
machine-root registry / node inventory
→ JobBinding OS identity
→ REAL preflight
→ quarantine unsafe imagery manifests
→ v10 physical-gate controller
→ strict imagery WorkLedger recorder（僅真 PASS 時）
```

### Preflight

`case0003_local_preflight.ps1` 在任何 business submit 前驗：UL7 identity、required tools/roots、workspace、JobBinding、DTM catalog、Engineering OS health。

### Unsafe imagery quarantine

`scripts/case0003_quarantine_unsafe_imagery.ps1`

v3/v2 manifest 若指向 canonical workspace 外 PNG/JPG/evidence，manifest 不直接刪除，而是移到：

`.openworker\quarantine\imagery\`

保存 rejected manifest SHA/reason 後，controller 看到 canonical manifest 缺失，重新取得該 imagery stage。

## 4. Imagery strict contract

### Street View

Canonical manifest：`streetview\browser\streetview-browser-screenshots.json`

Schema：`streetview-browser-screenshots/v3`。

Required：

- `transport=localexec`、host=UL7；
- manifest GEO = current accepted GEO；
- headings = 0/90/180/270 exactly once；
- producer `google / headless-render-webgl / angle-swiftshader-webgl`；
- 1920×1080、bytes>0；
- producer semantic visibility pass；
- each physical PNG SHA = producer receipt SHA；
- output path = manifest path；
- all artifact paths remain inside canonical workspace。

舊黑圖 acceptance 已撤銷。

### Orthophoto

Canonical manifest：`orthophoto\nlsc-photo2\orthophoto-photo2-workspace.json`

Schema：`orthophoto-workspace/v2`。

Required：

- `transport=localexec`、host=UL7；
- manifest GEO + producer plan GEO = current accepted GEO；
- producer `orthophoto-nlsc-photo2/v1`；
- provider=`nlsc`、layer=`PHOTO2`、zoom=19、tile count 1..25；
- `visibility.visible=true`；useful ratio >=0.20；stddev >=0.02；luma range >=0.10；
- physical JPEG SHA = producer output SHA；dimensions/bytes>0；
- JPG/evidence/manifest paths remain inside canonical workspace。

舊只有 `orthophoto-photo2-evidence.json` 的成果不再足以 PASS。

### Local parallel submit

`scripts/case0003_local_imagery_parallel.ps1`

Street View / Orthophoto 分 locks / agent slots 並行；一邊 strict PASS 時只補另一邊；`github_business_transport=false`。

## 5. Imagery stage WorkLedger history

`scripts/case0003_record_imagery_acceptance.py`

只有兩個 imagery strict gate 都通過才執行。它建立或復用 `progress` revision，將 current GEO、四張 Street View、PHOTO2 JPG、workspace manifests/evidence 與 physical SHA 寫入 WorkLedger，required checks：

- `Imagery Accepted GEO`
- `Street View Physical+Semantic QC`
- `Orthophoto Physical+Semantic QC`

revision 保持 `verifying`；同 fingerprint idempotent。它不得移動 whole-case `accepted_revision_id` 或 `delivered_revision_id`。

## 6. Terrain → Consumer/Blender + SceneX

AOI：`terrain.aoi.build` / `case0003_local_terrain_aoi.ps1`，需 10 個 terrain physical artifacts、`terrain-context/v1`、`usable_tiles>0`、SHA evidence。

Terrain gate 後：

```text
Terrain
├→ SceneX REAL browse
└→ strict imagery PASS → Consumer → Blender REAL
```

Consumer：`terrain.consumer.orchestrate`。  
Blender：`terrain.blender.execute`。  
SceneX：`scenex.terrain.real_browse`。

Blender 必須 `.blend` + render + evidence/handoff SHA consistency；SceneX 必須 active chunks>0、terrain geometry>0、1280×720 screenshot + region/evidence/screenshot SHA consistency。

## 7. AI-Engineering-OS

Blender + SceneX pass → `engineering_os.artifacts.ingest`。ArtifactStager 安全 stage 外部 workspace artifacts 入 OS Job WorkingDir並重算 SHA，不放寬 JobPathValidator。

current artifacts 必須 Review/Approval，才可 `engineering_os.delivery.publish`。publish 後仍驗 delivery manifest、checksum manifest、website、revision identity。

OS project/job identity由 persisted JobBinding 提供；explicit override mismatch fail-closed。

## 8. Drive / ChatGPT final review

OS Delivery pass 後：fresh mechanical verification → immutable review folder + deterministic ZIP → Drive sync。

ChatGPT connector 必須實際查看 Blender render、SceneX screenshot、evidence、delivery website。回傳 `connector-review-receipt.json`，綁 current revision、bundle manifest SHA、review ZIP SHA與 Drive folder/file IDs。

PASS 只先進 `ACCEPTED_PENDING_FINALIZE`；finalizer 再綁 current OS delivery identity與 current physical bytes，全部一致才寫 WorkLedger delivered pointer。

## 9. Next REAL action

在 UL7 使用最新版 OpenWorker / go-tool / owning repos 執行：

```powershell
.\scripts\case0003_local_continue_auto.ps1
```

預期最新舊 evidence 會因 v3/v2、current GEO、workspace-boundary gate 被淘汰，Street View / Orthophoto 由 local durable jobs重新取得。fresh imagery strict PASS 後才會寫 imagery progress history並繼續 AOI / Consumer / Blender / SceneX。

此 ChatGPT 環境目前沒有直接到 UL7 `127.0.0.1:8787` 的執行通道，因此不能假稱本輪已提交或已得到 REAL artifact；程式/手冊 hardening 不等於 UL7 REAL acceptance。
