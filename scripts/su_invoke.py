"""su_invoke.py - 附属技能调取器。

--app <slug>：按前缀解析 private/software_use_only-<app>，输出绝对路径＋调用契约
（供 skill/task 派发对等对话执行）；未命中回结构化 E_NOT_LEARNED 并建议 learn。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "private"
INDEX = PRIVATE / "index.json"
PREFIX = "software_use_only-"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def fail(code, detail, extra=None):
    payload = {"ok": False, "error": code, "detail": detail}
    if extra:
        payload.update(extra)
    emit(payload)
    return 2


def load_index():
    if not INDEX.exists():
        return None
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        return {"_error": str(err), "skills": []}


def ledger_digest(skill_dir, limit=5):
    path = skill_dir / "knowledge" / "experience.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows[-limit:]


CONTRACT = {
    "executor": "skill/task 派发的对等对话",
    "read_only_entry": "software-use/scripts/su_invoke.py",
    "steps": [
        "按 skill_path 的 SKILL.md 与 knowledge/experience.jsonl 执行真实操作",
        "真实操作＝调用 safe-mouse-automation 既有通道："
        "desktop_ops（打开/枚举）、app_ops（UIA 控件与菜单）、"
        "virtual_mouse（点击/打字/拖拽）、browser_cdp（浏览器）、"
        "batch_runner（批量）、screenshot_verify（前后截图验证）",
        "每一步先过 safety_gate、开 hud_overlay 会话；"
        "遇 human_gate（验证码/登录墙）立即停止并回报；"
        "SendInput 前台回退（real_input）须先征得用户同意",
        "视频类取证交 video-viewer（probe/extract/bisect/analyze）"
        "定位目标时刻，帧交 screen-vision/camera-vision、"
        "音频交 audio-perception 判读",
        "取证（截图/OCR 交 screen-vision/camera-vision，声音交 audio-perception）",
        "官方文档核对交 webfetch",
        "结束后回写：python scripts/su_reinforce.py --app <app> --outcome ok|fail --note ...",
    ],
    "forbidden": ["自研鼠标键盘模拟或复制依赖技能实现（只引用 id）",
                  "绕过 safe-mouse-automation 的 safety_gate/"
                  "human_gate 直接操作",
                  "把附属技能内容复制进公开文档",
                  "改写 experience.jsonl 历史条目",
                  "把 private/ 内容 git add/commit/push 或推到 GitHub（内容涉侵权）",
                  "手写 register.json（登记由 register.py 深度 2 扫描完成）"],
    "registration": "附属技能必须出现在 SMS register.json"
                     "（visibility=PRIVATE·parent=software-use·publish=false），"
                     "由 register.py --write 扫描登记；"
                     "注册＝强制（publish=false 不进 hub/公开索引）；发布＝只进 private/ 独立私有仓（GitHub PRIVATE）。",
}


def resolve(app):
    skill_dir = PRIVATE / (PREFIX + app)
    md = skill_dir / "SKILL.md"
    row = None
    doc = load_index()
    for item in (doc or {}).get("skills", []):
        if item.get("app") == app:
            row = item
            break
    return skill_dir, md, row


def main():
    ap = argparse.ArgumentParser(description="按前缀调取私有附属技能并输出调用契约")
    ap.add_argument("--app", required=True, help="slug（小写 [a-z0-9._-]）")
    ap.add_argument("--digest", type=int, default=5, help="附带最近 N 条经验")
    a = ap.parse_args()
    app = a.app.strip().lower()
    if not SLUG_RE.match(app):
        return fail("E_BAD_SLUG", "slug 必须为小写 [a-z0-9._-]+：%s" % app)
    skill_dir, md, row = resolve(app)
    if not md.exists():
        return fail("E_NOT_LEARNED", "未学习该软件的私有附属技能", {
            "name": PREFIX + app, "expected_path": str(skill_dir),
            "suggest": "python scripts/su_learn.py --app %s --evidence <证据> "
                       "--source <url> --note <要点>" % app})
    contract = dict(CONTRACT)
    contract.update({"app": app, "name": PREFIX + app,
                     "skill_path": str(skill_dir),
                     "visibility": "PRIVATE", "parent": "software-use",
                     "status": (row or {}).get("status", "draft"),
                     "confidence": (row or {}).get("confidence", 0.2),
                     "uses": (row or {}).get("uses", 0),
                     "used_skills": (row or {}).get("used_skills", []),
                     "recent_experience": ledger_digest(skill_dir, a.digest)})
    emit({"ok": True, "action": "invoke", **contract})
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as err:  # noqa: BLE001 - 结构化出口，禁裸 traceback
        sys.exit(fail("E_INVOKE", "%s: %s" % (type(err).__name__, err)))
