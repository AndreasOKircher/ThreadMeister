#!/usr/bin/env python3
"""Mechanical steps of /start-feature and /finish-feature. Stdlib only.

Same file in Track-On-Topo and ThreadMeister (keep the two copies identical).

  python scripts/feature_flow.py start <slug> [--issues 01-a 02-b]
  python scripts/feature_flow.py issues
  python scripts/feature_flow.py tests
  python scripts/feature_flow.py open-pr --summary "text" [--body-file FILE]
  python scripts/feature_flow.py after-merge [--slug SLUG]

Every command prints a short report. A line starting with "STOP:" means a human
or the model must decide before going on; the exit code is then not 0.
"""
import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def die(msg, code=1):
    print("STOP: " + msg)
    sys.exit(code)


def run(cmd, check=True, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=cwd)
    if check and r.returncode != 0:
        die("`%s` failed: %s" % (" ".join(cmd), (r.stderr or r.stdout).strip()))
    return r


def git(*args, check=True):
    return run(["git", *args], check=check).stdout.strip()


_top = run(["git", "rev-parse", "--show-toplevel"], check=False)
if _top.returncode != 0:
    die("not inside a git repository")
ROOT = Path(_top.stdout.strip())
SCRATCH = ROOT / ".scratch"


# ---------------------------------------------------------------- git helpers

def current_branch():
    return git("branch", "--show-current")


def default_branch():
    r = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], check=False)
    if r.returncode == 0 and "/" in r.stdout.strip():
        return r.stdout.strip().split("/", 1)[1]
    for b in ("main", "master"):
        if run(["git", "rev-parse", "--verify", "--quiet", b], check=False).returncode == 0:
            return b
    die("cannot find the default branch (no origin/HEAD, no main, no master)")


def require_clean_tree():
    dirty = git("status", "--porcelain", "--untracked-files=no")
    if dirty:
        die("tracked files have uncommitted changes. Commit, stash, or ask the user:\n" + dirty)
    untracked = git("status", "--porcelain", "--untracked-files=normal")
    if untracked:
        print("note: untracked files stay as they are (not touched):")
        print("\n".join("  " + ln for ln in untracked.splitlines() if ln.startswith("??")))


# ----------------------------------------------------------------- file helpers

def read(path):
    raw = path.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), eol


def write(path, text, eol="\n"):
    path.write_bytes(text.replace("\n", eol).encode("utf-8"))


# --------------------------------------------------------------------- tracker

def split_tracker(text):
    m = re.search(r"^## ", text, flags=re.M)
    return (text[:m.start()], text[m.start():]) if m else (text, "")


def parse_block(block):
    d = {}
    issues = []
    for line in block.splitlines():
        m = re.match(r"^\s+-\s+(\S+)", line)
        if m:
            issues.append(m.group(1))
            continue
        m = re.match(r"^([a-z_]+):[ \t]*(.*)$", line)
        if m:
            d[m.group(1)] = m.group(2).strip()
    d["issues"] = issues
    return d


def render_top(d):
    lines = ["%s: %s" % (k, v) if v != "" else "%s:" % k
             for k, v in d.items() if k != "issues"]
    lines.append("issues:")
    lines += ["  - " + i for i in d["issues"]]
    return "\n".join(lines) + "\n"


def render_section(d):
    label = d.get("status", "merged")
    n = d.get("round", "?")
    lines = ["## Round %s (%s)" % (n, label), ""]
    for k in ("branch", "round", "pr"):
        if k in d:
            lines.append("%s: %s" % (k, d[k]) if d[k] else "%s:" % k)
    lines.append("issues:")
    lines += ["  - " + i for i in d["issues"]]
    for k, v in d.items():
        if k not in ("status", "branch", "round", "pr", "issues"):
            lines.append("%s: %s" % (k, v))
    return "\n".join(lines) + "\n"


def tracker_path(slug):
    return SCRATCH / slug / ".feature-status.md"


def load_tracker(slug):
    p = tracker_path(slug)
    if not p.exists():
        return p, {"issues": []}, "", "\n"
    text, eol = read(p)
    top, rest = split_tracker(text)
    return p, parse_block(top), rest, eol


