#!/usr/bin/env python3
"""Judge ONE candidate patch in the official SWE-bench container.

    python3 judge_one.py <instance_id> <patch_file>

Prints exactly one verdict line:  VERDICT: RESOLVED | UNRESOLVED | ERROR ...

This replaces referee.py in the CONTAINER_APPEAL path.  referee.py assumed
pytest and broke on every sympy image (their testbeds grade via bin/test and
have no pytest at all).  Rather than teach our referee each repo dialect,
shell out to the official harness, which already knows all twelve -- commands,
log parsers, and labels.  2026-08-09: it confirmed all 18 fresh32 misses and
all 14 fresh32 wins, so it and the in-env judge agreed 32/32 on that run.

The judge environment is never modified: no pip installs into testbeds, no
substitute runners.  If the image cannot grade, the verdict is ERROR, not a
guess.
"""
import json, os, subprocess, sys, time

SWE = "/home/bard/swe"
PY = os.path.join(SWE, ".judge", "bin", "python")

def main():
    if len(sys.argv) != 3:
        print("VERDICT: ERROR usage: judge_one.py <instance_id> <patch_file>")
        return 2
    iid, pf = sys.argv[1], sys.argv[2]
    try:
        patch = open(pf).read()
    except OSError as e:
        print("VERDICT: ERROR cannot read %s: %s" % (pf, e))
        return 2
    if not patch.strip():
        print("VERDICT: UNRESOLVED empty patch")
        return 1
    tag = "appeal_%s_%d" % (iid.replace("__", "_"), int(time.time()))
    os.makedirs(os.path.join(SWE, "appeals"), exist_ok=True)
    pred_path = os.path.join(SWE, "appeals", tag + ".jsonl")
    with open(pred_path, "w") as f:
        f.write(json.dumps({"instance_id": iid,
                            "model_name_or_path": "appeal",
                            "model_patch": patch}) + "\n")
    try:
        subprocess.run(
            [PY, "-m", "swebench.harness.run_evaluation",
             "--dataset_name", "princeton-nlp/SWE-bench_Lite",
             "--predictions_path", pred_path,
             "--run_id", tag, "--namespace", "swebench",
             "--max_workers", "1"],
            cwd=SWE, capture_output=True, text=True, timeout=3300)
    except subprocess.TimeoutExpired:
        print("VERDICT: ERROR harness timeout")
        return 2
    report = os.path.join(SWE, "appeal.%s.json" % tag)
    if not os.path.exists(report):
        print("VERDICT: ERROR no report written")
        return 2
    d = json.load(open(report))
    if iid in (d.get("resolved_ids") or []):
        print("VERDICT: RESOLVED %s by official container" % iid)
        return 0
    if iid in (d.get("error_ids") or []):
        print("VERDICT: ERROR harness reported instance error")
        return 2
    print("VERDICT: UNRESOLVED %s in official container" % iid)
    return 1

if __name__ == "__main__":
    sys.exit(main())
