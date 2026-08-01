import json, os, sys, time
sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
os.environ["GEMINI_API_KEY"] = open(os.path.expanduser("~/swe/.gemini_env")).read().split("=",1)[1].strip()
os.environ["DISABLE_KB"] = "1"   # clean, no leakage
import swe_agent_v2 as A
A.HOST = "https://generativelanguage.googleapis.com/v1beta/openai"
A.MODEL = "gemini-2.5-flash"
SUBSET = ["pytest-dev__pytest-11148", "scikit-learn__scikit-learn-25747",
          "astropy__astropy-14365", "mwaskom__seaborn-3190"]
RESULTS = os.path.expanduser("~/swe/results_gemini.json")
CANON = json.load(open(os.path.expanduser("~/swe/canonical_python.json")))
insts = {i["instance_id"]: i for i in json.load(open(os.path.expanduser("~/swe/instances_full300.json")))}
try: results = json.load(open(RESULTS))
except Exception: results = []
done = {r["id"] for r in results}
print("GEMINI run: %s on %d instances (clean harness, env corrections on)" % (A.MODEL, len(SUBSET)), flush=True)
for iid in SUBSET:
    if iid in done: continue
    inst = insts[iid]; pin = CANON.get(iid)
    if pin: os.environ["PIN_PYTHON"] = pin
    if pin in ("3.6", "3.7"): os.environ["PIN_BACKEND"] = "conda"
    else: os.environ.pop("PIN_BACKEND", None)
    t0 = time.time()
    try: r = A.run_one(inst)
    except Exception as e: r = {"id": iid, "resolved": False, "error": "%s: %s" % (type(e).__name__, e)}
    r["model"] = A.MODEL; r["pinned_python"] = pin
    results.append(r); json.dump(results, open(RESULTS, "w"), indent=2)
    print("[GEMINI] %s resolved=%s p2=%s (%.0fs)" % (iid, r.get("resolved"), r.get("phase2_reason"), time.time()-t0), flush=True)
print("GEMINI SUBSET COMPLETE", flush=True)
