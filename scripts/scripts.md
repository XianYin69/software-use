# scripts（脚本库）

英文名、结构化 JSON 输出、异常统一 rc=2 带 `error` 码，禁止裸 traceback。

| 脚本 | 作用 | 关键参数 |
|---|---|---|
| `su_index.py` | 按前缀扫 `private/` → 生成/校验 `index.json`（YAML 头解析含块标量与流式列表） | `--build` `--find <KEY>` `--audit` `--list` `--register` |
| `su_learn.py` | 真实取证＋检索结论 → 附属技能草稿与经验条目（再学习同步 frontmatter 元数据） | `--app` `--evidence` `--source` `--note` `--title` `--triggers` `--tools` `--confidence` `--used-skills` |
| `su_invoke.py` | 解析附属技能路径并输出调用契约（含依赖通道与 `used_skills`） | `--app` `--digest N` |
| `su_reinforce.py` | 追加结果、uses+1、confidence 限幅、重建索引 | `--app` `--outcome ok|fail` `--note` `--evidence` `--source` `--used-skills` |
| `su_publish.py` | 双仓发布守卫：私有仓 init/提交/合入、两仓可见性校验、公开仓泄漏守卫（默认 dry-run） | `--guard` `--check-visibility` `--init-private` `--commit` `--integrate` `--status` `--remote` `--push` `--authorized-by-user` `--yes` |

## 典型调用

```
python scripts/su_learn.py --app vscode --evidence <截图目录> --source <官方文档URL> --note "..."
python scripts/su_index.py --build
python scripts/su_index.py --find vscode
python scripts/su_invoke.py --app vscode
python scripts/su_reinforce.py --app vscode --outcome ok --note "..."
python scripts/su_index.py --audit
```

## audit 出口（注册＝强制·发布只进私有仓）
`--audit` 失败一律 rc=2 且回结构化 JSON：`E_NOT_REGISTERED`（附属技能在 register.json
无条目，或 `visibility`/`parent`/`publish` 不符，列 id＋原因）、`E_LEAK_TO_PUBLIC`
（本体公开仓 `git ls-files private` 除 `private/.gitkeep` 外有被跟踪项）、`E_NO_GITIGNORE`
（`.gitignore` 缺 `private/*`）、`E_NO_GIT`（git 不可用/非仓库，无法核验跟踪状态）、
`E_NO_REGISTER`（register.json 不存在）、
`E_BAD_REGISTER`（不可解析或缺 `skills` 数组）。register.json 不可用时**不得**
当作「已登记」放行；通过时 `registered[]` 列出全部已正确登记的附属技能。

## su_publish 出口

- `--guard`：`E_LEAK_TO_PUBLIC`（附属技能混入本体公开仓）、`E_NO_GITIGNORE`（未排除
  `private/`）、`E_NO_PRIVATE_REPO`（`private/` 未 init 为独立私有仓）、`E_NO_REPO`。
- `--check-visibility`：`gh repo view --json visibility` 校验本体须 PUBLIC、附属须 PRIVATE，
  不符 `E_VISIBILITY_MISMATCH`；远端未配置回 `E_NO_REMOTE`（不得当作已校验放行）。
- `--init-private` / `--commit` / `--integrate`：默认 dry-run，须 `--yes` 才动盘；`--push`
  另须 `--authorized-by-user`（建仓与推送属远端动作，须用户当轮授权）。

## 约定

- 所有脚本以 `Path(__file__).parents[1]` 定位技能根，不依赖当前工作目录。
- 写盘一律 `.tmp` + `os.replace` 原子替换。
- `used_skills` 记录附属技能用到哪几个依赖技能（只引用 id）：learn/reinforce 均为**只追加**，随 `state.json` 落 `index.json`。
- `su_reinforce.py` 完成后自动调用 `su_index.py --build`，索引不手写。
