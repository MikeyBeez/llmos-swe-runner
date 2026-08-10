- NOTHING IS OBSERVABLE UNTIL THE CANVAS DRAWS. A reproduction that
  inspects artist properties, transforms, or ticks without forcing a draw
  observes the pre-render state and will stay red (or stay green) no
  matter what you fix. Force rendering first:
      fig.canvas.draw()            # or
      fig.savefig(io.BytesIO(), format="png")
  then assert on the post-draw state. Measured 2026-08-10: the one
  resolved matplotlib instance rendered before asserting; five misses
  asserted on properties without drawing and their reproductions never
  went green over a correct-file patch.
- Use a non-interactive backend at the top of every reproduction:
      import matplotlib; matplotlib.use("Agg")
  or the script can hang or behave differently headless.
- After a draw, concrete observables live on the renderer output:
  get_window_extent(), get_tightbbox(), tick label .get_text(), and the
  bytes of a saved PNG. Prefer these over pre-draw attribute reads.
