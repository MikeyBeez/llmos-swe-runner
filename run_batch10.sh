#!/bin/bash
# Overnight batch: 10 stratified SWE-bench Lite instances on the v2 agent.
while kill -0 $\{V9PID:-0\} 2>/dev/null; do sleep 60; done
cd ~/swe
cp -f results_v2.json results_v9_astropy.json 2>/dev/null
cp -f v2_pilot.log v9_pilot.log 2>/dev/null
~/swebench-venv/bin/python swe_lite_select.py 10 > batch10.log 2>&1
echo "=== batch10 start Fri Jul 10 10:47:23 AM CDT 2026 ===" >> batch10.log
PYTHONPATH=/home/bard/Code/LLMOS python3 -u swe_agent_v2.py 10 >> batch10.log 2>&1
echo "=== batch10 done Fri Jul 10 10:47:23 AM CDT 2026 ===" >> batch10.log
