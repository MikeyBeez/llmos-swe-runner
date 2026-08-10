#!/bin/bash
# Re-judge every fresh32 miss in the OFFICIAL swebench container.
# Late-green (oracle-refused) misses first -- the ones our env disbelieved.
cd /home/bard/swe
ORDER="sympy__sympy-17630 sympy__sympy-13043 sympy__sympy-14317 sympy__sympy-13895 sympy__sympy-15308 sympy__sympy-13971 sympy__sympy-13437 sympy__sympy-13177 sympy__sympy-13915 sympy__sympy-13146 sympy__sympy-16503 sympy__sympy-16281 sympy__sympy-16106 sympy__sympy-15609 sympy__sympy-15346 sympy__sympy-14308 sympy__sympy-14024 sympy__sympy-13773"
for i in $ORDER; do
  echo "=== $i ==="
  timeout 3000 python3 referee.py "$i" 2>&1
done
echo "REJUDGE18 DONE"
