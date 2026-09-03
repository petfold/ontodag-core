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
par = {}
for l in open(HERE / "build/core.od"):
    if l.startswith("#") or not l.strip():
        continue
    f = shlex.split(l)
    par[f[0]] = tuple(sorted(x for x in f[1:] if x != "*"))
roots = sorted(n for n, p in par.items() if not p)
src = target.read_text()
head = src[: src.index("CORE = (")]
head = re.sub(r"commit [0-9a-f]{7,}\)", f"commit {commit})", head)
head = re.sub(r"\*\*Ten branches\*\*: .*", "**Ten branches**: " + ", ".join(f"`{r}`" for r in roots) + ".", head)
body = "CORE = (\n" + "".join(f"    ({n!r}, {par[n]!r}),\n" for n in sorted(par)) + ")\n"
target.write_text(head + body)
print(len(par), "entries;", len(roots), "roots:", " ".join(roots))
