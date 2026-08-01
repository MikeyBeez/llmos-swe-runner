"""Phase A: build graphify graphs for a stratified sample of existing checkouts.

Deterministic, CPU-only, no model, no GPU. Graphs are cached per checkout in
<repo>/graphify-out and reused, so this is a one-time cost per instance.
"""
import os, subprocess, sys, collections

WORK = "/home/bard/swe/work"
G = "/home/bard/.graphify_venv/bin/graphify"
PER_REPO = int(os.environ.get("PER_REPO", "4"))
PAR = int(os.environ.get("PAR", "6"))

trees = sorted(os.listdir(WORK))
byrepo = collections.defaultdict(list)
for t in trees:
    byrepo[t.split("__")[0]].append(t)

sample = []
for repo in sorted(byrepo):
    sample.extend(byrepo[repo][:PER_REPO])
print("sample: %d instances across %d repos" % (len(sample), len(byrepo)), flush=True)

todo = [s for s in sample
        if not os.path.isfile(os.path.join(WORK, s, "graphify-out", "graph.json"))]
print("already built: %d   to build: %d" % (len(sample) - len(todo), len(todo)),
      flush=True)

running = []
def reap(block):
    while running and (block or len(running) >= PAR):
        for p, name in list(running):
            if p.poll() is not None:
                running.remove((p, name))
                print("  built %-34s rc=%s" % (name, p.returncode), flush=True)
        if running and (block or len(running) >= PAR):
            running[0][0].wait()

for name in todo:
    d = os.path.join(WORK, name)
    p = subprocess.Popen(["nice", "-n", "19", G, "update", ".", "--no-cluster"],
                         cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    running.append((p, name))
    reap(False)
reap(True)

ok = [s for s in sample
      if os.path.isfile(os.path.join(WORK, s, "graphify-out", "graph.json"))]
print("DONE: %d of %d have a graph" % (len(ok), len(sample)), flush=True)
with open("/home/bard/swe/graph_eval_sample.txt", "w") as f:
    f.write("\n".join(ok) + "\n")
