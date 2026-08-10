- NOTHING IS OBSERVABLE UNTIL DOCS ACTUALLY BUILD. A reproduction must
  create a minimal project (conf.py + one .rst or one autodoc-target
  module), run a real build, and assert on the OUTPUT (generated text/
  warnings), not on internal objects. The reliable harness for this is
  sphinx own test utilities or a subprocess sphinx-build into a tmp dir.
- Most Lite issues here are autodoc rendering: the observable is the
  generated documentation TEXT for a target signature/member. Build,
  read the produced file or captured warnings, assert on a substring.
- Builds are slow relative to other repos -- keep the project minimal
  (one source file) or the reproduction eats the phase budget.
