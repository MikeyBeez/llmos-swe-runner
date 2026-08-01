"""Continue SWE-bench Lite full-300 with the night's ENV corrections:
pin canonical Python (PIN_PYTHON), route 3.6/3.7 to conda (PIN_BACKEND),
spec-declared test deps auto-installed. KBs OFF (DISABLE_KB) for a clean number.
Resumable: skips ids already in results_full300.json."""
import json, os, sys, time, socket
sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
os.environ["DISABLE_KB"] = "1"
import swe_agent_v2 as A
RESULTS = os.path.expanduser("~/swe/results_full300.json")
CANON = json.load(open(os.path.expanduser("~/swe/canonical_python.json")))
insts = json.load(open(os.path.expanduser("~/swe/instances_full300.json")))
try: results = json.load(open(RESULTS))
except Exception: results = []
done = {r["id"] for r in results}
def wait_net():
    while True:
        try: socket.create_connection(("pypi.org", 443), timeout=10).close(); return
        except OSError: print("NET DOWN, waiting 60s", flush=True); time.sleep(60)
todo = [i for i in insts if i["instance_id"] not in done]
print("CONTINUE full300 (corrected): %d done, %d to go" % (len(done), len(todo)), flush=True)
for inst in insts:
    iid = inst["instance_id"]
    if iid in done: continue
    pin = CANON.get(iid)
    if pin: os.environ["PIN_PYTHON"] = pin
    else: os.environ.pop("PIN_PYTHON", None)
    if pin in ("3.6", "3.7"): os.environ["PIN_BACKEND"] = "conda"
    else: os.environ.pop("PIN_BACKEND", None)
    wait_net(); t0 = time.time()
    try: r = A.run_one(inst)
    except Exception as e: r = {"id": iid, "resolved": False, "error": "%s: %s" % (type(e).__name__, e)}
    r["pinned_python"] = pin
    results.append(r); json.dump(results, open(RESULTS, "w"), indent=2)
    n = sum(1 for x in results if x.get("resolved"))
    print("[%d/300] %s pin=%s resolved=%s (%.0fs) tally %d/%d" % (
        len(results), iid, pin, r.get("resolved"), time.time()-t0, n, len(results)), flush=True)
print("FULL300 CONTINUE COMPLETE", flush=True)
