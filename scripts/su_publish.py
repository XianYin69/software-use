"""su_publish.py — 双仓发布守卫：附属私有仓提交 / 两仓可见性校验 / 公开仓泄漏守卫。

模型：本体仓 `software-use` → GitHub PUBLIC；`private/` 是**独立附属仓的工作树**
（自带 .git 与 remote）→ GitHub PRIVATE，附属技能照走 功能分支→dev→main 并可推送。
「不公开」＝仓库可见性 PRIVATE，**不是不入库**；可见性不写进 frontmatter（重生成即抹），
由本脚本判定＋文档承载。默认 dry-run，写操作须 --yes；推送属远端动作须用户当轮授权。
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
PREFIX = "software_use_only-"
KEEP = "private/.gitkeep"
PUBLIC_EXPECT = "PUBLIC"
PRIVATE_EXPECT = "PRIVATE"
ISO_FMT = "%Y-%m-%dT%H:%M:%S"
PRIVATE_GITIGNORE = """# 临时产物
tmp/
*.tmp
*.json.tmp
__pycache__/
*.pyc
# index.json 由 su_index.py --build 生成（含本机绝对路径，不入库）
index.json
# IDE
.idea/
.vscode/
.kilo/
"""


def now_iso():
    return time.strftime(ISO_FMT)


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def fail(code, detail, **extra):
    out = {"ok": False, "error": code, "detail": detail, "at": now_iso()}
    out.update(extra)
    emit(out)
    sys.exit(2)


def run(cmd, cwd=None):
    try:
        p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError) as err:
        return 127, "%s 不可用：%s" % (cmd[0], err)
    return p.returncode, (p.stdout or "").strip()


def git(args, cwd):
    return run(["git"] + list(args), cwd)


def gh(args):
    return run(["gh"] + list(args))


def listed(out):
    return [x.strip() for x in out.replace("\0", "\n").splitlines() if x.strip()]


def repo_slug(path, default):
    """从 origin URL 解析 <owner>/<repo>；无 remote → (None, default)。"""
    rc, out = git(["remote", "get-url", "origin"], path)
    if rc != 0 or not out:
        return None, default
    m = re.search(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?/?$", out)
    return (m.group(1) + "/" + m.group(2), default) if m else (None, default)


def guard():
    """公开仓守卫：附属技能出现在本体仓索引/暂存区 → E_LEAK_TO_PUBLIC（rc=2）。"""
    if git(["rev-parse", "--git-dir"], ROOT)[0] != 0:
        fail("E_NO_REPO", "本体仓未 git init，无法守卫：%s" % ROOT)
    tracked = listed(git(["ls-files", "private"], ROOT)[1])
    staged = listed(git(["diff", "--cached", "--name-only", "--", "private"], ROOT)[1])
    hits = sorted({p for p in tracked + staged if p.replace("\\", "/") != KEEP})
    ignored = git(["check-ignore", "-q", "private/probe"], ROOT)[0] == 0
    in_repo = (PRIVATE / ".git").exists()
    out = {"ok": not hits and ignored and in_repo, "action": "guard",
           "public_tracked_private": hits, "private_ignored": ignored,
           "private_is_repo": in_repo, "at": now_iso()}
    if hits:
        out["error"] = "E_LEAK_TO_PUBLIC"
        out["detail"] = "附属技能混入本体公开仓，须 git rm --cached 回退后再提交"
        emit(out)
        sys.exit(2)
    if not ignored:
        out["error"] = "E_NO_GITIGNORE"
        out["detail"] = ".gitignore 未排除 private/，私有工作树会被误加入公开仓"
        emit(out)
        sys.exit(2)
    if not in_repo:
        out["error"] = "E_NO_PRIVATE_REPO"
        out["detail"] = "private/ 未 init 为独立私有仓——附属技能尚未入库（--init-private）"
        emit(out)
        sys.exit(2)
    out["detail"] = "公开仓 0 条 private 泄漏；private/ 是独立私有仓工作树"
    emit(out)
    sys.exit(0)


def check_visibility():
    """两仓可见性：本体须 PUBLIC、附属须 PRIVATE。远端未配置 → E_NO_REMOTE。"""
    pub = repo_slug(ROOT, "software-use")[0]
    pri = repo_slug(PRIVATE, "software-use-private")[0]
    if not pub or not pri:
        fail("E_NO_REMOTE", "远端未配置（建仓与推送须用户当轮授权），无法校验可见性",
             public=pub, private=pri, action="check-visibility")
    res, bad = [], []
    for want, slug in ((PUBLIC_EXPECT, pub), (PRIVATE_EXPECT, pri)):
        rc, out = gh(["repo", "view", slug, "--json", "visibility", "--jq", ".visibility"])
        got = (out or "").upper() if rc == 0 else None
        res.append({"repo": slug, "expect": want, "got": got or "UNKNOWN",
                    "raw": (out or "")[:120]})
        if got != want:
            bad.append(slug)
    out = {"ok": not bad, "action": "check-visibility", "repos": res, "at": now_iso()}
    if bad:
        out["error"] = "E_VISIBILITY_MISMATCH"
        out["detail"] = "可见性不符双仓模型：%s（附属仓误公开不可撤回，立即改仓库属性）" % ", ".join(bad)
        emit(out)
        sys.exit(2)
    emit(out)


def commit_tolerant(msg):
    """add + commit；无变更不算失败（幂等）。"""
    git(["add", "-A"], PRIVATE)
    rc, out = git(["commit", "-m", msg], PRIVATE)
    if rc != 0 and "nothing to commit" not in out:
        fail("E_COMMIT", "私有仓提交失败：%s" % out)
    return {"rc": rc, "out": out[:200]}


def run_seq(seq):
    log = []
    for args in seq:
        rc, out = git(args, PRIVATE)
        log.append({"cmd": "git " + " ".join(args), "rc": rc, "out": out[:160]})
        if rc != 0:
            return log, (args, out)
    return log, None


def init_flow(dry, remote):
    """private/ 建成独立私有仓工作树：init + .gitignore + 提交 + 配 remote（不推送）。"""
    need_init = not (PRIVATE / ".git").exists()
    need_gi = not (PRIVATE / ".gitignore").exists()
    if dry:
        emit({"ok": True, "action": "init-private", "dry_run": True,
              "planned": {"init": need_init, "gitignore": need_gi, "remote": remote},
              "detail": "未写盘：加 --yes 执行；推送与 gh repo create 须用户当轮授权"})
        return
    if need_gi:
        tmp = PRIVATE / ".gitignore.tmp"
        tmp.write_text(PRIVATE_GITIGNORE, encoding="utf-8")
        os.replace(tmp, PRIVATE / ".gitignore")
    if need_init:
        rc, out = git(["init", "-b", "main"], PRIVATE)
        if rc != 0:
            fail("E_INIT", "私有仓 init 失败：%s" % out)
    commit_tolerant("chore(private): init attached-skill repo (GitHub PRIVATE)")
    if remote:
        if git(["remote", "add", "origin", remote], PRIVATE)[0] != 0:
            git(["remote", "set-url", "origin", remote], PRIVATE)
    emit({"ok": True, "action": "init-private", "dry_run": False,
          "init": need_init, "gitignore": need_gi, "remote": remote or None,
          "at": now_iso()})


def commit_private(msg, branch, dry, push, authorized):
    """附属技能在私有仓按 功能分支→dev→main 提交（推送须用户当轮授权）。"""
    if not (PRIVATE / ".git").exists():
        fail("E_NO_PRIVATE_REPO", "private/ 未 init 为独立私有仓（先 --init-private --yes）")
    if push and not authorized:
        fail("E_NOT_AUTHORIZED", "推送属远端动作，须用户当轮授权（加 --authorized-by-user）")
    planned = ["git checkout -B %s" % branch, "git add -A + commit"]
    if push:
        planned.append("git push -u origin %s" % branch)
    if dry:
        emit({"ok": True, "action": "commit", "dry_run": True, "branch": branch,
              "planned": planned, "detail": "未写盘：加 --yes 执行"})
        return
    log, bad = run_seq([["checkout", "-B", branch]])
    if bad:
        fail("E_COMMIT", "切功能分支失败：%s" % bad[1], steps=log)
    commit_tolerant(msg or "chore(private): sync attached skills")
    if push:
        rc, out = git(["push", "-u", "origin", branch], PRIVATE)
        if rc != 0:
            fail("E_PUSH", "推送失败：%s" % out)
    emit({"ok": True, "action": "commit", "dry_run": False, "branch": branch,
          "pushed": bool(push), "at": now_iso()})


def integrate(branch, dry):
    """私有仓：功能分支 → dev → main（--no-ff 留合入痕迹；不推送）。"""
    if not (PRIVATE / ".git").exists():
        fail("E_NO_PRIVATE_REPO", "private/ 未 init 为独立私有仓")
    seq = []
    for tgt, base in (("dev", branch), ("main", "dev")):
        exists = git(["rev-parse", "--verify", "-q", tgt], PRIVATE)[0] == 0
        seq.append(["checkout", tgt] if exists else ["checkout", "-b", tgt, base])
        seq.append(["merge", "--no-ff", "-m",
                  "merge %s into %s (attached skills, PRIVATE repo)" % (base, tgt), base])
    if dry:
        emit({"ok": True, "action": "integrate", "dry_run": True,
              "planned": ["git " + " ".join(s) for s in seq]})
        return
    log, bad = run_seq(seq)
    if bad:
        fail("E_INTEGRATE", "私有仓合入失败：%s" % bad[1], steps=log)
    emit({"ok": True, "action": "integrate", "steps": log, "at": now_iso()})


def repo_brief(path):
    rc, head = git(["rev-parse", "--abbrev-ref", "HEAD"], path)
    if rc != 0:
        return {"path": str(path), "git": False}
    branches = listed(git(["branch", "--format=%(refname:short)"], path)[1])
    remote = git(["remote", "get-url", "origin"], path)[1] or None
    dirty = len(listed(git(["status", "--porcelain"], path)[1]))
    files = listed(git(["ls-files"], path)[1])
    attached = sorted({f.split("/")[0] for f in files if f.startswith(PREFIX)})
    return {"path": str(path), "git": True, "head": head, "branches": branches,
            "remote": remote, "dirty": dirty, "attached_skills": attached}


def status():
    emit({"ok": True, "action": "status", "public_repo": repo_brief(ROOT),
          "private_repo": repo_brief(PRIVATE),
          "model": "本体 PUBLIC 仓 ＋ private/ 独立 PRIVATE 仓（附属技能入库、可推送）",
          "at": now_iso()})

def main():
    ap = argparse.ArgumentParser(
        description="双仓发布守卫：附属私有仓提交 / 两仓可见性校验 / 公开仓泄漏守卫")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--guard", action="store_true", help="附属技能是否混入本体公开仓")
    g.add_argument("--check-visibility", action="store_true", help="gh 校验两仓可见性")
    g.add_argument("--init-private", action="store_true", help="把 private/ 建成独立私有仓")
    g.add_argument("--commit", action="store_true", help="私有仓提交附属技能")
    g.add_argument("--integrate", action="store_true", help="私有仓 功能分支→dev→main")
    g.add_argument("--status", action="store_true", help="两仓状态概览")
    ap.add_argument("--msg", default="", help="提交说明")
    ap.add_argument("--branch", default="feature/attached-skills", help="功能分支名")
    ap.add_argument("--remote", default="", help="私有仓 origin URL（只配不推）")
    ap.add_argument("--push", action="store_true", help="提交后推送（远端动作）")
    ap.add_argument("--authorized-by-user", action="store_true",
                    help="声明用户已当轮授权推送")
    ap.add_argument("--yes", action="store_true", help="真正写盘（默认 dry-run）")
    a = ap.parse_args()
    if a.guard:
        guard()
    if a.check_visibility:
        check_visibility()
    if a.status:
        status()
    if a.init_private:
        init_flow(not a.yes, a.remote)
    if a.commit:
        commit_private(a.msg, a.branch, not a.yes, a.push, a.authorized_by_user)
    if a.integrate:
        integrate(a.branch, not a.yes)


if __name__ == "__main__":
    main()
