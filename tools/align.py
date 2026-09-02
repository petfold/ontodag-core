"""Build the alignment table: one row per concept, its name in our
vocabulary, and where it sits in every source.

Concepts come from two places: Princeton Core WordNet's noun synsets (the
principled coverage cut) and the names of ontodag's shipped `core` pack
(sense 1 of the lemma, where WordNet has it).  WordNet synset offsets are
the hub: SUMO is aligned through its own synset mapping (relation kept —
`=` exact, `+` subsumed-by, `@` instance), every other source by matching
its normalised class labels against the synset's lemmas, and only when the
match is unique.  `align/overrides.tsv` (name  source  id, `-` to clear)
wins over everything automatic and may introduce concepts WordNet lacks.

Output: align/concepts.tsv and align/queue-align.tsv (ambiguities, name
collisions, unmatched core names) for a human to look at.
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from graph import Graph, normalise

ROOT = Path(__file__).resolve().parent.parent
WN = ROOT / "sources/wordnet/dict"
SOURCES = ["sumo", "schemaorg", "yago", "opencyc", "bfo", "dolce", "dul"]
LABEL_SOURCES = {"schemaorg": "cache/schemaorg.pkl", "yago": "cache/yago.pkl",
                 "opencyc": "cache/opencyc.pkl", "bfo": "cache/bfo.pkl",
                 "dolce": "cache/dolce.pkl", "dul": "cache/dul.pkl"}


# WordNet's lexicographer files (lex_filenum -> semantic field). A collision
# between two synsets of one lemma is disambiguated by this field rather than
# by a number, so names stay stable when the concept set changes and read as
# the qualifier they are: chip.food, chip.artifact.
LEXNAMES = {"03": "tops", "04": "act", "05": "animal", "06": "artifact", "07": "attribute",
            "08": "body", "09": "cognition", "10": "communication", "11": "event", "12": "feeling",
            "13": "food", "14": "group", "15": "location", "16": "motive", "17": "object",
            "18": "person", "19": "phenomenon", "20": "plant", "21": "possession", "22": "process",
            "23": "quantity", "24": "relation", "25": "shape", "26": "state", "27": "substance",
            "28": "time"}


def read_synsets():
    """offset -> (lemmas, gloss)."""
    out = {}
    for line in open(WN / "data.noun", encoding="latin-1"):
        if line.startswith("  "):
            continue
        head, _, gloss = line.partition("|")
        f = head.split()
        nw = int(f[3], 16)
        out[f[0]] = ([f[4 + 2 * i] for i in range(nw)], gloss.strip(), LEXNAMES.get(f[1], f[1]))
    return out


def read_sense_index():
    """sense_key -> offset (index.sense)."""
    return {l.split()[0]: l.split()[1] for l in open(WN / "index.sense", encoding="latin-1")}


def read_sense1():
    """lemma -> offset of sense 1 (index.noun; WordNet orders senses by frequency)."""
    out = {}
    for line in open(WN / "index.noun", encoding="latin-1"):
        if line.startswith("  "):
            continue
        f = line.split()
        p_cnt = int(f[3])
        out[f[0]] = f[4 + p_cnt + 2]
    return out


def read_core_wordnet(sense_index):
    """Core WordNet noun synsets: offsets, in file order."""
    offs = []
    for line in open(WN.parent / "core-wordnet.txt", encoding="latin-1"):
        f = line.split()
        if len(f) < 2 or f[0] != "n":
            continue
        key = f[1].strip("[]")
        off = sense_index.get(key)
        if off:
            offs.append(off)
    return offs


def read_sumo_mapping():
    """offset -> (term, relation) from SUMO's WordNetMappings30-noun.txt."""
    out = {}
    pat = re.compile(r"&%([A-Za-z0-9_-]+)([=+@:\[\]])")
    for line in open(ROOT / "sources/sumo/WordNetMappings/WordNetMappings30-noun.txt",
                     encoding="latin-1"):
        if line.startswith(";") or not line.strip():
            continue
        m = pat.search(line)
        if m:
            out[line.split()[0]] = (m.group(1), m.group(2))
    return out


