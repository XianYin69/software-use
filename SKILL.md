---
name: software-use
description: >
  在真实使用软件的过程中学习：真实取证＋网络检索 → 按固定前缀 software_use_only- 检索/创建
  私有附属技能 → 调取执行 → 在使用中强化。本体不含具体软件知识，判读与操作一律交依赖技能。
license: MIT
metadata:
  category: meta
  version: 0.4.0
---

# software-use

使用 `software-use` skill 来完成用户请求。

## 职责边界

- 只做四件事：**learn / resolve / invoke / reinforce**；具体软件经验落在 `private/software_use_only-<app>/`（**PRIVATE**，深度 2）。
- 判读与操作不自办：语义判读、输入模拟、视频定位一律交依赖技能，本体只编排与记账；分工表与通道清单见 [knowledge/依赖分工.md](knowledge/依赖分工.md)（附属技能以 `used_skills` 记录用到哪几个）。

## 四阶段

1. **learn**：真实取证（截图/OCR/日志/命令输出）＋检索 → `scripts/su_learn.py`；**视频类软件取证交 `video-viewer`**——用其 `probe`/`extract`/`bisect`/`analyze` 以画面＋声音二分定位到目标时刻（±tol 秒），再把截得的帧交 `screen-vision`/`camera-vision`、音频段交 `audio-perception` 判读，所用技能随 `--used-skills` 记入索引。
2. **resolve**：`scripts/su_index.py --find <关键词>` 命中则载入；未命中派 `Skill_Generator` 建附属技能。
3. **invoke**：`scripts/su_invoke.py --app <slug>` 输出绝对路径＋调用契约，交 skill/task 派发。**真实使用软件＝调用 `safe-mouse-automation` 的既有脚本通道**：`desktop_ops.py`（打开/枚举窗口）、`app_ops.py`（UIA 控件与菜单）、`virtual_mouse.py`（点击/打字/拖拽）、`browser_cdp.py`（浏览器）、`batch_runner.py`（批量）、`screenshot_verify.py`（前后截图验证）；**每一步先过 `safety_gate.py`、开 `hud_overlay.py` 会话，遇 `human_gate.py`（验证码/登录墙）立即停止并回报**；禁止自调 `SetForegroundWindow` 或移动物理光标，`SendInput` 前台回退（`real_input.py`）须先征得用户同意。
4. **reinforce**：`scripts/su_reinforce.py --app <slug> --outcome ok|fail [--used-skills a,b]` 追加经验并更新索引（只追加不改历史）。

## 注册与发布两层契约

附属技能**必须**登记 `register.json`（`visibility: PRIVATE`/`parent`/`publish: false`），但注册≠
发布：`publish=false` 只表示不进 hub 同步与公开索引。发布层＝进 `private/` **独立私有仓**（自带
`.git`/remote，走 功能分支→dev→main）可推 GitHub **PRIVATE** 仓——「不公开」＝仓库可见性
PRIVATE，**不是不入库**；可见性由仓库属性＋脚本判定＋文档承载，本体 frontmatter 不自造
`visibility`。校验：`su_index.py --audit`（`E_NOT_REGISTERED`/`E_LEAK_TO_PUBLIC`/
`E_NO_PRIVATE_REPO`/`E_NO_GITIGNORE`）、`su_publish.py --check-visibility`。详见
[knowledge/注册与发布两层模型.md](knowledge/注册与发布两层模型.md)。

## 索引

- [scripts/](scripts/scripts.md) · [knowledge/](knowledge/knowledge.md) · [resistance/](resistance/resistance.md) · [schemas/](schemas/schemas.md) · [dependence/](dependence/dependence.md) · [planned_tasks/](planned_tasks/README.md) · [README](README.md)

## 红线摘要

不得绕过 `safe-mouse-automation` 的 `safety_gate`/`human_gate`；不自研输入模拟；附属技能只引用
依赖、不复制其实现；附属技能必须登记 register.json、只入私有仓（禁入本体公开仓）；无证据不得
称「已学会」；强化只追加不改历史；写盘仅限本目录与 private/；不自判读语义。
详见 [resistance/红线约束.md](resistance/红线约束.md)。
> 前台回退的「用户同意」有两种：逐次同意，或附属技能 `state.json` 里 `foreground_fallback.allowed=true` 的**长期授权**（standing-grant， 由 `su_invoke.py` 随契约下发 `consent_token`/`scope`/`limits`）；两者都只对被点名的软件生效，执行时仍须逐步过 `safety_gate`＋`hud_overlay`＋前后焦点审计，越出 `limits` 即停。
