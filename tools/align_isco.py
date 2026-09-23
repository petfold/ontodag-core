"""ISCO-08 -> the occupations pack (docs/OCCUPATIONS.md, 2026-09-23).

WordNet has the occupations (its `worker` and `professional` cones, ~1,400
synsets); what the core's cut to Core WordNet lacked is a *selection*. ISCO-08's
index of occupational titles (7,018 titles, each with its unit group) supplies
it, as CPC did for services (UPPER.md §11): a synset enters the pack when one of
its lemmas is the base of an ISCO title — the word before the first comma or
colon, "Engineer, civil" -> engineer — and it carries that title's code as ISCO's
witness. A lemma whose titles spread over several unit groups carries their
longest common prefix (`engineer` -> 21); one spread over major groups carries
nothing and is queued.

Writes, under packs/occupations/align/ (all GENERATED — hand decisions go in
drop.tsv, names.tsv and the overrides.tsv section below the marker):
  occupations.tsv  offset  name  isco  note    the code map align.py reads
  sources.tsv      synset OFFSET               the selection
  overrides.tsv    name  isco  CODE            core concepts' codes, and the hinges
  queue-isco.tsv   what a human should look at: ambiguous codes, armed forces,
                   synsets another pack owns
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align import read_synsets                     # noqa: E402
from graph import Graph                            # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "packs/occupations/align"
INDEX = ROOT / "sources/isco/ISCO-08 -88 EN Index.xlsx"
CONES = {"09632518": "worker", "10480253": "professional"}
# core's hinges, aligned to the ISCO group they name (UPPER.md §7: the hinge is core's,
# the content the pack's): every ISCO occupation is a worker; major group 2 is
# "Professionals", 7 "Craft and related trades workers", 9 "Elementary occupations"
HINGES = {"worker": "isco-root", "professional": "2", "craftsman": "7", "laborer": "9"}
MARK = "# --- hand lines below this marker are kept by tools/align_isco.py ---"


def clean(text):
    return " ".join(text.replace("-", " ").replace("_", " ").split("(")[0].lower().split())


def phrases(title):
    """(phrase, specific) for an index title. The index inverts its titles —
    "Sitter, baby" is a baby sitter, "Engineer, civil" a civil engineer — so the
    first qualifier put back in front is the SPECIFIC phrase; the head alone is
    the generic one, which may name another sense of the word (an artist's
    sitter), and is trusted only for a lemma's most frequent sense."""
    head, _, rest = title.split(":")[0].partition(",")
    head = clean(head)
    out = [(head, False)]
    qual = clean(rest.split(",")[0]) if rest else ""
    if qual:
        out.append((f"{qual} {head}", True))
        out.append((f"{qual}{head}".replace(" ", ""), True))     # "baby sitter" -> babysitter
    return out


def read_index(path=INDEX):
    """phrase -> {unit code: [full titles]}, split into specific and generic."""
    specific = defaultdict(lambda: defaultdict(list))
    generic = defaultdict(lambda: defaultdict(list))
    ws = openpyxl.load_workbook(path, read_only=True).worksheets[0]
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0 or not row[0] or not row[2]:
            continue
        code = str(row[0]).zfill(4)
        for phrase, spec in phrases(str(row[2])):
            (specific if spec else generic)[phrase][code].append(str(row[2]))
    return specific, generic


def sense_order():
    """lemma -> its noun synsets, most frequent first (index.noun)."""
    out = {}
    for line in open(ROOT / "sources/wordnet/dict/index.noun", encoding="latin-1"):
        if line.startswith("  "):
            continue
        f = line.split()
        p_cnt = int(f[3])
        out[f[0]] = f[4 + p_cnt + 2:]
    return out


def instances():
    """Offsets of instance synsets (an `@i` pointer: a named individual)."""
    out = set()
    for line in open(ROOT / "sources/wordnet/dict/data.noun", encoding="latin-1"):
        if not line.startswith("  ") and " @i " in line.partition("|")[0]:
            out.add(line.split()[0])
    return out


def common(codes):
    """Longest common prefix of the codes — the group they share ('' when none)."""
    codes = sorted(codes)
    first, last = codes[0], codes[-1]
    n = 0
    while n < len(first) and first[n] == last[n]:
        n += 1
    return first[:n]


