"""YAGO 4 (2020-02-24) taxonomy -> Graph: the schema.org top (yago-wd-schema)
with Wikidata-derived classes hung under it (yago-wd-class).  Ids are URIs'
local names; labels are the local name with underscores read as spaces.
Root schema.org Thing."""
import gzip
import re
import sys
from pathlib import Path
from graph import Graph

SRC = Path(__file__).resolve().parent.parent / "sources/yago"
ROOT = "Thing"
LINE = re.compile(r"^<([^>]+)>\s+<http://www\.w3\.org/2000/01/rdf-schema#subClassOf>\s+<([^>]+)>")


def local(uri):
    return uri.rsplit("/", 1)[-1]


def extract(files=("yago-wd-schema.nt.gz", "yago-wd-class.nt.gz")):
    parents = {ROOT: set()}
    for f in files:
        with gzip.open(SRC / f, "rt", encoding="utf-8") as fh:
            for line in fh:
                m = LINE.match(line)
                if m:
                    a, b = local(m.group(1)), local(m.group(2))
                    parents.setdefault(a, set()).add(b)
                    parents.setdefault(b, set())
    nodes = {t: (t.replace("_", " "), sorted(ps)) for t, ps in parents.items()}
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    g = extract()
    g.save(sys.argv[1])
    print(len(g.nodes), "classes;", sum(1 for s in g.nodes if len(g.parents(s)) > 1), "with 2+ parents;",
          sum(1 for s, (_, ps) in g.nodes.items() if not ps), "roots")
