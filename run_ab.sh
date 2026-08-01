#!/bin/bash
# Isolation-discipline A/B. For each instance, run off vs on as FRESH subprocesses
# (the fix prompt is baked at import, so condition must be per-process). Fast
# instances first for early behavioral signal (reads vs experiments). Outcome +
# turns + tool-mix recorded per run in runs/ab/results.jsonl.
cd ~/swe
mkdir -p runs/ab
log(){ echo "$@" >> runs/ab/ab.log; }
one(){ log "=== cond=$1 $2 rep$3  $(date) ==="; python3 -u run_ab_one.py "$1" "$2" "$3" >> runs/ab/ab.log 2>&1; }

for inst in django__django-16255 django__django-16046 django__django-16379; do
  for rep in 1 2; do
    one off "$inst" "$rep"
    one on  "$inst" "$rep"
  done
done
# marquee: the 171-turn grind, on-only (off baseline = tonight's 171 turns / PASS)
one on django__django-16910 1
log "AB DONE $(date)"
