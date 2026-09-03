"""Regenerate ontodag's shipped domain packs from packs/<name>/build/<name>.od.

    python3 tools/regen_ontodag_packs.py <ontodag-core commit> [path/to/ontodag] [pack ...]

Writes src/ontodag/domain/<name>.py for every domain pack (default: all ten):
PACK = the pack's own claims as (name, parents); BORROWED = the names it hangs
things from that belong to a SIBLING pack (written as parentless entries so
the pack adopts alone, at top level until the sibling arrives — UPPER.md
§8.1); core's and the prelude's names are parents only, never entries, since
`pack NAME` applies core first.
"""
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
commit = sys.argv[1]
ontodag = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / "ontodag"
PACKS = sys.argv[3:] or ["physics", "mathematics", "chemistry", "biology", "medicine", "ai",
                         "economics", "computing", "geography", "space"]
sys.path.insert(0, str(ontodag / "src"))
from ontodag.core_ontology import CORE            # noqa: E402
from ontodag.prelude import DECLARATIONS          # noqa: E402

core_names = {n for n, _ in CORE} | {n for n, _ in DECLARATIONS}
(ontodag / "src/ontodag/domain").mkdir(exist_ok=True)


def read_od(path):
    par = {}
    for l in open(path):
        if l.startswith("#") or not l.strip():
            continue
        f = shlex.split(l)
        par[f[0]] = tuple(sorted(x for x in f[1:] if x != "*"))
    return par


for name in PACKS:
    par = read_od(HERE / "packs" / name / "build" / f"{name}.od")
    own = {n: p for n, p in par.items() if p and n not in core_names}
    borrowed = sorted(n for n, p in par.items() if not p and n not in core_names)
    mentioned = {x for p in own.values() for x in p}
    borrowed = [n for n in borrowed if n in mentioned]      # a borrowed name nothing hangs from is noise
    doc = f'''"""The `{name}` pack, version 1: {len(own)} categories, adopted by merge.

GENERATED — do not edit by hand. Built by consensus in the sister repo
github.com/petfold/ontodag-core (packs/{name}, commit {commit}) from WordNet 3.0
and Wikidata with hand rulings; every name is a plain word that no everyday
sense already owns (a pack never takes an everyday word). It presumes `core`,
which `pack {name}` applies first; core's names appear below only as parents.
`BORROWED` are names that belong to a sibling pack — entered parentless so
this pack adopts on its own, filed the moment the sibling is adopted
(refinement by merge). ontodag-core's docs/UPPER.md §8 is the record.
"""

VERSION = 1

BORROWED = {tuple(borrowed)!r}

# (name, parents) — sorted by name.
PACK = (
'''
    body = "".join(f"    ({n!r}, {own[n]!r}),\n" for n in sorted(own))
    body += "".join(f"    ({n!r}, ()),\n" for n in borrowed)
    (ontodag / "src/ontodag/domain" / f"{name}.py").write_text(doc + body + ")\n")
    print(f"{name:12} {len(own):5} categories, {len(borrowed)} borrowed: {' '.join(borrowed)}")
init = ontodag / "src/ontodag/domain/__init__.py"
if not init.exists():
    init.write_text('"""The shipped domain packs (generated in ontodag-core; see each module)."""\n')
