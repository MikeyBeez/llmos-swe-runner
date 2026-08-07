#!/bin/bash
# When the 5131 test finishes (all 4 attempts or a resolve), run the OTHER
# eight reds with the full stack including reconstruction repair.
cd /home/bard/swe
while pgrep -f "run_list.py" >/dev/null; do sleep 120; done
sleep 30
SWE_TEMP=0.6 REPERTOIRE_SEGMENTS=1 SEG1_TURNS=60 SEG_TURNS=10 REPERTOIRE_MAX=13 \
REPRO_GATE=1 PHASE_WALL_CAP=1800 REPRO_PROMOTE=1 REPRO_PROMOTE_MAX=3 \
REPRO_QUALITY=1 REPRO_SEED=1 GREEN_AUDIT=0 ORACLE_GATE=1 SIBLING_BODY=1 \
DIFF_HYGIENE=1 DIFF_REPAIR=1 MAX_ATTEMPTS=2 KEEP_FAILED=3 REPERTOIRE_WALL=2400 \
OUT_NAME=eight_red.json \
IDS=sympy__sympy-24909,scikit-learn__scikit-learn-25747,psf__requests-2674,pallets__flask-4992,pallets__flask-5063,pydata__xarray-4493,mwaskom__seaborn-3190,pylint-dev__pylint-7228 \
python3 -u run_list.py > runs/ornith/eight_red.log 2>&1
