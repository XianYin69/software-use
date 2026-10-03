# CHANGELOG
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
