"""Vector witnesses beside the everyday-sense audit: word frequencies and
embeddings next to tools/sense_audit.py's WordNet signals (Peter, 2026-10-23).

    VPY=~/.venvs/ontodag-vectors/bin/python
    $VPY tools/sense_vectors.py               # core: build/sense-audit.tsv
    $VPY tools/sense_vectors.py --pack NAME   # packs/NAME/build/sense-audit.tsv
    $VPY tools/sense_vectors.py --all         # core, then every pack
    $VPY tools/sense_vectors.py --evaluate    # how often each method's first
                                              # sense agrees with SemCor's
    $VPY tools/sense_vectors.py --learn       # how well misfit and trap find
                                              # what the reviews found

Run tools/sense_audit.py first. This adds columns to its sheet, in place:

  zipf         the name's frequency on the Zipf scale (wordfreq): 3 is once
               per million words. A leaf below about 2.5 is a shrink
               candidate; a frequent word holding a rare sense, a rename one.
  first        the noun sense the word's vector puts first, when it is not
               the sense the node holds: "OFFSET lemma: gloss"
  first_by     its lead over the held sense (the larger, the surer)
  twin         the other name whose gloss is nearest, when near enough to be
               the same thing; "=name" when it holds the very same synset
  twin_sim     the gloss similarity (cosine) of the twin
  parents_sim  the gloss similarity to each parent, lowest first. With
               several parents, a low one beside a high one is the
               OR-read-as-AND pattern.
  misfit       how suspect the node's placement is, 0 to 1 (a percentile in
               the store): its lowest parent similarity and its distance from
               its siblings, rank-averaged. Read from the top.
  trap         how likely the name reads as another sense than the one held,
               0 to 1: the vectors' lead for another first sense, WordNet's
               rank of the held sense, and the name's distance from its gloss,
               rank-averaged. Read from the top.

`--learn` scores these against what the 2026-10-22 pass and the 2026-10-16
review found, on core as it was before the pass (commit b3f89d7's sheet):
misfit ranks first the nodes the pass moved or cut (AUC 0.76; 28% of the
top 100 against a base rate of 4%), trap the names of
align/name-traps-v14.tsv (AUC 0.86; 30% of the top 100, base rate 3%).
Those negatives are only the names no review touched, so the precisions
are lower bounds: trap's unstarred top names (upgrade, trust, top, seal,
jack, column) look like traps the 2026-10-16 list missed.

These are witnesses for a reader, never verdicts. A vector measures
relatedness, not "is a" (building and dwelling are close), and a word's
vector leans to the sense its training text uses most: Wikipedia and news,
here, so `head` leans to the leader more than everyday speech would.

The "first" sense is the one whose words lie closest to the word's own
vector, the idea of McCarthy et al. 2004 ("Finding predominant word senses
in untagged text"). A sense's words are its other lemmas, its gloss and
examples, and the lemmas of its hypernyms and hyponyms; proper names (Cole
Porter, a sense of `porter`) do not compete. `--evaluate` checks it against
SemCor wherever SemCor's counts name a clear first sense (1,619 noun
lemmas): it agrees 58% of the time (chance 31%), and 82% of the time when
its lead is in the top quarter, `first_by` >= SURE below. McCarthy et al.'s
neighbour vote and a sentence encoder did worse here (56%, 42%).

Requirements (an analysis venv, not the build's):
    uv venv ~/.venvs/ontodag-vectors --python 3.12
    uv pip install --python ~/.venvs/ontodag-vectors/bin/python torch \\
        --index-url https://download.pytorch.org/whl/cpu
    uv pip install --python ~/.venvs/ontodag-vectors/bin/python \\
        sentence-transformers wordfreq
GloVe 6B 300d (Stanford, public domain; 862 MB from the Hugging Face mirror
stanfordnlp/glove) and the sentence encoder all-MiniLM-L6-v2 (Apache 2.0)
are fetched once into ~/.cache/ontodag-core/ and ~/.cache/huggingface/.
"""
import argparse
import csv
import io
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from sense_audit import wordnet  # noqa: E402  (WordNet 3.0 and SemCor's counts)

