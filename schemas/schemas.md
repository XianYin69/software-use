# schemas（结构定义）

机器可读契约，供 SMS 侧与脚本自检共同参照。

- [index.schema.json](index.schema.json)：`private/index.json`（`su_index.py --build` 产物）。
- [attached_skill.schema.json](attached_skill.schema.json)：附属技能目录与 `state.json` 约束。

## 约定

- 时间一律本地 ISO（`%Y-%m-%dT%H:%M:%S`）。
- `visibility`：附属 frontmatter 的**注册层契约标记**，一律 `PRIVATE`（另带 `parent`/`publish=false`，
  `publish=false`＝不进 hub 同步与公开索引，**不**表示不入 git）；**发布层**的仓库可见性由 GitHub
  仓库属性承载（本体仓 PUBLIC／附属仓 PRIVATE），由 `su_publish.py --check-visibility` 校验。
  本体 frontmatter 只允许 name/description/license/metadata，不得自造 `visibility`。
- `status`：`ready` / `draft` / `stale`。
- `confidence`：0~1 浮点，越界由脚本限幅。

## 校验

`su_index.py --build` 在扫描时即产出 `missing[]`（`E_NO_SKILL_MD` /
`E_BAD_SLUG` / `E_NAME_MISMATCH` / `E_VISIBILITY`），非空即 rc=1；
`--audit` 校验附属技能已登记 register.json（缺失/字段不符 rc=2 `E_NOT_REGISTERED`）且未混入本体公开仓（`E_LEAK_TO_PUBLIC`/`E_NO_GITIGNORE`/`E_NO_PRIVATE_REPO`）。
