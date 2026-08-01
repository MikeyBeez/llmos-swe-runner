"""Corrected restart of the 23 wrong-Python misses. Changes vs original:
pin canonical Python (PIN_PYTHON) + route 3.6/3.7 to conda (PIN_BACKEND) +
install spec-declared optional test deps (pandas/matplotlib, in-harness).
Writes results_rerun_corrected.json. Resumable."""
import json, os, sys, time
sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
import swe_agent_v2 as A
os.environ["DISABLE_KB"] = "1"  # clean env-only run: no per-package KB injection
RESULTS = os.path.expanduser("~/swe/results_rerun_corrected.json")
CANON = json.load(open(os.path.expanduser("~/swe/canonical_python.json")))
insts = json.load(open(os.path.expanduser("~/swe/instances_full300.json")))
full = json.load(open(os.path.expanduser("~/swe/results_full300.json")))
actual = {r["id"]: str(r.get("python")) for r in full}
missed = [r["id"] for r in full if not r.get("resolved")]
targets = [i for i in missed if CANON.get(i) and CANON[i] != actual.get(i)]
by_id = {i["instance_id"]: i for i in insts}
try: results = json.load(open(RESULTS))
except Exception: results = []
done = {r["id"] for r in results}
def net():
    import socket
    while True:
        try: socket.create_connection(("pypi.org", 443), timeout=10).close(); return
        except OSError: print("NET DOWN, waiting 60s", flush=True); time.sleep(60)
todo = [t for t in targets if t not in done]
print("CORRECTED rerun: %d targets, %d done, %d to go" % (len(targets), len(done), len(todo)), flush=True)
for iid in targets:
    if iid in done: continue
    inst = by_id.get(iid)
    if not inst:
        print("no instance data", iid, flush=True); continue
    pin = CANON.get(iid)
    os.environ["PIN_PYTHON"] = pin
    if pin in ("3.6", "3.7"): os.environ["PIN_BACKEND"] = "conda"
    else: os.environ.pop("PIN_BACKEND", None)
    net(); t0 = time.time()
    try: r = A.run_one(inst)
    except Exception as e: r = {"id": iid, "resolved": False, "error": "%s: %s" % (type(e).__name__, e)}
    r["pinned_python"] = pin; r["pinned_backend"] = os.environ.get("PIN_BACKEND"); r["was_python"] = actual.get(iid)
    results.append(r); json.dump(results, open(RESULTS, "w"), indent=2)
    n = sum(1 for x in results if x.get("resolved"))
    print("[%d/%d] %s %s->%s(%s) resolved=%s (%.0fs) tally %d" % (
        len(results), len(targets), iid, actual.get(iid), pin,
        os.environ.get("PIN_BACKEND", "uv"), r.get("resolved"), time.time()-t0, n), flush=True)
print("CORRECTED RERUN COMPLETE", flush=True)
