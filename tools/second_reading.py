"""List a pack's accepted edges that rest on ONE source (plus Claude's reading)
— the second-reading queue (UPPER.md §9) — with both glosses.

    python3 tools/second_reading.py --pack NAME [--sample N --seed S] [--rulings]

Default: edges whose only source witness is wordnet, wikidata, sumo, opencyc or
yago (Claude's `claude`/`claude-ruling` and Peter's `peter` do not count as
sources). --rulings adds the pure hub rulings (no source at all)."""
import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {"wordnet", "wikidata", "sumo", "opencyc", "yago", "schemaorg", "bfo", "dolce", "dul"}

ap = argparse.ArgumentParser()
ap.add_argument("--pack", required=True)
ap.add_argument("--sample", type=int, default=0)
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--rulings", action="store_true")
a = ap.parse_args()
gloss = {r["name"]: r["gloss"][:70] for r in csv.DictReader(open(ROOT / "packs" / a.pack / "align/concepts.tsv"), delimiter="\t")}
rows = []
for r in csv.DictReader(open(ROOT / "packs" / a.pack / "build/evidence.tsv"), delimiter="\t"):
    if r["status"] != "accepted":
        continue
    srcs = [w for w in r["for"].split() if w in SOURCES]
    if len(srcs) == 1 or (a.rulings and not srcs):
        rows.append((r["sub"], r["sup"], " ".join(srcs) or "ruling"))
if a.sample:
    rows = random.Random(a.seed).sample(rows, min(a.sample, len(rows)))
print(f"# {a.pack}: {len(rows)} edges")
for sub, sup, w in sorted(rows):
    print(f"{sub} ⊑ {sup} [{w}] | {gloss.get(sub, '')} | {gloss.get(sup, '')}")
