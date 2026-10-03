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


BLOCK_RE = re.compile(r"^[|>][+-]?\d*$")


def flow_list(val):
    """行内流式列表 ["a", "b"] / [] → 干净字符串数组。"""
    inner = val[1:-1].strip()
    if not inner:
        return []
    try:
        parsed = json.loads(val)
    except ValueError:
        parsed = None
    if isinstance(parsed, list):
        return [str(x).strip() for x in parsed if str(x).strip()]
    out = []
    for part in inner.split(","):
        part = part.strip().strip("'\"")
        if part:
            out.append(part)
    return out


def block_scalar(lines, idx, n):
    """收集块标量的所有更深缩进行，折叠为单行（换行→空格）。"""
    parts = []
    while idx < n:
        nxt = lines[idx]
        if nxt.strip() == "---":
            break
        if nxt.strip() and not nxt[:1].isspace():
            break
        parts.append(nxt.strip())
        idx += 1
    return " ".join(p for p in parts if p), idx


def clean_value(val):
    """去行内注释与包裹引号（保守：仅切空白后的 #）。"""
    if val.startswith("#"):
        return ""
    return val.split(" #", 1)[0].strip().strip("'\"")


def read_frontmatter(skill_md):
    """YAML 头解析：key: value、块标量 > | >- |-、行内流式列表、顶层列表项；
    嵌套映射（如 metadata: 下 category:）忽略且不污染上一个 key。"""
    text = skill_md.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta, key = {}, None
    idx, n = 1, len(lines)
    while idx < n:
        raw = lines[idx]
        if raw.strip() == "---":
            break
        if not raw.strip() or raw.lstrip().startswith("#"):
            idx += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent:
            stripped = raw.lstrip()
            if stripped.startswith("- ") and key:
                item = stripped[2:].strip().strip("'\"")
                cur = meta.get(key)
                cur = cur if isinstance(cur, list) else []
                cur.append(item)
                meta[key] = cur
            elif ":" in raw:
                key = None
            idx += 1
            continue
        if ":" not in raw:
            idx += 1
            continue
        key, val = raw.split(":", 1)
        key = key.strip()
        val = clean_value(val.strip())
        if BLOCK_RE.match(val):
            meta[key], idx = block_scalar(lines, idx + 1, n)
            continue
        if val.startswith("[") and val.endswith("]"):
            meta[key] = flow_list(val)
            idx += 1
            continue
        if val.startswith("{") and val.endswith("}"):
            meta[key] = []
            idx += 1
            continue
        meta[key] = val if val else []
        idx += 1
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
    """反查 SMS register.json：任何 software_use_only-* 出现即泄漏。
    register 缺失/损坏 → 结构化错误码（E_NO_REGISTER / E_BAD_REGISTER），
    checked=False 且由调用方回 rc=2，绝不静默通过。"""
    path = Path(register_path)
    if not path.exists():
        return {"checked": False, "register": str(path), "leaks": [],
                "error": "E_NO_REGISTER",
                "detail": "register.json 不存在，无法反查泄漏：%s" % path}
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, ValueError) as err:
        return {"checked": False, "register": str(path), "leaks": [],
                "error": "E_BAD_REGISTER",
                "detail": "register.json 不可解析：%s" % err}
    if not isinstance(doc, dict) or not isinstance(doc.get("skills"), list):
        return {"checked": False, "register": str(path), "leaks": [],
                "error": "E_BAD_REGISTER",
                "detail": "register.json 缺 skills 数组，格式不符"}
    leaks = []
    for row in doc["skills"]:
        if not isinstance(row, dict):
            continue
        ident = " ".join(str(row.get(k, "")) for k in
                         ("id", "name", "install_path")).lower()
        if PREFIX in ident or "\\private\\" in ident or "/private/" in ident:
            leaks.append(row.get("id") or row.get("name"))
    return {"checked": True, "register": str(path), "leaks": leaks,
            "error": "E_LEAK" if leaks else None,
            "detail": "反查 register.json 是否混入附属技能"}


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
        rc = 2 if res["error"] else 0
        emit({"ok": rc == 0, "action": "audit", "prefix": PREFIX,
              "indexed": doc["count"], "missing": missing, **res})
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
