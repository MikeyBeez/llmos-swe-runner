import json, os, sys
sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
import swe_agent_v2 as A
os.makedirs(A.WORK, exist_ok=True); os.makedirs(A.TRACES, exist_ok=True)
iid = "mwaskom__seaborn-3407"
insts = json.load(open(os.path.expanduser("~/swe/instances.json")))
inst = next(i for i in insts if i["instance_id"] == iid)
try:
    r = A.run_one(inst)
except Exception as e:
    r = {"id": iid, "resolved": False, "error": f"{type(e).__name__}: {e}"}
r["rerun"] = "80turn+patterns"
path = os.path.expanduser("~/swe/results_v2.json")
results = json.load(open(path))
results = [x for x in results if x.get("id") != iid] + [r]
json.dump(results, open(path, "w"), indent=2)
print("MERGED:", iid, "resolved:", r.get("resolved"), flush=True)
