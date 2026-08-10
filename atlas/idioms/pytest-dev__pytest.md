- The right reproduction here is usually PYTEST RUNNING PYTEST: write a
  tiny test file to a temp dir and invoke pytest on it in a subprocess,
  then assert on the child run RETURN CODE and OUTPUT TEXT. Both resolved
  pytest instances on 2026-08-10 did exactly this; asserting on internal
  objects without a child run tends to stay red over correct fixes.
- Do not run the child pytest in-process (pytest.main in the same
  interpreter) when the bug involves collection, caching, or reporting --
  state leaks between runs. Use subprocess + a fresh tmp dir.
- Assert on stable substrings of the child output (error message text,
  summary counts), not on exact full lines -- formatting varies by
  version and terminal width.
