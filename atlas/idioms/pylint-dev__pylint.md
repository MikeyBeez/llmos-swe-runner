- The right reproduction is PYLINT RUNNING AS A TOOL: write a small
  target .py file to a tmp dir, run pylint on it in a SUBPROCESS, and
  assert on the emitted message ids/text and exit code. This mirrors the
  measured pytest pattern (both resolved pytest instances ran the tool in
  a child process); asserting on checker internals without a child run
  observes the wrong layer.
- Assert on message IDs (e.g. W0612) or stable substrings, not full
  rendered lines -- output formatting varies by version.
- Disable everything except the checker under test
  (--disable=all --enable=<id>) or unrelated messages drown the signal.
