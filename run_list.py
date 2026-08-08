"""LAGUNA REGRESSION (Mikey, 2026-07-23): run every instance we have EVER
resolved, under the new model, same harness, same protocol.

"Then run all the passing examples. Let's see if we can still pass those.
You may need to start and stop a few times if the model responds too
differently."

Design points:
  - The passing set is built from ALL results history (runs/*/results*.json,
    results*.json, workshop iter*.json, graduated.json): any instance with
    resolved=true at least once. Frozen to runs/laguna/compare_set.json on
    first build so restarts see the same set.
  - Same config as workshop.py: TTS-2 (two draws at temperature 1.0, break on
    resolved), form_rank on GIVEN evidence chooses, same env vars, same
    python pinning. Different model is the ONLY variable.
  - RESUMABLE: results dump after every instance; done ids are skipped, so
    stop/fix/restart loses at most the in-flight instance.
  - Answer leakage rules unchanged: nothing here reads gold/test patches.

usage: run_passing.py            (build set if absent, run/resume)
       run_passing.py --rebuild  (rebuild the passing set first)
writes ~/swe/runs/laguna/compare1.json
"""
import json, os, sys, glob, time, socket, subprocess

SWE = os.path.expanduser("~/swe")
LDIR = os.path.join(SWE, "runs", "ornith")
os.makedirs(LDIR, exist_ok=True)
SETF = os.path.join(LDIR, "compare_set.json")
OUT = os.path.join(LDIR, os.environ.get("OUT_NAME","regress18.json"))
# Independent attempts per instance, selected by form_rank. This is the
# test-time-scaling lever: DeepSWE reports 42.2% at k=1 and 57.9% at k=8
# on the same 32B model. Our own history says the same thing -- 45% ever
# resolved against ~15% single-pass.
MAX_ATTEMPTS = int(os.environ.get("MAX_ATTEMPTS", "1"))
# how many FAILED patches to retain per instance for post-hoc refereeing
KEEP_FAILED = int(os.environ.get("KEEP_FAILED", "3"))
MODEL_TAG = "ornith-1.0-35b-llamacpp"

insts = {i["instance_id"]: i
         for i in json.load(open(os.path.join(SWE, "instances_full300.json")))}


def build_set():
    ever = set()
    srcs = (glob.glob(os.path.join(SWE, "runs", "*", "results*.json"))
            + glob.glob(os.path.join(SWE, "results*.json"))
            + glob.glob(os.path.join(SWE, "runs", "workshop", "iter*.json")))
    for p in srcs:
        try:
            d = json.load(open(p))
        except Exception:
            continue
        if not isinstance(d, list):
            continue
        for x in d:
            if isinstance(x, dict) and x.get("id") and x.get("resolved"):
                ever.add(x["id"])
    try:
        for g in json.load(open(os.path.join(SWE, "runs", "workshop",
                                             "graduated.json"))):
            if isinstance(g, dict) and g.get("id"):
                ever.add(g["id"])
    except Exception:
        pass
    ids = sorted(i for i in ever if i in insts)
    json.dump(ids, open(SETF, "w"), indent=1)
    print("passing set built: %d instances -> %s" % (len(ids), SETF))
    return ids


# run_list.py: same engine, explicit instance list from $IDS (comma separated).
# Everything else -- config, resume, leak rules -- is unchanged from
# run_regress18.py, so results are directly comparable.
ids = [x.strip() for x in os.environ.get("IDS", "").split(",") if x.strip()]
missing = [i for i in ids if i not in insts]
if not ids:
    raise SystemExit("set IDS=inst1,inst2,...")
if missing:
    raise SystemExit("unknown instance ids: %s" % missing)
print("explicit list: %d instances" % len(ids))


def busy():
    pats = "[w]orkshop.py|[r]erun_failed4.py|[r]un300_v3.py"
    return bool(subprocess.run(["pgrep", "-f", pats],
                               capture_output=True, text=True).stdout.strip())


while busy():
    print("busy: waiting", flush=True)
    time.sleep(180)

