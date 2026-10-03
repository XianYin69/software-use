# CHANGELOG
## 0.4.0 - 2026-10-03（返工：双仓可见性模型）
- 纠正 0.2.x 的错误实现：把「附属技能不公开」实现成 `private/*` 进 `.gitignore`、完全不入库不发布，违反 Skill_Generator `git工作流约束` 第 7 条（ignore 只允许临时产物与 IDE）与第 10 条（不公开＝仓库可见性 **PRIVATE**）。改为**双仓模型**：本体仓 GitHub PUBLIC；`private/` 为独立私有仓工作树（自带 `.git`/remote），附属技能照常入库、走 功能分支→dev→main、可推 GitHub **PRIVATE** 仓。注册层不变（`register.json` 强制；`publish=false` 只表示不进 hub 同步与公开索引，不表示不入 git）。
- 新增 `scripts/su_publish.py`：`--init-private`（本地 init＋`.gitignore`＋提交＋配 remote，不推送）、`--commit`/`--integrate`（私有仓分支流程）、`--check-visibility`（`gh repo view --json visibility`：本体须 PUBLIC、附属须 PRIVATE，不符 rc=2 `E_VISIBILITY_MISMATCH`；远端未配置 `E_NO_REMOTE`）、`--guard`（附属技能混入本体仓 → rc=2 `E_LEAK_TO_PUBLIC`；`private/` 未入库 → `E_NO_PRIVATE_REPO`）、`--status`。默认 dry-run，`--yes` 才动盘；`--push` 须 `--authorized-by-user`。
- frontmatter 去自造字段：本体 `SKILL.md` 删 `visibility: PUBLIC`（`gen_agent_prompt.py` 只认 name/description/license/metadata），版本移入 `metadata.version`；可见性由**仓库属性＋脚本判定＋文档**承载。附属 `visibility: PRIVATE` 保留为注册层契约标记（`register.py`/`su_index.py` 均读）。
- 同步：`su_index.py --audit` 的 `E_GIT_LEAK`→`E_LEAK_TO_PUBLIC` 并新增 `E_NO_PRIVATE_REPO`；`su_learn.py`/`su_invoke.py`/附属 `私有约束.md` 的「严禁入 git」改为「只入私有仓、禁入本体公开仓」；`.gitignore` 保留 `private/*` 但理由改写；新增 `knowledge/注册与发布两层模型.md`、`knowledge/依赖分工.md`（删 `注册强制与禁止发布.md`）；`SKILL.md`/`README.md`/`scripts.md`/`schemas.md`/`resistance/*` 同步；`deps.json` 增 `git`、`gh`（各附 `source_url`）。
- 实测：`--init-private --yes` 建成私有仓并完成 feature→dev→main；`--guard` PASS（公开仓 0 条 private 泄漏）；`--audit` PASS；`--check-visibility` 回 `E_NO_REMOTE`（远端未配置，建仓与推送留待用户当轮授权）。

## 0.3.0 - 2026-10-03
- **依赖落地（用户新增诉求）**：`deps.json` 增至 8 条——新增 `safe-mouse-automation`（invoke 阶段真实操作通道）与 `video-viewer`（learn 阶段视频取证），原有 Skill_Generator/camera-vision/screen-vision/audio-perception/webfetch/task_table 保留。
- `SKILL.md`：新增「依赖分工」表；learn 写明视频取证走 `video-viewer` probe/extract/bisect/analyze 二分定位后交判读技能；invoke 写明走 `safe-mouse-automation` 的 desktop_ops/app_ops/virtual_mouse/browser_cdp/batch_runner/screenshot_verify，每步先过 `safety_gate`、开 `hud_overlay`、遇 `human_gate` 即停回报，禁自调 `SetForegroundWindow`/移物理光标，`SendInput` 回退（`real_input`）须先获用户同意。
- `resistance/红线约束.md`：五条→八条，新增「不得绕过 safety_gate/human_gate」「不自研鼠标键盘模拟」「附属技能只引用依赖、不得复制实现」。
- `used_skills` 贯通：`su_learn.py --used-skills`（模板带依赖段）、`su_reinforce.py --used-skills`（只追加不改历史）、`su_index.py` 索引条目、`su_invoke.py` 契约回显；`schemas/` 两 schema 增可选 `used_skills` 数组。
- 顺带修 `su_reinforce.py` 未学习分支 `fail()` 传三参崩溃（定义只收两参）。
- 本体 `SKILL.md` frontmatter 补 `version: 0.3.0`（此前无版本字段）。

