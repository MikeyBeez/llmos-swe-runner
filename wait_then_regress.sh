#!/bin/bash
# After the sixty finishes: rerun the 18-instance regression suite under the
# CURRENT stack (sibling/green-audit/oracle-era harness). The known-good set
# is defended after every substantive change; the last full check predates
# the oracle work. Self-judged config inside run_regress18.py, unchanged, so
# the number stays comparable to the 16/18 baseline.
cd /home/bard/swe
while pgrep -f "run_list.py" >/dev/null; do sleep 300; done
sleep 60
python3 -u run_regress18.py > runs/ornith/regress18_v5.log 2>&1
