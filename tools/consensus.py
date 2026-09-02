"""The consensus pack: an edge A ⊑ B enters when at least MIN_WITNESSES
sources entail it and none entails the reverse, or when align/review.tsv
accepts it; a review rejection removes it whatever the witnesses say.
A concept enters when it is a declared root (align/roots.txt) or has an
accepted parent that entered — so nothing hangs from `*` by accident.

Writes build/core.od (the pack), build/evidence.tsv (every witnessed pair
with its status and witnesses) and build/queue.tsv (what a human should
look at: single-witness edges, disputes, cycles, unplaced concepts).
"""
import csv
import shlex
import sys
from collections import defaultdict
from pathlib import Path
from graph import dag_from_parents, write_od, resolve_reviews
from pack import Dirs, pack_arg

ROOT = Path(__file__).resolve().parent.parent
MIN_WITNESSES = 2


def main():
    dirs = Dirs(pack_arg())
    origin = {r["name"]: r.get("origin", "core") for r in csv.DictReader(open(dirs.concepts), delimiter="\t")}
    base = set()
    if dirs.pack:            # the core is already decided: it is the placed ground the pack attaches to
        base = {shlex.split(l)[0] for l in open(dirs.base_od) if not l.startswith("#")}
    for_, against = defaultdict(set), defaultdict(set)
    for tsv in sorted(dirs.views.glob("*.tsv")):
        src = tsv.stem
        for a, b in csv.reader(open(tsv), delimiter="\t"):
            for_[(a, b)].add(src)
            against[(b, a)].add(src)
    # Claude's per-edge judgements are a witness like the others: an accept
    # adds `claude` to the edge's witnesses (and its reversal to `against`),
    # a reject records a dissent that keeps the edge out of consensus.
    dissent = set()
    for sub, sup, dec, _ in resolve_reviews(dirs.align / "claude-review.tsv", dirs.concepts):
        if dec == "accept":
            for_[(sub, sup)].add("claude")
            against[(sup, sub)].add("claude")
        elif dec == "reject":
            dissent.add((sub, sup))
    review = {}
    for sub, sup, dec, _ in resolve_reviews(dirs.align / "review.tsv", dirs.concepts):
        review[(sub, sup)] = dec
        if dec == "accept":
            for_[(sub, sup)].add("peter")      # a ruling is a witness too: an edge no source states can still enter
    rp = dirs.align / "roots.txt"
    roots = {l.strip() for l in open(rp) if l.strip() and not l.startswith("#")} if rp.exists() else set()

    # A published version is sticky: every edge it entails stays accepted whatever a
    # new witness says (a rename or retraction never propagates by merge, so the
    # tool must not pretend otherwise); contradictions go to the queue for a ruling.
    published = set()
    pub = dirs.align / "published"
    if pub.exists():
        for od in pub.glob("*.od"):
            ppar = {}
            for l in open(od):
                if not l.startswith("#"):
                    f = shlex.split(l); ppar[f[0]] = [x for x in f[1:] if x != "*"]
            for a in ppar:
                seen, st = set(), list(ppar[a])
                while st:
                    x = st.pop()
                    if x in seen: continue
                    seen.add(x); st.extend(ppar.get(x, []))
                published.update((a, b) for b in seen)
    contradicted = []
    status = {}
    for pair, w in for_.items():
        if pair in published and review.get(pair) != "reject":
            status[pair] = "accepted"
            if against.get(pair) and review.get(pair) != "accept":      # ruled-on pairs stay quiet
                contradicted.append((pair, against[pair]))
            continue
        if dirs.pack and origin.get(pair[0]) == "base" and origin.get(pair[1]) == "base":
            continue                                   # the core's business, decided (or left) there
        r = review.get(pair)
        if r == "reject":
            status[pair] = "rejected"
        elif r == "accept":
            status[pair] = "accepted"
        elif against.get(pair):
            status[pair] = "disputed"          # some source places them the other way round
        elif pair in dissent and len(w) < MIN_WITNESSES:
            status[pair] = "dissented"         # Claude read the glosses and says no — a vote, not a veto:
                                               # two independent sources still carry an edge past it
        elif len(w) >= MIN_WITNESSES:
            status[pair] = "accepted"
        else:
            status[pair] = "single"
    accepted = defaultdict(list)
    for (a, b), st in status.items():
        if st == "accepted":
            accepted[a].append(b)

    # concepts enter from the roots downward through accepted edges
    placed = set(roots) | base
    changed = True
    while changed:
        changed = False
        for a, bs in accepted.items():
            if a not in placed and any(b in placed for b in bs):
                placed.add(a)
                changed = True
    own = placed - base if dirs.pack else placed
    parents = {n: [b for b in accepted.get(n, []) if b in placed] for n in own}
    # edges asserted about names the pack does not define (align/extra-edges.tsv)
    p = dirs.align / "extra-edges.tsv"
    if p.exists():
        for row in csv.reader(open(p), delimiter="\t"):
            if row and not row[0].startswith("#") and len(row) >= 2:
                sub, sup = row[0].strip(), row[1].strip()
                parents.setdefault(sup, [])
                parents.setdefault(sub, []).append(sup)
                placed.update((sub, sup))
    cycles = []
    if dirs.pack:
        # base parents are outside the file: keep them as nodes so the .od names them
        for n in list(parents):
            for b in parents[n]:
                parents.setdefault(b, [])
    dag = dag_from_parents(parents, on_cycle=lambda n, d: cycles.append((n, d)))
    if dirs.pack:                           # drop the borrowed base nodes' own root edges from the count
        pass
    write_od(dag, dirs.pack_od)

    with open(dirs.build / "evidence.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["sub", "sup", "status", "for", "against"])
        for (a, b), st in sorted(status.items()):
            w.writerow([a, b, st, " ".join(sorted(for_[(a, b)])), " ".join(sorted(against.get((a, b), ())))])
    concepts = {r["name"] for r in csv.DictReader(open(dirs.concepts), delimiter="\t")} - base
    with open(dirs.build / "queue.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["kind", "sub", "sup", "detail"])
        for n, d in cycles:
            w.writerow(["cycle", n, " ".join(d), "edges inside a cycle of accepted claims; dropped"])
        for (a, b), ag in sorted(contradicted):
            w.writerow(["contradicted-published", a, b, f"published edge; now reversed by {' '.join(sorted(ag))} — needs a ruling"])
        for (a, b), st in sorted(status.items()):
            if st == "disputed":
                w.writerow(["disputed", a, b, f"for {' '.join(sorted(for_[(a, b)]))}; reversed by {' '.join(sorted(against[(a, b)]))}"])
        for (a, b), st in sorted(status.items()):
            if st == "single" and a in placed and b in placed:
                w.writerow(["single", a, b, f"only {' '.join(for_[(a, b)])}"])
        for n in sorted(concepts - placed):
            supers = sorted(b for (a, b), st in status.items() if a == n and st != "rejected")
            w.writerow(["unplaced", n, " ".join(supers[:8]), "no accepted parent reaches a root"])
    counts = defaultdict(int)
    for st in status.values():
        counts[st] += 1
    print(f"pairs: {dict(counts)}; pack: {len(own)} concepts, "
          f"{len(cycles)} cycles, {len(concepts - placed)} unplaced")


if __name__ == "__main__":
    main()
