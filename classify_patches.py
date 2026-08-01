"""Taxonomy of SWE-bench Lite gold patches, cross-tabbed against our history.
Structural metrics are exact; category tags are heuristics over ADDED lines."""
import json, glob, re, collections

SWE = "/home/bard/swe"
insts = {i["instance_id"]: i for i in json.load(open(SWE + "/instances_full300.json"))}

res, att = set(), set()
for p in glob.glob(SWE + "/runs/*/*.json") + glob.glob(SWE + "/results*.json"):
    if "_set" in p:
        continue
    try:
        d = json.load(open(p))
    except Exception:
        continue
    if not isinstance(d, list):
        continue
    for x in d:
        if isinstance(x, dict) and x.get("id"):
            att.add(x["id"])
            if x.get("resolved"):
                res.add(x["id"])


def parse(patch):
    patch = patch or ""
    files = set(re.findall(r"^\+\+\+ b/(\S+)", patch, re.M))
    hunks = len(re.findall(r"^@@ ", patch, re.M))
    add = [l[1:] for l in patch.split("\n") if l.startswith("+") and not l.startswith("+++")]
    rem = [l[1:] for l in patch.split("\n") if l.startswith("-") and not l.startswith("---")]
    return files, hunks, add, rem


# category -> regex over the ADDED text
CATS = [
 ("new function/method", r"^\s*(def |class )"),
 ("guard / None-check",  r"if\s+\w+\s+is\s+(not\s+)?None|if\s+not\s+\w+|if\s+\w+\s+is\s+None"),
 ("exception handling",  r"\b(try:|except\b|raise\b|finally:)"),
 ("signature change",    r"^\s*def .*\("),
 ("conditional logic",   r"^\s*(if|elif|else)\b"),
 ("loop/iteration",      r"^\s*(for|while)\b|\benumerate\(|\bzip\("),
 ("kwarg / flag",        r"\w+\s*=\s*(True|False|None)\b"),
 ("type coercion",       r"\b(int|str|float|list|tuple|set|dict|bool)\("),
 ("string/format",       r"f\"|\.format\(|%\s*\(|\.join\(|\.split\("),
 ("import added",        r"^\s*(import |from \w+ import)"),
 ("comparison/operator", r"[=!<>]=|\bis\b|\bin\b|\bnot\b"),
 ("attribute access",    r"getattr\(|hasattr\(|setattr\(|self\.\w+"),
 ("case/regex switch",   r"re\.(IGNORECASE|MULTILINE|DOTALL)|\.(lower|upper|casefold)\(\)"),
 ("return change",       r"^\s*return\b"),
]

rows = []
for iid, inst in insts.items():
    files, hunks, add, rem = parse(inst.get("gold_patch"))
    text = "\n".join(add)
    tags = {name for name, rx in CATS if re.search(rx, text, re.M)}
    rows.append({
        "id": iid, "files": len(files), "hunks": hunks,
        "add": len(add), "rem": len(rem), "tags": tags,
        "resolved": iid in res, "attempted": iid in att,
    })

print("=" * 74)
print("STRUCTURE (all 300 gold patches)")
print("=" * 74)
def bucket(n, edges, labels):
    for e, l in zip(edges, labels):
        if n <= e:
            return l
    return labels[-1]

for field, edges, labels in (
    ("files", [1, 2, 3], ["1 file", "2 files", "3 files", "4+ files"]),
    ("hunks", [1, 2, 4], ["1 hunk", "2 hunks", "3-4 hunks", "5+ hunks"]),
    ("add",   [1, 5, 15, 40], ["1 line", "2-5", "6-15", "16-40", "41+"]),
):
    c = collections.Counter(bucket(r[field], edges, labels) for r in rows)
    print("\n  %s:" % field)
    for l in labels:
        if c[l]:
            print("     %-10s %3d (%2.0f%%)" % (l, c[l], 100 * c[l] / len(rows)))

print()
print("=" * 74)
print("CATEGORIES — and our success rate within each (attempted instances only)")
print("=" * 74)
print("  %-22s %5s %6s %7s %7s" % ("category", "n(300)", "tried", "solved", "rate"))
stats = []
for name, _ in CATS:
    grp = [r for r in rows if name in r["tags"]]
    tried = [r for r in grp if r["attempted"]]
    solved = [r for r in tried if r["resolved"]]
    rate = 100 * len(solved) / len(tried) if tried else float("nan")
    stats.append((rate, name, len(grp), len(tried), len(solved)))
for rate, name, n, tried, solved in sorted(stats):
    print("  %-22s %5d %6d %7d %6.0f%%" % (name, n, tried, solved, rate))

base_t = [r for r in rows if r["attempted"]]
base_s = [r for r in base_t if r["resolved"]]
print("\n  %-22s %5d %6d %7d %6.0f%%   <-- BASELINE" % ("ALL", len(rows), len(base_t), len(base_s), 100*len(base_s)/len(base_t)))

print()
print("=" * 74)
print("SUCCESS RATE BY PATCH SIZE (attempted only)")
print("=" * 74)
for lo, hi, lab in ((0,1,"1 line"),(2,5,"2-5 lines"),(6,15,"6-15"),(16,40,"16-40"),(41,10**6,"41+")):
    g = [r for r in rows if r["attempted"] and lo <= r["add"] <= hi]
    s = [r for r in g if r["resolved"]]
    if g:
        print("  %-10s n=%-4d solved=%-4d %5.0f%%" % (lab, len(g), len(s), 100*len(s)/len(g)))
for lab, f in (("1 file", lambda r: r["files"] <= 1), ("2+ files", lambda r: r["files"] >= 2)):
    g = [r for r in rows if r["attempted"] and f(r)]
    s = [r for r in g if r["resolved"]]
    if g:
        print("  %-10s n=%-4d solved=%-4d %5.0f%%" % (lab, len(g), len(s), 100*len(s)/len(g)))
