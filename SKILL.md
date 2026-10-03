---
name: software-use
description: >
  在真实使用软件的过程中学习：真实取证＋网络检索 → 按固定前缀 software_use_only- 检索/创建
  私有附属技能 → 调取执行 → 在使用中强化。本体不含具体软件知识，判读与操作一律交依赖技能。
license: MIT
visibility: PUBLIC
version: 0.3.0
metadata:
  category: meta
---

# software-use

使用 `software-use` skill 来完成用户请求。

## 职责边界

- 只做四件事：**learn / resolve / invoke / reinforce**；具体软件经验落在 `private/software_use_only-<app>/`（**PRIVATE**，深度 2）。
- 判读与操作不自办：语义判读、输入模拟、视频定位一律交下表依赖技能；本体只编排与记账（附属技能以 `used_skills` 记录用到哪几个）。

## 依赖分工（不自办＝交依赖）

| 能力 | 依赖技能 | 阶段 |
|---|---|---|
| 画面判读（截图/OCR/摄像头） | `screen-vision` / `camera-vision` | learn·invoke |
| 声音判读 | `audio-perception` | learn·invoke |
| 视频内容（画面＋声音联合、二分定位目标时刻） | `video-viewer` | learn |
| 实际操作（点击/打字/拖拽/浏览器 CDP/UIA） | `safe-mouse-automation` | invoke |
| 建附属技能 | `Skill_Generator` | resolve |
| 官方文档核对 | `webfetch` | learn |

## 四阶段

1. **learn**：真实取证（截图/OCR/日志/命令输出）＋检索 → `scripts/su_learn.py`；**视频类软件取证交 `video-viewer`**——用其 `probe`/`extract`/`bisect`/`analyze` 以画面＋声音二分定位到目标时刻（±tol 秒），再把截得的帧交 `screen-vision`/`camera-vision`、音频段交 `audio-perception` 判读，所用技能随 `--used-skills` 记入索引。
2. **resolve**：`scripts/su_index.py --find <关键词>` 命中则载入；未命中派 `Skill_Generator` 建附属技能。
3. **invoke**：`scripts/su_invoke.py --app <slug>` 输出绝对路径＋调用契约，交 skill/task 派发。**真实使用软件＝调用 `safe-mouse-automation` 的既有脚本通道**：`desktop_ops.py`（打开/枚举窗口）、`app_ops.py`（UIA 控件与菜单）、`virtual_mouse.py`（点击/打字/拖拽）、`browser_cdp.py`（浏览器）、`batch_runner.py`（批量）、`screenshot_verify.py`（前后截图验证）；**每一步先过 `safety_gate.py`、开 `hud_overlay.py` 会话，遇 `human_gate.py`（验证码/登录墙）立即停止并回报**；禁止自调 `SetForegroundWindow` 或移动物理光标，`SendInput` 前台回退（`real_input.py`）须先征得用户同意。
4. **reinforce**：`scripts/su_reinforce.py --app <slug> --outcome ok|fail [--used-skills a,b]` 追加经验并更新索引（只追加不改历史）。

## 注册与发布契约（注册＝强制·发布＝禁止）

附属技能必须登记进 SMS `register.json`（`visibility: PRIVATE`/`parent: software-use`/`publish: false`）——注册≠发布，`publish=false` 即永不进任何 git/remote/GitHub；`su_index.py --audit` 双向校验：未登记 `E_NOT_REGISTERED`、`private/` 被 git 跟踪 `E_GIT_LEAK`、缺 ignore `E_NO_GITIGNORE`、注册表缺失/损坏 `E_NO_REGISTER`/`E_BAD_REGISTER`（均 rc=2）。详见 [knowledge/注册强制与禁止发布.md](knowledge/注册强制与禁止发布.md)。

## 索引

- [scripts/](scripts/scripts.md) · [knowledge/](knowledge/knowledge.md) · [resistance/](resistance/resistance.md) · [schemas/](schemas/schemas.md) · [dependence/](dependence/dependence.md) · [planned_tasks/](planned_tasks/README.md) · [README](README.md)

## 红线摘要

不得绕过 `safe-mouse-automation` 的 `safety_gate`/`human_gate`；不自研鼠标键盘模拟；附属技能只引用依赖、不复制其实现；附属技能必须登记 register.json、严禁入 git；无证据不得称「已学会」；强化只追加不改历史；写盘仅限本目录与 private/；不自判读语义。详见 [resistance/红线约束.md](resistance/红线约束.md)。
