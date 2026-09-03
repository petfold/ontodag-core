"""Resolve English labels to Wikidata items by exact label/alias match, printing
every candidate with its description so a human picks the right QID.

    python3 tools/resolve_labels.py labels.txt > out.txt

One label per line; `#` comments ignored.  SPARQL `VALUES` over 35 labels a
query (the wbsearchentities API slowed to ~4 s a term in 2026-09); the
chunk-level failures the endpoint sometimes returns are printed as `!!` lines
so a silent empty chunk cannot pass for "no such item".  Retry those labels."""
import json
import sys
import time
import urllib.parse
import urllib.request

EP = "https://query.wikidata.org/sparql"
UA = "ontodag-core/0.1 (github.com/petfold/ontodag-core; upper ontology construction)"


def sparql(q):
    req = urllib.request.Request(EP + "?" + urllib.parse.urlencode({"query": q, "format": "json"}),
                                 headers={"User-Agent": UA})
    for a in range(5):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))["results"]["bindings"]
        except Exception:
            if a == 4:
                raise
            time.sleep(6 * (a + 1))


def main(path):
    labels = [l.strip() for l in open(path) if l.strip() and not l.startswith("#")]
    for i in range(0, len(labels), 35):
        chunk = labels[i:i + 35]
        vals = " ".join(json.dumps(l) + "@en" for l in chunk)
        q = f'''SELECT ?l ?x ?d WHERE {{ VALUES ?l {{ {vals} }} ?x rdfs:label|skos:altLabel ?l .
            FILTER NOT EXISTS {{ ?x wdt:P31 wd:Q5 }} FILTER NOT EXISTS {{ ?x wdt:P31 wd:Q13442814 }}
            FILTER NOT EXISTS {{ ?x wdt:P31 wd:Q4167410 }} FILTER NOT EXISTS {{ ?x wdt:P31 wd:Q7187 }}
            FILTER NOT EXISTS {{ ?x wdt:P31 wd:Q8054 }} FILTER NOT EXISTS {{ ?x wdt:P31 wd:Q4167836 }}
            OPTIONAL {{ ?x schema:description ?d FILTER(LANG(?d) = "en") }} }} LIMIT 700'''
        try:
            rows = sparql(q)
        except Exception as e:
            print("!! chunk failed:", " | ".join(chunk), e, flush=True)
            continue
        hits = {}
        for r in rows:
            hits.setdefault(r["l"]["value"], {})[r["x"]["value"].rsplit("/", 1)[-1]] = r.get("d", {}).get("value", "")[:70]
        for l in chunk:
            h = hits.get(l, {})
            print(f"{l:38}|" + " || ".join(f"{q} — {d}" for q, d in list(h.items())[:6]), flush=True)
        time.sleep(2)
    print("=== done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
