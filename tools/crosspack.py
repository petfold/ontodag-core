"""Cross-pack identity check: the same Wikidata QID or WordNet offset must carry
ONE name everywhere, and one name must not stand for two different things.

    python3 tools/crosspack.py            # all packs
    python3 tools/crosspack.py computing  # only collisions involving this pack

Reads packs/*/align/concepts.tsv (post-align, so names.tsv/overrides.tsv are
applied) and build/core.od.  Names are identity in OntoDAG (UPPER.md §1), so a
QID named `data-structure` in one pack and `data-structures` in another would
merge as two concepts — a collision that neither pack can see alone."""
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
focus = sys.argv[1] if len(sys.argv) > 1 else None

by_qid, by_off, by_name = defaultdict(set), defaultdict(set), defaultdict(set)
for cf in sorted(ROOT.glob("packs/*/align/concepts.tsv")):
    pack = cf.parts[-3]
    for r in csv.DictReader(open(cf), delimiter="\t"):
        if r["origin"] == "base":
            continue
        n = r["name"]
        if r.get("wikidata"):
            by_qid[r["wikidata"]].add((n, pack))
        if r.get("wordnet"):
            by_off[r["wordnet"]].add((n, pack))
        by_name[n].add((r.get("wikidata") or "", r.get("wordnet") or "", pack))

core = {line.split()[0] for line in open(ROOT / "build/core.od") if line.strip() and not line.startswith("#")}

def show(title, items):
    items = [(k, v) for k, v in items if not focus or any(p == focus for *_, p in v)]
    print(f"== {title}: {len(items)}")
    for k, v in sorted(items):
        print(" ", k, sorted(v))

show("one QID, several names", [(q, v) for q, v in by_qid.items() if len({n for n, _ in v}) > 1])
show("one WordNet offset, several names", [(o, v) for o, v in by_off.items() if len({n for n, _ in v}) > 1])
show("one name, different identities", [(n, v) for n, v in by_name.items()
     if len({(q, o) for q, o, _ in v if q or o}) > 1 and len({q for q, o, _ in v if q}) > 1 or
        len({o for q, o, _ in v if o}) > 1])
show("pack name that is also a core name", [(n, v) for n, v in by_name.items() if n in core])