CACHE = Path.home() / ".cache/ontodag-core"
GLOVE_URL = "https://huggingface.co/stanfordnlp/glove/resolve/main/glove.6B.zip"
ENCODER = "sentence-transformers/all-MiniLM-L6-v2"
COLUMNS = ["zipf", "first", "first_by", "twin", "twin_sim", "parents_sim", "misfit", "trap"]
NEIGHBOURS = 50            # the word's neighbours that vote (McCarthy et al.)
VOTERS = 100_000           # neighbours come from GloVe's most frequent words
HYPONYMS = 30              # a sense's hyponyms whose lemmas stand for it
SURE = 0.166               # first_by from here up: SemCor agreed 82% (--evaluate)
TWIN = 0.90                # gloss similarity of a near-twin: duplicates, but also
                           # siblings with parallel glosses (husband, wife)
STOP = set("""a an the of or and to in on for by with as at from that which who whom whose
    is are was were be been being its it this these those any some such other than into onto
    about used especially usually something someone one ones etc e g i e not no often more most
    very can may has have having made make makes s""".split())


def glove():
    """GloVe 6B 300d: {word: row} and the unit vectors, in GloVe's order
    (most frequent first). Converted once to .npy in the cache."""
    npy, voc = CACHE / "glove.6B.300d.npy", CACHE / "glove.6B.300d.vocab"
    if not npy.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        archive = CACHE / "glove.6B.zip"
        if not archive.exists():
            print(f"downloading {GLOVE_URL} (862 MB) ...", file=sys.stderr)
            part = archive.with_suffix(".part")
            with urllib.request.urlopen(GLOVE_URL) as src, open(part, "wb") as dst:
                shutil.copyfileobj(src, dst)
            part.rename(archive)
        words, rows = [], []
        with zipfile.ZipFile(archive) as zf, zf.open("glove.6B.300d.txt") as fh:
            for line in io.TextIOWrapper(fh, encoding="utf-8"):
                word, rest = line.rstrip("\n").split(" ", 1)
                words.append(word)
                rows.append(np.array(rest.split(), dtype=np.float32))
        m = np.vstack(rows)
        m /= np.linalg.norm(m, axis=1, keepdims=True) + 1e-9
        np.save(npy, m)
        voc.write_text("\n".join(words), encoding="utf-8")
    words = voc.read_text(encoding="utf-8").split("\n")
    return {w: i for i, w in enumerate(words)}, np.load(npy)


def tokens(text):
    return [t for t in re.findall(r"[a-z]+", text.lower().replace("_", " ")) if t not in STOP]


class Space:
    """GloVe, as the witnesses use it."""

    def __init__(self):
        self.vocab, self.m = glove()

    def mean(self, words):
        rows = [self.vocab[w] for w in words if w in self.vocab]
        if not rows:
            return None
        v = self.m[rows].mean(axis=0)
        n = np.linalg.norm(v)
        return v / n if n else None


_EXAMPLES, _HYPONYMS, _INSTANCES = {}, {}, set()


def _wordnet_extras(data):
    """WordNet's example sentences, hyponym links and instances (proper
    names: Cole Porter is a sense of `porter`), which `wordnet()` leaves out."""
    if not _EXAMPLES:
        for line in open(ROOT.parent / "wordnet/dict/data.noun", encoding="latin-1"):
            if line[:1].isdigit():
                offset, gloss = line.split(" ", 1)[0], line.split(" | ", 1)[-1]
                _EXAMPLES[offset] = " ".join(x.strip().strip('"') for x in gloss.split("; ")[1:]
                                            if x.strip().startswith('"'))
                if " @i " in line.split(" | ", 1)[0]:
                    _INSTANCES.add(offset)
        for offset, d in data.items():
            for h in d["hypers"]:
                _HYPONYMS.setdefault(h, []).append(offset)
    return _EXAMPLES, _HYPONYMS


