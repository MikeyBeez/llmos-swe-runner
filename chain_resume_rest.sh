#!/bin/bash
# After atlas_retest (pid 1859153) finishes, resume rest_all where it left
# off (OUT file already holds the completed instances; resume skips them).
while kill -0 1859153 2>/dev/null; do sleep 120; done
sleep 30
cd /home/bard/swe
env IDS="$(paste -sd, rest_all.txt)" OUT_NAME=rest_all.json \
  MAX_ATTEMPTS=1 ORACLE_GATE=1 CONTAINER_APPEAL=1 REPRO_CONTRACT=1 REPRO_FORCE_DRAW=1 \
  REPERTOIRE_SEGMENTS=1 REPERTOIRE_MAX=6 REPERTOIRE_WALL=2400 PHASE_WALL_CAP=1800 \
  SEG1_WALL_FRAC=0.4 SEG_ECHO=1 EDIT_LINE=1 THRASH_ECHO=1 \
  python3 run_list.py >> runs/ornith/rest_all.log 2>&1
echo "REST_ALL DONE" >> runs/ornith/rest_all.log
