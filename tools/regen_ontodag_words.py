"""Regenerate ontodag's src/ontodag/core_words.py: other words for core's
categories, from WordNet 3.0.

    python3 tools/regen_ontodag_words.py <ontodag-core commit> [path/to/ontodag]

Each core category in align/concepts.tsv carries its WordNet synset; its
words are that synset's other lemmas (`photograph`: photo, exposure,
picture, pic), lowercased, with WordNet's underscores as dashes, the
category's own name left out. They are a finding aid for people typing
(ontodag's docs/plans/BROWSER.md §17): never names, never stored.
"""
import csv
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
commit = sys.argv[1]
ontodag = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / "ontodag"
target = ontodag / "src/ontodag/core_words.py"
DATA = HERE / "sources/wordnet/dict/data.noun"

lemmas = {}
for line in open(DATA, encoding="latin-1"):
    if line.startswith("  "):
        continue
    f = line.split("|")[0].split()
    lemmas[f[0]] = [f[4 + 2 * i] for i in range(int(f[3], 16))]

core = {n for n in (shlex.split(line)[0] for line in open(HERE / "build/core.od")
                    if line.strip() and not line.startswith("#"))
        if "(" not in n}                           # canonical .od: a term's node is ontodag's
words = {}
for row in csv.DictReader(open(HERE / "align/concepts.tsv"), delimiter="\t"):
    name, sid = row["name"], row["wordnet"]
    if name not in core or not sid:
        continue
    found = []
    for lemma in lemmas.get(sid, []):
        w = lemma.lower().replace("_", "-")
        if w != name and w not in found:
            found.append(w)
    if found:
        words[name] = tuple(found)

HEAD = f'''"""Other words for the `core` pack's categories, from WordNet 3.0: a finding aid.

GENERATED — do not edit by hand. Produced in the sister repo
github.com/petfold/ontodag-core (tools/regen_ontodag_words.py, commit {commit}):
each core category's WordNet synset (align/concepts.tsv) and that synset's
other lemmas, so `photograph` has photo, exposure, picture and pic.

These words help a person find a category: typing "photo" can suggest
`photograph`. They are never names. Nothing here enters a store, and a word
is never read as the category it suggests (docs/plans/BROWSER.md §17). The
surface layer's aliases (docs/plans/SURFACE_LAYER.md §12) are a separate,
parked design.

WordNet 3.0 Copyright 2006 by Princeton University. All rights reserved.
Used under the WordNet licence; see NOTICE.
"""

'''
body = "WORDS = (\n" + "".join(f"    ({n!r}, {words[n]!r}),\n" for n in sorted(words)) + ")\n"
target.write_text(HEAD + body)
print(len(words), "categories with other words;", sum(len(w) for w in words.values()), "words")
