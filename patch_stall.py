"""No-progress watchdog for the fix phase (2026-07-25).

The dominant miss pattern in the traces is the agent circling: re-running the
same failing test, re-applying patches that land the file in a state it has
already visited, chasing a broken reproduction whose FileNotFoundError/Traceback
it can't distinguish from a real failure. It never stops, so it burns the whole
FIX_BUDGET (django-16910 ran ~190 turns and never converged).

This adds a signature-novelty watchdog to phase_run: if, over the last
`stall_window` turns, at most 2 produced a NEW result signature, the phase ends
with reason 'stalled'. It keys off REPETITION of outcomes, not on any self-check
verdict, so it's agnostic to the advisory-vs-canonical question. Enabled only
for the fix phase (bootstrap passes stall_window=None). Conservative window (25)
so it can't cut a productive agent, which keeps producing novel edits/results.
"""
import shutil, sys

SA = "/home/bard/Code/LLMOS/swe_agent_v2.py"
src = open(SA).read()
shutil.copy(SA, SA + ".bak-stall")


def rep(old, new, tag, count=1):
    n = src.count(old)
    if n != count:
        sys.exit("ABORT [%s]: anchor found %d times (need %d)" % (tag, n, count))
    return src.replace(old, new)


# ---- 1. FIX_STALL constant -------------------------------------------------
FB = 'FIX_BUDGET       = int(os.environ.get("FIX_BUDGET", "200"))'
src = rep(FB, FB + '\n'
          'FIX_STALL        = int(os.environ.get("FIX_STALL", "25"))  '
          '# no-progress watchdog: stop the fix phase after this many turns with '
          '<=2 novel results; 0 disables',
          "fix_stall_const")

# ---- 2. _result_sig helper, before phase_run -------------------------------
SIGDEF = '''def _result_sig(tool, result):
    """A stable signature of a tool OUTCOME, for the no-progress watchdog.
    Keys off content: re-running the same failing check or re-applying a patch
    that lands the file in a seen state looks identical, while a genuinely new
    edit or a new error looks different."""
    try:
        if isinstance(result, dict):
            for k in ("error", "stderr"):
                if result.get(k):
                    return tool + "|E|" + error_signature(str(result[k]))[:160]
            parts = [tool]
            for k in ("edited", "mode", "new_bytes", "delta_bytes",
                      "ok", "exit", "match", "match_count"):
                if k in result:
                    parts.append("%s=%s" % (k, result[k]))
            for k in ("stdout", "test_tail", "score_tail", "content"):
                if result.get(k):
                    parts.append(error_signature(str(result[k]))[:120])
                    break
            return "|".join(str(p) for p in parts)[:220]
        return tool + "|" + str(result)[:200]
    except Exception:
        return tool + "|?"


def phase_run('''
src = rep("def phase_run(", SIGDEF, "result_sig_def")

# ---- 3. signature: add stall_window=None -----------------------------------
src = rep("              emit=None):",
          "              emit=None, stall_window=None):",
          "signature")

# ---- 4. stall state init ---------------------------------------------------
CAT = "    _catalog = {}        # out<turn> -> full tool result, recall()-able"
src = rep(CAT, CAT + '\n'
          "    _seen_sigs = set()   # result signatures seen so far (no-progress watchdog)\n"
          "    _novel_hist = []     # per-turn: 1 if the result was new, else 0",
          "stall_init")

# ---- 5. the watchdog, right after the tool_result emit ----------------------
TR = '''        log(str(result)[:120])
        if emit:
            emit("tool_result", {"turn": turn, "tool": tool, "result": result})'''
src = rep(TR, TR + '''
        if stall_window:
            _sig = _result_sig(tool, result)
            _novel_hist.append(0 if _sig in _seen_sigs else 1)
            _seen_sigs.add(_sig)
            if (len(_novel_hist) >= stall_window
                    and sum(_novel_hist[-stall_window:]) <= 2):
                log("STALLED: only %d novel results in the last %d turns"
                    % (sum(_novel_hist[-stall_window:]), stall_window))
                if emit:
                    emit("stalled", {"turn": turn, "window": stall_window})
                return "stalled", messages, meta_log''',
          "watchdog")

# ---- 6. enable it for the fix phase only -----------------------------------
src = rep("checkpoint=ckpt, emit=_emit2)",
          "checkpoint=ckpt, emit=_emit2, stall_window=FIX_STALL)",
          "wire_phase2")

open(SA, "w").write(src)
print("patched swe_agent_v2.py (backup .bak-stall)")
