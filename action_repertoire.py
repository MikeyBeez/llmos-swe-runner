"""Repertoire of EDIT OPERATIONS, ordered simplest -> most invasive.
Generative (things to try), not descriptive (shapes to report).
Coverage measured against all 300 gold patches: does the ladder describe
what real fixes actually do?"""
import json, glob, re, collections

SWE = "/home/bard/swe"
insts = {i["instance_id"]: i for i in json.load(open(SWE + "/instances_full300.json"))}
res, att = set(), set()
for p in glob.glob(SWE + "/runs/*/*.json") + glob.glob(SWE + "/results*.json"):
    if "_set" in p: continue
    try: d = json.load(open(p))
    except Exception: continue
    if not isinstance(d, list): continue
    for x in d:
        if isinstance(x, dict) and x.get("id"):
            att.add(x["id"])
            if x.get("resolved"): res.add(x["id"])

def pairs(patch):
    """(removed, added) line pairs within hunks — what actually changed."""
    add = [l[1:] for l in (patch or "").split("\n") if l.startswith("+") and not l.startswith("+++")]
    rem = [l[1:] for l in (patch or "").split("\n") if l.startswith("-") and not l.startswith("---")]
    return add, rem

# ladder: (rung, name, test(add_text, rem_text, add, rem))
LADDER = [
 (1, "change an argument value",
  lambda a, r, A, R: bool(re.search(r"\w+\s*=\s*[^=]", a) and R and re.search(r"\w+\s*=\s*[^=]", r))),
 (1, "add an argument / flag",
  lambda a, r, A, R: bool(re.search(r"[(,]\s*\w+\s*=", a)) and len(A) <= 3),
 (1, "add case normalization",
  lambda a, r, A, R: bool(re.search(r"\.(lower|upper|casefold)\(\)|re\.IGNORECASE", a))),
 (2, "fix a name (attr/method/spelling)",
  lambda a, r, A, R: bool(R and len(A) == len(R) <= 2 and re.search(r"\.\w+", a) and
                          _namediff(a, r))),
 (2, "change a comparison operator",
  lambda a, r, A, R: bool(re.search(r"(==|!=|<=|>=|<|>|\bis\b|\bin\b)", a) and
                          R and re.search(r"(==|!=|<=|>=|<|>|\bis\b|\bin\b)", r))),
 (2, "change a literal/constant",
  lambda a, r, A, R: bool(R and len(A) == len(R) <= 2 and re.search(r"(\"[^\"]*\"|'[^']*'|\b\d+\b)", a))),
 (3, "add a guard / early return",
  lambda a, r, A, R: bool(re.search(r"if\s+.*(is None|is not None|not \w+|\bnot in\b)", a) or
                          re.search(r"^\s*(return|continue|raise)\b", a, re.M)) and not R),
 (3, "wrap in try/except",
  lambda a, r, A, R: bool(re.search(r"^\s*(try:|except\b)", a, re.M))),
 (3, "add a branch",
  lambda a, r, A, R: bool(re.search(r"^\s*(elif|else)\b", a, re.M))),
 (4, "change type coercion",
  lambda a, r, A, R: bool(re.search(r"\b(int|str|float|list|tuple|set|dict|bool)\(", a) and
                          R and re.search(r"\b(int|str|float|list|tuple|set|dict|bool)\(", r))),
 (4, "reorder / move statements",
  lambda a, r, A, R: bool(R and A and sorted(x.strip() for x in A) == sorted(x.strip() for x in R))),
 (5, "add a helper function/method",
  lambda a, r, A, R: bool(re.search(r"^\s*def \w+", a, re.M))),
 (5, "restructure logic (multi-line rewrite)",
  lambda a, r, A, R: len(A) > 15),
]

def _namediff(a, r):
    an = set(re.findall(r"\.(\w+)", a)); rn = set(re.findall(r"\.(\w+)", r))
    return bool((an ^ rn)) and len(an ^ rn) <= 3

hit = collections.Counter(); rung_hit = collections.Counter()
covered = 0
per_inst = {}
for iid, inst in insts.items():
    A, R = pairs(inst.get("gold_patch"))
    a, r = "\n".join(A), "\n".join(R)
    names = [(rung, name) for rung, name, f in LADDER if f(a, r, A, R)]
    per_inst[iid] = names
    if names:
        covered += 1
        lo = min(x[0] for x in names)
        rung_hit[lo] += 1
    for rung, name in names:
        hit[name] += 1

print("COVERAGE: %d of %d gold patches match >=1 operation (%.0f%%)" % (covered, len(insts), 100*covered/len(insts)))
print()
print("  %-40s %5s %7s %7s" % ("operation", "n", "tried", "solved%"))
for rung, name, _ in LADDER:
    g = [i for i, v in per_inst.items() if any(n == name for _, n in v)]
    t = [i for i in g if i in att]; s = [i for i in t if i in res]
    print("  %d. %-37s %5d %7d %6s" % (rung, name, len(g), len(t),
          ("%.0f%%" % (100*len(s)/len(t))) if t else "-"))
print()
print("SIMPLEST APPLICABLE RUNG (per instance) and our solve rate there:")
for rung in sorted(rung_hit):
    g = [i for i, v in per_inst.items() if v and min(x[0] for x in v) == rung]
    t = [i for i in g if i in att]; s = [i for i in t if i in res]
    print("   rung %d: n=%-3d tried=%-3d solved=%s" % (rung, len(g), len(t),
          ("%.0f%%" % (100*len(s)/len(t))) if t else "-"))
un = [i for i, v in per_inst.items() if not v]
print("\nUNCOVERED: %d  e.g. %s" % (len(un), ", ".join(sorted(un)[:4])))
