import json, os, sys, time
sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
os.environ["DISABLE_KB"] = "1"
os.environ["NUM_PREDICT"] = "8192"
import swe_agent_v2 as A
A.HOST = "http://127.0.0.1:8080"; A.MODEL = "vibethinker-3b"
# 10 head-to-head: 5 ornith MISSED, 5 ornith RESOLVED
SUBSET = [
  "scikit-learn__scikit-learn-25747", "astropy__astropy-14365", "pytest-dev__pytest-11148",
  "mwaskom__seaborn-3190", "sympy__sympy-24909",
  "django__django-16873", "matplotlib__matplotlib-26011", "sympy__sympy-24152",
  "pylint-dev__pylint-7114", "psf__requests-1963",
]
RESULTS = os.path.expanduser("~/swe/results_vibethinker.json")
CANON = json.load(open(os.path.expanduser("~/swe/canonical_python.json")))
insts = {i["instance_id"]: i for i in json.load(open(os.path.expanduser("~/swe/instances_full300.json")))}
try: results = json.load(open(RESULTS))
except Exception: results = []
done = {r["id"] for r in results}
print("VIBETHINKER: %s on %d instances (num_predict=8192, clean)" % (A.MODEL, len(SUBSET)), flush=True)
for iid in SUBSET:
    if iid in done: continue
    inst = insts[iid]; pin = CANON.get(iid)
    if pin: os.environ["PIN_PYTHON"] = pin
    if pin in ("3.6","3.7"): os.environ["PIN_BACKEND"]="conda"
    else: os.environ.pop("PIN_BACKEND", None)
    t0 = time.time()
    try: r = A.run_one(inst)
    except Exception as e: r = {"id": iid, "resolved": False, "error": "%s: %s" % (type(e).__name__, e)}
    r["model"] = A.MODEL
    results.append(r); json.dump(results, open(RESULTS, "w"), indent=2)
    n = sum(1 for x in results if x.get("resolved"))
    print("[VIBE %d/%d] %s resolved=%s p2=%s (%.0fs) tally %d" % (
        len(results), len(SUBSET), iid, r.get("resolved"), r.get("phase2_reason"), time.time()-t0, n), flush=True)
print("VIBETHINKER COMPLETE", flush=True)
