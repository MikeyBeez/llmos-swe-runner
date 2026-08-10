#!/bin/bash
# After newrepos1 (pid 1689303) finishes: build the list of EVERY Lite
# instance still never run under the ornith harness and run them all.
# The list is generated AFTER newrepos1 exits, so its instances and any
# other completed work are excluded automatically.
while kill -0 1689303 2>/dev/null; do sleep 120; done
sleep 30
cd /home/bard/swe
python3 - <<PYEOF
import json, glob
import pyarrow.parquet as pq
ids=[str(x) for x in pq.read_table("lite.parquet",columns=["instance_id"]).column("instance_id").to_pylist()]
att=set()
for p in glob.glob("runs/ornith/*.json"):
    try: d=json.load(open(p))
    except Exception: continue
    if not isinstance(d,list): continue
    for r in d:
        if isinstance(r,dict):
            i=r.get("id") or r.get("instance_id")
            if i: att.add(i)
left=[i for i in ids if i not in att]
open("rest_all.txt","w").write("\n".join(left)+"\n")
print("remaining never-run-under-ornith:", len(left))
PYEOF
env IDS="$(paste -sd, rest_all.txt)" OUT_NAME=rest_all.json \
  MAX_ATTEMPTS=1 ORACLE_GATE=1 CONTAINER_APPEAL=1 \
  REPERTOIRE_SEGMENTS=1 REPERTOIRE_MAX=6 REPERTOIRE_WALL=2400 PHASE_WALL_CAP=1800 \
  SEG1_WALL_FRAC=0.4 SEG_ECHO=1 EDIT_LINE=1 THRASH_ECHO=1 \
  python3 run_list.py > runs/ornith/rest_all.log 2>&1
echo "REST_ALL DONE" >> runs/ornith/rest_all.log