def read_overrides():
    """name -> {source: id}; also the set of names introduced by overrides."""
    ov = defaultdict(dict)
    p = ROOT / "align/overrides.tsv"
    if p.exists():
        for row in csv.reader(open(p), delimiter="\t"):
            if not row or row[0].startswith("#") or len(row) < 3:
                continue
            ov[row[0].strip()][row[1].strip()] = row[2].strip()
    return ov


def main():
    synsets = read_synsets()
    sense_index = read_sense_index()
    sense1 = read_sense1()
    sumo_map = read_sumo_mapping()
    overrides = read_overrides()
    queue = []

    # --- concepts: core pack names first (their spelling is reviewed), then Core WordNet
    core = Graph.load(ROOT / "cache/core.pkl")
    concepts = {}            # name -> offset or None
    by_offset = {}           # offset -> name
    for name in sorted(core.nodes):
        if name == "*":
            continue
        off = sense1.get(name.replace("-", "_"))
        if "wordnet" in overrides.get(name, {}):          # a hub override decides the synset up front
            off = overrides[name]["wordnet"]
            off = None if off == "-" else off
        if off is None:
            queue.append((name, "core name has no WordNet noun sense", ""))
        elif off in by_offset:
            queue.append((name, f"same synset as {by_offset[off]!r}", off))
            continue
        else:
            by_offset[off] = name
        concepts[name] = off
    for off in read_core_wordnet(sense_index):
        if off in by_offset:
            continue
        name = normalise(synsets[off][0][0])
        if name in concepts:
            base, qual = name, f"{name}.{synsets[off][2]}"
            if qual in concepts:                      # same lemma, same field: number it
                n = 2
                while f"{qual}.{n}" in concepts:
                    n += 1
                qual = f"{qual}.{n}"
            queue.append((qual, f"name collision with {base!r} — " + synsets[off][1][:60], off))
            name = qual
        concepts[name] = off
        by_offset[off] = name
    for name, ov in overrides.items():
        if name not in concepts:
            concepts[name] = ov.get("wordnet") or None

    # --- label indexes of the label-aligned sources
    graphs = {s: Graph.load(ROOT / p) for s, p in LABEL_SOURCES.items()}
    indexes = {s: g.label_index() for s, g in graphs.items()}

    rows = []
    for name, off in sorted(concepts.items()):
        if "wordnet" in overrides.get(name, {}):          # an override moves the hub too
            off = overrides[name]["wordnet"] or None
            off = None if off == "-" else off
        # Match on the concept's own name or the synset's FIRST lemma only:
        # matching every lemma made `saying` (lemmas saying/expression/locution)
        # align to Cyc's `expression`, 32K descendants of noise.
        # ... and for an overridden core name, its own name only: `software-library`
        # (first lemma `library`) must not land on schema.org's Library building.
        keys = {normalise(name.split(".")[0])}
        row = {"name": name, "wordnet": off or "", "sumo": "", "sumo_rel": ""}
        if off and off in sumo_map:
            row["sumo"], row["sumo_rel"] = sumo_map[off]
        for s in LABEL_SOURCES:
            hits = sorted({i for k in keys for i in indexes[s].get(k, [])})
            if len(hits) == 1:
                row[s] = hits[0]
            else:
                row[s] = ""
                if len(hits) > 1:
                    queue.append((name, f"{s}: {len(hits)} classes match "
                                  f"{sorted(keys)}", " ".join(hits[:6])))
        for s, v in overrides.get(name, {}).items():
            row[s] = "" if v == "-" else v
        row["gloss"] = (synsets[off][1][:90] if off else "")
        rows.append(row)

    cols = ["name", "wordnet", "sumo", "sumo_rel"] + list(LABEL_SOURCES) + ["gloss"]
    with open(ROOT / "align/concepts.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, cols, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    with open(ROOT / "align/queue-align.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["name", "issue", "ids"])
        w.writerows(queue)
    cover = {s: sum(1 for r in rows if r[s]) for s in ["wordnet", "sumo"] + list(LABEL_SOURCES)}
    print(f"{len(rows)} concepts; aligned:", ", ".join(f"{s} {n}" for s, n in cover.items()),
          f"; {len(queue)} queued for review")


if __name__ == "__main__":
    main()
