# software-use

在**真实使用软件的过程中**学习：取证 → 检索 → 建/找私有附属技能 → 调取 → 强化。
本体 `PUBLIC`；附属技能全部 `PRIVATE` 且**必须**登记进 SMS register.json（`publish: false`＝永不进 git/GitHub）。

## 结构

- [`SKILL.md`](SKILL.md)：入口（YAML frontmatter，`visibility: PUBLIC`）。
- [`agent/`](agent/)：四格式提示词（CLAUDE.md / .cursorrules / instructions.md / agent_prompt.md）。
- [`scripts/`](scripts/scripts.md)：`su_index` / `su_learn` / `su_invoke` / `su_reinforce`。
- [`knowledge/`](knowledge/knowledge.md)：元知识（前缀规范、注册与发布契约、四阶段、只追加）。
- [`schemas/`](schemas/schemas.md)：`index.schema.json`、`attached_skill.schema.json`。
- [`resistance/`](resistance/resistance.md)：[红线约束](resistance/红线约束.md)、
  [降级策略](resistance/降级策略.md)。
- [`private/`](private/)：附属技能落位（深度 2，**登记 register.json·禁止入 git**）＋ `index.json`。
- [`dependence/`](dependence/dependence.md)：依赖清单 8 条（每条附 `source_url`）。
- [`planned_tasks/`](planned_tasks/README.md)：计划任务声明（当前为空，到期由 SMS 调度）。
- [`asset/`](asset/asset.md) · [`LICENSE`](LICENSE) · [`CHANGELOG.md`](CHANGELOG.md)

## 依赖（不自办＝交依赖技能）

画面 `screen-vision`/`camera-vision` · 声音 `audio-perception` ·
视频取证 `video-viewer`（probe/extract/bisect/analyze 二分定位目标时刻）·
实际操作 `safe-mouse-automation`（每步先过 `safety_gate`、开 `hud_overlay`，
遇 `human_gate` 立即停止回报；禁自调 SetForegroundWindow/移物理光标）·
建附属技能 `Skill_Generator` · 文档核对 `webfetch` · 编排 `task_table`。
附属技能以 `used_skills` 记录用到哪几个（只引用 id，不复制实现）。

## 快速上手

```
python scripts/su_learn.py --app <slug> --evidence <路径> --source <URL> \
       --note <要点> --used-skills screen-vision,safe-mouse-automation
python scripts/su_index.py --build && python scripts/su_index.py --find <slug>
python scripts/su_invoke.py --app <slug>
python scripts/su_reinforce.py --app <slug> --outcome ok --note <新发现> \
       [--used-skills video-viewer]
python scripts/su_index.py --audit
```

## 注册与发布机制

`register.py` 深度 1 扫完后追加深度 2（`<skill>/private/*`），附属技能因此可被 SMS
索引与派发，条目带 `visibility`/`parent`/`publish`；`--audit` 双向校验：未登记 →
`E_NOT_REGISTERED`，进 git → `E_GIT_LEAK`/`E_NO_GITIGNORE`（均 rc=2）。

## 编辑规则

所有 `.md` ≤ 50 行；悬空链接为 0（`python <Skill_Generator>/scripts/check-links.py --root .`）；
依赖须过 `lint-deps.py`。