def save_tracker(path, top, rest, eol="\n"):
    out = render_top(top)
    if rest:
        out += "\n" + rest
    write(path, out, eol)


def find_feature(slug=None):
    """Return (slug, top-dict) of the feature this branch belongs to."""
    if slug:
        _, top, _, _ = load_tracker(slug)
        if not top.get("branch"):
            die("no tracker for slug '%s'" % slug)
        return slug, top
    branch = current_branch()
    for p in sorted(SCRATCH.glob("*/.feature-status.md")):
        text, _ = read(p)
        top = parse_block(split_tracker(text)[0])
        if top.get("branch") == branch:
            return p.parent.name, top
    die("no .scratch/*/.feature-status.md lists branch '%s'. Pass --slug." % branch)


def issue_status(path):
    m = re.search(r"^Status:[ \t]*(\S+)", read(path)[0], flags=re.M)
    return m.group(1) if m else "?"


def issue_path(slug, stem):
    return SCRATCH / slug / "issues" / (stem + ".md")


def commit(paths, message):
    git("add", *paths)
    if run(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0:
        git("commit", "-m", message)
    return git("rev-parse", "--short", "HEAD")


# -------------------------------------------------------------------- start

def cmd_start(a):
    slug = a.slug
    issues_dir = SCRATCH / slug / "issues"
    if not issues_dir.is_dir():
        die("no folder %s" % issues_dir)
    if a.issues:
        chosen = [i.removesuffix(".md") for i in a.issues]
        for i in chosen:
            if not issue_path(slug, i).exists():
                die("no issue file %s" % issue_path(slug, i))
    else:
        chosen = [p.stem for p in sorted(issues_dir.glob("*.md"))
                  if issue_status(p) == "ready-for-agent"]
    if not chosen:
        die("no issue with Status: ready-for-agent in %s" % issues_dir)

    require_clean_tree()

    path, top, rest, eol = load_tracker(slug)
    rounds = [int(x) for x in re.findall(r"^round:[ \t]*(\d+)", path.read_text("utf-8") if path.exists() else "", flags=re.M)]
    for ln in git("branch", "-a", "--list", "*%s-r*" % slug, check=False).splitlines():
        m = re.search(r"%s-r(\d+)\s*$" % re.escape(slug), ln)
        if m:
            rounds.append(int(m.group(1)))
    n = max(rounds, default=0) + 1

    cur = current_branch()
    if cur.startswith("claude/"):
        branch = cur
        print("cloud session: keeping branch %s" % branch)
    else:
        base = default_branch()
        branch = "%s-r%d" % (slug, n)
        if run(["git", "rev-parse", "--verify", "--quiet", branch], check=False).returncode == 0:
            die("branch %s already exists" % branch)
        git("checkout", base)
        git("pull", "--ff-only", "origin", base)
        git("checkout", "-b", branch)

    for i in chosen:
        p = issue_path(slug, i)
        text, e = read(p)
        text = re.sub(r"^(Status:[ \t]*)ready-for-agent", r"\1on-branch", text, count=1, flags=re.M)
        write(p, text, e)

    if top.get("branch"):  # earlier round: keep it as a history section
        rest = render_section(top) + ("\n" + rest if rest else "")
    new_top = {"status": "in-progress", "branch": branch, "round": str(n), "pr": "",
               "issues": chosen}
    save_tracker(path, new_top, rest, eol)
    sha = commit([str(SCRATCH / slug)], "start(%s): claim round r%d -> on-branch" % (slug, n))

    print("Round:   r%d" % n)
    print("Branch:  %s" % branch)
    print("Claimed (on-branch): " + ", ".join(chosen))
    print("Claim commit: %s. Work is now on %s." % (sha, branch))


# ---------------------------------------------------------------- finish: issues

def cmd_issues(a):
    slug, top = find_feature(a.slug)
    bad, smoke = [], []
    for i in top["issues"]:
        p = issue_path(slug, i)
        if not p.exists():
            bad.append("%s: file missing" % i)
            continue
        st = issue_status(p)
        has_sum = "## Implementation Summary" in read(p)[0]
        print("  %-45s %-16s summary=%s" % (i, st, "yes" if has_sum else "NO"))
        if st == "ready-for-human":
            smoke.append(i)
        elif st != "completed" or not has_sum:
            bad.append("%s: Status=%s, summary=%s" % (i, st, has_sum))
    base = default_branch()
    changed = git("diff", "--name-only", "%s...HEAD" % base, check=False).splitlines()
    if (ROOT / "docs/changelog.md").exists() and any(c.startswith("core/") for c in changed) \
            and "docs/changelog.md" not in changed:
        print("warning: core/ changed but docs/changelog.md did not.")
    if (ROOT / "docs/agents/cross-step-seams.md").exists() and any(c.startswith("src/") for c in changed):
        print("reminder: cross-cutting round? Walk docs/agents/cross-step-seams.md.")
    if bad:
        die("issues not finished:\n  " + "\n  ".join(bad))
    if smoke:
        die("ask the user to run the manual smoke test for: " + ", ".join(smoke) +
            ". When confirmed, set them to Status: completed and commit.", code=3)
    print("OK: all %d issues completed." % len(top["issues"]))


# ---------------------------------------------------------------- finish: tests

def venv_python():
    for rel in (".venv/Scripts/python.exe", ".venv/bin/python"):
        if (ROOT / rel).exists():
            return str(ROOT / rel)
    return sys.executable


def test_commands():
    cmds = []
    npm = shutil.which("npm")
    if (ROOT / "package.json").exists() and npm:
        cmds.append([npm, "test"])
    py = venv_python()
    has_xdist = run([py, "-c", "import xdist"], check=False).returncode == 0
    cmds.append([py, "-m", "pytest"] + (["-n", "auto"] if has_xdist else ["-q"]))
    return cmds


def result_file(slug):
    return ROOT / ".git" / ("feature-flow-%s.json" % slug)


def cmd_tests(a):
    slug, _ = find_feature(a.slug)
    if git("status", "--porcelain", "--untracked-files=no"):
        die("tracked files have uncommitted changes. Commit first so the result belongs to a commit.")
    sha = git("rev-parse", "HEAD")
    results, ok_all = [], True
    for cmd in test_commands():
        print("running: " + " ".join(cmd))
        r = run(cmd, check=False)
        lines = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.strip()]
        summary = next((ln.strip("= ") for ln in reversed(lines)
                        if re.search(r"\b(passed|failed|error)", ln)), lines[-1] if lines else "(no output)")
        ok = r.returncode == 0
        ok_all &= ok
        results.append({"cmd": " ".join(Path(cmd[0]).name if i == 0 else c for i, c in enumerate(cmd)),
                        "ok": ok, "summary": summary})
        print("  %s: %s" % ("PASS" if ok else "FAIL", summary))
        if not ok:
            print("\n".join(lines[-40:]))
    if not ok_all:
        die("tests failed. Fix, commit, run `tests` again.")
    result_file(slug).write_text(json.dumps({"sha": sha, "results": results}), "utf-8")
    print("OK: full suite green at %s." % sha[:7])


