# software-use

在**真实使用软件的过程中**学习：取证 → 检索 → 建/找私有附属技能 → 调取 → 强化。
本体 `PUBLIC`（可被 SMS register.json 索引），附属技能全部 `PRIVATE`。

## 结构

- [`SKILL.md`](SKILL.md)：入口（YAML frontmatter，`visibility: PUBLIC`）。
- [`agent/`](agent/)：四格式提示词（CLAUDE.md / .cursorrules / instructions.md / agent_prompt.md）。
- [`scripts/`](scripts/scripts.md)：`su_index` / `su_learn` / `su_invoke` / `su_reinforce`。
- [`knowledge/`](knowledge/knowledge.md)：元知识（前缀规范、深度1机制、四阶段、只追加）。
- [`schemas/`](schemas/schemas.md)：`index.schema.json`、`attached_skill.schema.json`。
- [`resistance/`](resistance/resistance.md)：[红线约束](resistance/红线约束.md)、
  [降级策略](resistance/降级策略.md)。
- [`private/`](private/)：附属技能落位（深度 2，**不进 register.json**）＋ `index.json`。
- [`dependence/`](dependence/dependence.md)：依赖清单（每条附 `source_url`）。
- [`planned_tasks/`](planned_tasks/README.md)：计划任务声明（当前为空，到期由 SMS 调度）。
- [`asset/`](asset/asset.md) · [`LICENSE`](LICENSE) · [`CHANGELOG.md`](CHANGELOG.md)

## 快速上手

```
python scripts/su_learn.py --app <slug> --evidence <路径> --source <URL> --note <要点>
python scripts/su_index.py --build && python scripts/su_index.py --find <slug>
python scripts/su_invoke.py --app <slug>
python scripts/su_reinforce.py --app <slug> --outcome ok --note <新发现>
python scripts/su_index.py --audit
```

## 私有机制

`register.py` 只扫 `root + glob(root/*)`（深度 1），`private/*` 结构上不可能被登记；
`--audit` 反查 register.json 作双保险，出现 `software_use_only-*` 即 FAIL。

## 编辑规则

所有 `.md` ≤ 50 行；悬空链接为 0（`python <Skill_Generator>/scripts/check-links.py --root .`）；
依赖须过 `lint-deps.py`。
