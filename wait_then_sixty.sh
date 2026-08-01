#!/bin/bash
# Overnight chain, stage 2 (2026-08-01, Mikey: "queue up 60. The worst that
# can happen is they wont finish"). Waits for BOTH the running four_audit and
# the chained four_oracle (wait_then_oracle.sh) to finish, then runs 60 fresh
# instances -- never attempted before tonight -- with the full new stack:
# ORACLE_GATE on, so results are ORACLE-GATED numbers. MAX_ATTEMPTS=2 to
# favour breadth over depth overnight. run_list resumes from sixty_oracle.json
# if interrupted.
cd /home/bard/swe
while pgrep -f "run_list.py" >/dev/null || pgrep -f "wait_then_oracle" >/dev/null; do sleep 180; done
sleep 30
SWE_TEMP=0.6 REPERTOIRE_SEGMENTS=1 SEG1_TURNS=60 SEG_TURNS=10 REPERTOIRE_MAX=13 \
REPRO_GATE=1 PHASE_WALL_CAP=1800 REPRO_PROMOTE=1 REPRO_PROMOTE_MAX=3 \
REPRO_QUALITY=1 REPRO_SEED=1 GREEN_AUDIT=0 ORACLE_GATE=1 \
MAX_ATTEMPTS=2 KEEP_FAILED=3 SIBLING_BODY=1 REPERTOIRE_WALL=2400 \
OUT_NAME=sixty_oracle.json \
IDS=$(cat /home/bard/swe/sixty.ids) \
python3 -u run_list.py > runs/ornith/sixty_oracle.log 2>&1
