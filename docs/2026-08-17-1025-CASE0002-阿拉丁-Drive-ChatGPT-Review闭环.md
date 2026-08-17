# CASE 0002 阿拉丁 — Google Drive → ChatGPT 成果审查闭环

时间：2026-08-17 10:25（Asia/Taipei）  
状态：IMPLEMENTED；OpenWorker CI VERIFYING；真实阿拉丁 Review Bundle 待 Studio/ComfyX/OpenMAIC 同工作目录成果完成后 handoff

## 目标

让 Case 0002 不再以 Action `success`、文件非空或 SHA 一致作为最终质量结论。机械验证继续负责 provenance / reopen / decode / SHA；OpenWorker 将不可变成果包复制到 Google Drive 临时审查区，再由 ChatGPT 实际查看图片、PPTX、影片和 evidence，返回结构化 PASS / TUNE / TOOL_GAP / FAIL。

Google Drive 只作为临时 review exchange；`WorkLedger` 仍是 revision / artifact SHA / review verdict / parameter delta / owning-repo rework 的 durable authority。

## 新增接口

### `scripts/case0002_review_handoff.py`

- work code：`CASE-0002-ALADDIN`
- assigned host：`DESKTOP-ODAQN0D`
- 支持 `--phase storyboard|final`
- 默认 Drive root 来自 `OPENWORKER_REVIEW_DRIVE_ROOT`
- 使用通用 `ReviewCycle`，不复制 Case 0003 的核心实现

Storyboard phase 必需：

- `presentation/storyboard-request.bound.json`
- `presentation/storyboard.pptx`
- `presentation/storyboard.manifest.json`
- 至少一张 `visual-assets/**/*.png|jpg|jpeg`
- `evidence/*.json` 自动加入 bundle

Final phase 在上述基础上强制至少一个非空 `.mp4`。

Handoff 前：

1. 每个物理文件先登记到 WorkLedger。
2. 创建 required `LLM Semantic Review = pending` check。
3. ReviewCycle 建 immutable bundle。
4. bundle 内每个 artifact 记录 SHA256 / size。
5. atomic copy 到 Drive sync folder。
6. copy 后整棵文件树重新 SHA 比对。
7. revision 进入 `blocked / WAITING_LLM_REVIEW`。
8. accepted/delivered pointer 都保持空。

## 审查维度

- story / storyboard semantic correctness
- Aladdin / Genie character consistency
- scene / magic-lamp continuity
- shot composition / camera readability
- storyboard image quality and video-reference reuse suitability
- OpenMAIC slide readability / image placement
- final phase temporal coherence / motion quality
- subtitles / delivery quality
- parameter tuning opportunities
- real tool gaps requiring owning-repository repair

## 参数治理

LLM 只能对 allowlist 参数返回 TUNE：

- `video.duration_sec`
- `video.width`
- `video.height`
- `video.acceleration_profile`
- `video.seed`
- `presentation.image_scale`

模型路径、workflow ID、ComfyUI node、checkpoint 等不属于可自由调参项；若审查发现缺能力，应返回 TOOL_GAP 并指定 owning repo / capability / verification plan。

## `scripts/case0002_apply_llm_review.py`

读取 ChatGPT review receipt，并经过 `review_gap.apply_review_finding(...)`：

- PASS → required LLM check passed → accept revision → deliver revision
- TUNE → 当前 revision blocked → 新开 tuning child revision，记录 parameter delta
- TOOL_GAP → 归一化为 governed FAIL → `REWORK_REQUIRED`，保留 owning repo / gap capability / verification plan
- FAIL → `REWORK_REQUIRED`

因此不能用手动状态修改绕过 LLM review gate。

## 永久测试

`tests/test_case0002_review.py` 锁住：

1. storyboard handoff 后 accepted/delivered pointer 必须仍为空。
2. revision 必须是 blocked / waiting LLM review。
3. Drive 目标必须实际出现 `review-request.json`。
4. PASS receipt 才能 accept + deliver 同一 reviewed revision。
5. final phase 没有实体 MP4 必须 fail-closed。

实现 commits：

- `bf1078543e6cd01e3ede9a2795842162057eac7d` — Case 0002 Drive handoff wrapper
- `ebab68bdf7f29da65791ac898e5ed1806525393b` — ChatGPT review receipt apply
- `29478b8d9b0ad461c19176f4560d16f5eb9f6675` — governance regression tests

最新 OpenWorker CI：`31987877806`，当前 pytest / GUI jobs 正在执行；未提前标绿。

## Case 0002 正式闭环

```text
Comfyx-Studio DirectorProjectPlan
  ↓
ComfyX IMAGE reference/storyboard assets
  ↓
Studio receipt revalidation + stable-ID binding
  ↓
OpenMAIC editable storyboard.pptx
  ↓
ComfyX VIDEO + final assembly
  ↓
mechanical QC / reopen / SHA / provenance
  ↓
OpenWorker immutable Review Bundle
  ↓
Google Drive temporary review exchange
  ↓
ChatGPT physical artifact inspection
  ├─ PASS → accept/deliver
  ├─ TUNE → child revision → rerun → review again
  └─ TOOL_GAP/FAIL → owning repo repair → REAL rerun → review again
```

## 下一步

1. 等 Case 0002 同工作目录至少形成一张 REAL storyboard/reference image + image-bound PPTX。
2. 先执行 `--phase storyboard` handoff，让 ChatGPT 检查分镜与人物/场景连续性。
3. 分镜 PASS 后才继续 VIDEO 主线；若 TUNE/TOOL_GAP，先修再生成，避免错误视觉资产扩散到所有视频镜头。
4. final MP4、字幕、QC 完成后执行 `--phase final` 第二次审查。
5. 只有 final review PASS 才推进 OpenWorker accepted/delivered pointer。
