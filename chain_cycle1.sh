#!/bin/bash
# SINGLE-EXAMPLE LOOP, cycle 1 (methodology agreed 2026-08-11).
# The example: matplotlib-23299, the specimen the diagnosis ladder was built
# from. It already ran and failed; the fix (DIAG_GATE) is committed; this is
# the ONE re-run. Judge by mechanism: the trace diag record should show the
# differential run and a writer-role site declaration -- rc_context, not
# get_backend -- before any resolve is even read.
while kill -0 1859153 2>/dev/null; do sleep 60; done
sleep 20
cd /home/bard/swe
env IDS="matplotlib__matplotlib-23299" OUT_NAME=cycle1_23299.json \
  MAX_ATTEMPTS=1 ORACLE_GATE=1 CONTAINER_APPEAL=1 \
  DIAG_GATE=1 REPRO_CONTRACT=1 REPRO_FORCE_DRAW=1 \
  REPERTOIRE_SEGMENTS=1 REPERTOIRE_MAX=6 REPERTOIRE_WALL=2400 PHASE_WALL_CAP=1800 \
  SEG1_WALL_FRAC=0.4 SEG_ECHO=1 EDIT_LINE=1 THRASH_ECHO=1 \
  python3 run_list.py > runs/ornith/cycle1_23299.log 2>&1
echo "CYCLE1 DONE" >> runs/ornith/cycle1_23299.log
