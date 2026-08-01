"""Full SWE-bench Lite run — RESUMABLE.
Skips ids already in results_full300.json, so the monitor can stop the run,
fix the harness, relaunch, and lose nothing. Reloads swe_agent_v2 per
instance so harness fixes take effect on relaunch without staleness."""
import json, os, sys, time
sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
import swe_agent_v2 as A

def wait_for_network():
    """Mikey: if you cannot get a network connection out, stop.
    An instance attempted without network is not a measurement.
    Block (loudly) until connectivity returns."""
    import socket, time as _t
    down_since = None
    while True:
        try:
            s = socket.create_connection(("pypi.org", 443), timeout=10)
            s.close()
            if down_since:
                print(f"NETWORK RESTORED after {_t.time()-down_since:.0f}s — resuming", flush=True)
            return
        except OSError:
            if down_since is None:
                down_since = _t.time()
                print("NETWORK DOWN — pausing before next instance (checking every 60s)", flush=True)
            _t.sleep(60)

os.makedirs(A.WORK, exist_ok=True); os.makedirs(A.TRACES, exist_ok=True)
RESULTS = os.path.expanduser("~/swe/results_full300.json")
insts = json.load(open(os.path.expanduser("~/swe/instances_full300.json")))
try:
    results = json.load(open(RESULTS))
except Exception:
    results = []
done = {r["id"] for r in results}
print(f"resume: {len(done)} done, {len(insts)-len(done)} to go", flush=True)
for inst in insts:
    if inst["instance_id"] in done:
        continue
    wait_for_network()
    t0 = time.time()
    try:
        r = A.run_one(inst)
    except Exception as e:
        r = {"id": inst["instance_id"], "resolved": False,
             "error": f"{type(e).__name__}: {e}"}
    results.append(r)
    json.dump(results, open(RESULTS, "w"), indent=2)
    n = sum(1 for x in results if x.get("resolved"))
    iid = inst["instance_id"]
    ok = r.get("resolved")
    dt = time.time() - t0
    print(f"[{len(results)}/300] {iid} resolved={ok} ({dt:.0f}s) — tally {n}/{len(results)}", flush=True)
print("FULL RUN COMPLETE", flush=True)
