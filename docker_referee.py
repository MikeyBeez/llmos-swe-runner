"""Referee django-15061 in the official SWE-bench image.

Our harness says our patch fails. Docker settles whether that is the PATCH or
our ENVIRONMENT. Three runs in the official image, each on a clean checkout:

  1. base + test_patch, no fix   -> F2P must FAIL   (proves the tests bite)
  2. gold + test_patch           -> F2P must PASS   (proves the image is sane)
  3. ours + test_patch           -> whichever it is (the actual question)

Reading the gold patch here is post-hoc refereeing, never a runtime read.
"""
import json, subprocess, tempfile, os, re
import pandas as pd

IID = "django__django-15061"
IMG = "swebench/sweb.eval.x86_64.django_1776_django-15061:latest"

df = pd.read_parquet("/home/bard/swe/lite_full.parquet")
r = df[df.instance_id == IID].iloc[0]
f2p = json.loads(r.FAIL_TO_PASS) if isinstance(r.FAIL_TO_PASS, str) else list(r.FAIL_TO_PASS)

def label(nid):
    m = re.search(r"\(([\w.]+)\)", nid)
    return "%s.%s" % (m.group(1), nid.split(" ")[0]) if m else nid
labels = " ".join(label(x) for x in f2p)

ours = subprocess.run("git diff -- django", shell=True,
                      cwd="/home/bard/swe/work/" + IID,
                      capture_output=True, text=True).stdout or ""

def run(name, patch):
    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as f:
        f.write(r.test_patch + ("\n" + patch if patch.strip() else ""))
        pf = f.name
    os.chmod(pf, 0o644)
    inner = ("cd /testbed && git checkout -- . && git apply /tmp/p.patch && "
             "./tests/runtests.py --parallel 1 " + labels + " 2>&1 | tail -14")
    out = subprocess.run(["docker", "run", "--rm", "-v", pf + ":/tmp/p.patch",
                          IMG, "bash", "-lc", inner],
                         capture_output=True, text=True, timeout=900)
    os.unlink(pf)
    txt = (out.stdout or "") + (out.stderr or "")
    ok = bool(re.search(r"^OK", txt, re.M))
    print("=" * 68, flush=True)
    print("%s  ->  %s" % (name, "PASS" if ok else "FAIL"), flush=True)
    print("\n".join(txt.strip().splitlines()[-8:]), flush=True)
    return ok

print("FAIL_TO_PASS: %s" % labels, flush=True)
print("our patch: %d bytes\n" % len(ours), flush=True)
a = run("1. base, no fix       (must FAIL)", "")
b = run("2. GOLD patch         (must PASS)", r.patch)
c = run("3. OUR patch          (the question)", ours)
print("\nVERDICT:", flush=True)
if (not a) and b:
    print("  image is sane: fails without a fix, passes with gold.")
    print("  our patch %s in the official image." % ("PASSES" if c else "FAILS"))
    print("  -> %s" % ("OUR HARNESS IS WRONG" if c
                       else "THE PATCH IS WRONG -- harness agrees with docker"))
else:
    print("  inconclusive: base=%s gold=%s" % (a, b))