def sense_text(data, offset, lemma):
    """The words that stand for a sense: its other lemmas (twice), its gloss
    and examples, and its hypernyms' and hyponyms' lemmas."""
    examples, hyponyms = _wordnet_extras(data)
    d = data[offset]
    own = set(tokens(lemma))
    words = [w for l in d["words"] for w in tokens(l) if w not in own] * 2 + tokens(d["gloss"])
    words += [w for w in tokens(examples.get(offset, "")) if w not in own]
    for h in d["hypers"] + hyponyms.get(offset, [])[:HYPONYMS]:
        words += [w for l in data[h]["words"] for w in tokens(l) if w not in own]
    return words


def first_senses(lemmas, index, data, space, method="direct"):
    """{lemma: [(offset, score), ...] best first} for lemmas with several
    noun senses. `neighbours` is McCarthy et al.'s vote; `direct` compares
    the word's own vector with each sense's."""
    out = {}
    todo = []
    _wordnet_extras(data)
    for lemma in lemmas:
        senses = [o for o in index.get(lemma, []) if o not in _INSTANCES]   # kinds, not names
        w = space.mean(tokens(lemma))
        if len(senses) < 2 or w is None:
            continue
        vecs = [(o, space.mean(sense_text(data, o, lemma))) for o in senses]
        vecs = [(o, v) for o, v in vecs if v is not None]
        if len(vecs) >= 2:
            todo.append((lemma, w, vecs))
    if method == "direct":
        for lemma, w, vecs in todo:
            out[lemma] = sorted(((o, float(v @ w)) for o, v in vecs), key=lambda x: -x[1])
        return out
    voters = space.m[:VOTERS]
    own = [{space.vocab.get(t) for t in tokens(lemma)} for lemma, _, _ in todo]
    for start in range(0, len(todo), 256):
        batch = todo[start:start + 256]
        sims = np.stack([w for _, w, _ in batch]) @ voters.T            # (b, VOTERS)
        for k, (lemma, w, vecs) in enumerate(batch):
            row = sims[k]
            row[[i for i in own[start + k] if i is not None and i < VOTERS]] = -1
            near = np.argpartition(-row, NEIGHBOURS)[:NEIGHBOURS]
            weights = row[near]
            senses = np.stack([v for _, v in vecs])                   # (s, 300)
            fit = np.clip(senses @ voters[near].T, 0, None)           # (s, n)
            share = fit / (fit.sum(axis=0, keepdims=True) + 1e-9)     # each voter splits its vote
            score = share @ weights
            out[lemma] = sorted(((o, float(s)) for (o, _), s in zip(vecs, score)),
                                key=lambda x: -x[1])
    return out


def encoder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(ENCODER, device="cpu")


_ENCODED = {}


def encode(model, texts):
    """Unit vectors for `texts`; each text is encoded once per run (the packs
    share core's)."""
    todo = sorted({t for t in texts if t not in _ENCODED})
    if todo:
        vecs = model.encode(todo, batch_size=128, normalize_embeddings=True, show_progress_bar=False)
        _ENCODED.update(zip(todo, vecs))
    return np.stack([_ENCODED[t] for t in texts]) if texts else np.zeros((0, 384), np.float32)


