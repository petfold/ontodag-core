"""Regenerate ontodag's shipped domain packs from packs/<name>/build/<name>.od.

    python3 tools/regen_ontodag_packs.py <ontodag-core commit> [path/to/ontodag] [pack ...]

Writes src/ontodag/domain/<name>.py for every domain pack (default: all ten):
PACK = the pack's own claims as (name, parents); BORROWED = the names it hangs
things from that belong to a SIBLING pack (written as parentless entries so
the pack adopts alone, at top level until the sibling arrives — UPPER.md
§8.1); core's and the prelude's names are parents, and entries only where the
pack refines them with a parent of its own; `pack NAME` applies core first.
"""
import shlex
import re
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
from ontodag.packs import pack_entries            # noqa: E402

core_names = {n for n, _ in CORE} | {n for n, _ in DECLARATIONS}
(ontodag / "src/ontodag/domain").mkdir(exist_ok=True)


PRELUDE = {n: set(p) for n, p in pack_entries("prelude")}


def read_od(path):
    """A pack's own lines: the .od is written canonical, so it also holds the
    relation terms' nodes and the prelude's declarations, which are not the
    pack's claims. A name at top level is a borrowed stub, unless it carries
    its gloss here (step7 glosses a name on its owner only): then it is the
    pack's own top-level name, read as ('*',) and written parentless, as
    core writes its branches (not in BORROWED, so ontodag knows it is owned)."""
    par, glossed = {}, set()
    for l in open(path):
        if l.startswith("#:meta "):
            glossed.add(shlex.split(l)[1])
        if l.startswith("#") or not l.strip():
            continue
        f = shlex.split(l)
        if "(" in f[0]:
            continue
        parents = [x for x in f[1:] if x != "*" and x not in PRELUDE.get(f[0], ())]
        if f[0] in PRELUDE and not parents:
            continue
        if not parents and f[1:] == ["*"] and f[0] in glossed and f[0] not in core_names:
            parents = ["*"]
        par[f[0]] = tuple(sorted(parents))
    return par


ALL = {n: read_od(HERE / "packs" / n / "build" / f"{n}.od") for n in PACKS}


def uses(name, borrowed):
    """The sibling packs whose own entries the borrowed names are: a soft
    dependency, which `odag pack` offers (ontodag packs.uses)."""
    return tuple(sorted({q for b in borrowed for q, par in ALL.items()
                         if q != name and par.get(b)}))


for name in PACKS:
    par = read_od(HERE / "packs" / name / "build" / f"{name}.od")
    own = {n: p for n, p in par.items() if p and n not in core_names}
    # A pack's entry for a core name refines it: an extra parent from the pack
    # (step7's refine rows). Merged into a store with core, core's own edge
    # becomes implied and reduction drops it.
    own.update({n: p for n, p in par.items() if p and n in core_names
                and n not in {d for d, _ in DECLARATIONS}})
    borrowed = sorted(n for n, p in par.items() if not p and n not in core_names)
    mentioned = {x[x.index("(") + 1:-1] if "(" in x else x      # about(x), in(x): the argument
                 for p in own.values() for x in p}
    borrowed = [n for n in borrowed if n in mentioned]      # a borrowed name nothing hangs from is noise
    target = ontodag / "src/ontodag/domain" / f"{name}.py"
    # VERSION is a hand-bumped fact about the pack's history, not derivable from the
    # .od: keep whatever the existing module says (1 for a new pack); bump it by hand
    # when the pack's claims change, since a rename or retraction never propagates by merge.
    m = re.search(r"^VERSION = (\d+)$", target.read_text(), re.M) if target.exists() else None
    version = int(m.group(1)) if m else 1
    doc = f'''"""The `{name}` pack, version {version}: {len(own)} categories, adopted by merge.

GENERATED — do not edit by hand. Built by consensus in the sister repo
github.com/petfold/ontodag-core (packs/{name}, commit {commit}) from WordNet 3.0
and Wikidata with hand rulings; every name is a plain word that no everyday
sense already owns (a pack never takes an everyday word). It presumes `core`,
which `pack {name}` applies first; core's names appear below as parents, and as
entries only where the pack refines them (adds a parent from the pack).
`BORROWED` are names that belong to a sibling pack — entered parentless so
this pack adopts on its own, filed the moment the sibling is adopted
(refinement by merge); `USES` names those siblings, a soft dependency.
ontodag-core's docs/UPPER.md §8 is the record.
"""

VERSION = {version}

BORROWED = {tuple(borrowed)!r}

# The sibling packs the borrowed names belong to: offered by `odag pack`,
# never adopted for you (core, by contrast, always comes along).
USES = {uses(name, borrowed)!r}

# (name, parents) — sorted by name.
PACK = (
'''
    body = "".join(f"    ({n!r}, {() if own[n] == ('*',) else own[n]!r}),\n" for n in sorted(own))
    body += "".join(f"    ({n!r}, ()),\n" for n in borrowed)
    target.write_text(doc + body + ")\n")
    print(f"{name:12} {len(own):5} categories, {len(borrowed)} borrowed: {' '.join(borrowed)}")
init = ontodag / "src/ontodag/domain/__init__.py"
if not init.exists():
    init.write_text('"""The shipped domain packs (generated in ontodag-core; see each module)."""\n')
