# scripts（脚本库）

英文名、结构化 JSON 输出、异常统一 rc=2 带 `error` 码，禁止裸 traceback。

| 脚本 | 作用 | 关键参数 |
|---|---|---|
| `su_index.py` | 按前缀扫 `private/` → 生成/校验 `index.json` | `--build` `--find <KEY>` `--audit` `--list` `--register` |
| `su_learn.py` | 真实取证＋检索结论 → 附属技能草稿与经验条目 | `--app` `--evidence` `--source` `--note` `--title` `--triggers` `--tools` `--confidence` |
| `su_invoke.py` | 解析附属技能路径并输出调用契约 | `--app` `--digest N` |
| `su_reinforce.py` | 追加结果、uses+1、confidence 限幅、重建索引 | `--app` `--outcome ok|fail` `--note` `--evidence` `--source` |

## 典型调用

```
python scripts/su_learn.py --app vscode --evidence <截图目录> --source <官方文档URL> --note "..."
python scripts/su_index.py --build
python scripts/su_index.py --find vscode
python scripts/su_invoke.py --app vscode
python scripts/su_reinforce.py --app vscode --outcome ok --note "..."
python scripts/su_index.py --audit
```

## 约定

- 所有脚本以 `Path(__file__).parents[1]` 定位技能根，不依赖当前工作目录。
- 写盘一律 `.tmp` + `os.replace` 原子替换。
- `su_reinforce.py` 完成后自动调用 `su_index.py --build`，索引不手写。
