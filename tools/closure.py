"""Closure check: every (concept, ancestor) pair in a store's transitive
closure, tested against each source's own entailments (views/<source>.tsv).

    python3 tools/closure.py                # core: writes build/closure.tsv
    python3 tools/closure.py --pack NAME    # one pack: packs/NAME/build/closure.tsv
    python3 tools/closure.py --packs        # every pack, one summary line each

For a pair (X, Z): E = sources whose own graph entails X ⊑ Z; T = sources
that align both X and Z; R = sources that entail Z ⊑ X. Class 0-testable
(T but no E) is what to read: no source says it although some could have.

A pack's concepts climb into core and into sibling packs, so the graph is
the union of core and every pack's non-stub entries, and a source's
entailments and alignments are the union of what its views say in core and
in every pack. Only the pairs whose subject is the pack's own entry are
reported for that pack.
"""
import csv, shlex, collections, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ["wordnet", "sumo", "opencyc", "wikidata", "yago", "schemaorg",
           "gpt", "cpc", "iana", "bfo", "dolce", "dul", "claude"]
PACKS = sorted(d.name for d in (ROOT / "packs").iterdir()
               if (d / "build" / f"{d.name}.od").exists())
CLASSES = ["2+", "1", "0-testable", "0-untestable", "reversed"]

# step7 renames, in their order (views and concepts.tsv predate them). A name
# can be freed and reused (bank -> river-bank, then
# depository-financial-institution -> bank), so the rows apply in sequence.
ren = []
for line in open(ROOT / "align/renames-step7.tsv"):
    if line.startswith("#") or not line.strip():
        continue
    r = line.rstrip("\n").split("\t")
    if r[0] == "pack" or len(r) < 4 or r[3] == "drop":
        continue
    ren.append((r[1], r[2]))
memo_new = {}
def new(n):
    if n not in memo_new:
        m = n
        for old, to in ren:
            if m == old:
                m = to
        memo_new[n] = m
    return memo_new[n]

def entries(path):
    for l in open(path):
        if l.startswith("#") or not l.strip():
            continue
        f = shlex.split(l)
        yield f[0], f[1:]

# the union graph; owner[x] is the store whose non-stub entry x is
par, owner = {}, {}
for store, path in [("core", ROOT / "build/core.od")] + \
        [(p, ROOT / f"packs/{p}/build/{p}.od") for p in PACKS]:
    for name, ps in entries(path):
        if "(" in name:
            continue                                  # a term's node (canonical .od)
        if ps == ["*"] and name in par:
            continue                                  # a borrowed name
        names = [x for x in ps if x != "*" and "(" not in x]
        if ps != ["*"]:
            owner.setdefault(name, store)
        par[name] = sorted(set(par.get(name, [])) | set(names))
memo = {}
def anc(n):
    if n in memo:
        return memo[n]
    s = set()
    for p in par.get(n, []):
        s.add(p); s |= anc(p)
    memo[n] = s
    return s

homes = [ROOT] + [ROOT / "packs" / p for p in PACKS]
entails = {s: set() for s in SOURCES}
aligned = {s: set() for s in SOURCES}
for home in homes:
    for s in SOURCES:
        p = home / f"views/{s}.tsv"
        if p.exists():
            for line in open(p):
                a, b = line.rstrip("\n").split("\t")[:2]
                entails[s].add((new(a), new(b)))
    for r in csv.DictReader(open(home / "align/concepts.tsv"), delimiter="\t"):
        for s in SOURCES:
            if s != "claude" and r.get(s):
                aligned[s].add(new(r["name"]))
    if home != ROOT and (home / "views/claude.od").exists():
        for name, ps in entries(home / "views/claude.od"):
            if ps != ["*"]:
                aligned["claude"].add(new(name))
for name, _ in entries(ROOT / "align/core-v1.od"):
    aligned["claude"].add(new(name))

def cls(E, T, R):
    if R and not E: return "reversed"
    if len(E) >= 2: return "2+"
    if len(E) == 1: return "1"
    if T: return "0-testable"
    return "0-untestable"

def check(store):
    rows = []
    for x in sorted(n for n, o in owner.items() if o == store):
        for z in anc(x):
            E = [s for s in SOURCES if (x, z) in entails[s]]
            T = [s for s in SOURCES if x in aligned[s] and z in aligned[s]]
            R = [s for s in SOURCES if (z, x) in entails[s]]
            rows.append((x, z, E, T, R))
    out = ROOT / ("build" if store == "core" else f"packs/{store}/build") / "closure.tsv"
    with open(out, "w") as f:
        f.write("class\tsub\tancestor\tentailed_by\ttestable_in\treversed_in\n")
        for x, z, E, T, R in sorted(rows, key=lambda r: (cls(*r[2:]), r[0], r[1])):
            f.write(f"{cls(E,T,R)}\t{x}\t{z}\t{' '.join(E)}\t{' '.join(T)}\t{' '.join(R)}\n")
    return rows

if "--packs" in sys.argv:
    print(f"{'pack':12s} {'entries':>7s} {'pairs':>7s} " + " ".join(f"{k:>12s}" for k in CLASSES))
    for p in PACKS:
        rows = check(p)
        c = collections.Counter(cls(*r[2:]) for r in rows)
        n = sum(1 for o in owner.values() if o == p)
        print(f"{p:12s} {n:7d} {len(rows):7d} " + " ".join(f"{c[k]:12d}" for k in CLASSES))
else:
    store = sys.argv[sys.argv.index("--pack") + 1] if "--pack" in sys.argv else "core"
    rows = check(store)
    c = collections.Counter(cls(*r[2:]) for r in rows)
    print(len(rows), f"pairs in {store}'s closure")
    for k in CLASSES:
        print(f"  {k:14s} {c[k]}")
    single = collections.Counter(r[2][0] for r in rows if len(r[2]) == 1)
    print("  single-source pairs by source:", single.most_common())
