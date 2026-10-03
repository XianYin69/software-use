"""su_index.py - 私有附属技能索引器。

按固定前缀 software_use_only- 扫描 private/（深度 2），生成/校验 index.json；
--audit 校验附属技能已登记进 SMS register.json（注册＝强制），并校验其未混入本体公开仓（混入公开仓＝泄漏）；
--find 关键词检索。全部输出结构化 JSON。
"""
import argparse
import json
import os
import re
import subprocess
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
            "used_skills": state.get("used_skills", []),
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


def rebuild_index():
    """learn/reinforce 写盘后共用的索引重建（唯一实现，勿复制第二份）。

    子进程跑 `su_index.py --build`，返回 (rc, stderr)：rc=0 索引已刷新；
    rc!=0 即 index.json 陈旧，调用方须回结构化错误码，不得静默。
    """
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "su_index.py"), "--build"],
        capture_output=True, text=True)
    return proc.returncode, (proc.stderr or "").strip()[:200]


def git_tracked_private():
    """`git -C <software-use> ls-files private` → 被跟踪清单；
    git 不可用/非仓库 → None（调用方须判为 E_NO_GIT，不得静默通过）。"""
    try:
        proc = subprocess.run(["git", "-C", str(ROOT), "ls-files", "private"],
                              capture_output=True, text=True)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return [ln.strip().replace("\\", "/")
            for ln in (proc.stdout or "").splitlines() if ln.strip()]


def gitignore_ok():
    """`.gitignore` 是否含 `private/*`（附属技能永不入库的第一道闸）。"""
    path = ROOT / ".gitignore"
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if line.strip() == "private/*":
            return True
    return False


def _bad(register_path, code, detail):
    return {"checked": False, "register": str(register_path), "registered": [],
            "unregistered": [], "errors": [code], "error": code, "detail": detail}


def audit(register_path, rows=None):
    """契约反转：附属技能**必须**登记进 SMS register.json（visibility=PRIVATE、
    parent=software-use）——缺失或不符 → E_NOT_REGISTERED；进 git 才是泄漏 →
    E_LEAK_TO_PUBLIC（公开仓 ls-files private 除 .gitkeep 外有项）/
    E_NO_GITIGNORE（缺 private/*）；private/ 未 init 为独立私有仓 → E_NO_PRIVATE_REPO。
    register 缺失/损坏仍回 E_NO_REGISTER / E_BAD_REGISTER，checked=False 由调用方 rc=2。"""
    path = Path(register_path)
    if rows is None:
        rows, _ = scan()
    if not path.exists():
        return _bad(path, "E_NO_REGISTER",
                    "register.json 不存在，无法确认附属技能已登记：%s" % path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, ValueError) as err:
        return _bad(path, "E_BAD_REGISTER", "register.json 不可解析：%s" % err)
    if not isinstance(doc, dict) or not isinstance(doc.get("skills"), list):
        return _bad(path, "E_BAD_REGISTER", "register.json 缺 skills 数组，格式不符")
    by_id = {str(r.get("id") or r.get("name")): r for r in doc["skills"]
             if isinstance(r, dict)}
    registered, unregistered = [], []
    for row in rows:
        ent = by_id.get(row["name"])
        if ent is None:
            unregistered.append({"id": row["name"], "reason": "register.json 无条目"})
            continue
        why = []
        if str(ent.get("visibility", "")).upper() != "PRIVATE":
            why.append("visibility=%r 应为 PRIVATE" % ent.get("visibility"))
        if ent.get("parent") != PARENT:
            why.append("parent=%r 应为 %r" % (ent.get("parent"), PARENT))
        if ent.get("publish") is not False:
            why.append("publish=%r 应为 false（不进 hub 同步与公开索引）" % ent.get("publish"))
        if why:
            unregistered.append({"id": row["name"], "reason": "；".join(why)})
        else:
            registered.append(row["name"])
    errors = []
    detail = []
    if unregistered:
        errors.append("E_NOT_REGISTERED")
        detail.append("附属技能未正确登记：%s" % json.dumps(unregistered,
                                                            ensure_ascii=False))
    tracked = git_tracked_private()
    if tracked is None:
        errors.append("E_NO_GIT")
        detail.append("git 不可用/非仓库，无法核验 private/ 未被跟踪——不得当作无泄漏放行")
    else:
        leaked = [f for f in tracked if f != "private/.gitkeep"]
        if leaked:
            errors.append("E_LEAK_TO_PUBLIC")
            detail.append("附属技能混入本体公开仓：%s" % ", ".join(leaked))
    if not (PRIVATE / ".git").exists():
        errors.append("E_NO_PRIVATE_REPO")
        detail.append("private/ 未 init 为独立私有仓，附属技能尚未入库"
                      "（跑 su_publish.py --init-private --yes）")
    if not gitignore_ok():
        errors.append("E_NO_GITIGNORE")
        detail.append(".gitignore 缺 `private/*`，附属技能会随提交进入本体公开仓")
    detail.append("注册＝强制（publish=false 不进 hub/公开索引）；发布＝进 private/ 独立"
                  "私有仓（GitHub PRIVATE），禁止混入本体公开仓")
    return {"checked": True, "register": str(path), "registered": registered,
            "unregistered": unregistered, "git_tracked": tracked,
            "errors": errors, "error": errors[0] if errors else None,
            "detail": "；".join(detail)}


def main():
    ap = argparse.ArgumentParser(
        description="私有附属技能索引：按前缀 software_use_only- 扫 private/")
    ap.add_argument("--build", action="store_true", help="扫描并生成 index.json")
    ap.add_argument("--find", metavar="KEY", help="按 name/app/触发词检索")
    ap.add_argument("--audit", action="store_true",
                    help="校验附属技能已登记 register.json（注册强制·发布只进私有仓）")
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