# ---------------------------------------------------------------- finish: PR

def cmd_open_pr(a):
    slug, top = find_feature(a.slug)
    branch, n = top["branch"], top["round"]
    if current_branch() != branch:
        die("you are on '%s', the tracker says '%s'" % (current_branch(), branch))
    rf = result_file(slug)
    if not rf.exists():
        die("no test result. Run `tests` first.")
    data = json.loads(rf.read_text("utf-8"))
    outside = [f for f in git("diff", "--name-only", data["sha"], "HEAD").splitlines()
               if not f.startswith(".scratch/")]
    if outside:
        die("code changed after the last green test run (%s ...). Run `tests` again." % outside[0])
    base = default_branch()

    path, t, rest, eol = load_tracker(slug)
    t["status"] = "awaiting-review"
    save_tracker(path, t, rest, eol)
    commit([str(path)], "finish(%s): round r%s awaiting-review" % (slug, n))
    git("push", "-u", "origin", branch)

    body = Path(a.body_file).read_text("utf-8") if a.body_file else "## Summary\n\n%s\n" % a.summary
    if "## Issues" not in body:
        body += "\n## Issues\n\n" + "\n".join("- " + i for i in top["issues"]) + "\n"
    if "## Evidence" not in body:
        body += "\n## Evidence\n\n" + "\n".join(
            "- `%s`: %s" % (r["cmd"], r["summary"]) for r in data["results"]) + "\n"
    bodyfile = ROOT / ".git" / "feature-flow-pr-body.md"
    bodyfile.write_text(body, "utf-8")
    title = "%s r%s: %s" % (slug, n, a.summary)

    gh = shutil.which("gh")
    if not gh:
        remote = git("remote", "get-url", "origin").removesuffix(".git")
        print("gh not installed. Open: %s/compare/%s...%s?expand=1" % (remote, base, branch))
        print("Title: " + title)
        print("Body file: " + str(bodyfile))
        return
    existing = run([gh, "pr", "view", branch, "--json", "url", "-q", ".url"], check=False)
    if existing.returncode == 0 and existing.stdout.strip():
        url = existing.stdout.strip()
        run([gh, "pr", "edit", branch, "--title", title, "--body-file", str(bodyfile)])
    else:
        url = run([gh, "pr", "create", "--base", base, "--head", branch, "--title", title,
                   "--body-file", str(bodyfile)]).stdout.strip().splitlines()[-1]
    path, t, rest, eol = load_tracker(slug)
    t["pr"] = url
    save_tracker(path, t, rest, eol)
    commit([str(path)], "finish(%s): record PR url" % slug)
    git("push", "origin", branch)
    print("PR: " + url)
    print("Next (human): smoke test by checking out %s, then click Squash and merge." % branch)