sys.path.insert(0, os.path.expanduser("~/Code/LLMOS"))
os.environ.pop("DISABLE_KB", None)
os.environ["USE_SPEC_ENV"] = "1"
os.environ["TOOL_BUDGET_RECENT"] = "6000"
os.environ["TOOL_BUDGET_OLD"] = "1200"
os.environ["TOOL_RECENT_TURNS"] = "16"
os.environ["TRIAGE"] = "1"
os.environ["ATLAS_DIR"] = os.path.expanduser("~/swe/atlas")
import swe_agent_v2 as A

CANON = json.load(open(os.path.join(SWE, "canonical_python.json")))
try:
    results = json.load(open(OUT))
except Exception:
    results = []
done = {r["id"] for r in results}
print("resume: %d of %d already done" % (len(done), len(ids)), flush=True)


def form_rank(r):
    _g = r.get("given_tests_ok")
    given = ((8 if _g is True else (-8 if _g is False else 0))
             + int(r.get("syntax_ok", True) is not False) * 4
             + int((r.get("patch_bytes") or 0) > 0))
    self_authored = (int(bool(r.get("fix_verified_by_model"))) * 0.4
                     + int(bool(r.get("repro_green"))) * 0.2
                     + int(bool(r.get("probe_green"))) * 0.1)
    return given + self_authored


def wait_net():
    while True:
        try:
            socket.create_connection(("pypi.org", 443), timeout=10).close()
            return
        except OSError:
            time.sleep(60)


