#!/bin/bash
cd ~/swe
echo "compare3(inject) waiter started $(date)" >> runs/ornith/compare3.log
while true; do
  n=$(python3 count_compare2.py 2>/dev/null || echo 0)
  [ "$n" -ge 18 ] && break
  sleep 120
done
echo "compare2 done (n=$n); starting compare3 NEIGHBOR_INJECT=1 $(date)" >> runs/ornith/compare3.log
NEIGHBOR_INJECT=1 python3 -u run_ornith_compare3.py >> runs/ornith/compare3.log 2>&1
