"""Context + GPU-idle analysis over the laguna regression traces.

Answers two questions before flipping llama-server to --parallel 2:
  1. Peak context per instance -- does a 65k/slot split truncate our agent loops?
  2. GPU-idle fraction -- how much wall-clock is pip/pytest with the GPU asleep?

Throughput constants are TODAY'S MEASURED post-tuning numbers from run_laguna.sh.
Prefill is estimated cache-aware: llama.cpp reuses the common prefix, so the real
prefill work per turn is the DELTA over the previous turn's prompt+eval, not the
whole prompt. Both naive and cache-aware totals are reported so the gap is visible.
"""
import json, os, glob

DECODE_TPS = 69.39     # measured post-tune
PREFILL_TPS = 2744.0   # measured post-tune, big-chunk
TRACES = os.path.expanduser("~/swe/traces_v2")
REG = os.path.expanduser("~/swe/runs/laguna/regress1.json")

reg = json.load(open(REG))
rows = []

for r in reg:
    iid = r["id"]
    p = os.path.join(TRACES, iid + ".trace.json")
    if not os.path.isfile(p):
        continue
    try:
        t = json.load(open(p))
    except Exception:
        continue

    peak = 0
    eval_tot = 0
    prefill_naive = 0
    prefill_cached = 0

    for key in ("phase1_meta", "phase2_meta"):
        meta = [m for m in t.get(key) or [] if isinstance(m, dict)]
        prev_end = None
        for m in meta:
            pt = m.get("prompt_tokens") or 0
            et = m.get("eval_tokens") or 0
            peak = max(peak, pt + et)
            eval_tot += et
            prefill_naive += pt
            if prev_end is None:
                prefill_cached += pt          # first turn: full prefill
            else:
                # new tokens = this prompt minus what the cache already holds
                prefill_cached += max(0, pt - prev_end)
            prev_end = pt + et

    dec_s = eval_tot / DECODE_TPS
    pre_s = prefill_cached / PREFILL_TPS
    gpu_s = dec_s + pre_s
    wall = r.get("attempt_secs") or r.get("secs") or 0
    idle = max(0, wall - gpu_s)
    rows.append(dict(iid=iid, resolved=r.get("resolved"), peak=peak,
                     eval_tot=eval_tot, pre_naive=prefill_naive,
                     pre_cached=prefill_cached, dec_s=dec_s, pre_s=pre_s,
                     gpu_s=gpu_s, wall=wall, idle=idle,
                     idle_pct=(100.0 * idle / wall) if wall else 0))

rows.sort(key=lambda x: -x["peak"])

print("%-32s %-4s %8s %8s %8s %7s %7s %7s" %
      ("instance", "res", "peak_ctx", "eval_tok", "pre_tok", "gpu_s", "wall_s", "idle%"))
print("-" * 92)
for x in rows:
    print("%-32s %-4s %8d %8d %8d %7.0f %7d %6.0f%%" %
          (x["iid"][:32], "OK" if x["resolved"] else "--", x["peak"],
           x["eval_tot"], x["pre_cached"], x["gpu_s"], x["wall"], x["idle_pct"]))

n = len(rows)
if n:
    peaks = sorted(x["peak"] for x in rows)
    tot_wall = sum(x["wall"] for x in rows)
    tot_gpu = sum(x["gpu_s"] for x in rows)
    tot_dec = sum(x["dec_s"] for x in rows)
    tot_pre = sum(x["pre_s"] for x in rows)
    print("-" * 92)
    print("n = %d traces" % n)
    print()
    print("PEAK CONTEXT")
    print("  max      %7d tokens" % peaks[-1])
    print("  p90      %7d" % peaks[int(0.9 * (n - 1))])
    print("  median   %7d" % peaks[n // 2])
    print("  min      %7d" % peaks[0])
    over65 = sum(1 for v in peaks if v > 65536)
    over120 = sum(1 for v in peaks if v > 122880)
    print("  > 65536 (2-slot limit): %d of %d instances" % (over65, n))
    print("  > 122880 (94%% of 131072): %d of %d" % (over120, n))
    print()
    print("GPU OCCUPANCY (cache-aware prefill)")
    print("  total wall      %8.0f s  (%.1f h)" % (tot_wall, tot_wall / 3600))
    print("  total GPU       %8.0f s  (decode %.0f + prefill %.0f)" % (tot_gpu, tot_dec, tot_pre))
    print("  total idle      %8.0f s  (%.1f h)" % (tot_wall - tot_gpu, (tot_wall - tot_gpu) / 3600))
    print("  GPU busy        %8.1f%% of wall-clock" % (100.0 * tot_gpu / tot_wall))
    print("  GPU IDLE        %8.1f%% of wall-clock" % (100.0 * (tot_wall - tot_gpu) / tot_wall))
    print()
    naive = sum(x["pre_naive"] for x in rows)
    cached = sum(x["pre_cached"] for x in rows)
    print("  prefill tokens: naive %d vs cache-aware %d (cache saves %.1f%%)"
          % (naive, cached, 100.0 * (1 - cached / naive) if naive else 0))
    print()
    print("  => a 2nd runner can only fill idle time. Theoretical ceiling on")
    print("     throughput gain from --parallel 2 = 1 / (GPU busy fraction),")
    print("     capped by contention: %.2fx" % (1.0 / (tot_gpu / tot_wall)))
