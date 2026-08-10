#!/bin/bash
# Wait for tail35 (pid 1643911) to finish, then run the never-run-under-ornith
# new-repo set with the canonical-judge appeal path live.
while kill -0 1643911 2>/dev/null; do sleep 120; done
sleep 30
cd /home/bard/swe
env IDS="$(paste -sd, newrepos.txt)" OUT_NAME=newrepos1.json \
  MAX_ATTEMPTS=1 ORACLE_GATE=1 CONTAINER_APPEAL=1 \
  REPERTOIRE_SEGMENTS=1 REPERTOIRE_MAX=6 REPERTOIRE_WALL=2400 PHASE_WALL_CAP=1800 \
  SEG1_WALL_FRAC=0.4 SEG_ECHO=1 EDIT_LINE=1 THRASH_ECHO=1 \
  python3 run_list.py > runs/ornith/newrepos1.log 2>&1
echo "NEWREPOS1 DONE" >> runs/ornith/newrepos1.log
