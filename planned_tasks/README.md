# planned_tasks（计划任务）

本目录声明**由 SMS 调度器到期执行**的计划任务。技能自身**不得**自行执行计划任务。

## 建立流程

1. 复制 [`template.json`](template.json) 为 `pt-<skill>-<slug>.json`（`<skill>`＝本技能 id，`<slug>`＝任务短名，小写中横线）。
2. 按模板填写字段（字段名**不得改动**——SMS 读取端按同名解析）。
3. `schedule.mode` 三选一：`at`（填 `at`）/ `cron`（填 `cron`）/ `interval`（填 `every_min`）；未用的键保留占位即可。
4. `session.key` 填 `<skill>:<id>`，执行记录挂到该 session 关联链。
5. 由 SMS 调度器读取到期条目并执行，回写 `status` / `last_run` / `runs` / `next_run`。

## 约束

- **一任务一文件**；文件名必须为 `pt-<skill>-<slug>.json`，与内部 `id` 一致。
- **原子写**：先写临时文件（`*.tmp`）再替换目标，禁止就地截断重写。
- `status` 仅取 `pending` / `running` / `done` / `paused` / `failed`。
- 时间一律**本地 ISO**（`YYYY-MM-DDTHH:MM`），不带时区后缀。
- `depends` 为前置任务 id 数组；前置未 `done` 则本任务不触发。
- **删除文件即注销**该任务（无需另行登记）。
- 缓存与运行态文件不得写入技能目录之外的位置；本目录只放任务声明。
- 新增/删除任务须记入 `CHANGELOG.md` 并走 update 审批流。

## 条目 schema（与 SMS 读取端一致）

```json
{"id":"pt-<skill>-<slug>","title":"","skill":"<技能id>","input":"到期要执行的诉求文本",
 "schedule":{"mode":"at|cron|interval","at":"2026-09-30T08:00","cron":"0 8 * * *","every_min":60},
 "session":{"kind":"cron","key":"<skill>:<id>"},"status":"pending",
 "created":"<ISO本地>","next_run":"<ISO本地>","last_run":null,"runs":0,
 "notify":"shell","depends":[]}
```

## 相关

- 生成入口：`branch/流程/初始化/建立计划任务/`（技能生成时由该节点写入本目录）
- 模板脚本：`scripts/init-planned-tasks.py`（默认预览，`--yes` 写盘，已有不覆盖）
