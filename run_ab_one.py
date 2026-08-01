"""One A/B run: run_ab_one.py <cond:on|off> <instance_id> <rep>.
Sets ISOLATE_DISCIPLINE per condition BEFORE importing the harness (the fix
prompt is baked at import), runs the instance once, and records outcome +
turns + tool-mix (reads vs experiments) to runs/ab/results.jsonl. Per-run
events go to runs/ab/ev/<cond>_<inst>_<rep>.jsonl so turns/tool-mix are clean.
"""
import json, os, sys, time, socket

SWE = os.path.expanduser("~/swe")
cond, iid, rep = sys.argv[1], sys.argv[2], sys.argv[3]
ABDIR = os.path.join(SWE, "runs", "ab")
os.makedirs(os.path.join(ABDIR, "ev"), exist_ok=True)
evpath = os.path.join(ABDIR, "ev", "%s_%s_%s.jsonl" % (cond, iid, rep))

os.environ["ISOLATE_DISCIPLINE"] = "1" if cond == "on" else "0"
os.environ["LLMOS_EVENTS"] = evpath
os.environ.pop("DISABLE_KB", None)
os.environ["USE_SPEC_ENV"] = "1"
os.environ["TOOL_BUDGET_RECENT"] = "6000"
os.environ["TOOL_BUDGET_OLD"] = "1200"
os.environ["TOOL_RECENT_TURNS"] = "16"
os.environ["TRIAGE"] = "1"
os.environ["ATLAS_DIR"] = os.path.join(SWE, "atlas")

sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
import swe_agent_v2 as A

insts = {i["instance_id"]: i
         for i in json.load(open(os.path.join(SWE, "instances_full300.json")))}
CANON = json.load(open(os.path.join(SWE, "canonical_python.json")))
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


def wait_net():
    while True:
        try:
            socket.create_connection(("pypi.org", 443), timeout=10).close()
            return
        except OSError:
            time.sleep(60)


wait_net()
t0 = time.time()
try:
    r = A.run_one(inst)
except Exception as e:
    r = {"resolved": False, "error": str(e)}
secs = round(time.time() - t0)

turns = reads = exps = patches = 0
try:
    for line in open(evpath):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("phase") != "fix":
            continue
        if e.get("type") == "generation":
            turns += 1
        elif e.get("type") == "tool_call":
            t = e.get("tool")
            if t in ("read_range", "locate"):
                reads += 1
            elif t in ("check", "reproduce"):
                exps += 1
            elif t == "patch":
                patches += 1
except Exception:
    pass

rec = {"cond": cond, "id": iid, "rep": rep, "resolved": bool(r.get("resolved")),
       "secs": secs, "fix_turns": turns, "reads": reads, "exps": exps,
       "patches": patches}
open(os.path.join(ABDIR, "results.jsonl"), "a").write(json.dumps(rec) + "\n")
print("AB %-3s %-24s rep%s -> %-4s turns=%d reads=%d exps=%d patch=%d secs=%d"
      % (cond, iid, rep, "PASS" if rec["resolved"] else "miss",
         turns, reads, exps, patches, secs), flush=True)
