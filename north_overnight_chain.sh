#!/bin/bash
# Overnight chain: wait for easy run, seed full1 from easy results (avoid
# redoing them), then run North over the full 104-set until morning.
cd /home/bard/swe
while pgrep -f "[r]un_north_easy.py" >/dev/null; do sleep 60; done
echo "$(date): easy run done, seeding + starting North full regression" >> runs/north/chain.log
python3 -c "
import json, os
easy = json.load(open(\"runs/north/easy1.json\")) if os.path.isfile(\"runs/north/easy1.json\") else []
full = json.load(open(\"runs/north/full1.json\")) if os.path.isfile(\"runs/north/full1.json\") else []
have = {r[\"id\"] for r in full}
for r in easy:
    if r[\"id\"] not in have:
        full.append(r); have.add(r[\"id\"])
json.dump(full, open(\"runs/north/full1.json\",\"w\"), indent=2)
print(\"seeded full1 with\", len(full), \"results\")
" >> runs/north/chain.log 2>&1
NUM_PREDICT=4096 nohup python3 -u run_north_full.py >> runs/north/full1.log 2>&1
echo "$(date): North full regression finished/stopped" >> runs/north/chain.log
