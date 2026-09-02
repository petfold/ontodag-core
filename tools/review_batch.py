"""Print single-witness edges for review, with both glosses, so a judgement
can be made per line.  Filter by branch (a placed ancestor) and by witness.

    python3 tools/review_batch.py --branch substance --witness wordnet --limit 80
"""
import argparse
import csv
import shlex
from collections import defaultdict
from pathlib import Path
from pack import Dirs, pack_arg

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--branch")
ap.add_argument("--witness")
ap.add_argument("--limit", type=int, default=100)
ap.add_argument("--skip", type=int, default=0)
ap.add_argument("--all", action="store_true", help="include transitive pairs, not just the witness's direct edges")
PACK = pack_arg()
a = ap.parse_args()
dirs = Dirs(PACK)

rows_ = list(csv.DictReader(open(dirs.concepts), delimiter="\t"))
gloss = {r["name"]: r["gloss"] for r in rows_}
origin = {r["name"]: r.get("origin", "core") for r in rows_}
parents = defaultdict(list)
for od in ([dirs.base_od, dirs.pack_od] if PACK else [dirs.pack_od]):
    for l in open(od):
        if not l.startswith("#"):
            f = shlex.split(l)
            parents.setdefault(f[0], [])
            parents[f[0]] += [p for p in f[1:] if p != "*"]
def under(n, b):
    seen, st = set(), [n]
    while st:
        x = st.pop()
        if x == b:
            return True
        for p in parents.get(x, []):
            if p not in seen:
                seen.add(p); st.append(p)
    return False
from graph import resolve_reviews
reviewed = {(a, b) for a, b, _, _ in resolve_reviews(dirs.align / "claude-review.tsv", dirs.concepts)}
# Direct edges of each witness's reduced view: judging the closure is wasted
# reading, since a ⊑ c follows once a ⊑ b and b ⊑ c are in.
direct = set()
for od in dirs.views.glob("*.od"):
    if a.witness and od.stem != a.witness:
        continue
    for l in open(od):
        if not l.startswith("#"):
            f = shlex.split(l)
            direct.update((f[0], p) for p in f[1:])
rows = [r for r in csv.DictReader(open(dirs.build / "evidence.tsv"), delimiter="\t")
        if r["status"] == "single" and (r["sub"], r["sup"]) not in reviewed
        and (a.all or (r["sub"], r["sup"]) in direct)
        and (not a.witness or r["for"] == a.witness)
        and r["sup"] in parents                      # sub may be unplaced: this edge is how it gets in
        and (not PACK or origin.get(r["sub"]) == PACK or origin.get(r["sup"]) == PACK)
        and (not a.branch or under(r["sub"], a.branch))]
print(f"# {len(rows)} candidates; showing {a.skip}..{a.skip + a.limit}")
for r in rows[a.skip:a.skip + a.limit]:
    print(f"{r['sub']} ⊑ {r['sup']}  [{r['for']}] | {gloss.get(r['sub'], '')[:48]} | {gloss.get(r['sup'], '')[:40]}")
