"""A fetched Wikidata piece (sources/wikidata/<name>.json) -> Graph.  Ids are
QIDs, labels English, root a synthetic node above the pull's roots."""
import json
import sys
from pathlib import Path
from graph import Graph

ROOT = Path(__file__).resolve().parent.parent
TOP = "wikidata-root"


def extract(*names):
    """Several pulls merge into one graph (core.json = the WordNet-mapped items,
    mathematics.json = the bounded walks); edges are the union."""
    labels, edges, roots = {}, set(), set()
    for name in names:
        d = json.load(open(ROOT / "sources/wikidata" / f"{name}.json"))
        labels.update(d["labels"]); edges |= {tuple(e) for e in d["edges"]}; roots |= {q for q, _ in d["roots"]}
    parents = {q: [] for q in labels}
    for c, p in edges:
        if c in parents and p in parents:
            parents[c].append(p)
    nodes = {TOP: ("wikidata root", [])}
    for q, lab in labels.items():
        nodes[q] = (lab, sorted(set(parents[q])) or ([TOP] if q in roots else []))
    return Graph(nodes, TOP)


if __name__ == "__main__":
    *names, out = sys.argv[1:]
    g = extract(*names)
    g.save(out)
    print(len(g.nodes), "items;", sum(1 for s in g.nodes if len(g.parents(s)) > 1), "with 2+ parents")
