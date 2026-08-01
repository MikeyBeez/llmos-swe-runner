import json, os
import pandas as pd
df = pd.read_parquet(os.path.expanduser("~/swe/lite_full.parquet"))
# Interleave repos (round-robin, newest first per repo) so a recurring
# repo-specific harness error surfaces early instead of 3 days in.
groups = {r: g.sort_values("created_at", ascending=False).reset_index(drop=True)
          for r, g in df.groupby("repo")}
out, i = [], 0
while len(out) < len(df):
    for r in sorted(groups):
        if i < len(groups[r]):
            row = groups[r].iloc[i]
            out.append({
                "instance_id":       row.instance_id,
                "repo":              row.repo,
                "base_commit":       row.base_commit,
                "problem_statement": row.problem_statement,
                "test_patch":        row.test_patch,
                "gold_patch":        row.patch,
                "FAIL_TO_PASS":      json.loads(row.FAIL_TO_PASS),
                "PASS_TO_PASS":      json.loads(row.PASS_TO_PASS)[:6],
            })
    i += 1
json.dump(out, open(os.path.expanduser("~/swe/instances_full300.json"), "w"))
print("wrote", len(out), "instances")
