"""Second places: the edges one source alone proposes, and what they
would add to the shipped core (docs/UPPER.md §17).

    python3 tools/second_places.py [--sample N] [--seed S]
    python3 tools/second_places.py --shape [--names whale,knife]

Reads build/evidence.tsv (one row per candidate edge, with its status and
its witnesses) and the core that the installed ontodag ships. For every
single-witness edge whose two ends are both in that core it asks whether
the edge would give the concept a place it does not already have, and
whether that place is under a top-level category the concept is not under
yet. It prints the counts, the sources, and a random sample to read.

The names in evidence.tsv predate some renames, so edges on renamed
concepts are not matched: the counts are a floor.

`--shape` describes instead the vocabulary as shipped, core and the ten
domain packs merged: how many nodes have several parents, how many of
those parents are terms, and where the named concepts are filed.
"""
import argparse
import collections
import csv
import random
from pathlib import Path

from ontodag import dimensions, packs, prelude
from ontodag.dag import OntoDAG

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ["physics", "mathematics", "chemistry", "biology", "medicine", "ai",
           "economics", "computing", "geography", "space"]
NAMES = "whale,bat,salmon,tomato,knife,gold,bicycle,nurse,bread,milk"


def parents_of(dag, node):
    return sorted(p.name for p in node.parents if dag.nodes.get(p.name) is p)


def shape(names):
    dag = OntoDAG()
    prelude.apply(dag)
    for name in ["core", *DOMAINS]:
        dag.merge(packs.adoption_dag(dag, name))
    by_head = collections.Counter()
    plain = with_term = leaves = 0
    for node in dag.nodes.values():
        above = parents_of(dag, node)
        terms = [p for p in above if dimensions.split_term(p) is not None
                 and not dimensions.is_kind_node(p)]
        for term in terms:
            by_head[dimensions.split_term(term)[0]] += 1
        if len(above) > 1:
            plain += not terms
            with_term += bool(terms)
            leaves += not node.neighbors
    several = plain + with_term
    print(f"nodes: {len(dag.nodes)}; with several parents: {several} "
          f"({100 * several / len(dag.nodes):.1f}%), {leaves} of them "
          f"leaves")
    print(f"  all their parents plain: {plain}; a term among them: "
          f"{with_term}")
    print("  edges to a term, by head:", dict(by_head))
    for name in names:
        node = dag.nodes.get(name)
        print(f"  {name} ⊑ {', '.join(parents_of(dag, node))}"
              if node is not None else f"  {name}: not in the vocabulary")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample", type=int, default=14)
    parser.add_argument("--seed", type=int, default=3)
    parser.add_argument("--shape", action="store_true")
    parser.add_argument("--names", default=NAMES)
    args = parser.parse_args()
    if args.shape:
        shape(args.names.split(","))
        return

    with open(ROOT / "build/evidence.tsv") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    print("candidate edges:", len(rows),
          dict(collections.Counter(r["status"] for r in rows)))

    dag = OntoDAG()
    prelude.apply(dag)
    dag.merge(packs.adoption_dag(dag, "core"))
    tops = {top.name for top in dag.root.neighbors}
    known = {}

    def above(name):
        if name not in known:
            known[name] = {a.name for a in
                           dag.get_ancestors(name, computed=False)}
        return known[name]

    def tops_of(name):
        return (above(name) | {name}) & tops

    single = [r for r in rows if r["status"] == "single"
              and r["sub"] in dag.nodes and r["sup"] in dag.nodes]
    print("single-witness edges with both ends in the shipped core:",
          len(single))
    new, implied, loops = [], 0, 0
    for r in single:
        if r["sup"] in above(r["sub"]):
            implied += 1
        elif r["sub"] == r["sup"] or r["sub"] in above(r["sup"]):
            loops += 1
        else:
            new.append(r)
    crossing = [r for r in new if not tops_of(r["sub"]) & tops_of(r["sup"])]
    within = [r for r in new if tops_of(r["sub"]) & tops_of(r["sup"])]
    print(f"  already implied: {implied}; would close a loop: {loops}; "
          f"would add a place: {len(new)}")
    print(f"  concepts that would gain a place: "
          f"{len({r['sub'] for r in new})} of {len(dag.nodes)} nodes")
    print(f"  places under a top-level category the concept is not yet "
          f"under: {len(crossing)}")
    print("  by source:", dict(collections.Counter(
        s for r in new for s in r["for"].split())))

    rng = random.Random(args.seed)
    for label, pool in (("under another top-level category", crossing),
                        ("under a top-level category it has", within)):
        print(f"--- {args.sample} at random, {label} ---")
        for r in rng.sample(pool, min(args.sample, len(pool))):
            now = ", ".join(sorted(
                p.name for p in dag.nodes[r["sub"]].parents
                if dag.nodes.get(p.name) is p))
            print(f"   {r['sub']} ⊑ {r['sup']}   [{r['for']}]   "
                  f"now under: {now}")


if __name__ == "__main__":
    main()
