"""su_index.py - 私有附属技能索引器。

按固定前缀 software_use_only- 扫描 private/（深度 2），生成/校验 index.json；
--audit 反查 SMS register.json 防泄漏；--find 关键词检索。全部输出结构化 JSON。
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "private"
INDEX = PRIVATE / "index.json"
PREFIX = "software_use_only-"
PARENT = "software-use"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ISO_FMT = "%Y-%m-%dT%H:%M:%S"
DEFAULT_REGISTER = Path(
    r"C:\Users\User\AppData\Local\SMS\registry\register.json")


def now_iso():
    return time.strftime(ISO_FMT)


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def fail(code, detail):
    emit({"ok": False, "error": code, "detail": detail})
    return 2


def read_frontmatter(skill_md):
    """极简 YAML 头解析（仅 key: value / 列表项），避免引入外部依赖。"""
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta, key = {}, None
    for raw in lines[1:]:
        if raw.strip() == "---":
            break
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1] in (" ", "\t") and raw.lstrip().startswith("- "):
            if key:
                meta.setdefault(key, []).append(raw.lstrip()[2:].strip().strip("'\""))
            continue
        if ":" in raw and not raw.startswith(" "):
            key, val = raw.split(":", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            meta[key] = val if val else []
    return meta


def as_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [str(value)]


def load_state(skill_dir):
    path = skill_dir / "state.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        return {"_state_error": str(err)}


def scan():
    rows, missing = [], []
    if not PRIVATE.exists():
        return rows, missing
    for entry in sorted(PRIVATE.iterdir()):
        if not entry.is_dir() or not entry.name.startswith(PREFIX):
            continue
        slug = entry.name[len(PREFIX):]
        md = entry / "SKILL.md"
        if not md.exists():
            missing.append({"name": entry.name, "reason": "E_NO_SKILL_MD"})
            continue
        fm = read_frontmatter(md)
        state = load_state(entry)
        if not SLUG_RE.match(slug):
            missing.append({"name": entry.name, "reason": "E_BAD_SLUG"})
            continue
        if fm.get("name") != entry.name:
            missing.append({"name": entry.name, "reason": "E_NAME_MISMATCH"})
        if fm.get("visibility", "PRIVATE").upper() != "PRIVATE":
            missing.append({"name": entry.name, "reason": "E_VISIBILITY"})
        rows.append({
            "name": entry.name,
            "app": slug,
            "path": str(entry),
            "title": fm.get("title") or entry.name,
            "version": fm.get("version", "0.1.0"),
            "summary": fm.get("description", "") or fm.get("summary", ""),
            "triggers": as_list(fm.get("triggers")),
            "tools": as_list(fm.get("tools")),
            "visibility": "PRIVATE",
            "parent": fm.get("parent", PARENT),
            "confidence": float(state.get("confidence", 0.2)),
            "uses": int(state.get("uses", 0)),
            "last_used": state.get("last_used"),
            "learned_from": state.get("learned_from", []),
            "evidence": state.get("evidence", []),
            "status": state.get("status", "draft"),
        })
    return rows, missing


STALE_DAYS = 90


def touch_status(row):
    """draft→ready 升格、久未用置 stale（只改状态位，不动历史）。"""
    if row["status"] == "draft" and row["confidence"] > 0.3:
        row["status"] = "ready"
    last = row.get("last_used") or ""
    if last and row["status"] == "ready":
        try:
            used = time.mktime(time.strptime(last[:19], ISO_FMT))
            if (time.time() - used) / 86400.0 > STALE_DAYS:
                row["status"] = "stale"
        except ValueError:
            pass
    return row


def build(write=True):
    rows, missing = scan()
    rows = [touch_status(r) for r in rows]
    doc = {"version": "1.0", "generated_at": now_iso(), "prefix": PREFIX,
           "count": len(rows), "skills": rows, "missing": missing}
    if write:
        PRIVATE.mkdir(parents=True, exist_ok=True)
        tmp = INDEX.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        os.replace(tmp, INDEX)
    return doc, missing


def audit(register_path):
    """反查 SMS register.json：任何 software_use_only-* 出现即泄漏。"""
    leaks = []
    path = Path(register_path)
    if not path.exists():
        return {"checked": False, "register": str(path), "leaks": leaks,
                "note": "register.json 不存在，视为无泄漏"}
    try:
        doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError) as err:
        return {"checked": False, "register": str(path), "leaks": [],
                "note": "register.json 不可读: %s" % err}
    for row in doc.get("skills", []):
        ident = " ".join([str(row.get("id", "")), str(row.get("name", "")),
                          str(row.get("install_path", ""))]).lower()
        if PREFIX in ident or "\\private\\" in ident:
            leaks.append(row.get("id") or row.get("name"))
    return {"checked": True, "register": str(path), "leaks": leaks,
            "note": "反查 register.json 是否混入附属技能"}


def main():
    ap = argparse.ArgumentParser(
        description="私有附属技能索引：按前缀 software_use_only- 扫 private/")
    ap.add_argument("--build", action="store_true", help="扫描并生成 index.json")
    ap.add_argument("--find", metavar="KEY", help="按 name/app/触发词检索")
    ap.add_argument("--audit", action="store_true", help="反查 register.json 防泄漏")
    ap.add_argument("--list", action="store_true", help="列出全部索引条目")
    ap.add_argument("--register", default=str(DEFAULT_REGISTER),
                    help="register.json 路径（默认 SMS registry）")
    a = ap.parse_args()
    if a.audit:
        doc, missing = build(write=False)
        res = audit(a.register)
        rc = 2 if res["leaks"] else 0
        emit({"ok": rc == 0, "action": "audit", "prefix": PREFIX,
              "indexed": doc["count"], "missing": missing,
              "error": "E_LEAK" if res["leaks"] else None, **res})
        return rc
    if a.find:
        doc, _ = build(write=False)
        key = a.find.lower()
        hits = [s for s in doc["skills"] if key in s["name"].lower()
                or key in s["app"].lower()
                or any(key in t.lower() for t in s["triggers"])]
        emit({"ok": bool(hits), "action": "find", "query": a.find,
              "prefix": PREFIX, "hits": hits,
              "error": None if hits else "E_NOT_LEARNED",
              "hint": None if hits else "先跑 su_learn.py --app <slug> 取证学习"})
        return 0 if hits else 2
    if a.list:
        doc, _ = build(write=False)
        emit({"ok": True, "action": "list", "count": doc["count"],
              "skills": doc["skills"]})
        return 0
    doc, missing = build()
    emit({"ok": not missing, "action": "build", "index": str(INDEX),
          "count": doc["count"], "missing": missing,
          "skills": [s["name"] for s in doc["skills"]]})
    return 0 if not missing else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as err:  # noqa: BLE001 - 统一结构化出口，禁裸 traceback
        sys.exit(fail("E_INDEX", "%s: %s" % (type(err).__name__, err)))
