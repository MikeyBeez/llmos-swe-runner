import json
try:
    print(len(json.load(open("/home/bard/swe/runs/ornith/compare2.json"))))
except Exception:
    print(0)
