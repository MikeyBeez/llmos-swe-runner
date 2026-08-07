#!/bin/bash
# chain_untried.sh -- 2026-08-03, Mikey heading to bed.
# "Stop working on the failures for now... queue up all the ones we haven't
# tried yet." Waits for the eight_red run (PID 811601) to finish, then runs
# all 107 never-attempted Lite instances (66 django, 41 sympy; repo-grouped,
# django first for faster early completions). Fresh import arms everything
# added today: idioms atlas, oracle-refusal spec hints, SPEC_PROBE.
# run_list resumes from OUT_NAME, so restarts are safe.
PID=811601
while kill -0 "$PID" 2>/dev/null; do sleep 120; done
sleep 30

cd /home/bard/swe || exit 1

IDS=$(python3 -c "import json; print(','.join(json.load(open('untried_ids.json'))))")
if [ -z "$IDS" ]; then
    echo "chain_untried: no ids" >> runs/ornith/untried.log
    exit 1
fi
echo "chain_untried: launching $(python3 -c "import json; print(len(json.load(open('untried_ids.json'))))") instances" >> runs/ornith/untried.log

export IDS
export OUT_NAME=untried.json
export MAX_ATTEMPTS=2 KEEP_FAILED=3
export SWE_TEMP=0.6 REPERTOIRE_SEGMENTS=1 REPERTOIRE_MAX=13
export REPERTOIRE_WALL=2400 PHASE_WALL_CAP=1800
export ORACLE_GATE=1 GREEN_AUDIT=0 SPEC_PROBE=1 COVERAGE_GAP=1 SIBLING_BODY=1 DIFF_HYGIENE=1 DIFF_REPAIR=1
exec python3 -u run_list.py >> runs/ornith/untried.log 2>&1
