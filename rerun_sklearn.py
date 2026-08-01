import json, os, sys
sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
import swe_agent_v2 as A
os.makedirs(A.WORK, exist_ok=True); os.makedirs(A.TRACES, exist_ok=True)
insts = json.load(open(os.path.expanduser("~/swe/instances.json")))
inst = next(i for i in insts if "scikit-learn" in i["instance_id"])
try:
    r = A.run_one(inst)
except Exception as e:
    r = {"id": inst["instance_id"], "resolved": False, "error": f"{type(e).__name__}: {e}"}
path = os.path.expanduser("~/swe/results_v2.json")
results = json.load(open(path))
results = [x for x in results if "scikit-learn" not in x.get("id","")] + [r]
json.dump(results, open(path, "w"), indent=2)
print("MERGED:", r.get("id"), "resolved:", r.get("resolved"), "env_ok:", r.get("env_ok"))
