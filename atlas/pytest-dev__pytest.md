CODE ATLAS for pytest-dev/pytest — where past issues were actually fixed
(from this system's own resolved runs; treat as evidence, verify by reading — past fixes suggest, they do not decide)

- Module imported twice under import-mode=importlib
    -> src/_pytest/pathlib.py
- Rewrite fails when first expression of file is a number and mistaken as docstring 
    -> src/_pytest/assertion/rewrite.py
- Improve default logging format
    -> src/_pytest/logging.py
- Hostname and timestamp properties in generated JUnit XML reports
    -> src/_pytest/junitxml.py
- INTERNALERROR when exception in __repr__
    -> src/_pytest/_io/saferepr.py
- Incorrect caching of skipif/xfail string condition evaluation
    -> src/_pytest/mark/evaluate.py
- skipping: --runxfail breaks pytest.mark.skip location reporting
    -> src/_pytest/skipping.py
- Pytest 6: Dynamically adding xfail marker in test no longer ignores failure
    -> src/_pytest/skipping.py
- Wrong path to test file when directory changed in fixture
    -> src/_pytest/_code/code.py
