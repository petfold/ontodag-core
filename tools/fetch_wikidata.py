"""Pull a bounded piece of Wikidata's subclass graph (P279) into
sources/wikidata/<name>.json: breadth-first from the roots in a roots file,
`depth` levels down each, English labels attached.  Bounded on purpose —
the transitive closure under `algebraic structure` is 55,000 items because
everything is a set; four levels of direct subclasses is what a pack wants.

    python3 tools/fetch_wikidata.py packs/mathematics/align/wikidata-roots.tsv mathematics

roots file:  QID<TAB>depth<TAB>note
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EP = "https://query.wikidata.org/sparql"
UA = "ontodag-core/0.1 (github.com/petfold/ontodag-core; upper ontology construction)"


def sparql(query):
    req = urllib.request.Request(EP + "?" + urllib.parse.urlencode({"query": query, "format": "json"}),
                                 headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))["results"]["bindings"]
        except Exception as e:                       # 429 / timeouts: back off and retry
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))


def children_of(qids):
    """(child, parent, childLabel) for every direct P279 child of any qid, English labels only."""
    out = []
    for i in range(0, len(qids), 60):
        chunk = " ".join(f"wd:{q}" for q in qids[i:i + 60])
        rows = sparql(f"""SELECT ?c ?p ?cl WHERE {{ VALUES ?p {{ {chunk} }} ?c wdt:P279 ?p .
            ?c rdfs:label ?cl . FILTER(LANG(?cl) = "en") }}""")
        out += [(r["c"]["value"].rsplit("/", 1)[-1], r["p"]["value"].rsplit("/", 1)[-1], r["cl"]["value"]) for r in rows]
        time.sleep(1)
    return out


def labels_of(qids):
    out = {}
    for i in range(0, len(qids), 100):
        chunk = " ".join(f"wd:{q}" for q in qids[i:i + 100])
        for r in sparql(f'SELECT ?x ?l WHERE {{ VALUES ?x {{ {chunk} }} ?x rdfs:label ?l . FILTER(LANG(?l) = "en") }}'):
            out[r["x"]["value"].rsplit("/", 1)[-1]] = r["l"]["value"]
        time.sleep(1)
    return out


def main(roots_file, name):
    roots = []
    for line in open(roots_file):
        if line.strip() and not line.startswith("#"):
            q, d = line.split("\t")[:2]
            roots.append((q.strip(), int(d)))
    labels = labels_of([q for q, _ in roots])
    edges, seen = set(), set(q for q, _ in roots)
    for root, depth in roots:
        frontier = [root]
        for level in range(depth):
            kids = children_of(frontier)
            new = []
            for c, p, cl in kids:
                edges.add((c, p))
                labels.setdefault(c, cl)
                if c not in seen:
                    seen.add(c); new.append(c)
            print(f"  {labels[root]!r} level {level + 1}: {len(kids)} edges, {len(new)} new items", file=sys.stderr)
            frontier = new
            if not frontier:
                break
    # cross edges: P279 links among everything fetched, so a root's own parents
    # and links between branches are present too (natural number -> integer)
    ids = sorted(seen)
    for i in range(0, len(ids), 80):
        chunk = " ".join(f"wd:{q}" for q in ids[i:i + 80])
        for r in sparql(f"SELECT ?c ?p WHERE {{ VALUES ?c {{ {chunk} }} ?c wdt:P279 ?p . }}"):
            c, p = r["c"]["value"].rsplit("/", 1)[-1], r["p"]["value"].rsplit("/", 1)[-1]
            if p in seen:
                edges.add((c, p))
        time.sleep(0.7)
    out = ROOT / "sources/wikidata" / f"{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"roots": roots, "labels": labels, "edges": sorted(edges)}, open(out, "w"), indent=0)
    print(f"{out}: {len(labels)} items, {len(edges)} P279 edges")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
