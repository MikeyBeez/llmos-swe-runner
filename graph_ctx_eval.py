"""Does querying the graph with the symbols the ISSUE names find the fix site --
and does it find it when grep on the same symbols does not?

MOTIVATION, n=1, which is exactly why this exists. django-15902 burned 11,642s.
Asking this checkout's graph about `ManagementForm` -- a symbol in the issue
title -- returned RenderableMixin at django/forms/utils.py:L71, the machinery
that raises the deprecation warning. That looked decisive. But grep for
`ManagementForm` also finds formsets.py, which is where the gold fix goes. So
the honest question is not "does the graph find it" but "does the graph find it
when the model's existing tool would not".

METHOD, per instance:
  symbols  <- extracted from problem_statement (legitimate agent input)
  grep     <- files containing any of those symbols   (what `locate` gives today)
  graph    <- files named in `affected <sym>` output  (what we would add)
  truth    <- files touched by the gold patch          (post-hoc analysis only)

Reported: gold in grep, gold in graph, and the one that decides it -- gold in
graph but NOT in grep. That last number is the entire value of the proposal.

Leak rules: problem_statement is the agent's own input. The gold patch is read
here for scoring only and never at runtime.
"""
import json, os, re, subprocess, sys, collections
sys.path.insert(0, "/home/bard/Code/LLMOS")
import pandas as pd

WORK = "/home/bard/swe/work"
G = "/home/bard/.graphify_venv/bin/graphify"
MAX_SYMS = int(os.environ.get("MAX_SYMS", "6"))

STOP = set("""The This That When Then With From For And But Not You Your It Its
If Is Are Was Were Has Have Had Can Will Would Could Should Django Python None
True False Error Exception Traceback Description Summary Steps Expected Actual
Note Version Windows Linux Mac OS I A An In On At To Of As By Or So We They
Add Remove Fix Use Using Used Make Made Get Set New Old All Any One Two""".split())

BACKTICK = re.compile(r"`([A-Za-z_][\w.]{2,})`")
CAMEL = re.compile(r"\b([A-Z][a-z]+(?:[A-Z][a-z0-9]+)+)\b")
CALL = re.compile(r"\b([a-z_][\w]{3,})\s*\(")
DOTTED = re.compile(r"\b([a-z_][\w]*\.[A-Za-z_][\w]+)\b")
SNAKE = re.compile(r"\b([a-z]+_[a-z_]{2,})\b")


def symbols(ps):
    """Identifier-shaped tokens the reporter actually wrote."""
    seen, out = set(), []
    for rx in (BACKTICK, CAMEL, DOTTED, CALL, SNAKE):
        for m in rx.finditer(ps or ""):
            s = m.group(1).strip(".")
            if s in STOP or s in seen or len(s) < 4:
                continue
            seen.add(s)
            out.append(s)
    # longest first: more distinctive names are better graph keys
    out.sort(key=lambda s: (-len(s), s))
    return out[:MAX_SYMS]


FILEPAT = re.compile(r"([\w./-]+\.(?:py|pyx))")


def graph_files(repo, syms):
    out = set()
    for s in syms:
        try:
            r = subprocess.run([G, "affected", s, "--depth", "2"], cwd=repo,
                               capture_output=True, text=True, timeout=90)
        except subprocess.SubprocessError:
            continue
        txt = r.stdout or ""
        if "No unique node match" in txt or "No affected nodes" in txt:
            continue
        for m in FILEPAT.finditer(txt):
            p = m.group(1)
            if os.path.isfile(os.path.join(repo, p)):
                out.add(p)
    return out


def grep_files(repo, syms):
    """What `locate` gives today: files containing any of those symbols."""
    out = set()
    for s in syms:
        try:
            r = subprocess.run(
                ["grep", "-rl", "--include=*.py", "-F", s, "."],
                cwd=repo, capture_output=True, text=True, timeout=90)
        except subprocess.SubprocessError:
            continue
        for line in (r.stdout or "").splitlines():
            p = line.lstrip("./")
            if "/.venv/" in p or p.startswith(".venv"):
                continue
            out.add(p)
    return out


FILEHDR = re.compile(r"^\+\+\+ b/(.+)$", re.M)
DIFFSPLIT = re.compile(r"^diff --git ", re.M)


def gold_files(patch):
    out = set()
    for chunk in DIFFSPLIT.split(patch or ""):
        m = FILEHDR.search(chunk)
        if m:
            out.add(m.group(1).strip())
    return out


df = pd.read_parquet("/home/bard/swe/lite_full.parquet")
rows = {r.instance_id: r for _, r in df.iterrows()}
sample = [l.strip() for l in open("/home/bard/swe/graph_eval_sample.txt") if l.strip()]

tot = collections.Counter()
detail = []
for iid in sample:
    inst = rows.get(iid)
    repo = os.path.join(WORK, iid)
    if inst is None or not os.path.isdir(repo):
        continue
    syms = symbols(inst.problem_statement)
    if not syms:
        tot["no symbols"] += 1
        continue
    truth = gold_files(inst.patch)
    if not truth:
        continue
    gph = graph_files(repo, syms)
    grp = grep_files(repo, syms)
    g_hit, r_hit = bool(truth & gph), bool(truth & grp)
    tot["n"] += 1
    tot["graph finds gold"] += g_hit
    tot["grep finds gold"] += r_hit
    tot["GRAPH ONLY"] += (g_hit and not r_hit)
    tot["grep only"] += (r_hit and not g_hit)
    tot["neither"] += (not g_hit and not r_hit)
    tot["graph empty"] += (not gph)
    detail.append((iid, g_hit, r_hit, len(gph), len(grp), syms[:3]))
    print("  %-34s graph=%-5s grep=%-5s |g|=%-4d |r|=%-4d %s"
          % (iid.split("__")[-1], g_hit, r_hit, len(gph), len(grp), syms[:3]),
          flush=True)

print()
print("ISSUE-SYMBOL GRAPH LOOKUP vs GREP, on %d instances" % tot["n"])
for k in ["graph finds gold", "grep finds gold", "GRAPH ONLY", "grep only",
          "neither", "graph empty"]:
    print("   %-18s %3d  (%3.0f%%)" % (k, tot[k], 100.0*tot[k]/max(tot["n"], 1)))
print()
print("   GRAPH ONLY is the whole proposal: gold file the graph named and grep")
print("   on the same symbols did not.")
