"""Regenerate ontodag's src/ontodag/core_ontology.py from build/core.od.

    python3 tools/regen_ontodag_core.py <ontodag-core commit> [path/to/ontodag]

Keeps the existing module docstring (substituting the commit hash and the
branch list), rewrites CORE from the .od: every node with its parents, roots
with none; the prelude's kind nodes appear as subjects (their edges to
`attribute` are the pack's) and never as roots.
"""
import re, shlex, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
commit = sys.argv[1]
ontodag = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / "ontodag"
target = ontodag / "src/ontodag/core_ontology.py"
sys.path.insert(0, str(ontodag / "src"))
from ontodag.packs import pack_entries               # noqa: E402
prelude = {n: set(p) for n, p in pack_entries("prelude")}
par = {}
for l in open(HERE / "build/core.od"):
    if l.startswith("#") or not l.strip():
        continue
    f = shlex.split(l)
    # core.od is written canonical, so it holds the relation terms' nodes and
    # the prelude's declarations too; CORE holds core's own claims only
    if "(" in f[0]:
        continue
    parents = [x for x in f[1:] if x != "*" and x not in prelude.get(f[0], ())]
    if f[0] in prelude and not parents:
        continue
    par[f[0]] = tuple(sorted(parents))
roots = sorted(n for n, p in par.items() if not p)
src = target.read_text()
head = src[: src.index("CORE = (")]
head = re.sub(r"commit [0-9a-f]{7,}\)", f"commit {commit})", head)
count = ["zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve","thirteen","fourteen"][len(roots)].capitalize() if len(roots) < 15 else str(len(roots))
head = re.sub(r"\*\*\w+ branches\*\*: .*", f"**{count} branches**: " + ", ".join(f"`{r}`" for r in roots) + ".", head)
body = "CORE = (\n" + "".join(f"    ({n!r}, {par[n]!r}),\n" for n in sorted(par)) + ")\n"
target.write_text(head + body)
print(len(par), "entries;", len(roots), "roots:", " ".join(roots))
