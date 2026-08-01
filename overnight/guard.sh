#!/bin/bash
# Busy-check for the overnight improvement loop. Prints BUSY or PROCEED.
LOCK=~/swe/overnight/LOCK
if pgrep -f "harness.run_evaluation" >/dev/null 2>&1; then echo "BUSY: docker eval running"; exit 1; fi
if [ -f "$LOCK" ]; then
  age=$(( $(date +%s) - $(stat -c %Y "$LOCK") ))
  if [ "$age" -lt 2400 ]; then echo "BUSY: lock held (${age}s < 2400s)"; exit 1; fi
fi
touch "$LOCK"; echo "PROCEED"; exit 0