## 0.2.0 - 2026-10-03
- **契约反转（用户澄清）**：附属技能 `software_use_only-*` **必须**登记进 SMS
  `register.json`（否则 SMS 索引不到、派发不到）；「不公开」＝不进 GitHub/不进任何 git（内容涉侵权），不是不注册。
- `register.py` 深度 1 后追加深度 2（`<skill>/private/*`），entry 新增
  `visibility`/`parent`/`publish`（PRIVATE→`publish=false`），doc `version` 1.1.0。
- `su_index.py --audit`：「出现即 `E_LEAK`」改为「缺失即 `E_NOT_REGISTERED`」，
  新增 `E_GIT_LEAK`（`git ls-files private` 除 `.gitkeep` 外有项）、`E_NO_GITIGNORE`
  （缺 `private/*`）与 `E_NO_GIT`（git 不可用亦不得放行）；
  保留 `E_NO_REGISTER`/`E_BAD_REGISTER`。
- `su_learn.py` RES_TMPL / `su_invoke.py` CONTRACT 文案同步；删除「手写 register.json」指示。
- `sync_skills.py _copy()` ignore `private`/`__pycache__`/`*.pyc`，报告新增 `skipped` 字段——堵住 hub→客户端→GitHub 的真实泄漏路径。
- 文档同步：`SKILL.md`/`README.md`/`scripts.md`/`resistance/*`/`schemas.md`/`knowledge/*`；
  `knowledge/深度1扫描保证私有.md` → `knowledge/注册强制与禁止发布.md`。
## 0.1.1 - 2026-10-03
- 修 `su_index.py read_frontmatter()`：支持块标量 `>`/`|`/`>-`/`|-`（缩进续行折叠为单行）、行内流式列表（JSON 解析，失败退逗号切分去引号，空列表回 `[]`）、顶层 `- ` 列表项、BOM（`utf-8-sig`）；嵌套映射（`metadata:` 下 `category:`）保持忽略且不污染上一个 key。
- 效果：`index.json` 的 `summary` 不再是 `">"`；`triggers`/`tools` 不再是 `["[\"python\", \"py\"]"]` 双层包裹，而是干净字符串数组。
- 修 `su_index.py --audit`：register.json 缺失/不可解析/缺 `skills` 数组 → 结构化 `E_NO_REGISTER`/`E_BAD_REGISTER` 且 rc=2，不再静默 rc=0 放行。
- 修 `su_learn.py`：再学习（附属技能已存在）时同步 frontmatter 的 `title`/`triggers`/`tools`，不再静默丢弃。
- `learned_from` 经带 `--source` 实测**无缺陷**（URL 正确落 state.json 与索引）。
- 红线 1 补充：反查不可用亦视为 FAIL；`scripts.md` 增「audit 出口」小节。

## 0.1.0 - 2026-10-03

- init：按 `software-use_design.md` 定稿契约创建技能（Skill_Generator 创建路径）。
- 本体 `visibility: PUBLIC`；附属技能 `private/software_use_only-<app>`（深度 2）`PRIVATE`。
- 四脚本落地：`su_index.py`（前缀扫描/`--find`/`--audit`）、`su_learn.py`（取证→草稿）、
  `su_invoke.py`（路径＋调用契约）、`su_reinforce.py`（只追加、uses+1、confidence 限幅）。
- `schemas/`：`index.schema.json`、`attached_skill.schema.json`。
- `knowledge/` 四条元知识；`resistance/` 五条红线 + 降级策略。
- `dependence/deps.json`：Skill_Generator / camera-vision / screen-vision /
  audio-perception / webfetch / task_table，每条附 `source_url`，过 `lint-deps.py`。
- 自测：learn demo → index --find 命中 → invoke 出契约 → reinforce conf 0.6→0.7 uses=1
  → audit PASS（register.json 无 `software_use_only-*`）。
- MIT `LICENSE`、`planned_tasks/`（空）、`agent/` 四格式提示词、`.gitignore` 齐备。
