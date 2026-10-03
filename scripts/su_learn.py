"""su_learn.py - 真实使用取证 → 私有附属技能草稿。

--app <slug> --evidence <文件或目录> --source <url>：把真实使用证据与检索结论
汇成经验条目（append-only），并在 private/ 落 software_use_only-<app> 草稿。
无证据不得声称已学会：evidence 为空 → status=draft 且 confidence ≤ 0.3。
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from su_index import rebuild_index

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "private"
PREFIX = "software_use_only-"
PARENT = "software-use"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ISO_FMT = "%Y-%m-%dT%H:%M:%S"
MAX_DRAFT_CONF = 0.3


def now_iso():
    return time.strftime(ISO_FMT)


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def fail(code, detail):
    emit({"ok": False, "error": code, "detail": detail})
    return 2


def clamp(value):
    return max(0.0, min(1.0, float(value)))


def collect_evidence(raw):
    """证据归一：文件/目录 → 相对可溯的条目列表。"""
    items = []
    for token in [t.strip() for t in raw.split(",") if t.strip()]:
        path = Path(token)
        if path.is_dir():
            for f in sorted(path.rglob("*")):
                if f.is_file():
                    items.append(str(f))
        elif path.is_file():
            items.append(str(path))
        else:
            items.append(token)
    return items


SKILL_TMPL = """---
name: {name}
description: >
  {app} 的私有操作经验附属技能（不公开）：由 software-use 在真实使用中取证学习，
  仅供 software-use 经前缀索引调取与强化。
license: MIT
visibility: PRIVATE
parent: software-use
version: 0.1.0
title: {title}
triggers: {triggers}
tools: {tools}
metadata:
  category: meta
---

# {name}

使用 `software-use` 来完成用户请求（本技能为私有附属，不直接对外调用）。

## 定位

- 目标软件：{app}
- 学习来源：{sources}
- 经验台账：[`knowledge/experience.jsonl`](knowledge/experience.jsonl)（只追加）
- 状态：{status}（confidence {conf} / uses {uses}）

## 使用

1. 由 software-use 的 `su_index.py --find {app}` 命中后，经 `su_invoke.py` 取调用契约。
2. 执行中产生的新快捷键/坑/成功路径，用 `su_reinforce.py --app {app}` 回写。

## 约束

- 见 [resistance/私有约束.md](resistance/私有约束.md)：不外泄、不改写历史。
"""

RES_TMPL = """# 私有约束（{name}）

