"""A fetched Wikidata piece (sources/wikidata/<name>.json) -> Graph.  Ids are
QIDs, labels English, root a synthetic node above the pull's roots."""
import json
import sys
from pathlib import Path
from graph import Graph

ROOT = Path(__file__).resolve().parent.parent
TOP = "wikidata-root"


def extract(name):
    d = json.load(open(ROOT / "sources/wikidata" / f"{name}.json"))
    parents = {q: [] for q in d["labels"]}
    for c, p in d["edges"]:
        if c in parents and p in parents:
            parents[c].append(p)
    nodes = {TOP: ("wikidata root", [])}
    roots = {q for q, _ in d["roots"]}
    for q, lab in d["labels"].items():
        nodes[q] = (lab, sorted(set(parents[q])) or ([TOP] if q in roots else []))
    return Graph(nodes, TOP)


if __name__ == "__main__":
    g = extract(sys.argv[1])
    g.save(sys.argv[2])
    print(len(g.nodes), "items;", sum(1 for s in g.nodes if len(g.parents(s)) > 1), "with 2+ parents")
