# software-use

在**真实使用软件的过程中**学习：取证 → 检索 → 建/找私有附属技能 → 调取 → 强化。
双仓模型：本体仓 GitHub **PUBLIC**，附属技能仓 GitHub **PRIVATE**（都发布，差别在仓库属性）。
附属技能另**必须**登记进 SMS register.json（`publish: false`＝不进 hub 同步与公开索引）。

## 结构

- [`SKILL.md`](SKILL.md)：入口（YAML frontmatter，仅 name/description/license/metadata）。
- [`agent/`](agent/)：四格式提示词（CLAUDE.md / .cursorrules / instructions.md / agent_prompt.md）。
- [`scripts/`](scripts/scripts.md)：`su_index` / `su_learn` / `su_invoke` / `su_reinforce` / `su_publish`。
- [`knowledge/`](knowledge/knowledge.md)：元知识（前缀规范、注册与发布契约、四阶段、只追加）。
- [`schemas/`](schemas/schemas.md)：`index.schema.json`、`attached_skill.schema.json`。
- [`resistance/`](resistance/resistance.md)：[红线约束](resistance/红线约束.md) · [降级策略](resistance/降级策略.md)。
- [`private/`](private/)：附属技能落位（深度 2）＝**独立私有仓工作树**（自带 `.git`/remote；登记 register.json、入库可推 GitHub PRIVATE，但不得混入本体公开仓）＋ `index.json`。
- [`dependence/`](dependence/dependence.md)：依赖清单 8 条（每条附 `source_url`）。
- [`planned_tasks/`](planned_tasks/README.md)：计划任务声明（当前为空，到期由 SMS 调度）。
- [`asset/`](asset/asset.md) · [`LICENSE`](LICENSE) · [`CHANGELOG.md`](CHANGELOG.md)

## 依赖（不自办＝交依赖技能）

画面/声音/视频判读、真实输入操作（每步先过 `safety_gate`、遇 `human_gate` 即停）、建附属技能、
文档核对一律交依赖技能，本体只编排与记账；清单见 [knowledge/依赖分工.md](knowledge/依赖分工.md)。

## 快速上手

```
python scripts/su_learn.py --app <slug> --evidence <路径> --source <URL> \
       --note <要点> --used-skills screen-vision,safe-mouse-automation
python scripts/su_index.py --build && python scripts/su_index.py --find <slug>
python scripts/su_invoke.py --app <slug>
python scripts/su_reinforce.py --app <slug> --outcome ok --note <新发现> \
       [--used-skills video-viewer]
python scripts/su_index.py --audit
python scripts/su_publish.py --guard && python scripts/su_publish.py --status
```

## 注册与发布（两层）

- 注册层：`register.py` 深度 1 后追加深度 2（`<skill>/private/*`），附属技能带
  `visibility=PRIVATE`/`parent`/`publish=false` 登记；`--audit` 缺失即 `E_NOT_REGISTERED`。
- 发布层：附属技能**入 `private/` 独立私有仓并可推 GitHub PRIVATE 仓**（`su_publish.py
  --init-private` / `--commit` / `--integrate`）；`--check-visibility` 校验本体 PUBLIC／
  附属 PRIVATE（`E_VISIBILITY_MISMATCH`）；`--guard` 防附属混入本体公开仓（`E_LEAK_TO_PUBLIC`）。
- 本仓 `.gitignore` 排除 `private/*` 的理由是「它是另一个仓的工作树」，**不是**「绝不发布」。

## 编辑规则

所有 `.md` ≤ 50 行；悬空链接为 0（`python <Skill_Generator>/scripts/check-links.py --root .`）；
依赖须过 `lint-deps.py`。
