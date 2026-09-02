"""Every Wikidata item that carries a WordNet 3.1 synset id (P8814), with its
English label, plus every P279 edge among those items -> sources/wikidata/core.json
in fetch_wikidata.py's format.  This is the exact hub alignment: our concepts
are WordNet synsets, so these items align by identifier, not by label."""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EP = "https://query.wikidata.org/sparql"
UA = "ontodag-core/0.1 (github.com/petfold/ontodag-core; mailto:peter.foldiak@gmail.com)"


def sparql(query, tries=6):
    req = urllib.request.Request(EP + "?" + urllib.parse.urlencode({"query": query, "format": "json"}), headers={"User-Agent": UA})
    for attempt in range(tries):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))["results"]["bindings"]
        except Exception as e:
            print(f"  retry {attempt + 1}: {str(e)[:60]}", file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    raise SystemExit("gave up")


def main():
    items, wn = {}, {}
    # no ORDER BY/OFFSET over 36k rows (the endpoint times out): split by the
    # synset id's leading digits instead — nouns run 00…15, sixteen small queries
    for prefix in [f"{i:02d}" for i in range(16)]:
        rows = sparql(f"""SELECT ?i ?w ?l WHERE {{ ?i wdt:P8814 ?w . FILTER(STRSTARTS(?w, "{prefix}"))
                          OPTIONAL {{ ?i rdfs:label ?l . FILTER(LANG(?l) = "en") }} }}""")
        for r in rows:
            q = r["i"]["value"].rsplit("/", 1)[-1]
            items[q] = r.get("l", {}).get("value", items.get(q, q))
            wn.setdefault(q, []).append(r["w"]["value"])
        print(f"  prefix {prefix}: {len(rows)} rows, {len(items)} items so far", file=sys.stderr)
        time.sleep(2)
    ids = sorted(items)
    edges = set()
    for i in range(0, len(ids), 120):
        chunk = " ".join(f"wd:{q}" for q in ids[i:i + 120])
        for r in sparql(f"SELECT ?c ?p WHERE {{ VALUES ?c {{ {chunk} }} ?c wdt:P279 ?p . }}"):
            c, p = r["c"]["value"].rsplit("/", 1)[-1], r["p"]["value"].rsplit("/", 1)[-1]
            if p in items:
                edges.add((c, p))
        if (i // 120) % 25 == 0:
            print(f"  edges: {i}/{len(ids)} items scanned, {len(edges)} edges", file=sys.stderr)
        time.sleep(0.8)
    out = ROOT / "sources/wikidata/core.json"
    json.dump({"roots": [], "labels": items, "edges": sorted(edges), "wordnet31": wn}, open(out, "w"), indent=0)
    print(f"{out}: {len(items)} items, {len(edges)} P279 edges among them")


if __name__ == "__main__":
    main()
