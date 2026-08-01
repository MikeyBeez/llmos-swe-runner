#!/usr/bin/env python3
"""The archived "failed patch" was not the model's patch.

FOUND 2026-08-01 the first time the archive ever fired, on astropy-14365.
The archived diff was 2156 bytes and contained three references to
astropy/io/ascii/tests/test_qdp.py -- including the helper `lowercase_header`,
which is from the OFFICIAL test patch, not from the model.

Two causes stacked:

 1. score() applies the graded test patch to the work tree (`git apply
    _t.patch`) and does not revert it. run_list archives AFTER run_one
    returns, so by then the tree holds the model's patch PLUS the test patch.

 2. The guard against that was `git diff -- . ':(exclude)tests'`, which
    excludes a TOP-LEVEL tests/ directory. Django's tests are top-level so it
    worked and looked correct for months. astropy's live at
    astropy/io/ascii/tests/, and the pathspec does not match nested
    directories at all. Verified: the django-16910 archive is clean, the
    astropy one is not.

The comment on that line said the exclusion existed so the referee would not
double-apply the test patch. It was doing the opposite -- handing the referee
a patch with the test patch already baked in.

FIX: stop reconstructing the diff. score() already writes the model's patch to
traces_v2/<id>.patch BEFORE it applies the test patch, so that file is exactly
what we want, by construction, with no pathspec guesswork. Verified: 926 bytes,
zero test references, and it matches the recorded patch_bytes exactly. Keep the
git-diff path only as a fallback, now with a pathspec that also catches nested
test directories.
"""
import os
import shutil
import py_compile

ROOT = "/home/bard/swe"
FILE = "run_list.py"

OLD = '''                _wt = os.path.join(SWE, "work", iid)
                # tests excluded: the referee applies the graded test patch
                # itself, so including them here would double-apply.
                _d = subprocess.run("git diff -- . ':(exclude)tests'",
                                    shell=True, cwd=_wt, capture_output=True,
                                    text=True, timeout=120).stdout or ""'''

NEW = '''                _wt = os.path.join(SWE, "work", iid)
                # score() writes the model's patch to traces_v2/<id>.patch
                # BEFORE it applies the graded test patch to the tree. That
                # file is the artifact we want, by construction.
                #
                # Do NOT rebuild it from the work tree here. score() leaves
                # the test patch applied, so a diff taken now contains it --
                # and the old guard, ':(exclude)tests', only excludes a
                # TOP-LEVEL tests/ directory. Django's tests are top-level so
                # it looked right; astropy's are at astropy/io/ascii/tests/
                # and sailed straight through. Measured 2026-08-01: the
                # astropy-14365 archive came out 2156 bytes carrying the
                # official test helper `lowercase_header`, against 926 bytes
                # for the real patch.
                _d = ""
                _tp = os.path.join(SWE, "traces_v2", iid + ".patch")
                try:
                    with open(_tp) as _fh:
                        _d = _fh.read()
                except OSError:
                    pass
                if not _d.strip():
                    # fallback only. glob pathspecs so nested test dirs are
                    # actually excluded this time.
                    _d = subprocess.run(
                        "git diff -- . ':(exclude,glob)**/tests/**' "
                        "':(exclude,glob)**/test/**' "
                        "':(exclude,glob)**/test_*.py' "
                        "':(exclude,glob)**/*_test.py' "
                        "':(exclude,glob)**/tests.py'",
                        shell=True, cwd=_wt, capture_output=True,
                        text=True, timeout=120).stdout or ""'''

path = os.path.join(ROOT, FILE)
with open(path, encoding="utf-8") as f:
    src = f.read()
n = src.count(OLD)
if n != 1:
    raise SystemExit("ABORT: anchor count %d != 1" % n)
print("anchor verified")

shutil.copy2(path, path + ".bak-archiveleak")
with open(path, "w", encoding="utf-8") as f:
    f.write(src.replace(OLD, NEW, 1))
py_compile.compile(path, doraise=True)
print("patched + compiled: %s" % FILE)
