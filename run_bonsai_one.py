"""Run ONE instance under Bonsai, same config/harness as run_bonsai_compare.py.
Appends the labeled result to runs/bonsai/compare1.json (replacing any prior
entry for that id). Usage: python3 run_bonsai_one.py <instance_id>
"""
import json, os, sys, time, socket

SWE = os.path.expanduser("~/swe")
LDIR = os.path.join(SWE, "runs", "bonsai")
os.makedirs(LDIR, exist_ok=True)
OUT = os.path.join(LDIR, "compare1.json")
MODEL_TAG = "bonsai-27b-ternary-q2_0"

if len(sys.argv) < 2:
    sys.exit("usage: run_bonsai_one.py <instance_id>")
iid = sys.argv[1]
insts = {i["instance_id"]: i
         for i in json.load(open(os.path.join(SWE, "instances_full300.json")))}
if iid not in insts:
    sys.exit("unknown instance %s" % iid)

sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
os.environ.pop("DISABLE_KB", None)
os.environ["USE_SPEC_ENV"] = "1"
os.environ["TOOL_BUDGET_RECENT"] = "6000"
os.environ["TOOL_BUDGET_OLD"] = "1200"
os.environ["TOOL_RECENT_TURNS"] = "16"
os.environ["TRIAGE"] = "1"
os.environ["ATLAS_DIR"] = os.path.expanduser("~/swe/atlas")
os.environ["LLMOS_EVENTS"] = os.path.join(SWE, "runs", "bonsai", "events.jsonl")
import swe_agent_v2 as A

CANON = json.load(open(os.path.join(SWE, "canonical_python.json")))
pin = CANON.get(iid)
if pin:
    os.environ["PIN_PYTHON"] = pin
else:
    os.environ.pop("PIN_PYTHON", None)
if pin in ("3.6", "3.7"):
    os.environ["PIN_BACKEND"] = "conda"
else:
    os.environ.pop("PIN_BACKEND", None)


def wait_net():
    while True:
        try:
            socket.create_connection(("pypi.org", 443), timeout=10).close()
            return
        except OSError:
            time.sleep(60)


inst = insts[iid]
wait_net()
t0 = time.time()
print("\n=== SINGLE bonsai run: %s ===" % iid, flush=True)
try:
    r = A.run_one(inst)
except Exception as e:
    r = {"id": iid, "resolved": False, "error": str(e)}
r["attempt"] = 1
r["attempt_secs"] = round(time.time() - t0)
r["attempts_made"] = 1
r["model"] = MODEL_TAG
try:
    results = json.load(open(OUT))
except Exception:
    results = []
results = [x for x in results if x.get("id") != iid]
results.append(r)
json.dump(results, open(OUT, "w"), indent=2)
print("[single] %s -> %s (%ds)"
      % (iid, "RESOLVED" if r.get("resolved") else "miss", r["attempt_secs"]),
      flush=True)
