#!/bin/bash
# chain_ablate.sh -- 2026-08-08.
# Waits for the live sympy run to exit, then reruns the SAME fifteen django
# reds as django_red4 with PATTERN_ABLATE=20. Every other flag is identical to
# red4 (which scored 4/15) so the ablation is the only deliberate variable.
# run_list resumes from OUT_NAME, so a restart is safe.
PID=1564076
while kill -0 "$PID" 2>/dev/null; do sleep 120; done
sleep 30

cd /home/bard/swe || exit 1
LOG=runs/ornith/django_red5_ablate.log

IDS=$(python3 -c "import json; print(','.join(r['id'] for r in json.load(open('runs/ornith/django_red4.json'))))")
if [ -z "$IDS" ]; then
    echo "chain_ablate: no ids" >> "$LOG"
    exit 1
fi

# refuse to start if a runner is somehow already up (guard on comm, not cmdline:
# a bare pgrep matches this script's own text)
for p in $(pgrep -f run_list.py 2>/dev/null); do
    c=$(cat /proc/$p/comm 2>/dev/null)
    case "$c" in python*) echo "chain_ablate: runner $p already up, aborting" >> "$LOG"; exit 1;; esac
done

echo "chain_ablate: launching $(echo "$IDS" | tr ',' '\n' | wc -l) instances with PATTERN_ABLATE=20" >> "$LOG"
export IDS
export OUT_NAME=django_red5_ablate.json
export MAX_ATTEMPTS=2 KEEP_FAILED=3
export BANK_AUDIT=1 BANK_AUDIT_MAX=6 ORACLE_GATE=1 REPRO_STRENGTH=1
export SPEC_PROBE=1 COVERAGE_GAP=1 SIBLING_BODY=1 DIFF_HYGIENE=1 DIFF_REPAIR=1
export PATTERN_ABLATE=20
exec python3 -u run_list.py >> "$LOG" 2>&1