for iid in [i for i in ids if i not in done]:
    inst = insts[iid]
    pin = CANON.get(iid)
    if pin:
        os.environ["PIN_PYTHON"] = pin
    else:
        os.environ.pop("PIN_PYTHON", None)
    if pin in ("3.6", "3.7"):
        os.environ["PIN_BACKEND"] = "conda"
    else:
        os.environ.pop("PIN_BACKEND", None)
    attempts = []
    _base_budget = A.FIX_BUDGET
    for k in range(MAX_ATTEMPTS):
        wait_net()
        A.FIX_BUDGET = _base_budget if k == 0 else A.RETRY_FIX_BUDGET
        t0 = time.time()
        try:
            r = A.run_one(inst)
        except Exception as e:
            r = {"id": iid, "resolved": False, "error": str(e)}
        r["attempt"] = k + 1
        r["attempt_secs"] = round(time.time() - t0)
        # Keep the diff of each FAILED attempt -- a failure is the artifact
        # worth putting in front of an independent judge, and the next
        # attempt's revert destroys it. Successes are already archived in
        # traces/. Retain the last KEEP_FAILED per instance, pruned by mtime.
        if not r.get("resolved"):
            try:
                _pdir = os.path.join(LDIR, "patches")
                os.makedirs(_pdir, exist_ok=True)
                _wt = os.path.join(SWE, "work", iid)
                # score() writes the model's patch to traces_v2/<id>.patch
                # BEFORE it applies the graded test patch to the tree. That
                # file is the artifact we want, by construction.
                #
                # Do NOT rebuild it from the work tree here. score() leaves
                # the test patch applied, so a diff taken now contains it --
                # and the old guard, ':(exclude)tests', only excludes a
                # TOP-LEVEL tests/ directory. Django's tests are top-level so
                # it looked right; astropy's are at astropy/io/ascii/tests/
                # and sailed straight through. Measured 2026-08-01: the
                # astropy-14365 archive came out 2156 bytes carrying the
                # official test helper `lowercase_header`, against 926 bytes
                # for the real patch.
                _d = ""
                _tp = os.path.join(SWE, "traces_v2", iid + ".patch")
                try:
                    with open(_tp) as _fh:
                        _d = _fh.read()
                except OSError:
                    pass
                if not _d.strip():
                    # fallback only. glob pathspecs so nested test dirs are
                    # actually excluded this time.
                    _d = subprocess.run(
                        "git diff -- . ':(exclude,glob)**/tests/**' "
                        "':(exclude,glob)**/test/**' "
                        "':(exclude,glob)**/test_*.py' "
                        "':(exclude,glob)**/*_test.py' "
                        "':(exclude,glob)**/tests.py'",
                        shell=True, cwd=_wt, capture_output=True,
                        text=True, timeout=120).stdout or ""
                _stem = os.path.join(_pdir, "%s.attempt%d" % (iid, k + 1))
                with open(_stem + ".patch", "w") as _fh:
                    _fh.write(_d)
                # a bare diff does not say what it scored
                with open(_stem + ".json", "w") as _fh:
                    json.dump({k2: r.get(k2) for k2 in
                               ("id", "attempt", "secs", "score_tail",
                                "syntax_ok", "seen_red", "repro_green",
                                "given_tests_ok", "patch_bytes")},
                              _fh, indent=1)
                r["patch_saved"] = len(_d)
                # prune: keep the newest KEEP_FAILED for this instance
                _mine = sorted(
                    (f for f in os.listdir(_pdir)
                     if f.startswith(iid + ".attempt") and f.endswith(".patch")),
                    key=lambda f: os.path.getmtime(os.path.join(_pdir, f)),
                    reverse=True)
                for _old in _mine[KEEP_FAILED:]:
                    for _ext in (".patch", ".json"):
                        try:
                            os.remove(os.path.join(
                                _pdir, _old[:-6] + _ext))
                        except OSError:
                            pass
            except Exception as _e:
                r["patch_saved"] = "error: %s" % _e
        # CONTAINER APPEAL (Mikey, 2026-08-02): our env graded GOLD itself as
        # a failure on xarray-5131. Any in-env failure gets re-judged in the
        # OFFICIAL swebench image; referee.py refuses to mean anything unless
        # base fails and gold passes there first. If the container says the
        # archived patch resolves, the in-env verdict was environmental and
        # the attempt is recorded as resolved (resolved_by=container).
        # Mikey, precisely: appeal ONLY a patch we had reason to BELIEVE --
        # its own reproduction went green, or the fix tests passed and only
        # the regression leg failed. A patch nobody believed just failed.
        _believed = bool(r.get("repro_green")) or "F2P passed" in (r.get("score_tail") or "")
        if not r.get("resolved") and _believed and os.environ.get("CONTAINER_APPEAL", "0") == "1":
            try:
                _rc = subprocess.run(
                    ["python3", "referee.py", iid],
                    cwd=SWE, capture_output=True, text=True, timeout=2400)
                _out = (_rc.stdout or "") + (_rc.stderr or "")
                _tag = "attempt%d" % (k + 1)
                _line = next((l for l in _out.splitlines()
                              if _tag in l and ("PASS" in l or "RESOLVED" in l)), "")
                print(" -- container appeal: %s" % (_line or _out.strip().splitlines()[-1][:120] if _out.strip() else "no output"), flush=True)
                if _line:
                    r["resolved"] = True
                    r["resolved_by"] = "container"
                    r["score_tail"] = "in-env FAIL overturned by official container"
            except Exception as _e:
                print(" -- container appeal error: %s" % type(_e).__name__, flush=True)
        attempts.append(r)
        if r.get("resolved"):
            break
    A.FIX_BUDGET = _base_budget
    # SELECTION AUTHORITY (2026-08-08, gated, default OFF).
    # Under ORACLE_GATE the run already spends an oracle bit INSIDE the walk:
    # BANK_AUDIT probes banked candidates and submits one it KNOWS passes. The
    # cross-attempt pick then threw that answer away, because form_rank is
    # deliberately blind to the grade -- so a BANK_AUDIT win, which by
    # construction carries no self-belief, loses to a confident miss.
    # Measured over every run log to date: 318 instances, the gap fires twice
    # (django-12908, sympy-12419) -- 0.6 pts lifetime, but BOTH land after
    # BANK_AUDIT shipped, where it is 2 of 8 wins discarded.
    #
    # RANK_ORACLE=1 makes the oracle the authority END TO END, and only when
    # ORACLE_GATE=1 is already set -- i.e. only for runs whose number is
    # ALREADY a research number that may never be compared to pass@1. With
    # RANK_ORACLE unset (the default) behaviour is bit-identical to before and
    # `resolved` stays leaderboard-legal. Every record names the policy it was
    # selected under, so the two can never be silently pooled.
    _rank_oracle = (os.environ.get("RANK_ORACLE", "0") == "1"
                    and os.environ.get("ORACLE_GATE", "0") == "1")
    if _rank_oracle:
        chosen = dict(max(
            attempts, key=lambda _a: (bool(_a.get("resolved")), form_rank(_a))))
    else:
        chosen = dict(max(attempts, key=form_rank))
    chosen["selection_policy"] = "oracle" if _rank_oracle else "blind"
    chosen["attempts_made"] = len(attempts)
    # RANK TELEMETRY (2026-08-08). The two-metric design below deliberately
    # lets a BANK_AUDIT win lose to a higher-self-belief miss. That is the
    # intended behaviour, but until now the LOSING attempt's evidence was
    # thrown away, so auditing a gap meant re-reading the run log. Record the
    # whole ranking, so every gap is diagnosable from the results file alone.
    # TELEMETRY ONLY -- this does not change selection.
    chosen["attempt_ranks"] = [
        {"attempt": _i + 1,
         "rank": round(form_rank(_a), 3),
         "resolved": bool(_a.get("resolved")),
         "given_tests_ok": _a.get("given_tests_ok"),
         "syntax_ok": _a.get("syntax_ok"),
         "patch_bytes": _a.get("patch_bytes"),
         "repro_green": bool(_a.get("repro_green")),
         "probe_green": bool(_a.get("probe_green")),
         "fix_verified_by_model": bool(_a.get("fix_verified_by_model"))}
        for _i, _a in enumerate(attempts)]
    chosen["model"] = MODEL_TAG
    # TWO METRICS, RECORDED SEPARATELY, NEVER MIXED.
    #
    # form_rank must not see the grade: that is what makes `resolved` a
    # leaderboard-legal pass@1 number, since a real entry submits one patch
    # without knowing the answer. But form_rank ranks on the model's OWN
    # confidence, and BANK_AUDIT exists to find wins the model has no
    # confidence in. Measured 2026-08-07 on django-12908: try 2 resolved via
    # BANK_AUDIT after the walk hit its wall cap with no green reproduction,
    # so it scored 0.0 on self-belief; the failed try 1 outranked it and a
    # real win was written down as a miss.
    #
    # Do not "fix" this by letting resolved dominate form_rank -- that makes
    # the submission oracle-selected. Record both numbers instead.
    chosen["any_attempt_resolved"] = any(bool(a.get("resolved"))
                                         for a in attempts)
    chosen["resolved_attempt"] = next(
        (i + 1 for i, a in enumerate(attempts) if a.get("resolved")), None)
    results.append(chosen)
    json.dump(results, open(OUT, "w"), indent=2)
    n_res = sum(1 for x in results if x.get("resolved"))
    n_any = sum(1 for x in results if x.get("any_attempt_resolved"))
    _flag = ""
    if chosen.get("any_attempt_resolved") and not chosen.get("resolved"):
        _won = next((x for x in chosen["attempt_ranks"] if x["resolved"]), None)
        _sub = max(chosen["attempt_ranks"], key=lambda x: x["rank"])
        _flag = ("   [!] attempt %s RESOLVED (rank %.1f) but form_rank "
                 "submitted attempt %s (rank %.1f)"
                 % (chosen.get("resolved_attempt"),
                    (_won or {}).get("rank", 0.0),
                    _sub["attempt"], _sub["rank"]))
    print("[%d/%d] %s -> %s   (submitted %d/%d | any-attempt %d/%d)%s"
          % (len(results), len(ids), iid,
             "RESOLVED" if chosen.get("resolved") else "miss",
             n_res, len(results), n_any, len(results), _flag), flush=True)

n_res = sum(1 for x in results if x.get("resolved"))
print("DONE: %d/%d still pass under %s" % (n_res, len(results), MODEL_TAG))
