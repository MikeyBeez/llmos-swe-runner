"""Phase B: structured live-event emission from phase_run (2026-07-25).

phase_run only ever print()ed per-turn summary lines. This adds an append-only
JSONL event bus so the monitor can show EVERYTHING a run does live: the full
generation each turn (content + reasoning + tokens), every tool call with its
full arguments and the handler it dispatched to, every tool result, plus gate/
critic/phase markers.

Contract: emission is BEST-EFFORT and can never slow or break a run. Every
write is wrapped; the emit param defaults to None so non-SWE callers are
unchanged. Fields are capped so one giant result can't bloat a line.
"""
import shutil, sys

SA = "/home/bard/Code/LLMOS/swe_agent_v2.py"
src = open(SA).read()
shutil.copy(SA, SA + ".bak-events")


def rep(old, new, tag):
    n = src.count(old)
    if n != 1:
        sys.exit("ABORT [%s]: anchor found %d times (need 1)" % (tag, n))
    return src.replace(old, new, 1)


# ---- 1. emitter infrastructure, after the path constants ----------------
MIR = 'MIRRORS = os.path.expanduser("~/swe/mirrors")'
INFRA = MIR + '''

# --- live event bus (2026-07-25): append-only JSONL of everything a run does,
# tailed live by the monitor on :8899. Best-effort: never raises, never blocks
# a run. Path from $LLMOS_EVENTS, else a single shared stream under runs/live/.
import threading as _threading
EVENTS_PATH = (os.environ.get("LLMOS_EVENTS")
               or os.path.expanduser("~/swe/runs/live/events.jsonl"))
_events_lock = _threading.Lock()
_events_seq = [0]


def _cap_ev(v, n=20000):
    """Bound one field so a huge result/generation can't bloat the line. The
    complete output is still in the trace; this stream is for watching."""
    if isinstance(v, str):
        return v if len(v) <= n else v[:n] + " \\u2026[+%d chars]" % (len(v) - n)
    try:
        s = json.dumps(v, default=str)
    except Exception:
        s = str(v)
    if len(s) <= n:
        return v
    return s[:n] + " \\u2026[+%d chars]" % (len(s) - n)


def make_emitter(instance_id, phase, run_id=None):
    """Return emit(ev_type, fields) appending one JSON line to EVENTS_PATH."""
    def emit(ev_type, fields=None):
        try:
            with _events_lock:
                _events_seq[0] += 1
                seq = _events_seq[0]
            rec = {"seq": seq, "ts": time.time(), "type": ev_type,
                   "instance_id": instance_id, "phase": phase}
            if run_id:
                rec["run_id"] = run_id
            if fields:
                for k, v in fields.items():
                    rec[k] = _cap_ev(v)
            line = json.dumps(rec, default=str)
            d = os.path.dirname(EVENTS_PATH)
            if d and not os.path.isdir(d):
                os.makedirs(d, exist_ok=True)
            with open(EVENTS_PATH, "a") as fh:
                fh.write(line + "\\n")
        except Exception:
            pass
    return emit
'''
src = rep(MIR, INFRA, "infra")

# ---- 2. phase_run signature gets emit=None ------------------------------
SIG = "              budget, gate=None, log=print, checkpoint=None, worksheet=None):"
src = rep(SIG,
          "              budget, gate=None, log=print, checkpoint=None, worksheet=None,\n"
          "              emit=None):",
          "signature")

# ---- 3. generation event ------------------------------------------------
GEN = '''        meta_log.append({"turn": turn,
                          "prompt_tokens": meta.get("prompt_tokens"),
                          "eval_tokens":   meta.get("eval_tokens")})'''
src = rep(GEN, GEN + '''
        if emit:
            emit("generation", {"turn": turn,
                                "content": msg.get("content") or "",
                                "reasoning": (msg.get("reasoning_content")
                                              or msg.get("thinking") or ""),
                                "eval_tokens": meta.get("eval_tokens"),
                                "prompt_tokens": meta.get("prompt_tokens")})''',
          "generation")

# ---- 4. tool_call event -------------------------------------------------
TC = '''        log(f"  [{turn:>2}] {tool}({str(args)[:80]}) -> ", end="", flush=True)'''
src = rep(TC, TC + '''
        if emit:
            emit("tool_call", {"turn": turn, "tool": tool,
                               "function": target, "args": args,
                               "args_error": args_err})''',
          "tool_call")

# ---- 5. tool_result event -----------------------------------------------
TR = '''        log(str(result)[:120])'''
src = rep(TR, TR + '''
        if emit:
            emit("tool_result", {"turn": turn, "tool": tool, "result": result})''',
          "tool_result")

# ---- 6. declared / gate / critic markers --------------------------------
DECL = '''            log(f"DECLARED {tool}")'''
src = rep(DECL, DECL + '''
            if emit:
                emit("declared", {"turn": turn, "tool": tool})''', "declared")

GATE = '''                log("GATE-REJECTED")'''
src = rep(GATE, GATE + '''
                if emit:
                    emit("gate", {"turn": turn, "decision": "rejected"})''', "gate")

CRIT = '''                log(f"  [critic] {advice[:100]}")'''
src = rep(CRIT, CRIT + '''
                if emit:
                    emit("critic", {"turn": turn, "advice": advice})''', "critic")

# ---- 7. wire phase 1 ----------------------------------------------------
P1P = '    print(" -- phase 1: bootstrap --", flush=True)'
src = rep(P1P, P1P + '''
    _emit1 = make_emitter(inst["instance_id"], "bootstrap")
    _emit1("phase_start", {"budget": BOOTSTRAP_BUDGET, "repo": inst["repo"]})''',
          "p1_start")

P1CALL = '''    b_reason, b_msgs, b_meta = phase_run(cpu, BOOTSTRAP_TOOLS, BOOTSTRAP_TOOL2SYS,
                                          b_handlers, BOOTSTRAP_SYSTEM_PROMPT,
                                          goal, BOOTSTRAP_BUDGET,
                                          gate=_boot_gate,
                                          checkpoint=ckpt)'''
src = rep(P1CALL, P1CALL.replace("checkpoint=ckpt)", "checkpoint=ckpt, emit=_emit1)"),
          "p1_call")

P1END = '''    env_ok = env_ready(b_state)
    if not env_ok and b_state.get("sanity_ok"):'''
src = rep(P1END, '''    env_ok = env_ready(b_state)
    _emit1("phase_end", {"reason": b_reason, "env_ok": env_ok})
    if not env_ok and b_state.get("sanity_ok"):''', "p1_end")

# ---- 8. wire phase 2 ----------------------------------------------------
P2CALL = '''    f_reason, f_msgs, f_meta = phase_run(cpu2, FIX_TOOLS, FIX_TOOL2SYS,
                                          f_handlers, FIX_SYSTEM_PROMPT,
                                          fix_goal, FIX_BUDGET,
                                          worksheet=lambda: _rw(f_state),
                                          gate=_fix_gate,
                                          checkpoint=ckpt)'''
src = rep(P2CALL, '''    _emit2 = make_emitter(inst["instance_id"], "fix")
    _emit2("phase_start", {"budget": FIX_BUDGET, "repo": inst["repo"]})
''' + P2CALL.replace("checkpoint=ckpt)", "checkpoint=ckpt, emit=_emit2)") + '''
    _emit2("phase_end", {"reason": f_reason})''', "p2_call")

open(SA, "w").write(src)
print("patched swe_agent_v2.py (backup .bak-events)")
