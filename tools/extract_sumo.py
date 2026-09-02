"""SUMO (KIF) -> Graph from `(subclass A B)` assertions.  Default is the
upper level only (Merge.kif); pass more .kif files to include the mid-level
and domain ontologies.  Ids are SUMO term names, root Entity."""
import re
import sys
from pathlib import Path
from graph import Graph

SRC = Path(__file__).resolve().parent.parent / "sources/sumo"
ROOT = "Entity"
PAT = re.compile(r"^\(subclass\s+([A-Za-z0-9_-]+)\s+([A-Za-z0-9_-]+)\)", re.M)


def extract(files=("Merge.kif",)):
    parents = {}
    for f in files:
        text = open(SRC / f, encoding="utf-8", errors="replace").read()
        for a, b in PAT.findall(text):
            parents.setdefault(a, []).append(b)
            parents.setdefault(b, [])
    nodes = {t: (t, sorted(set(ps))) for t, ps in parents.items()}
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    out, files = sys.argv[1], sys.argv[2:] or ["Merge.kif"]
    g = extract(files)
    g.save(out)
    print(len(g.nodes), "terms from", files, ";", sum(1 for s in g.nodes if len(g.parents(s)) > 1), "with 2+ parents")
