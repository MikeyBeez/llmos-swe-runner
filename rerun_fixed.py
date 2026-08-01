"""Re-run the MISSED instances from the 7/12 full300 run through the FIXED
harness (commit e902eda: pandas/matplotlib test-extras install so importorskip
F2P tests RUN instead of skip->miss; scorer skipped_only flag; stronger
self-verification prompt). Writes results_rerun.json — does NOT touch
results_full300.json (single source of truth). Resumable."""
import json, os, sys, time
sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
import swe_agent_v2 as A

RESULTS = os.path.expanduser("~/swe/results_rerun.json")
FULL    = os.path.expanduser("~/swe/results_full300.json")
insts   = json.load(open(os.path.expanduser("~/swe/instances_full300.json")))
full    = json.load(open(FULL))
missed  = [r["id"] for r in full if not r.get("resolved")]
by_id   = {i["instance_id"]: i for i in insts}

try:
    results = json.load(open(RESULTS))
except Exception:
    results = []
done = {r["id"] for r in results}

def net():
    import socket
    while True:
        try:
            socket.create_connection(("pypi.org", 443), timeout=10).close(); return
        except OSError:
            print("NETWORK DOWN - waiting 60s", flush=True); time.sleep(60)

todo = [m for m in missed if m not in done]
print(f"RERUN start: {len(missed)} missed total, {len(done)} already done, {len(todo)} to go", flush=True)
for iid in missed:
    if iid in done:
        continue
    inst = by_id.get(iid)
    if not inst:
        print("MISSING INSTANCE DATA:", iid, flush=True)
        results.append({"id": iid, "resolved": False, "error": "instance not found"})
        json.dump(results, open(RESULTS, "w"), indent=2)
        continue
    net()
    t0 = time.time()
    try:
        r = A.run_one(inst)
    except Exception as e:
        r = {"id": iid, "resolved": False, "error": f"{type(e).__name__}: {e}"}
    results.append(r)
    json.dump(results, open(RESULTS, "w"), indent=2)
    n = sum(1 for x in results if x.get("resolved"))
    print(f"[{len(results)}/{len(missed)}] {iid} resolved={r.get('resolved')} "
          f"({time.time()-t0:.0f}s) - rerun tally {n}/{len(results)}", flush=True)
print("RERUN COMPLETE", flush=True)
