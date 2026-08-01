#!/bin/bash
# Chain (2026-08-01): when the running four_audit finishes, launch the SAME
# four instances with ORACLE_GATE=1 and GREEN_AUDIT=0. Two runs, one variable
# apart: audit-only (self-judged) vs oracle-gated. The pair measures how much
# of the 27% incomplete-fix class each approach converts. Numbers from the
# oracle run are ORACLE-GATED and must never be compared to self-judged runs.
cd /home/bard/swe
while pgrep -f "run_list.py" >/dev/null; do sleep 120; done
sleep 30
SWE_TEMP=0.6 REPERTOIRE_SEGMENTS=1 SEG1_TURNS=60 SEG_TURNS=10 REPERTOIRE_MAX=13 \
REPRO_GATE=1 PHASE_WALL_CAP=1800 REPRO_PROMOTE=1 REPRO_PROMOTE_MAX=3 \
REPRO_QUALITY=1 REPRO_SEED=1 GREEN_AUDIT=0 ORACLE_GATE=1 \
MAX_ATTEMPTS=4 KEEP_FAILED=3 SIBLING_BODY=1 REPERTOIRE_WALL=2400 \
OUT_NAME=four_oracle.json \
IDS=astropy__astropy-14365,django__django-16820,django__django-16255,django__django-15498 \
python3 -u run_list.py > runs/ornith/four_oracle.log 2>&1
