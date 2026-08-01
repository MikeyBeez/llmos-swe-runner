"""Env-gated scientific-debugging discipline for the fix phase (A/B, 2026-07-26).

Measured motivation: on hard bugs the agent reads ~2.7x more than it experiments
(django-16910: 55 reads vs 7 probes over 171 turns) -- it theorizes from reading
code instead of running a probe to test WHERE the fault is. The current prompt
even biases toward 'when in doubt, PATCH'. This appends an OVERRIDE, active only
when ISOLATE_DISCIPLINE=1, that flips the fix phase to hypothesis -> probe ->
observe -> patch. Env-gated so on/off is a clean one-variable A/B. Additive
(anchored append), not an edit of existing prompt logic.
"""
import shutil, sys

FT = "/home/bard/Code/LLMOS/swe_fix_tools.py"
src = open(FT).read()
shutil.copy(FT, FT + ".bak-isolate")

ANCHOR = ('    "Make the smallest change that fixes the issue. Every turn MUST call "\n'
          '    "exactly one tool."\n'
          ')')
if src.count(ANCHOR) != 1:
    sys.exit("ABORT: anchor found %d times (need 1)" % src.count(ANCHOR))

BLOCK = ANCHOR + '''


# --- Scientific-debugging discipline (A/B, env-gated 2026-07-26) --------------
if os.environ.get("ISOLATE_DISCIPLINE") == "1":
    FIX_SYSTEM_PROMPT = FIX_SYSTEM_PROMPT + (
        "\\n\\nOVERRIDE -- DEBUG BY EXPERIMENT, NOT BY READING:\\n"
        "Do NOT theorize from reading code. Every hypothesis about the bug is "
        "cheap to test, so TEST it. Loop:\\n"
        "  (a) state ONE hypothesis: 'the fault is in <function>, which returns "
        "X but should return Y'.\\n"
        "  (b) IMMEDIATELY run a `check` probe that constructs the minimal input "
        "and PRINTS the suspect value (call the function; print what it returns "
        "vs. what it should). One probe that prints the divergence is worth ten "
        "file reads.\\n"
        "  (c) read the probe OUTPUT; keep or revise the hypothesis.\\n"
        "  (d) patch ONLY after a probe has pinned the fault to a specific line "
        "or branch -- then verify with another probe.\\n"
        "HARD RULES: never read_range more than TWICE in a row without running a "
        "probe in between; never patch a location you have not first confirmed "
        "with a probe that printed the wrong value there. A 5-line experiment "
        "that prints an intermediate value beats re-reading the source or "
        "re-running the full suite. If you have reasoned more than a few "
        "sentences without running a probe, stop and run one.")
'''
src = src.replace(ANCHOR, BLOCK, 1)
open(FT, "w").write(src)
print("patched swe_fix_tools.py (env-gated ISOLATE_DISCIPLINE, backup .bak-isolate)")
