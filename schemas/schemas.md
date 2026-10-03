# schemas（结构定义）

机器可读契约，供 SMS 侧与脚本自检共同参照。

- [index.schema.json](index.schema.json)：`private/index.json`（`su_index.py --build` 产物）。
- [attached_skill.schema.json](attached_skill.schema.json)：附属技能目录与 `state.json` 约束。

## 约定

- 时间一律本地 ISO（`%Y-%m-%dT%H:%M:%S`）。
- `visibility`：本体 `PUBLIC`，附属一律 `PRIVATE`。
- `status`：`ready` / `draft` / `stale`。
- `confidence`：0~1 浮点，越界由脚本限幅。

## 校验

`su_index.py --build` 在扫描时即产出 `missing[]`（`E_NO_SKILL_MD` /
`E_BAD_SLUG` / `E_NAME_MISMATCH` / `E_VISIBILITY`），非空即 rc=1；
`--audit` 反查 register.json，泄漏 rc=2 `E_LEAK`。
