"""Each source's view of *our* vocabulary: for every aligned concept A, the
aligned concepts B that the source entails A ⊑ B (B's id is a proper
ancestor of A's id in the source graph).  Two concepts on the same source
id are indistinguishable there and entail nothing about each other.

Writes views/<source>.tsv (A  B pairs) and views/<source>.od (the reduced
DAG, browsable with odag).  `wordnet` is a source like the others (hub
offsets are ids), and `claude` is ontodag's shipped core pack — the
common-sense witness, with no more standing than SUMO.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path
from graph import Graph, dag_from_parents, write_od

ROOT = Path(__file__).resolve().parent.parent
GRAPHS = {"wordnet": "cache/wordnet.pkl", "sumo": "cache/sumo-mid.pkl",
          "schemaorg": "cache/schemaorg.pkl", "yago": "cache/yago.pkl",
          "opencyc": "cache/opencyc.pkl", "bfo": "cache/bfo.pkl",
          "dolce": "cache/dolce.pkl", "dul": "cache/dul.pkl", "claude": "cache/core.pkl"}


def main():
    rows = list(csv.DictReader(open(ROOT / "align/concepts.tsv"), delimiter="\t"))
    for source, pkl in GRAPHS.items():
        g = Graph.load(ROOT / pkl)
        if source == "claude":
            aligned = {r["name"]: r["name"] for r in rows if r["name"] in g.nodes}
        else:
            aligned = {r["name"]: r[source] for r in rows if r.get(source) and r[source] in g.nodes}
        # SUMO's mapping has a relation: `=` the synset IS the term, `+`/`@` the
        # synset sits strictly BELOW the term.  A `+` concept may be a subclass
        # (A ⊑ term(A) ⊑ ...) but never a superclass (X ⊑ term(B) says nothing
        # about X ⊑ B), and two concepts on one term relate only when the
        # upper one is `=`.
        rel = {r["name"]: r.get("sumo_rel", "=") or "=" for r in rows} if source == "sumo" else {}
        rev = defaultdict(list)
        for name, sid in aligned.items():
            if not rel or rel[name] == "=":
                rev[sid].append(name)
        pairs = {}
        for name, sid in aligned.items():
            above = set()
            ids = g.ancestors(sid)
            if rel and rel[name] != "=":
                ids = ids | {sid}
            for a in ids:
                above.update(rev.get(a, ()))
            above.discard(name)
            pairs[name] = sorted(above)
        with open(ROOT / f"views/{source}.tsv", "w", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            for a, bs in sorted(pairs.items()):
                for b in bs:
                    w.writerow([a, b])
        notes = []
        dag = dag_from_parents(pairs, on_cycle=lambda n, d: notes.append((n, d)))
        write_od(dag, ROOT / f"views/{source}.od")
        n_pairs = sum(len(v) for v in pairs.values())
        print(f"{source:10s} {len(aligned):5d} concepts aligned, {n_pairs:6d} entailments"
              + (f", {len(notes)} cycles broken" if notes else ""))


if __name__ == "__main__":
    main()
