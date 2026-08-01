"""Retry ornith's FAILURES from the 18-instance compare set, on the fully
updated harness (stall watchdog + file-hint redirect + live events). Reads the
prior compare1.json to find the missed instances; runs each once (MAX_ATTEMPTS
=1, FIX_BUDGET 200); writes runs/ornith/failures1.json; streams rich events to
runs/ornith/events.jsonl (the ◆ source in the monitor's Live tab). Resumable.
"""
import json, os, sys, time, socket

SWE = os.path.expanduser("~/swe")
ODIR = os.path.join(SWE, "runs", "ornith")
OUT = os.path.join(ODIR, "failures1.json")
MODEL_TAG = "ornith-1.0-35b-llamacpp"

ids = json.load(open(os.path.join(ODIR, "compare_set.json")))
try:
    prior = {x["id"]: x for x in json.load(open(os.path.join(ODIR, "compare1.json")))}
except Exception:
    prior = {}
missed = [i for i in ids if not prior.get(i, {}).get("resolved")]
print("retrying %d prior failures: %s" % (len(missed), missed), flush=True)

insts = {i["instance_id"]: i
         for i in json.load(open(os.path.join(SWE, "instances_full300.json")))}

sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
os.environ.pop("DISABLE_KB", None)
os.environ["USE_SPEC_ENV"] = "1"
os.environ["TOOL_BUDGET_RECENT"] = "6000"
os.environ["TOOL_BUDGET_OLD"] = "1200"
os.environ["TOOL_RECENT_TURNS"] = "16"
os.environ["TRIAGE"] = "1"
os.environ["ATLAS_DIR"] = os.path.expanduser("~/swe/atlas")
os.environ["LLMOS_EVENTS"] = os.path.join(ODIR, "events.jsonl")
import swe_agent_v2 as A

CANON = json.load(open(os.path.join(SWE, "canonical_python.json")))
try:
    results = json.load(open(OUT))
except Exception:
    results = []
done = {r["id"] for r in results}
print("resume: %d of %d already retried" % (len(done), len(missed)), flush=True)


def wait_net():
    while True:
        try:
            socket.create_connection(("pypi.org", 443), timeout=10).close()
            return
        except OSError:
            time.sleep(60)


for iid in [i for i in missed if i not in done]:
    inst = insts[iid]
    pin = CANON.get(iid)
    if pin:
        os.environ["PIN_PYTHON"] = pin
    else:
        os.environ.pop("PIN_PYTHON", None)
    if pin in ("3.6", "3.7"):
        os.environ["PIN_BACKEND"] = "conda"
    else:
        os.environ.pop("PIN_BACKEND", None)
    wait_net()
    t0 = time.time()
    try:
        r = A.run_one(inst)
    except Exception as e:
        r = {"id": iid, "resolved": False, "error": str(e)}
    r["attempt"] = 1
    r["attempt_secs"] = round(time.time() - t0)
    r["attempts_made"] = 1
    r["model"] = MODEL_TAG
    results = [x for x in results if x.get("id") != iid]
    results.append(r)
    json.dump(results, open(OUT, "w"), indent=2)
    n = sum(1 for x in results if x.get("resolved"))
    print("[%d/%d] %s -> %s (%ds)  [recovered so far: %d]"
          % (len(results), len(missed), iid,
             "RESOLVED" if r.get("resolved") else "miss", r["attempt_secs"], n),
          flush=True)

n = sum(1 for x in results if x.get("resolved"))
print("DONE: recovered %d/%d of ornith's prior failures on the updated harness"
      % (n, len(results)), flush=True)
