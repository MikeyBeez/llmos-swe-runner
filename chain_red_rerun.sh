#!/bin/bash
# chain_red_rerun.sh -- 2026-08-02
# Waits for the eight_red run (PID 811601) to finish, then reruns whatever
# it left unresolved, in a FRESH python. The fresh import is the point:
# it picks up the spec-reconstruction hints added today (dunder-symmetry +
# return-idiom oracle hint, PACKAGE IDIOMS atlas section), which the live
# process cannot see. Clean A/B: same instances, same config, hints armed.
PID=811601
while kill -0 "$PID" 2>/dev/null; do sleep 120; done
sleep 30

cd /home/bard/swe || exit 1

IDS=$(python3 - <<'PY'
import json
want = "pydata__xarray-5131,sympy__sympy-24909,scikit-learn__scikit-learn-25747,pallets__flask-5063,pydata__xarray-4493,mwaskom__seaborn-3190,pylint-dev__pylint-7228".split(",")
try:
    done = {r["id"]: bool(r.get("resolved")) for r in json.load(open("runs/ornith/eight_red.json"))}
except Exception:
    done = {}
print(",".join(i for i in want if not done.get(i, False)))
PY
)
if [ -z "$IDS" ]; then
    echo "chain: everything resolved, nothing to rerun" >> runs/ornith/red_rerun.log
    exit 0
fi
echo "chain: rerunning with new hints: $IDS" >> runs/ornith/red_rerun.log

export IDS
export OUT_NAME=red_rerun.json
export MAX_ATTEMPTS=2 KEEP_FAILED=3
export SWE_TEMP=0.6 REPERTOIRE_SEGMENTS=1 REPERTOIRE_MAX=13
export REPERTOIRE_WALL=2400 PHASE_WALL_CAP=1800
export ORACLE_GATE=1 GREEN_AUDIT=0 SPEC_PROBE=1 SIBLING_BODY=1 DIFF_HYGIENE=1 DIFF_REPAIR=1
exec python3 -u run_list.py >> runs/ornith/red_rerun.log 2>&1