def evaluate():
    """How often each method's first sense is SemCor's clear first sense
    (the most tagged sense, tagged at least 5 times and twice the next)."""
    index, data, tags, _ = wordnet()
    gold = {}
    for lemma, senses in index.items():
        counts = sorted(((tags.get((lemma, o), 0), o) for o in senses), reverse=True)
        if len(senses) >= 2 and counts[0][0] >= 5 and counts[0][0] >= 2 * counts[1][0]:
            gold[lemma] = counts[0][1]
    space = Space()
    results = {}
    for method in ("neighbours", "direct"):
        ranked = first_senses(gold, index, data, space, method)
        hits = sum(ranked[l][0][0] == gold[l] for l in ranked)
        results[method] = (hits, len(ranked))
        if method == "direct":
            leads = sorted(((r[0][1] - r[1][1], r[0][0] == gold[l]) for l, r in ranked.items()),
                           reverse=True)
            for share in (0.25, 0.5):
                top = leads[: int(len(leads) * share)]
                print(f"direct, lead in the top {share:.0%} (first_by >= {top[-1][0]:.3f}): "
                      f"{sum(h for _, h in top) / len(top):.0%} agree")
    lemmas = sorted(first_senses(gold, index, data, space, "direct"))
    model = encoder()
    words = encode(model, [l.replace("_", " ") for l in lemmas])
    pairs = [(l, o) for l in lemmas for o in index[l]]
    glosses = encode(model, [f"{l.replace('_', ' ')}: {data[o]['gloss']}" for l, o in pairs])
    at = {l: i for i, l in enumerate(lemmas)}
    best = {}
    for (lemma, o), g in zip(pairs, glosses):
        s = float(g @ words[at[lemma]])
        if lemma not in best or s > best[lemma][1]:
            best[lemma] = (o, s)
    hits = sum(best[l][0] == gold[l] for l in lemmas)
    results["encoder"] = (hits, len(lemmas))
    chance = np.mean([1 / len(index[l]) for l in lemmas])
    print(f"{len(gold)} lemmas with a clear SemCor first sense; chance agreement {chance:.0%}")
    for method, (hits, n) in results.items():
        print(f"  {method:10s} {hits}/{n} = {hits / n:.0%}")


def auc(scores, labels):
    """The chance that a random positive scores above a random negative
    (ties count half): 0.5 is no better than chance."""
    s, y = np.asarray(scores, float), np.asarray(labels, bool)
    _, inverse, counts = np.unique(s, return_inverse=True, return_counts=True)
    ranks = (np.cumsum(counts) - (counts - 1) / 2)[inverse]
    pos, neg = y.sum(), (~y).sum()
    return (ranks[y].sum() - pos * (pos + 1) / 2) / (pos * neg)


