"""Google Product Taxonomy -> the everyday goods layer of core (2026-09-03).

GPT is a coverage source: its kinds say which everyday artifacts, foods and
supplies a marketplace needs names for.  WordNet defines them.  This tool
aligns every GPT kind label (singular, from tools/extract_gpt.py) to a WordNet
noun synset — unique lemma, else the senses under the department's hinge
(artifact / food / organism / substance), else the sense under the GPT
parent's own synset — and writes:

  align/gpt-synsets.tsv   offset  name  note      the chosen synsets and the
                          hypernyms needed to reach core; read by align.py like
                          names.tsv, so these synsets enter core's candidates
  build/gpt-ambiguous.tsv label  senses...        kinds with several admissible
                          senses, for a human/Claude pick (append the pick to
                          align/gpt-picks.tsv: label  offset)
  build/gpt-unmatched.tsv label  path             kinds WordNet has no noun for
                          (retail compounds: "guitar stand", "X accessories")

Names: the GPT label when it is one of the synset's lemmas (what shoppers say),
else WordNet's first lemma; a name already taken in core gets a `.gpt` marker
here and is hand-named before the build (the no-qualified-names rule).
"""
import collections
import csv
import pickle
import sys
from pathlib import Path
from graph import Graph, normalise

ROOT = Path(__file__).resolve().parent.parent
ART, ORG, SUBST, PERSON = "00021939", "00004475", "00019613", "00007846"
FOOD = {"00021265", "07555863", "07566340", "07881800"}       # nutrient, solid food, foodstuff, beverage
DEPT = {"food, beverages & tobacco": FOOD | {ART, SUBST}, "animals & pet supplies": {ART, ORG} | FOOD,
        "health & beauty": {ART, SUBST}, "hardware": {ART, SUBST}, "home & garden": {ART, ORG, SUBST},
        "media": {ART, "06254669"}, "software": {"06566077", ART}, "business & industrial": {ART, SUBST}}


def main():
    g = Graph.load(ROOT / "cache/gpt.pkl"); nodes = g.nodes
    wn = Graph.load(ROOT / "cache/wordnet.pkl")
    lem, lemmas, gloss = collections.defaultdict(list), {}, {}
    for line in open(ROOT / "sources/wordnet/dict/data.noun", encoding="latin-1"):
        if line.startswith("  "):
            continue
        head, _, gl = line.partition("|"); f = head.split(); sid, nw = f[0], int(f[3], 16)
        lemmas[sid] = [f[4 + 2 * i] for i in range(nw)]; gloss[sid] = gl.strip().split(";")[0][:90]
        for l in lemmas[sid]:
            lem[l.lower()].append(sid)
    picks = {}
    p = ROOT / "align/gpt-picks.tsv"
    if p.exists():
        for row in csv.reader(open(p), delimiter="\t"):
            if row and not row[0].startswith("#") and len(row) >= 2:
                picks[row[0].strip()] = row[1].strip()

    def dept(s):
        while nodes[s][1] and nodes[s][1][0] != "gpt-root":
            s = nodes[s][1][0]
        return nodes[s][0]

    def path(s):
        out = []
        while s != "gpt-root":
            out.append(nodes[s][0]); s = nodes[s][1][0]
        return " > ".join(reversed(out))

    order, stack = [], ["gpt-root"]
    while stack:
        x = stack.pop(); order.append(x); stack.extend(g.children.get(x, []))
    chosen, ambiguous, unmatched = {}, {}, []
    for s in order:
        if s == "gpt-root":
            continue
        l = nodes[s][0]
        if " & " in l:
            continue
        if l in picks:
            if picks[l] != "-":
                chosen[s] = picks[l]
            continue
        h = lem.get(l.replace(" ", "_"), [])
        if not h:
            unmatched.append((l, path(s))); continue
        hinges = DEPT.get(dept(s), {ART})
        cand = [x for x in h if wn.ancestors(x) & hinges and PERSON not in wn.ancestors(x)]
        if len(cand) > 1:
            q, guide = nodes[s][1][0], None
            while q and q != "gpt-root":
                if q in chosen:
                    guide = chosen[q]; break
                q = nodes[q][1][0] if nodes[q][1] else None
            if guide:
                c2 = [x for x in cand if guide in wn.ancestors(x)]
                if c2:
                    cand = c2
        if len(cand) == 1:
            chosen[s] = cand[0]
        elif len(cand) > 1:
            ambiguous[l] = cand
        else:
            unmatched.append((l, path(s) + "   [WordNet has only non-goods senses]"))

    # The baseline is core WITHOUT this layer: concepts.tsv already carries the synsets a previous
    # run of this tool put in, so subtract them (by offset) or the second run finds nothing new.
    prev = set()
    gp = ROOT / "align/gpt-synsets.tsv"
    if gp.exists():
        prev = {r[0] for r in csv.reader(open(gp), delimiter="\t") if r and not r[0].startswith("#")}
    rows_ = [r for r in csv.DictReader(open(ROOT / "align/concepts.tsv"), delimiter="\t") if r.get("wordnet") not in prev]
    core = {r["wordnet"]: r["name"] for r in rows_ if r.get("wordnet")}
    taken = {r["name"] for r in rows_}
    syn = set(chosen.values()) - set(core)
    chain = set()      # no hypernym chain: views.py entails through unaligned synsets, so a new
                       # synset hangs from its nearest aligned WordNet ancestor in core by itself
    label_of = collections.defaultdict(set)
    for s, off in chosen.items():
        label_of[off].add(nodes[s][0])
    rows, collisions = [], 0
    for off in sorted(syn | chain):
        gpt_labels = sorted(label_of.get(off, []))
        name = None
        for l in gpt_labels:
            if l.replace(" ", "_") in [x.lower() for x in lemmas[off]]:
                name = normalise(l); break
        name = name or normalise(lemmas[off][0])
        if name in taken:                       # core owns the word in another sense: try the synset's other lemmas
            alts = [normalise(l) for l in lemmas[off][1:] if normalise(l) not in taken and "." not in normalise(l)]
            if alts:
                name = alts[0]
            else:
                name += ".gpt"; collisions += 1
        taken.add(name)
        rows.append((off, name, ("gpt: " + "; ".join(gpt_labels) if gpt_labels else "hypernym chain to core") + " — " + gloss[off]))
    with open(ROOT / "align/gpt-synsets.tsv", "w") as f:
        f.write("# offset\tname\tnote — GENERATED by tools/align_gpt.py from the Google Product Taxonomy; do not edit (hand names go in names.tsv, sense picks in gpt-picks.tsv)\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    with open(ROOT / "build/gpt-ambiguous.tsv", "w") as f:
        f.write("# label\tsenses (offset: gloss) — pick one into align/gpt-picks.tsv as `label<TAB>offset` (or `-` to skip)\n")
        for l, cand in sorted(ambiguous.items()):
            f.write(l + "\t" + "\t".join(f"{c}: {gloss[c]}" for c in cand) + "\n")
    with open(ROOT / "build/gpt-unmatched.tsv", "w") as f:
        f.write("# label\tGPT path — kinds WordNet has no noun for\n")
        for l, pth in sorted(unmatched):
            f.write(f"{l}\t{pth}\n")
    print(f"GPT kinds aligned {len(chosen)} -> {len(set(chosen.values()))} synsets ({len(syn)} new to core, "
          f"{len(chain)} hypernyms to connect them); {len(ambiguous)} ambiguous; {len(unmatched)} unmatched; "
          f"{collisions} names collide with core (marked .gpt)")


if __name__ == "__main__":
    main()