1. 本技能位于 software-use/private/ 下，深度 2，结构上不得进 register.json。
2. 不得把本技能 id 或内容复制进 software-use 的公开文档/示例。
3. knowledge/experience.jsonl 只追加，禁止改写或删除历史条目。
4. 无真实证据的条目 status=draft，confidence ≤ 0.3。
"""


def sync_frontmatter(md, title, triggers, tools):
    """再学习时同步 frontmatter 的 title/triggers/tools（只改元数据行，
    不动正文与历史；空值不覆盖已有值）。"""
    text = md.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines))
                if lines[i].strip() == "---"), None)
    if end is None:
        return False
    updates = {"title": title or "",
               "triggers": json.dumps(triggers, ensure_ascii=False)
               if triggers else "",
               "tools": json.dumps(tools, ensure_ascii=False)
               if tools else ""}
    changed = False
    for i in range(1, end):
        key, sep, _ = lines[i].partition(":")
        if not sep:
            continue
        name = key.strip()
        if name in updates and updates[name]:
            new_line = "%s: %s" % (name, updates[name])
            if new_line != lines[i].rstrip():
                lines[i] = new_line
                changed = True
    if changed:
        tmp = md.with_suffix(".md.tmp")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(tmp, md)
    return changed


SOURCES_PREFIX = "- 学习来源："


def sync_sources_line(md, sources):
    """重写附属技能 SKILL.md 的「- 学习来源：」单行（learn/reinforce 共用）。

    只动这一行：正文其余内容与 knowledge/experience.jsonl 一律不碰
    （红线3 只追加不改历史）。值取合并后的 learned_from，渲染为 JSON 数组。
    """
    if not md.exists():
        return False
    lines = md.read_text(encoding="utf-8-sig").splitlines()
    new_line = SOURCES_PREFIX + json.dumps(sources, ensure_ascii=False)
    changed = False
    for i, line in enumerate(lines):
        if line.startswith(SOURCES_PREFIX):
            if line.rstrip() != new_line:
                lines[i] = new_line
                changed = True
            break
    if changed:
        tmp = md.with_suffix(".md.tmp")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(tmp, md)
    return changed


def write_attached(skill_dir, app, title, triggers, tools, sources,
                   status, conf, uses):
    name = PREFIX + app
    (skill_dir / "knowledge").mkdir(parents=True, exist_ok=True)
    (skill_dir / "resistance").mkdir(parents=True, exist_ok=True)
    (skill_dir / "planned_tasks").mkdir(parents=True, exist_ok=True)
    md = skill_dir / "SKILL.md"
    created = not md.exists()
    if created:
        md.write_text(SKILL_TMPL.format(
            name=name, app=app, title=title or app,
            triggers=json.dumps(triggers, ensure_ascii=False),
            tools=json.dumps(tools, ensure_ascii=False),
            sources=json.dumps(sources, ensure_ascii=False),
            status=status, conf=conf, uses=uses), encoding="utf-8")
        (skill_dir / "resistance" / "私有约束.md").write_text(
            RES_TMPL.format(name=name), encoding="utf-8")
        (skill_dir / "CHANGELOG.md").write_text(
            "# CHANGELOG\n\n- %s init by su_learn (app=%s)\n"
            % (now_iso(), app), encoding="utf-8")
    else:
        sync_frontmatter(md, title, triggers, tools)
    return created


def append_entry(path, entry):
    """经验台账只追加（可审计、可回溯）。"""
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(
        description="真实使用取证 + 网络检索 → 私有附属技能经验条目")
    ap.add_argument("--app", required=True, help="slug（小写 [a-z0-9._-]）")
    ap.add_argument("--evidence", default="", help="证据文件或目录，逗号分隔")
    ap.add_argument("--source", default="", help="检索来源 URL，逗号分隔")
    ap.add_argument("--note", default="", help="本次学到的操作要点")
    ap.add_argument("--title", default="", help="人类可读标题")
    ap.add_argument("--triggers", default="", help="触发词，逗号分隔")
    ap.add_argument("--tools", default="", help="涉及工具/命令，逗号分隔")
    ap.add_argument("--confidence", type=float, default=None,
                    help="自评置信度 0~1（无证据强制 ≤0.3）")
    a = ap.parse_args()
    app = a.app.strip().lower()
    if not SLUG_RE.match(app):
        return fail("E_BAD_SLUG", "slug 必须为小写 [a-z0-9._-]+：%s" % app)
    evidence = collect_evidence(a.evidence)
    sources = [s.strip() for s in a.source.split(",") if s.strip()]
    if not a.note and not evidence:
        return fail("E_NO_EVIDENCE", "至少提供 --note 或 --evidence 之一")
    status = "ready" if evidence else "draft"
    conf = clamp(a.confidence if a.confidence is not None
                 else (0.6 if evidence else 0.2))
    if not evidence:
        conf = min(conf, MAX_DRAFT_CONF)
    skill_dir = PRIVATE / (PREFIX + app)
    skill_dir.mkdir(parents=True, exist_ok=True)
    created = write_attached(
        skill_dir, app, a.title,
        [t.strip() for t in a.triggers.split(",") if t.strip()],
        [t.strip() for t in a.tools.split(",") if t.strip()],
        sources, status, conf, 0)
    ledger = skill_dir / "knowledge" / "experience.jsonl"
    append_entry(ledger, {"ts": now_iso(), "kind": "learn", "app": app,
                          "note": a.note, "evidence": evidence,
                          "sources": sources, "confidence": conf,
                          "status": status})
    state_path = skill_dir / "state.json"
    state = {"app": app, "status": status, "confidence": conf, "uses": 0,
             "last_used": None, "learned_from": sources, "evidence": evidence}
    if state_path.exists():
        old = json.loads(state_path.read_text(encoding="utf-8"))
        merged = list(old.get("evidence", []))
        for item in evidence:
            if item not in merged:
                merged.append(item)
        state["evidence"] = merged
        state["uses"] = int(old.get("uses", 0))
        state["last_used"] = old.get("last_used")
        state["learned_from"] = sorted(set(old.get("learned_from", []))
                                       | set(sources))
    tmp = state_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    os.replace(tmp, state_path)
    sync_sources_line(skill_dir / "SKILL.md", state["learned_from"])
    index_rc, index_stderr = rebuild_index()
    payload = {"ok": index_rc == 0, "action": "learn", "name": PREFIX + app,
               "path": str(skill_dir), "created": created, "status": status,
               "confidence": conf, "evidence_count": len(evidence),
               "ledger": str(ledger), "learned_from": state["learned_from"],
               "index_rc": index_rc, "index_stderr": index_stderr or None}
    if index_rc != 0:
        payload["error"] = "E_INDEX_STALE"
        payload["detail"] = ("附属技能已写盘但 index.json 未刷新（rc=%s），"
                             "索引仍陈旧" % index_rc)
        emit(payload)
        return 2
    emit(payload)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as err:  # noqa: BLE001 - 结构化出口，禁裸 traceback
        sys.exit(fail("E_LEARN", "%s: %s" % (type(err).__name__, err)))
