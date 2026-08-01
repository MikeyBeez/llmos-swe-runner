"""One more flask run WITH the OUTPUT-MAP KB live (v3.6). Parked in the
workshop, so run directly. TTS-2, best-by-form. Waits for GPU idle first.
Writes ~/swe/runs/workshop/flask_kb_rerun.json."""
import json, os, sys, time, socket, subprocess

OUT = os.path.expanduser("~/swe/runs/workshop/flask_kb_rerun.json")
IID = "pallets__flask-5063"


def busy():
    return bool(subprocess.run(["pgrep", "-f", "workshop.py|run300|rerun_probe"],
               capture_output=True, text=True).stdout.strip())


while busy():
    print("waiting for GPU idle", flush=True)
    time.sleep(120)
print("idle -> flask rerun with OUTPUT-MAP KB", flush=True)
time.sleep(15)

sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
os.environ.pop("DISABLE_KB", None)          # KB ON -- the whole point
os.environ["USE_SPEC_ENV"] = "1"
os.environ["TOOL_BUDGET_RECENT"] = "6000"
os.environ["TOOL_BUDGET_OLD"] = "1200"
os.environ["TOOL_RECENT_TURNS"] = "16"
os.environ["TRIAGE"] = "1"
os.environ["ATLAS_DIR"] = os.path.expanduser("~/swe/atlas")
import swe_agent_v2 as A

insts = {i["instance_id"]: i
         for i in json.load(open(os.path.expanduser("~/swe/instances_full300.json")))}
CANON = json.load(open(os.path.expanduser("~/swe/canonical_python.json")))
inst = insts[IID]
pin = CANON.get(IID)
if pin:
    os.environ["PIN_PYTHON"] = pin


def selfv(r):
    return bool(r.get("fix_verified_by_model")) and (r.get("patch_bytes") or 0) > 0


def rank(r):
    return (int(bool(r.get("fix_verified_by_model"))) * 8
            + int(bool(r.get("repro_green"))) * 4
            + int(bool(r.get("probe_green"))) * 2
            + int((r.get("patch_bytes") or 0) > 0))


attempts = []
for k in range(2):
    while True:
        try:
            socket.create_connection(("pypi.org", 443), timeout=10).close(); break
        except OSError:
            time.sleep(60)
    t0 = time.time()
    try:
        r = A.run_one(inst)
    except Exception as e:
        r = {"id": IID, "resolved": False, "error": str(e)}
    attempts.append(r)
    print("[attempt %d] resolved=%s probe=%s rank=%d (%.0fs)"
          % (k + 1, r.get("resolved"), r.get("probe_status"), rank(r), time.time() - t0), flush=True)
    if selfv(r):
        break

chosen = dict(max(attempts, key=rank))
json.dump(chosen, open(OUT, "w"), indent=2)
# what headers did it write?
import glob
p = os.path.expanduser("~/swe/traces_v2/%s.patch" % IID)
heads = [l for l in open(p).read().splitlines()
         if "headers" in l.lower() or "Subdomain" in l or "Host" in l or "Domain" in l] if os.path.exists(p) else []
print("\nRESULT: resolved=%s  score_tail=%s"
      % (chosen.get("resolved"), (chosen.get("score_tail") or "")[-100:].replace("\n", " ")), flush=True)
print("headers written:", [h.strip()[:90] for h in heads[:4]], flush=True)
