#!/bin/bash
# Wait for the running instance (astropy-14995, instance 2) to finish -> then
# STOP the compare runner (which would otherwise waste ~25 min on django-15061,
# an instance every model misses) and instead run ONE known-solvable instance:
# django-15347 (ornith 289s, north 589s, both solved). Fair second data point.
cd ~/swe
echo "watcher: waiting for instance 2 to finish $(date)" >> runs/bonsai/swap.log
while true; do
  n=$(python3 -c "import json,os; f='runs/bonsai/compare1.json'; print(len(json.load(open(f))) if os.path.exists(f) else 0)" 2>/dev/null)
  [ -z "$n" ] && n=0
  if [ "$n" -ge 2 ]; then break; fi
  sleep 30
done
echo "watcher: instance 2 done (n=$n), stopping compare runner $(date)" >> runs/bonsai/swap.log
pkill -9 -f "[r]un_bonsai_compare.py"
sleep 4
nohup python3 -u run_bonsai_one.py django__django-15347 >> runs/bonsai/compare1.log 2>&1 &
echo "watcher: launched django-15347 (pid $!) $(date)" >> runs/bonsai/swap.log
