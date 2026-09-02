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
import sys
from collections import defaultdict
from pathlib import Path
from graph import dag_from_parents, write_od

ROOT = Path(__file__).resolve().parent.parent
MIN_WITNESSES = 2


def main():
    for_, against = defaultdict(set), defaultdict(set)
    for tsv in sorted((ROOT / "views").glob("*.tsv")):
        src = tsv.stem
        for a, b in csv.reader(open(tsv), delimiter="\t"):
            for_[(a, b)].add(src)
            against[(b, a)].add(src)
    # Claude's per-edge judgements are a witness like the others: an accept
    # adds `claude` to the edge's witnesses (and its reversal to `against`),
    # a reject records a dissent that keeps the edge out of consensus.
    p = ROOT / "align/claude-review.tsv"
    dissent = set()
    if p.exists():
        for row in csv.reader(open(p), delimiter="\t"):
            if row and not row[0].startswith("#") and len(row) >= 3:
                pair = (row[0].strip(), row[1].strip())
                if row[2].strip() == "accept":
                    for_[pair].add("claude")
                    against[(pair[1], pair[0])].add("claude")
                elif row[2].strip() == "reject":
                    dissent.add(pair)
    review = {}
    p = ROOT / "align/review.tsv"
    if p.exists():
        for row in csv.reader(open(p), delimiter="\t"):
            if row and not row[0].startswith("#") and len(row) >= 3:
                review[(row[0].strip(), row[1].strip())] = row[2].strip()
    roots = {l.strip() for l in open(ROOT / "align/roots.txt") if l.strip() and not l.startswith("#")}

    status = {}
    for pair, w in for_.items():
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
    placed = set(roots)
    changed = True
    while changed:
        changed = False
        for a, bs in accepted.items():
            if a not in placed and any(b in placed for b in bs):
                placed.add(a)
                changed = True
    parents = {n: [b for b in accepted.get(n, []) if b in placed] for n in placed}
    cycles = []
    dag = dag_from_parents(parents, on_cycle=lambda n, d: cycles.append((n, d)))
    write_od(dag, ROOT / "build/core.od")

    with open(ROOT / "build/evidence.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["sub", "sup", "status", "for", "against"])
        for (a, b), st in sorted(status.items()):
            w.writerow([a, b, st, " ".join(sorted(for_[(a, b)])), " ".join(sorted(against.get((a, b), ())))])
    concepts = {r["name"] for r in csv.DictReader(open(ROOT / "align/concepts.tsv"), delimiter="\t")}
    with open(ROOT / "build/queue.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["kind", "sub", "sup", "detail"])
        for n, d in cycles:
            w.writerow(["cycle", n, " ".join(d), "edges inside a cycle of accepted claims; dropped"])
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
    print(f"pairs: {dict(counts)}; pack: {len(placed)} concepts, {len(dag.nodes) - 1} placed, "
          f"{len(cycles)} cycles, {len(concepts - placed)} unplaced")


if __name__ == "__main__":
    main()
