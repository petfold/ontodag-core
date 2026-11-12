"""Real items for a branch of the vocabulary, from Wikidata.

    python3 tools/instances.py place OUT.od [--per-class 40]

The shipped packs hold categories and no items, so nothing in them is
filed under two aspects at once, which is where an OntoDAG stops being a
tree (docs/UPPER.md §17). This writes a store that has such items: for
every category below BRANCH that is aligned with a Wikidata item, up to
`--per-class` things Wikidata calls an instance of it (P31), each filed
under every category of the branch it is an instance of. The store is
core and the ten domain packs with those items added, saved as an `.od`
file that `odag -f OUT.od` opens.

Only direct instance-of statements are used, and an item's name is its
Wikidata id. The file is not tracked: Wikidata changes, and so would it.

The requests name this tool to Wikidata, as its policy asks; set
WIKIDATA_UA to send another name.
"""
import argparse
import collections
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ontodag import native, packs, prelude
from ontodag.dag import OntoDAG

ROOT = Path(__file__).resolve().parent.parent
EP = "https://query.wikidata.org/sparql"
UA = os.environ.get(
    "WIKIDATA_UA",
    "ontodag-core/0.1 (github.com/petfold/ontodag-core; upper ontology construction)")
DOMAINS = ["physics", "mathematics", "chemistry", "biology", "medicine", "ai",
           "economics", "computing", "geography", "space"]
PAUSE = 1.5           # seconds between queries


def sparql(query):
    url = EP + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    for attempt in range(6):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(request, timeout=90) as answer:
                return json.load(answer)["results"]["bindings"]
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(10 * (attempt + 1))
    return None


def qid(binding):
    return binding["value"].rsplit("/", 1)[1]


def aligned():
    """name -> Wikidata id, from core's and every pack's concepts table."""
    found = {}
    tables = [ROOT / "align/concepts.tsv",
              *sorted((ROOT / "packs").glob("*/align/concepts.tsv"))]
    for path in tables:
        with open(path, encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row.get("wikidata"):
                    found.setdefault(row["name"], row["wikidata"])
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("branch", help="the category whose cone gets items")
    parser.add_argument("out", help="the .od file to write")
    parser.add_argument("--per-class", type=int, default=40)
    args = parser.parse_args()

    dag = OntoDAG()
    prelude.apply(dag)
    for name in ["core", *DOMAINS]:
        dag.merge(packs.adoption_dag(dag, name))
    if args.branch not in dag.nodes:
        raise SystemExit(f"no category {args.branch!r}")
    cone = {n.name for n in dag.get_descendants(dag.nodes[args.branch],
                                                computed=False)}
    cone.add(args.branch)
    ids = aligned()
    names_of = collections.defaultdict(list)
    for name in sorted(cone):
        if name in ids:
            names_of[ids[name]].append(name)
    classes = sorted(names_of)
    print(f"{len(cone)} categories at or below {args.branch}, "
          f"{len(classes)} Wikidata ids among them", file=sys.stderr)

    items = set()
    for start in range(0, len(classes), 20):
        chunk = classes[start:start + 20]
        parts = " UNION ".join(
            f"{{ SELECT ?i WHERE {{ ?i wdt:P31 wd:{c} }} "
            f"LIMIT {args.per_class} }}" for c in chunk)
        rows = sparql(f"SELECT ?i WHERE {{ {parts} }}")
        if rows is None:
            print(f"  classes {start}–{start + len(chunk)}: no answer, "
                  f"left out", file=sys.stderr)
        else:
            items.update(qid(row["i"]) for row in rows)
        time.sleep(PAUSE)
    items = sorted(i for i in items if i not in names_of)
    print(f"{len(items)} instances found", file=sys.stderr)

    filed = collections.defaultdict(set)
    for start in range(0, len(items), 150):
        chunk = " ".join(f"wd:{i}" for i in items[start:start + 150])
        rows = sparql(f"SELECT ?i ?c WHERE {{ VALUES ?i {{ {chunk} }} "
                      f"?i wdt:P31 ?c }}")
        for row in rows or ():
            for name in names_of.get(qid(row["c"]), ()):
                filed[qid(row["i"])].add(name)
        time.sleep(PAUSE)

    spread = collections.Counter()
    for item in sorted(filed):
        dag.put(item, sorted(filed[item]))
        spread[len([p for p in dag.nodes[item].parents
                    if dag.nodes.get(p.name) is p])] += 1
    native.save(dag, args.out)
    used = {name for names in filed.values() for name in names}
    print(f"{len(filed)} items filed under {len(used)} categories; by the "
          f"number of parents they keep: "
          + ", ".join(f"{k}: {v}" for k, v in sorted(spread.items())))
    print(f"written: {args.out}")


if __name__ == "__main__":
    main()