# ---------------------------------------------------------- finish: after merge

def cmd_after_merge(a):
    slug, top = find_feature(a.slug)
    branch = top["branch"]
    gh = shutil.which("gh")
    if not gh:
        die("gh is not installed; cannot check that the PR is merged.")
    info = json.loads(run([gh, "pr", "view", branch, "--json", "state,mergeCommit,url"]).stdout)
    if info["state"] != "MERGED":
        die("PR %s is %s, not MERGED." % (info["url"], info["state"]))
    require_clean_tree()
    base = default_branch()
    git("checkout", base)
    git("pull", "--ff-only", "origin", base)
    path, t, rest, eol = load_tracker(slug)
    t["status"] = "merged"
    t["merged_as"] = (info.get("mergeCommit") or {}).get("oid", "")[:7]
    t["merged_on"] = datetime.date.today().isoformat()
    save_tracker(path, t, rest, eol)
    sha = commit([str(path)], "finish(%s): round r%s merged" % (slug, t.get("round")))
    run(["git", "branch", "-D", branch], check=False)
    print("Merged as %s. Tracker -> merged (local commit %s on %s, NOT pushed: ask the user)." %
          (t["merged_as"], sha, base))
    print("Local branch %s deleted. Remote branch: delete on GitHub or enable auto-delete." % branch)
    if not (ROOT / ".github" / "workflows").exists():
        print("No CI in this repo, so running the tests on %s:" % base)
        for cmd in test_commands():
            r = run(cmd, check=False)
            tail = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.strip()][-1:]
            print("  %s: %s" % ("PASS" if r.returncode == 0 else "FAIL", tail[0] if tail else ""))
            if r.returncode != 0:
                die("tests are red on %s. Open a revert PR; set tracker status post-merge-test-failed." % base)
    else:
        print("GitHub Actions runs on %s. If red: open a revert PR." % base)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("slug")
    s.add_argument("--issues", nargs="+", help="issue stems; default: all ready-for-agent")
    s.set_defaults(fn=cmd_start)
    for name, fn in (("issues", cmd_issues), ("tests", cmd_tests), ("open-pr", cmd_open_pr),
                     ("after-merge", cmd_after_merge)):
        p = sub.add_parser(name)
        p.add_argument("--slug", help="default: found from the current branch")
        if name == "open-pr":
            p.add_argument("--summary", required=True)
            p.add_argument("--body-file", help="Markdown with ## Summary and ## Merge Danger")
        p.set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
