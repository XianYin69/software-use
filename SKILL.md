---
name: software-use
description: >
  在真实使用软件的过程中学习：真实取证＋网络检索 → 按固定前缀 software_use_only- 检索/创建
  私有附属技能 → 调取执行 → 在使用中强化。本体不含任何具体软件知识。
license: MIT
visibility: PUBLIC
metadata:
  category: meta
---

# software-use

使用 `software-use` skill 来完成用户请求。

## 职责边界

- 只做四件事：**learn（取证学习）/ resolve（前缀索引检索）/ invoke（调取）/ reinforce（强化）**。
- 具体软件经验一律落在 `private/software_use_only-<app>/`（**PRIVATE**，深度 2）。
- 语义判读不自办：画面交 `screen-vision`/`camera-vision`，声音交 `audio-perception`，
  新建附属技能交 `Skill_Generator`，官方文档核对交 `webfetch`。

## 四阶段

1. **learn**：真实操作取证（截图/OCR/命令输出/日志）＋检索 → `scripts/su_learn.py`。
2. **resolve**：`scripts/su_index.py --find <关键词>` 命中则载入；未命中派 Skill_Generator 建附属技能。
3. **invoke**：`scripts/su_invoke.py --app <slug>` 输出绝对路径＋调用契约，交 skill/task 派发。
4. **reinforce**：`scripts/su_reinforce.py --app <slug> --outcome ok|fail` 追加经验并更新索引。

## 不公开的机制

`register.py` 只扫 `root + glob(root/*)`（深度 1），故 `private/` 下结构上不可能被登记；
`su_index.py --audit` 反查 register.json，出现任何 `software_use_only-*` 即 FAIL（rc=2, `E_LEAK`）；register 缺失或不可解析同样 FAIL，回 `E_NO_REGISTER`/`E_BAD_REGISTER`（rc=2），绝不静默通过。

## 索引

- [scripts/](scripts/scripts.md) · [knowledge/](knowledge/knowledge.md) ·
  [resistance/](resistance/resistance.md) · [schemas/](schemas/schemas.md) ·
  [dependence/](dependence/dependence.md) · [planned_tasks/](planned_tasks/README.md) ·
  [README](README.md)

## 红线摘要

附属技能不得进公开索引；无证据不得称「已学会」；强化只追加不改历史；
写盘仅限本目录与 private/；不自判读语义。详见 [resistance/红线约束.md](resistance/红线约束.md)。
