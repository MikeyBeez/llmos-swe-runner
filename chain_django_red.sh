#!/bin/bash
# chain_django_red.sh -- 2026-08-05
# Waits for the untried run (PID 937911) to finish, then re-attacks the Django
# reds in a FRESH python so it picks up mechanisms added mid-run:
#   - coverage-gap (crash bucket: patches that throw on an unexercised path)
#   - repair_wrap_block (the 12453 malformed class)
#   - idioms atlas + grain-of-salt hint (wrong-behaviour / spec-inference)
# Clean A/B: same instances, everything armed. run_list resumes from OUT_NAME.
PID=937911
while kill -0 "$PID" 2>/dev/null; do sleep 120; done
sleep 30
cd /home/bard/swe || exit 1

IDS=$(python3 -c "
import json
d=json.load(open('runs/ornith/untried.json'))
reds=[r['id'] for r in d if not r.get('resolved') and r['id'].startswith('django')]
print(','.join(reds))
")
if [ -z "$IDS" ]; then
    echo 'chain_django_red: no django reds' >> runs/ornith/django_red.log
    exit 0
fi
echo "chain_django_red: rerunning $(echo $IDS | tr ',' '\n' | wc -l) django reds" >> runs/ornith/django_red.log

export IDS
export OUT_NAME=django_red_rerun.json
export MAX_ATTEMPTS=2 KEEP_FAILED=3
export SWE_TEMP=0.6 REPERTOIRE_SEGMENTS=1 REPERTOIRE_MAX=13
export REPERTOIRE_WALL=2400 PHASE_WALL_CAP=1800
export ORACLE_GATE=1 GREEN_AUDIT=0 SPEC_PROBE=1 COVERAGE_GAP=1 SIBLING_BODY=1 DIFF_HYGIENE=1 DIFF_REPAIR=1
exec python3 -u run_list.py >> runs/ornith/django_red.log 2>&1
