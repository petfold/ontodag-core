"""Regenerate ontodag's src/ontodag/core_words.py: other words for core's
categories, from WordNet 3.0.

    python3 tools/regen_ontodag_words.py <ontodag-core commit> [path/to/ontodag]

Each core category's WordNet synset is the `wn30` beside its gloss in
build/core.od; its words are that synset's other lemmas (`photograph`:
photo, exposure, picture, pic), lowercased, with WordNet's underscores as
dashes, the category's own name left out. They are a finding aid for people typing
(ontodag's docs/plans/BROWSER.md §17): never names, never stored.
"""
import json
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

# core's names as ontodag ships them (tools/regen_ontodag_core.py runs first):
# the canonical .od also holds the prelude's names (pressure) and terms' nodes
sys.path.insert(0, str(ontodag / "src"))
from ontodag.core_ontology import CORE             # noqa: E402
core = {n for n, _ in CORE}
# each name's current sense, as build/core.od records it: align/concepts.tsv
# holds consensus's synsets, which the v14 rulings re-sensed in hundreds of places
senses = {}
for line in open(HERE / "build/core.od"):
    if line.startswith("#:meta "):
        _, name, meta = shlex.split(line)
        senses[name] = json.loads(meta).get("wn30", "")[:-2]
words = {}
for name, sid in sorted(senses.items()):
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
each core category's WordNet synset (its wn30 in build/core.od) and that synset's
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
