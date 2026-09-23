"""The widened cut's candidate queue (docs/COVERAGE.md §2, W1; 2026-09-23).

Frequency proposes, judgement disposes: this lists WordNet noun senses that
neither core nor any pack holds and that one of two frequency sources says a
person meets —

  * SemCor: the sense itself tagged at least SEMCOR times (index.sense); the
    corpus is the 1960s Brown sample, so it over-weights military ranks and
    laboratory chemistry and knows nothing of pizza;
  * wordfreq (Zipf scale over subtitles, Wikipedia, news, web — modern, but
    blind to part of speech): the lemma at least ZIPF, and only when its NOUN
    use dominates (its tagged noun count at least its verb, adjective and
    adverb counts; an untagged lemma only when WordNet knows it as nothing but
    a noun) — which removes `have`, `great`, `white`.

The sense taken for a wordfreq hit is the lemma's most frequent noun sense.
Out: instances, quantities (values, UPPER.md §7), and senses WordNet marks as
disparaging, obscene, profane, archaic or a trade name (usage domains). Slang
and colloquial senses stay, flagged. Nothing here enters a pack: the queue is
read by hand, area by area, and what is taken goes through align/views/
consensus/review like everything else.

    pip install wordfreq            # optional: without it, SemCor alone
    python3 tools/queue_wide.py [--semcor 3] [--zipf 4.0]

Writes build/queue-wide.tsv: offset  lemma  field  semcor  zipf  why  nearest
placed ancestor  flags  gloss — most frequent first.
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align import read_synsets                     # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WN = ROOT / "sources/wordnet/dict"
EXCLUDE = {"06717170": "disparaging", "06718862": "ethnic slur", "07124340": "obscene",
           "07128527": "profane", "07073447": "archaic", "06845599": "trade name",
           "06851742": "trademark"}
FLAG = {"07157273": "slang", "07075172": "colloquial"}
POS = {"1": "noun", "2": "verb", "3": "adj", "4": "adv", "5": "adj"}


def read_data():
    """offset -> (hypernyms, instance?, usage domains)."""
    out = {}
    for line in open(WN / "data.noun", encoding="latin-1"):
        if line.startswith("  "):
            continue
        f = line.partition("|")[0].split()
        nw = int(f[3], 16)
        i = 4 + 2 * nw
        n = int(f[i]); i += 1
        hyp, inst, usage = [], False, set()
        for _ in range(n):
            sym, tgt, pos, _ = f[i:i + 4]; i += 4
            if sym in ("@", "@i") and pos == "n":
                hyp.append(tgt)
                inst = inst or sym == "@i"
            elif sym == ";u":
                usage.add(tgt)
        out[f[0]] = (hyp, inst, usage)
    return out


def read_counts():
    """(noun sense offset -> tag count, lemma -> {pos: tag count})."""
    sense, lemma = defaultdict(int), defaultdict(lambda: defaultdict(int))
    for line in open(WN / "index.sense", encoding="latin-1"):
        key, off, _, cnt = line.split()
        lem, _, rest = key.partition("%")
        pos = POS.get(rest[0], "?")
        lemma[lem][pos] += int(cnt)
        if pos == "noun":
            sense[off] += int(cnt)
    return sense, lemma


def read_index(pos):
    """lemma -> offsets, most frequent first (index.<pos>)."""
    out = {}
    for line in open(WN / f"index.{pos}", encoding="latin-1"):
        if line.startswith("  "):
            continue
        f = line.split()
        out[f[0]] = f[4 + int(f[3]) + 2:]
    return out


def placed():
    """offset -> name, and the set of names, over core and every pack."""
    by_off, names = {}, set()
    for f in [ROOT / "align/concepts.tsv"] + sorted((ROOT / "packs").glob("*/align/concepts.tsv")):
        for r in csv.DictReader(open(f), delimiter="\t"):
            names.add(r["name"].lower())
            if r.get("wordnet"):
                by_off.setdefault(r["wordnet"], r["name"])
    return by_off, names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semcor", type=int, default=3)
    ap.add_argument("--zipf", type=float, default=4.0)
    args = ap.parse_args()
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        zipf_frequency = None
        print("wordfreq not installed: SemCor only", file=sys.stderr)
    synsets, data = read_synsets(), read_data()
    sense_cnt, lemma_cnt = read_counts()
    nouns = read_index("noun")
    other_pos = set(read_index("verb")) | set(read_index("adj")) | set(read_index("adv"))
    by_off, names = placed()

    def nearest(off):
        frontier, seen = list(data[off][0]), set()
        while frontier:
            nxt = []
            for h in frontier:
                if h in seen:
                    continue
                seen.add(h)
                if h in by_off:
                    return by_off[h]
                nxt += data.get(h, ([], 0, 0))[0]
            frontier = nxt
        return ""

    cand = {}
    for off, (lemmas, gloss, field, _) in synsets.items():
        if sense_cnt[off] >= args.semcor:
            cand[off] = "semcor"
    if zipf_frequency:
        for lem, offs in nouns.items():
            if "_" in lem or not lem.isalpha():
                continue
            c = lemma_cnt.get(lem, {})
            noun = c.get("noun", 0)
            dominant = noun >= max(c.get("verb", 0), c.get("adj", 0), c.get("adv", 0)) and (noun > 0 or lem not in other_pos)
            if dominant and zipf_frequency(lem, "en") >= args.zipf:
                cand.setdefault(offs[0], "zipf")
    rows = []
    for off, why in cand.items():
        lemmas, gloss, field, _ = synsets[off]
        hyp, inst, usage = data[off]
        if off in by_off or inst or field == "quantity" or usage & set(EXCLUDE):
            continue
        z = zipf_frequency(lemmas[0].replace("_", " "), "en") if zipf_frequency else 0.0
        flags = [FLAG[u] for u in usage if u in FLAG]
        if any(l.lower().replace("_", "-") in names for l in lemmas):
            flags.append("word present in another sense")
        rows.append((off, lemmas[0], field, sense_cnt[off], round(z, 2), why, nearest(off), ",".join(flags), gloss[:90]))
    rows.sort(key=lambda r: (-(r[3] + 10 * r[4]), r[1]))
    with open(ROOT / "build/queue-wide.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["offset", "lemma", "field", "semcor", "zipf", "why", "nearest", "flags", "gloss"])
        w.writerows(rows)
    by_field = defaultdict(int)
    for r in rows:
        by_field[r[2]] += 1
    fresh = sum(1 for r in rows if "word present" not in r[7])
    print(f"{len(rows)} candidates ({fresh} whose words are nowhere yet): "
          + ", ".join(f"{k} {v}" for k, v in sorted(by_field.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
