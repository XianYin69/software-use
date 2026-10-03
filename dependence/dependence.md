# dependence（依赖声明）

声明本技能包依赖的技能包/软件/仓库地址：每行一条 `名称 | 类型 | 来源`，类型为 skill|software|repo。

**每条依赖必须附原始链接**：机器可读清单 `deps.json`，条目字段 `name / source_url / license / version / install / checked_at`；`source_url` 为 GitHub/GitLab/官方仓库或发布页原始链接（本地技能用 `local://<skill-id>`）。缺 `source_url` 即判不合格，`python scripts/lint-deps.py` 报错退出。SMS 据该链接联网检索/下载到技能目录（须网络授权）。

SMS 安装时本目录条目与本体接受同样检查与净化（trust 标注·未审/隔离拒装·仓库下载须网络授权·见 skill_manage_system pkg_deps.py）。
