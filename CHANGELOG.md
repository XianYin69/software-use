# CHANGELOG

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
