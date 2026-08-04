# llmos-swe-runner

The orchestration and evaluation layer for running a local language model against
[SWE-bench Lite](https://www.swebench.com/). This repository schedules instances,
retries them, archives every patch, and judges results with an independent referee.
The agent and its fix-time harness live in a separate repository,
[MikeyBeez/LLMOS](https://github.com/MikeyBeez/LLMOS); this repo drives it.

The system under test is a single 35B model (`ornith-1.0-35b-llamacpp`) served by
`llama-server` on one consumer GPU. Nothing here is model-specific — point it at any
OpenAI-compatible endpoint and it runs.

## The two-metric rule (read this first)

Every number this runner produces belongs to exactly one of two regimes, and the two
are never compared. Keeping them separate is the whole integrity claim, so it is worth
stating plainly before anything else.

The **leaderboard-legal** regime is what the official SWE-bench rules permit: one
attempt per instance, no use of the hidden tests or their names, no use of the issue's
`hints` field. A number reported this way is directly comparable to published results.

The **oracle-gated research** regime is what this runner uses by default to study the
model. It may retry an instance, and it consults a harness-side oracle that runs the
hidden tests *outside the model's context* and returns a single bit — pass or fail —
used only for control flow. The model never sees test content; it only ever experiences
"not solved yet, keep working." This produces a much higher solve rate, and that rate
**cannot** be placed beside a leaderboard number. It measures something different: what
the model can do inside a feedback loop, and how often a patch that is correct for the
reported issue still misses a requirement the issue never stated.

Runs in the two regimes write to different output files by construction (`OUT_NAME`),
and the oracle is off unless `ORACLE_GATE=1` is set. If you are producing a citable
number, set `ORACLE_GATE=0`, `MAX_ATTEMPTS=1`, and leave every mechanism that reads test
knowledge disabled.

## Leak discipline

At runtime the harness never reads the gold patch or the `FAIL_TO_PASS` / `PASS_TO_PASS`
labels' *content*. The oracle applies the hidden test patch, runs it, reverses it, and
deletes it from the tree before any later tool call could surface it; what crosses back
into the run is one bit of control flow. The referee described below *does* read the gold
patch, but only after the fact, as an independent judge — never during a run.

## Layout

`run_list.py` is the entry point. It takes an explicit list of instances in the `IDS`
environment variable, runs each one, dumps results after every instance, and skips
instances already present in the output file so a stopped run resumes cleanly. It imports
the agent from `~/Code/LLMOS` (the `LLMOS` repo) — that is where the model loop, the
repertoire walk, and all the fix-time mechanisms live.

`referee.py` is an independent judge that rebuilds a patch inside the official SWE-bench
Docker image. It runs two controls before it will rule: the unpatched code must fail the
graded tests, and the gold patch must pass them. If either control misbehaves it reports
`INCONCLUSIVE` rather than a finding — the case where a benchmark instance grades nothing
in a given environment. It defaults to judging archived patches, not the live work tree,
and refuses `--tree` while a runner is executing (judging a half-finished edit once
produced a phantom verdict). `docker_referee.py` is the batch form.

`atlas/` is a per-repository knowledge store carried between runs. Each `<repo>.md` records
where past issues were actually fixed (evidence, not instructions — the model still reads
and verifies). `atlas/idioms/<repo>.md` holds hand-curated, library-specific conventions
distilled from failures: sympy returns `S.One` not a bare `1`; Django deprecates before it
removes; queryset composition must preserve `GROUP BY`. `atlas/ledger.jsonl` is the append
log the `<repo>.md` files are regenerated from.

`instances_full300.json` and `canonical_python.json` are the frozen instance set and the
per-instance Python pinning. The `run_*.py` / `run_*.sh` files are historical launch
configurations for specific experiments; `run_list.py` supersedes them.

## Running

Point at the LLMOS checkout, name your instances, choose a regime, and launch. A typical
oracle-gated research run:

```sh
export IDS="django__django-11039,sympy__sympy-20154"
export OUT_NAME=my_run.json          # output goes to runs/ornith/my_run.json
export MAX_ATTEMPTS=2                 # up to two independent attempts per instance
export ATLAS_DIR=~/swe/atlas         # enable the code atlas + idioms
export ORACLE_GATE=1                 # harness-side oracle (research metric only)
python3 -u run_list.py
```

The run is resumable: rerun the same command and instances already in `my_run.json` are
skipped. Because a single GPU serves the model, never launch a second run while one is
live — check `pgrep -f run_list.py` first.

A leaderboard-legal run instead:

```sh
export IDS="django__django-11039"
export OUT_NAME=legal_run.json
export MAX_ATTEMPTS=1
unset ORACLE_GATE
python3 -u run_list.py
```

## Mechanisms

The fix-time mechanisms are implemented in the `LLMOS` harness and switched on through the
launch environment. Each is deterministic where it can be, warns rather than refuses, and
is off by default. Briefly:

`ORACLE_GATE` runs the hidden tests harness-side and refuses a green reproduction that the
graded tests reject — the incomplete-fix guard. `SPEC_PROBE` computes, from the syntax tree
after each patch, things the issue text cannot tell the model: sibling operator methods the
edit left untouched, bare-literal returns in a file that compares canonical objects by
identity, other uses of a rarely-named attribute, and undefined names (missing imports).
`COVERAGE_GAP` runs the reproduction under `trace` at the green moment and names any line the
patch *added* that the reproduction never actually executed — a line with no runtime evidence
behind it. `DIFF_HYGIENE` and `DIFF_REPAIR` lint and deterministically repair collateral
whitespace and transcription drift in the diff. `SIBLING_BODY` flags when the model has pasted
a neighboring function's body into the one it is editing. A compile gate in the scorer refuses
to grade a tree that does not parse. `CONTAINER_APPEAL` sends a believed-correct patch that
failed unit tests to the Docker referee; it is expensive and off by default.

These names are toggles you set in the environment; their code and rationale are documented in
the `LLMOS` repository.

## Related reading

Two write-ups cover the ideas this runner exists to test: *The Wrong Basin* (retrieval failure
between near-identical functions, and the sibling-body detector) and *One Assertion Short* (the
gap between the issue a model is shown and the hidden tests it is graded against, and the
deterministic probes built in response).
