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
from pack import Dirs, pack_arg

ROOT = Path(__file__).resolve().parent.parent
WN = ROOT / "sources/wordnet/dict"
SOURCES = ["sumo", "schemaorg", "yago", "opencyc", "bfo", "dolce", "dul"]
LABEL_SOURCES = {"schemaorg": "cache/schemaorg.pkl", "yago": "cache/yago.pkl", "wikidata": "cache/wikidata.pkl",
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
        i = 4 + 2 * nw
        npts = int(f[i]); i += 1
        topics = []
        for _ in range(npts):
            sym, tgt, pos, _ = f[i:i + 4]; i += 4
            if sym == ";c":                      # member of this TOPIC domain
                topics.append(tgt)
        out[f[0]] = ([f[4 + 2 * i] for i in range(nw)], gloss.strip(), LEXNAMES.get(f[1], f[1]), topics)
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


def read_wikidata_map():
    """WordNet 3.0 noun offset -> QID, through Wikidata's P8814 (3.1 ids) and the
    3.1->3.0 sense-key bridge.  Exact, so it beats label matching."""
    import json
    try:
        d = json.load(open(ROOT / "sources/wikidata/core.json"))
        m31 = json.load(open(ROOT / "sources/wordnet31/noun31to30.json"))
    except FileNotFoundError:
        return {}
    out = {}
    for q, ids in d.get("wordnet31", {}).items():
        for w in ids:
            if w.endswith("-n") and w[:-2] in m31:
                out.setdefault(m31[w[:-2]], q)
    return out


def read_overrides(d):
    """name -> {source: id}; also the set of names introduced by overrides."""
    ov = defaultdict(dict)
    p = d / "overrides.tsv"
    if p.exists():
        for row in csv.reader(open(p), delimiter="\t"):
            if not row or row[0].startswith("#") or len(row) < 3:
                continue
            ov[row[0].strip()][row[1].strip()] = row[2].strip()
    return ov


def read_names(d):
    """offset -> chosen name (align/names.tsv: offset  name  note) — the hand-picked
    names for concepts whose word is taken by another sense."""
    out = {}
    p = d / "names.tsv"
    if p.exists():
        for row in csv.reader(open(p), delimiter="\t"):
            if row and not row[0].startswith("#") and len(row) >= 2 and row[1].strip():
                out[row[0].strip()] = row[1].strip()
    return out


def read_drops(d):
    """Concepts left out of the pack on review (align/drop.tsv: offset-or-name  reason)."""
    out = set()
    p = d / "drop.tsv"
    if p.exists():
        for row in csv.reader(open(p), delimiter="\t"):
            if row and not row[0].startswith("#"):
                out.add(row[0].strip())
    return out


def read_sources(d, synsets, wn):
    """packs/<name>/align/sources.tsv: `topic OFFSET` (nouns WordNet tags with
    that domain), `cone OFFSET` (everything below it), `synset OFFSET`."""
    offs = []
    for row in csv.reader(open(d / "sources.tsv"), delimiter="\t"):
        if not row or row[0].startswith("#"):
            continue
        kind, off = row[0].strip(), row[1].strip()
        if kind == "topic":
            offs += [o for o, v in synsets.items() if off in v[3]]
        elif kind == "cone":
            offs += [o for o in wn.nodes if off in wn.ancestors(o)]
        elif kind == "synset":
            offs.append(off)
    seen, out = set(), []
    for o in offs:
        if o in synsets and o not in seen:
            seen.add(o); out.append(o)
    return out


def main():
    dirs = Dirs(pack_arg())
    synsets = read_synsets()
    chosen = read_names(dirs.align)
    drops = read_drops(dirs.align)
    sense_index = read_sense_index()
    sense1 = read_sense1()
    sumo_map = read_sumo_mapping()
    wd_map = read_wikidata_map()
    overrides = read_overrides(dirs.align)
    queue = []
    base_rows = []
    if dirs.pack:
        # the pack builds on the core: its concepts come in unchanged (names and
        # alignments are settled there) and only the pack's own candidates are named here
        base_rows = list(csv.DictReader(open(dirs.base_concepts), delimiter="\t"))

    # --- concepts: core pack names first (their spelling is reviewed), then Core WordNet
    core = Graph.load(ROOT / "cache/core.pkl")
    concepts = {}            # name -> offset or None
    by_offset = {}           # offset -> name
    for r in base_rows:                                   # pack mode: the core's concepts, fixed
        concepts[r["name"]] = r["wordnet"] or None
        if r["wordnet"]:
            by_offset[r["wordnet"]] = r["name"]
    for name in ([] if dirs.pack else sorted(core.nodes)):
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
    if dirs.pack:
        wn = Graph.load(ROOT / "cache/wordnet.pkl")
        candidates = [o for o in read_sources(dirs.align, synsets, wn) if o not in drops and o not in by_offset]
    else:
        candidates = [o for o in read_core_wordnet(sense_index) if o not in drops]
    # names.tsv may name a synset Core WordNet lacks (attribute, body part): it joins the candidates
    candidates += [o for o in chosen if o not in candidates and o in synsets and o not in drops]
    reserved = {normalise(synsets[o][0][0]) for o in candidates} | set(chosen.values())
    for off in candidates:
        if off in by_offset:
            continue
        name = normalise(synsets[off][0][0])
        if off in chosen:
            name = chosen[off]
        elif name in concepts:
            # The bare word is taken by another sense.  Prefer another lemma of
            # this synset that is not itself a concept and not a bare word in
            # WordNet's sense-1 position of some other concept (`bag` ->
            # `handbag`); fall back to the lexicographer field (`chip.food`).
            base = name
            alt = next((normalise(l) for l in synsets[off][0][1:]
                        if normalise(l) not in concepts and normalise(l) not in reserved), None)
            qual = alt or f"{name}.{synsets[off][2]}"
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
    for d in drops:
        concepts.pop(d, None)

    # --- label indexes of the label-aligned sources
    graphs = {s: Graph.load(ROOT / p) for s, p in LABEL_SOURCES.items()}
    indexes = {s: g.label_index() for s, g in graphs.items()}

    rows = []
    base_names = {r["name"] for r in base_rows}
    for name, off in sorted(concepts.items()):
        if name in base_names:
            r = dict(next(r for r in base_rows if r["name"] == name)); r["origin"] = "base"
            for src, v in overrides.get(name, {}).items():      # a pack may align a core name to its own sources
                r[src] = "" if v == "-" else v
            rows.append(r); continue
        if "wordnet" in overrides.get(name, {}):          # an override moves the hub too
            off = overrides[name]["wordnet"] or None
            off = None if off == "-" else off
        # Match on the concept's own name or the synset's FIRST lemma only:
        # matching every lemma made `saying` (lemmas saying/expression/locution)
        # align to Cyc's `expression`, 32K descendants of noise.
        # ... and for an overridden core name, its own name only: `software-library`
        # (first lemma `library`) must not land on schema.org's Library building.
        # Qualified names (chip.food, agent.person) are the non-primary senses and
        # must not borrow the bare word's label: `agent.person` matched DUL's Agent.
        keys = set() if "." in name else {normalise(name)}
        row = {"name": name, "wordnet": off or "", "sumo": "", "sumo_rel": ""}
        if off and off in sumo_map:
            row["sumo"], row["sumo_rel"] = sumo_map[off]
        for s in LABEL_SOURCES:
            if s == "wikidata" and off and off in wd_map and wd_map[off] in graphs[s].nodes:
                row[s] = wd_map[off]                       # exact, by synset id
                continue
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
        row["origin"] = dirs.pack or "core"
        rows.append(row)

    cols = ["name", "wordnet", "sumo", "sumo_rel"] + list(LABEL_SOURCES) + ["gloss", "origin"]
    with open(dirs.concepts, "w", newline="") as fh:
        w = csv.DictWriter(fh, cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(dirs.align / "queue-align.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["name", "issue", "ids"])
        w.writerows(queue)
    cover = {s: sum(1 for r in rows if r.get(s)) for s in ["wordnet", "sumo"] + list(LABEL_SOURCES)}
    print(f"{len(rows)} concepts" + (f" ({sum(1 for r in rows if r.get('origin') != 'base')} new in pack {dirs.pack})" if dirs.pack else "") + "; aligned:", ", ".join(f"{s} {n}" for s, n in cover.items()),
          f"; {len(queue)} queued for review")


if __name__ == "__main__":
    main()
