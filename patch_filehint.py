"""Redirecting 'file not found' for the fix phase (2026-07-25).

67+ miss traces hit 'file not found' from read_range/patch. The recurring cause
is the model aiming at a path it invented: its own inline reproduction script
(never a real file), an absolute /work path, or a guessed test path. A bare
'file not found' doesn't correct the false belief, so the model loops. Replace
both sites with a message that (a) names the reproduction/scratch confusion and
(b) points at locate() + real source, and suggests the real path when a file of
that basename exists elsewhere in the repo.
"""
import shutil, sys

FT = "/home/bard/Code/LLMOS/swe_fix_tools.py"
src = open(FT).read()
shutil.copy(FT, FT + ".bak-filehint")

# ---- 1. module-level helper, before the fix-handler factory ----------------
ANCHOR = "def make_fix_handlers("
if src.count(ANCHOR) != 1:
    sys.exit("ABORT: anchor %r found %d times (need 1)" % (ANCHOR, src.count(ANCHOR)))

HELP = '''def _missing_file_hint(path, repo_dir):
    """A redirecting error for a path that is not a real repo file. The top
    miss cause is the model reading/patching a path it invented -- its inline
    reproduction script, an absolute /work path, or a guessed test file. A bare
    'file not found' does not correct the false belief, so it loops."""
    p = str(path)
    if ("_reproduction" in p or "/work/" in p or p.startswith("/")
            or ".." in p.split("/")):
        return ("not a repo file: %r. reproduction/check scripts run inline -- "
                "they are NOT saved files you can read or patch. Only real "
                "source files under the repo root can be read/edited (e.g. "
                "'django/...', 'src/...'). Use locate(pattern=...) to find the "
                "real path; never guess or invent file paths." % p)
    hint = ("file not found: %r. Do NOT guess file paths -- use "
            "locate(pattern=...) to find the real location, then read_range / "
            "patch that exact path." % p)
    try:
        base = os.path.basename(p)
        if base:
            for root, dirs, files in os.walk(repo_dir):
                dirs[:] = [d for d in dirs if d not in
                           (".git", ".venv", ".condaenv", "node_modules",
                            "__pycache__")]
                if base in files:
                    rel = os.path.relpath(os.path.join(root, base), repo_dir)
                    hint += " (a file named %r exists at %r)" % (base, rel)
                    break
    except OSError:
        pass
    return hint


'''
src = src.replace(ANCHOR, HELP + ANCHOR, 1)

# ---- 2. both file-not-found sites use it -----------------------------------
OLD = 'return {"error": f"file not found: {path}"}'
NEW = 'return {"error": _missing_file_hint(path, repo_dir)}'
n = src.count(OLD)
if n != 2:
    sys.exit("ABORT: file-not-found line found %d times (need 2)" % n)
src = src.replace(OLD, NEW)

open(FT, "w").write(src)
print("patched swe_fix_tools.py (backup .bak-filehint), replaced %d sites" % n)
