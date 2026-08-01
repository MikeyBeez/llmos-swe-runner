#!/bin/bash
# Stuck-breaker live A/B. Varies STUCK_ESCALATE only; ISOLATE_DISCIPLINE off and
# TRUNC_RETRY on in both arms. Waits for the prior A/B marquee (run_ab_one.py) to
# finish first -- single GPU, llama-server --parallel 1. Fresh subprocess per cell.
cd ~/swe
mkdir -p runs/ab_stuck
log(){ echo "$@" >> runs/ab_stuck/ab.log; }
one(){ log "=== cond=$1 $2 rep$3  $(date) ==="; python3 -u run_ab_stuck_one.py "$1" "$2" "$3" >> runs/ab_stuck/ab.log 2>&1; }

# wait out the currently-running prior A/B (its last cell is the 16910 marquee)
log "waiting for prior A/B (run_ab_one.py) to finish  $(date)"
while pgrep -f "run_ab_one.py" >/dev/null 2>&1; do sleep 60; done
log "prior A/B done; starting stuck A/B  $(date)"

for inst in django__django-16255 django__django-16046 django__django-16379; do
  for rep in 1 2; do
    one off "$inst" "$rep"
    one on  "$inst" "$rep"
  done
done
# marquee: the long 16910 grind with the breaker on, to confirm it does NOT bite a
# legitimate long solve (offline replay: 0 blocked on this instance).
one on django__django-16910 1
log "AB_STUCK DONE $(date)"