def learn():
    """Score misfit and trap against what the reviews found, on core as it
    was before the 2026-10-22 pass: misfit against the nodes whose parent
    the pass moved or cut (applied, not reverted), trap against the names
    of align/name-traps-v14.tsv. The negatives are the names no decision
    touched, so the precisions are lower bounds: a misfiled node nobody
    caught counts against the score."""
    import subprocess
    text = subprocess.run(["git", "show", "b3f89d7:build/sense-audit.tsv"], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout
    own = [r for r in csv.DictReader((l for l in text.splitlines() if not l.startswith("#")),
                                     delimiter="\t") if r["name"]]
    index, data, _, _ = wordnet()
    space, model = Space(), encoder()
    vectors = encode(model, [text_of(r) for r in own])
    at = {r["name"]: i for i, r in enumerate(own)}
    ranked = first_senses([r["name"].replace("-", "_") for r in own], index, data, space)
    for i, r in enumerate(own):
        scored = sorted(float(vectors[i] @ vectors[at[p]]) for p in r["parents"].split() if p in at)
        r["_lowest"] = scored[0] if scored else None
        r["_n"] = len(scored)
        order = ranked.get(r["name"].replace("-", "_"))
        r["_lead"] = order[0][1] - dict(order)[r["wn30"]] if order and r["wn30"] in dict(order) else 0.0
    misfit_scores(own, vectors)
    trap_scores(own, model)
    decided = {}
    for r in csv.DictReader((l for l in open(ROOT / "align/sense-review-v14.tsv")
                             if not l.startswith("#")), delimiter="\t"):
        if r["pack"] == "core":
            decided.setdefault(r["name"], set()).add((r["action"], r["apply"] == "yes"))
    traps = {l.split("\t")[1] for l in open(ROOT / "align/name-traps-v14.tsv")
             if l.startswith("core\t")}

    def report(what, rows, score, positive):
        s = [float(r[score]) for r in rows]
        y = [positive(r) for r in rows]
        top = np.argsort(s, kind="stable")[::-1][:100]
        print(f"  {what}: AUC {auc(s, y):.2f}; {np.mean([y[i] for i in top]):.0%} of the top 100 "
              f"(base rate {np.mean(y):.0%}, {sum(y)} of {len(y)})")
        print("    top 20:", ", ".join(rows[i]["name"] + ("*" if y[i] else "")
                                       for i in top[:20]))

    moved = lambda r: any(a in ("move", "cut") and ok for a, ok in decided.get(r["name"], ()))  # noqa: E731
    cut = lambda r: any(a == "cut" and ok for a, ok in decided.get(r["name"], ()))  # noqa: E731
    clean = [r for r in own if r["misfit"] and (moved(r) or r["name"] not in decided)]
    print(f"core before the 2026-10-22 pass: {len(own)} names (* marks a positive)")
    report("misfit ranks the nodes the pass moved or cut", clean, "misfit", moved)
    multi = [r for r in own if r["_n"] >= 2 and (cut(r) or r["name"] not in decided)]
    for r in multi:
        r["_far"] = -r["_lowest"]
    report("lowest parent similarity, among names with several parents, ranks those that "
           "lost one", multi, "_far", cut)
    glossed = [r for r in own if r["trap"]]
    report("trap ranks the name traps of 2026-10-16", glossed, "trap", lambda r: r["name"] in traps)


def sheet_path(pack):
    return ROOT / ("build/sense-audit.tsv" if pack == "core" else f"packs/{pack}/build/sense-audit.tsv")


def read_sheet(pack):
    lines = sheet_path(pack).read_text(encoding="utf-8").splitlines()
    head = [l for l in lines if l.startswith("#")]
    rows = list(csv.DictReader((l for l in lines if not l.startswith("#")), delimiter="\t"))
    return head, rows


def text_of(row):
    """What the encoder reads for a name: the name, and its gloss."""
    name = row["name"].replace("-", " ").replace(".", " ")
    return f"{name}: {row['gloss']}" if row.get("gloss") else name


def percentile(values):
    """Each value's rank among the others, 0 (least) to 1 (most)."""
    order = np.argsort(np.argsort(values, kind="stable"), kind="stable")
    return order / max(len(values) - 1, 1)


def siblings_distance(own, vectors):
    """1 - similarity to the centroid of the other children of the node's
    parents (None with fewer than two such siblings)."""
    children = {}
    for i, r in enumerate(own):
        for p in r["parents"].split():
            children.setdefault(p, []).append(i)
    out = []
    for i, r in enumerate(own):
        mates = sorted({j for p in r["parents"].split() for j in children.get(p, []) if j != i})
        if len(mates) < 2:
            out.append(None)
            continue
        c = vectors[mates].mean(axis=0)
        out.append(1 - float(vectors[i] @ (c / np.linalg.norm(c))))
    return out


def misfit_scores(own, vectors):
    """misfit: the lowest parent similarity (low is suspect) and the distance
    from the siblings (high is suspect), rank-averaged, as a percentile."""
    sib = siblings_distance(own, vectors)
    idx = [i for i, r in enumerate(own) if r["_lowest"] is not None]
    for r in own:
        r["misfit"] = ""
    if len(idx) < 2:
        return
    a = percentile([-own[i]["_lowest"] for i in idx])
    b = percentile([sib[i] if sib[i] is not None else 0.0 for i in idx])
    for k, s in zip(idx, percentile((a + b) / 2)):
        own[k]["misfit"] = f"{s:.2f}"


def trap_scores(own, model):
    """trap: the vectors' lead for another first sense, WordNet's rank of
    the held sense, and the name's distance from its gloss, rank-averaged,
    as a percentile. Only names with a gloss."""
    idx = [i for i, r in enumerate(own) if r.get("gloss")]
    for r in own:
        r["trap"] = ""
    if len(idx) < 2:
        return
    names = encode(model, [own[i]["name"].replace("-", " ").replace(".", " ") for i in idx])
    glosses = encode(model, [own[i]["gloss"] for i in idx])
    far = -(names * glosses).sum(axis=1)
    lead = [own[i]["_lead"] for i in idx]
    rank = [int(own[i]["rank"]) if own[i]["rank"].isdigit() else 0 for i in idx]
    mix = (percentile(far) + percentile(lead) + percentile(rank)) / 3
    for k, s in zip(idx, percentile(mix)):
        own[k]["trap"] = f"{s:.2f}"


def witness(pack, index, data, space, model, core_rows=None):
    from wordfreq import zipf_frequency
    head, rows = read_sheet(pack)
    own = [r for r in rows if r["parents"] or pack == "core"]   # not a pack's stubs
    pool = own + ([r for r in core_rows if r["name"] not in {o["name"] for o in own}]
                  if core_rows else [])
    vectors = encode(model, [text_of(r) for r in pool])
    at = {r["name"]: i for i, r in enumerate(pool)}
    by_synset = {}
    for r in pool:
        if r["wn30"]:
            by_synset.setdefault(r["wn30"], []).append(r["name"])
    lemmas = [r["name"].replace("-", "_") for r in own]
    ranked = first_senses(lemmas, index, data, space)
    sims = vectors[: len(own)] @ vectors.T                           # own names against the pool
    for i, r in enumerate(own):
        sims[i, i] = -1
    for i, r in enumerate(own):
        r["zipf"] = f"{zipf_frequency(r['name'].replace('-', ' '), 'en'):.2f}"
        r["first"] = r["first_by"] = ""
        order = ranked.get(r["name"].replace("-", "_"))
        if order and r["wn30"] and order[0][0] != r["wn30"]:
            held = dict(order).get(r["wn30"])
            if held is not None:
                best = order[0][0]
                lemma = data[best]["words"][0]
                r["first"] = f"{best} {lemma}: {data[best]['gloss'][:90]}"
                r["first_by"] = f"{order[0][1] - held:.3f}"
        same = [n for n in by_synset.get(r["wn30"], []) if n != r["name"]] if r["wn30"] else []
        j = int(np.argmax(sims[i]))
        if same:
            r["twin"], r["twin_sim"] = "=" + same[0], "1.00"
        elif sims[i, j] >= TWIN:
            r["twin"], r["twin_sim"] = pool[j]["name"], f"{sims[i, j]:.2f}"
        else:
            r["twin"] = r["twin_sim"] = ""
        scored = sorted((float(vectors[i] @ vectors[at[p]]), p)
                        for p in r["parents"].split() if p in at)  # a term or a prelude name has no row
        r["parents_sim"] = " ".join(f"{p}:{s:.2f}" for s, p in scored)
        r["_lowest"] = scored[0][0] if scored else None
        r["_lead"] = 0.0
        if order and r["wn30"] in dict(order):
            r["_lead"] = order[0][1] - dict(order)[r["wn30"]]
    misfit_scores(own, vectors[: len(own)])
    trap_scores(own, model)
    for r in rows:
        for c in COLUMNS:
            r.setdefault(c, "")
    fields = [c for c in rows[0] if c not in COLUMNS and not c.startswith("_")] + COLUMNS
    with open(sheet_path(pack), "w", newline="", encoding="utf-8") as f:
        f.write("\n".join(head) + "\n")
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n",
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{sheet_path(pack).relative_to(ROOT)}: {len(own)} names, "
          f"{sum(1 for r in own if r['first'])} with another first sense "
          f"({sum(1 for r in own if r['first'] and float(r['first_by']) >= SURE)} sure), "
          f"{sum(1 for r in own if r['twin'])} with a twin", file=sys.stderr)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pack", default="core")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--evaluate", action="store_true")
    ap.add_argument("--learn", action="store_true")
    args = ap.parse_args()
    if args.evaluate:
        evaluate()
        return
    if args.learn:
        learn()
        return
    index, data, _, _ = wordnet()
    space, model = Space(), encoder()
    packs = [args.pack]
    if args.all:
        packs = ["core"] + sorted(p.parent.parent.name
                                  for p in (ROOT / "packs").glob("*/build/sense-audit.tsv"))
    core_rows = None
    for pack in packs:
        if pack != "core" and core_rows is None:
            core_rows = read_sheet("core")[1]       # a pack's twins and parents may be core's
        rows = witness(pack, index, data, space, model, None if pack == "core" else core_rows)
        if pack == "core":
            core_rows = rows


if __name__ == "__main__":
    main()
