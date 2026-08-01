#!/bin/bash
# BLAST_RADIUS live A/B. Varies BLAST_RADIUS only (standard harness otherwise).
# Waits for the stuck A/B (run_ab_stuck_one.py) to finish first -- single GPU.
# Focus: the broke-neighbor instances, where neighbor_tests should let the agent
# self-catch its regression.
cd ~/swe
mkdir -p runs/ab_blast
log(){ echo "$@" >> runs/ab_blast/ab.log; }
one(){ log "=== cond=$1 $2 rep$3  $(date) ==="; python3 -u run_ab_blast_one.py "$1" "$2" "$3" >> runs/ab_blast/ab.log 2>&1; }
log "waiting for stuck A/B (run_ab_stuck_one.py) to finish  $(date)"
while pgrep -f "run_ab_stuck_one.py" >/dev/null 2>&1; do sleep 60; done
log "stuck A/B done; starting BLAST_RADIUS A/B  $(date)"
for inst in django__django-16255 django__django-16379; do
  for rep in 1 2; do
    one off "$inst" "$rep"
    one on  "$inst" "$rep"
  done
done
log "AB_BLAST DONE $(date)"