def owned_elsewhere():
    """Offsets core and the other packs already hold: offset -> owner."""
    out = {}
    for r in csv.DictReader(open(ROOT / "align/concepts.tsv"), delimiter="\t"):
        if r.get("wordnet"):
            out[r["wordnet"]] = ("core", r["name"])
    for f in sorted((ROOT / "packs").glob("*/align/concepts.tsv")):
        pack = f.parts[-3]
        if pack == "occupations":
            continue
        for r in csv.DictReader(open(f), delimiter="\t"):
            if r.get("wordnet") and r.get("origin") not in ("base", "", None):
                out.setdefault(r["wordnet"], (pack, r["name"]))
    return out


def main():
    PACK.mkdir(parents=True, exist_ok=True)
    synsets = read_synsets()
    wn = Graph.load(ROOT / "cache/wordnet.pkl")
    specific, generic = read_index()
    order = sense_order()
    owned = owned_elsewhere()
    # every person synset, not only the worker/professional cones: WordNet files many
    # occupations elsewhere (tailor under garment-maker, mechanic under skilled worker's
    # siblings); ISCO's titles do the selecting, the first-sense rule the disambiguating
    # instances out: a named person (Samuel Barber, the composer) is no occupation, and
    # as the lemma's first person sense it made the barber lose the first-sense test
    named = instances()
    cone = [o for o in synsets if synsets[o][2] == "person" and o not in named]
    in_cone = set(cone)

    def first_sense(lemma, off):
        """Is `off` the lemma's most frequent sense among the cone's synsets?"""
        return next((o for o in order.get(lemma.lower(), []) if o in in_cone), None) == off
    rows, selected, core_codes, queue = [], [], {}, []
    for off in sorted(cone):
        lemmas, gloss = synsets[off][0], synsets[off][1]
        codes = defaultdict(list)
        for lemma in lemmas:
            key = clean(lemma)
            for code, titles in specific.get(key, {}).items():
                codes[code] += titles
            if first_sense(lemma, off):
                for code, titles in generic.get(key, {}).items():
                    codes[code] += titles
        if not codes:
            continue
        code = common(codes)
        if not code:
            # titles spread over major groups (chef: 3434 chefs, 9411 cooks): take the
            # major group holding two thirds of them, if one does
            by_major = defaultdict(list)
            for c, ts in codes.items():
                by_major[c[0]] += [c] * len(ts)
            major, cs = max(by_major.items(), key=lambda kv: len(kv[1]))
            if len(cs) * 3 >= 2 * sum(len(v) for v in by_major.values()):
                code = common(set(cs))
        titles = sorted({t for ts in codes.values() for t in ts})
        note = f"{'; '.join(titles[:3])}{' …' if len(titles) > 3 else ''} — {gloss[:60]}"
        if not code:
            queue.append((off, lemmas[0], "codes span major groups: " + " ".join(sorted(codes)), gloss[:60]))
            continue
        if code.startswith("0"):
            queue.append((off, lemmas[0], f"armed forces ({code}): ranks stay out unless ruled in", gloss[:60]))
            continue
        if off in owned:
            owner, name = owned[off]
            if owner == "core":
                core_codes[name] = code                # a core concept: ISCO witnesses it through overrides
            else:
                queue.append((off, lemmas[0], f"held by the {owner} pack as {name!r} (isco {code})", gloss[:60]))
            continue
        rows.append((off, "", code, note))
        selected.append(off)
    with open(PACK / "occupations.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["# offset", "name", "isco", "note — GENERATED by tools/align_isco.py"])
        w.writerows(rows)
    with open(PACK / "sources.tsv", "w", newline="") as fh:
        fh.write("# kind\toffset\tnote — GENERATED by tools/align_isco.py: WordNet synsets an ISCO-08 title names\n")
        for off in selected:
            fh.write(f"synset\t{off}\t{synsets[off][0][0]}\n")
    hand = []
    ov = PACK / "overrides.tsv"
    if ov.exists():
        text = open(ov).read()
        if MARK in text:
            hand = text.split(MARK, 1)[1].strip("\n").splitlines()
    with open(ov, "w", newline="") as fh:
        fh.write("# name\tsource\tid — GENERATED above the marker by tools/align_isco.py\n")
        for name, code in sorted({**core_codes, **HINGES}.items()):
            fh.write(f"{name}\tisco\t{code}\n")
        fh.write(MARK + "\n")
        for line in hand:
            fh.write(line + "\n")
    with open(PACK / "queue-isco.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["offset", "lemma", "issue", "gloss"])
        w.writerows(queue)
    print(f"{len(cone)} person synsets; {len(selected)} selected for the pack, "
          f"{len(core_codes)} core concepts given an ISCO code, {len(queue)} queued")


if __name__ == "__main__":
    main()
