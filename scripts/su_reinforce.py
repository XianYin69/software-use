"""su_reinforce.py - 在使用中强化附属技能。

--app <slug> --outcome ok|fail --note ...：把本次真实结果追加进
knowledge/experience.jsonl（只追加、不改历史），uses+1、confidence 限幅增减、
last_used 刷新，久未用自动脱离 stale；随后重建 index.json。
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from su_index import rebuild_index
from su_learn import sync_sources_line, sync_used_line

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "private"
PREFIX = "software_use_only-"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ISO_FMT = "%Y-%m-%dT%H:%M:%S"
STEP_OK = 0.1
STEP_FAIL = -0.15


def now_iso():
    return time.strftime(ISO_FMT)


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def fail(code, detail):
    emit({"ok": False, "error": code, "detail": detail})
    return 2


def clamp(value):
    return round(max(0.0, min(1.0, float(value))), 3)




def main():
    ap = argparse.ArgumentParser(description="追加真实使用结果并更新索引状态")
    ap.add_argument("--app", required=True, help="slug（小写 [a-z0-9._-]）")
    ap.add_argument("--outcome", required=True, choices=["ok", "fail"],
                    help="本次真实结果")
    ap.add_argument("--note", required=True, help="新快捷键/坑/成功路径")
    ap.add_argument("--evidence", default="", help="本次证据，逗号分隔")
    ap.add_argument("--source", default="", help="本次检索来源，逗号分隔")
    ap.add_argument("--used-skills", default="",
                    help="本次用到的依赖技能 id，逗号分隔（只追加不改历史）")
    a = ap.parse_args()
    app = a.app.strip().lower()
    if not SLUG_RE.match(app):
        return fail("E_BAD_SLUG", "slug 非法：%s" % app)
    skill_dir = PRIVATE / (PREFIX + app)
    if not (skill_dir / "SKILL.md").exists():
        return fail("E_NOT_LEARNED",
                    "先 learn 再 reinforce（期望路径 %s）" % skill_dir)
    state_path = skill_dir / "state.json"
    state = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    conf = clamp(float(state.get("confidence", 0.2))
                 + (STEP_OK if a.outcome == "ok" else STEP_FAIL))
    uses = int(state.get("uses", 0)) + 1
    status = "ready" if conf > 0.3 else "draft"
    evidence = [e.strip() for e in a.evidence.split(",") if e.strip()]
    sources = [s.strip() for s in a.source.split(",") if s.strip()]
    used = [u.strip().lower() for u in a.used_skills.split(",")
            if u.strip()]
    ledger = skill_dir / "knowledge" / "experience.jsonl"
    entry = {"ts": now_iso(), "kind": "reinforce", "app": app,
             "outcome": a.outcome, "note": a.note, "evidence": evidence,
             "sources": sources, "confidence": conf, "uses": uses,
             "used_skills": used}
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    merged = list(state.get("evidence", []))
    for item in evidence:
        if item not in merged:
            merged.append(item)
    new_state = {"app": app, "status": status, "confidence": conf,
                 "uses": uses, "last_used": now_iso(),
                 "learned_from": sorted(set(state.get("learned_from", []))
                                        | set(sources)),
                 "used_skills": sorted(set(state.get("used_skills", []))
                                       | set(used)),
                 "evidence": merged}
    tmp = state_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(new_state, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    os.replace(tmp, state_path)
    chlog = skill_dir / "CHANGELOG.md"
    with chlog.open("a", encoding="utf-8") as fh:
        fh.write("- %s reinforce %s conf=%.3f uses=%d :: %s\n"
                 % (new_state["last_used"], a.outcome, conf, uses, a.note))
    sync_sources_line(skill_dir / "SKILL.md", new_state["learned_from"])
    sync_used_line(skill_dir / "SKILL.md", new_state["used_skills"])
    index_rc, index_stderr = rebuild_index()
    emit({"ok": index_rc == 0, "action": "reinforce",
          "name": PREFIX + app, "outcome": a.outcome, "confidence": conf,
          "uses": uses, "status": status, "last_used": new_state["last_used"],
          "ledger": str(ledger), "learned_from": new_state["learned_from"],
          "used_skills": new_state["used_skills"],
          "index_rc": index_rc, "index_stderr": index_stderr or None,
          "error": None if index_rc == 0 else "E_INDEX_STALE"})
    return 0 if index_rc == 0 else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as err:  # noqa: BLE001 - 结构化出口，禁裸 traceback
        sys.exit(fail("E_REINFORCE", "%s: %s" % (type(err).__name__, err)))
