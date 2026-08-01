CODE ATLAS for pytest-dev/pytest — where past issues were actually fixed
(from this system's own resolved runs; treat as evidence, verify by reading — past fixes suggest, they do not decide)

- Incorrect caching of skipif/xfail string condition evaluation
    -> src/_pytest/mark/evaluate.py
- skipping: --runxfail breaks pytest.mark.skip location reporting
    -> src/_pytest/skipping.py
- Pytest 6: Dynamically adding xfail marker in test no longer ignores failure
    -> src/_pytest/nodes.py, src/_pytest/skipping.py
- Improve default logging format
    -> src/_pytest/logging.py
- Rewrite fails when first expression of file is a number and mistaken as docstring 
    -> src/_pytest/assertion/rewrite.py
- Module imported twice under import-mode=importlib
    -> src/_pytest/pathlib.py
