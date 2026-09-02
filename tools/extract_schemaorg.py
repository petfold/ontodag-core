"""schema.org (JSON-LD release file) -> Graph.  Only `schema:` classes;
`rdfs:subClassOf` may be one object or a list.  Root schema:Thing.  Data
types (schema:DataType descendants) are kept — they show as one branch."""
import json
import sys
from pathlib import Path
from graph import Graph

SRC = Path(__file__).resolve().parent.parent / "sources/schemaorg/schemaorg-current-https.jsonld"
ROOT = "schema:Thing"


def _ids(v):
    if v is None:
        return []
    if isinstance(v, dict):
        return [v["@id"]]
    if isinstance(v, list):
        return [x["@id"] if isinstance(x, dict) else x for x in v]
    return [v]


def extract(path=SRC):
    graph = json.load(open(path))["@graph"]
    nodes = {}
    for n in graph:
        if n.get("@type") != "rdfs:Class" or not n["@id"].startswith("schema:"):
            continue
        label = n.get("rdfs:label")
        if isinstance(label, dict):
            label = label.get("@value")
        parents = [p for p in _ids(n.get("rdfs:subClassOf")) if p.startswith("schema:")]
        nodes[n["@id"]] = (label or n["@id"][7:], parents)
    for s, (lab, ps) in nodes.items():
        nodes[s] = (lab, [p for p in ps if p in nodes])
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    g = extract()
    g.save(sys.argv[1])
    print(len(g.nodes), "classes;", sum(1 for s in g.nodes if len(g.parents(s)) > 1), "with 2+ parents;",
          sum(1 for s, (_, ps) in g.nodes.items() if not ps), "roots")
