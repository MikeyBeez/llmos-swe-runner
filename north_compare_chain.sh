#!/bin/bash
# Wait for ornith compare to finish, switch server to North, run North over the
# SAME 18 instances on 1-pass/200 for a clean both-models-same-config head-to-head.
cd /home/bard/swe
while pgrep -f "[r]un_ornith_compare.py" >/dev/null; do sleep 60; done
echo "$(date): ornith compare done, switching to North" >> runs/north/compare_chain.log
bash /home/bard/start_north_tuned.sh >> runs/north/compare_chain.log 2>&1
# wait for health
for i in $(seq 1 30); do sleep 5; curl -sf -m3 localhost:8080/health >/dev/null 2>&1 && break; done
rm -f runs/north/north_compare1.json
NUM_PREDICT=4096 nohup python3 -u run_north_compare.py >> runs/north/north_compare1.log 2>&1
echo "$(date): North compare finished" >> runs/north/compare_chain.log
