"""Phase B: does the call graph pick better blast-radius tests than path proximity?

THE QUESTION. When the model edits the right place, do the tests we choose to run
as a regression check actually cover the behaviour that changed? Path proximity
scores test files by path similarity to the edited source file. The call graph
names the files that inherit from, reference, or call the edited code.

METHOD. For each sampled checkout: read the GOLD patch to learn which file and
line the fix belongs at -- a post-hoc analysis read, never done at runtime -- then
ask both rankers for their top-k test files and check whether the FAIL_TO_PASS
module is among them. F2P is the behaviour the fix is supposed to change, so a
ranker that surfaces it is a ranker that would have noticed a wrong fix.

This is an UPPER BOUND on the runtime benefit: it assumes the model edits the
right place. It measures the ranker, not the agent.
"""
import json, os, re, sys, glob, collections
sys.path.insert(0, "/home/bard/Code/LLMOS")
import pandas as pd
import graph_tools as gt
from swe_fix_tools import _fault_proximity

WORK = "/home/bard/swe/work"
K = int(os.environ.get("K", "6"))

df = pd.read_parquet("/home/bard/swe/lite_full.parquet")
rows = {r.instance_id: r for _, r in df.iterrows()}
sample = [l.strip() for l in open("/home/bard/swe/graph_eval_sample.txt") if l.strip()]

HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+", re.M)
FILE = re.compile(r"^\+\+\+ b/(.+)$", re.M)
DIFFSPLIT = re.compile(r"^diff --git ", re.M)


def gold_sites(patch):
    """EVERY (file, pre-image line) in the gold patch, not just the first.

    First version took only the first hunk, and for a lot of patches that is
    the import block at the top of the file -- django-11019 gave
    django/forms/widgets.py:6, which has no enclosing def or class at all, so
    the graph was asked nothing and scored as "empty". That understated the
    graph and would have made this evaluation lie in the direction of my own
    prior conclusion. Take all hunks and union what they find.
    """
    out = []
    for chunk in DIFFSPLIT.split(patch or ""):
        f = FILE.search(chunk)
        if not f:
            continue
        path = f.group(1).strip()
        for h in HUNK.finditer(chunk):
            out.append((path, int(h.group(1))))
    return out


def f2p_files(inst, repo_dir):
    """FAIL_TO_PASS entries -> repo-relative test file paths that exist."""
    v = inst.FAIL_TO_PASS
    ids = json.loads(v) if isinstance(v, str) else list(v)
    out = set()
    for nid in ids:
        if "::" in nid:                      # pytest style
            p = nid.split("::", 1)[0]
            if os.path.isfile(os.path.join(repo_dir, p)):
                out.add(p)
            continue
        m = re.search(r"\(([\w.]+)\)", nid)   # django "test_x (a.b.C)"
        dotted = m.group(1) if m else nid
        parts = [p for p in dotted.split(".") if p]
        for cut in range(len(parts), 0, -1):
            cand = os.path.join(*parts[:cut]) + ".py"
            for base in ("tests", ""):
                full = os.path.join(repo_dir, base, cand) if base else \
                    os.path.join(repo_dir, cand)
                if os.path.isfile(full):
                    out.add(os.path.relpath(full, repo_dir))
                    cut = 0
                    break
            if cut == 0:
                break
    return out


def all_test_files(repo_dir):
    out = []
    for pat in ("**/test_*.py", "**/tests/**/*.py", "**/*_test.py",
                "**/tests.py"):
        for p in glob.glob(os.path.join(repo_dir, pat), recursive=True):
            if "/.venv/" in p or "/graphify-out/" in p:
                continue
            r = os.path.relpath(p, repo_dir)
            if r not in out:
                out.append(r)
    return out


tot = collections.Counter()
detail = []
for iid in sample:
    inst = rows.get(iid)
    repo = os.path.join(WORK, iid)
    if inst is None or not os.path.isdir(repo):
        continue
    sites = [(f, l) for f, l in gold_sites(inst.patch)
             if os.path.isfile(os.path.join(repo, f))]
    if not sites:
        tot["no gold site"] += 1
        continue
    truth = f2p_files(inst, repo)
    if not truth:
        tot["no F2P file resolved"] += 1
        continue

    graphed, seen_g = [], set()
    for f, l in sites[:8]:
        for t in gt.test_files_near(repo, f, l, log=lambda *a: None):
            if t not in seen_g:
                seen_g.add(t)
                graphed.append(t)
    graphed = graphed[:K]
    cand = all_test_files(repo)
    files = list(dict.fromkeys(f for f, _l in sites))
    prox = sorted(cand, key=lambda t: (-_fault_proximity(t, files), t))[:K]

    g_hit = bool(truth & set(graphed))
    p_hit = bool(truth & set(prox))
    tot["n"] += 1
    tot["graph hit"] += g_hit
    tot["proximity hit"] += p_hit
    tot["graph only"] += (g_hit and not p_hit)
    tot["proximity only"] += (p_hit and not g_hit)
    tot["both"] += (g_hit and p_hit)
    tot["neither"] += (not g_hit and not p_hit)
    tot["graph empty"] += (not graphed)
    detail.append((iid, g_hit, p_hit, len(graphed), sorted(truth)[:1]))

print("blast-radius test selection, top-%d, on %d instances with a graph and a"
      " resolvable F2P file" % (K, tot["n"]))
print()
for k in ["graph hit", "proximity hit", "both", "graph only", "proximity only",
          "neither", "graph empty"]:
    n = tot[k]
    print("   %-16s %3d  (%3.0f%%)" % (k, n, 100.0*n/max(tot["n"], 1)))
print()
print("   skipped: %d no gold site, %d no F2P file resolved"
      % (tot["no gold site"], tot["no F2P file resolved"]))
print()
print("%-34s %6s %6s %6s %s" % ("instance", "graph", "prox", "n_graph", "an F2P file"))
for iid, g, p, ng, t in sorted(detail, key=lambda x: (x[1], x[2])):
    print("%-34s %6s %6s %6d %s" % (iid.split("__")[-1], g, p, ng, t[0] if t else ""))
