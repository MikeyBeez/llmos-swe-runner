#!/bin/bash
# Wait for the current batch (pid 1533835), then rerun all 9 instances on
# the strict fix phase (red->green reproduction gate) + reflex error search
# + mid-run critic. Archives the old batch's results first.
while kill -0 1533835 2>/dev/null; do sleep 60; done
cd ~/swe
cp -f results_v2.json results_batch_oldfix.json 2>/dev/null
cp -f batch10.log batch_oldfix.log 2>/dev/null
rm -f results_v2.json
echo "=== batch9 STRICT fix phase start $(date) ===" > batch10.log
PYTHONPATH=/home/bard/Code/LLMOS python3 -u swe_agent_v2.py 9 >> batch10.log 2>&1
echo "=== batch done $(date) ===" >> batch10.log
