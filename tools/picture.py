"""Pictures of the pack: DOT files for the top (roots + their biggest
children), the upper levels, and the whole pack, nodes coloured by branch.

    python3 tools/picture.py            # writes docs/img/{top,upper,core}.dot
    dot -Tsvg docs/img/top.dot -o docs/img/top.svg
"""
import shlex
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/img"
BRANCH_COLOURS = {          # fill for nodes wholly inside one branch; mixed ancestry stays neutral
    "physical-object": "#dbe7d3", "event": "#f3dfc8", "agent": "#d9e3ef", "attribute": "#ecdcec",
    "information": "#f6efc5", "place": "#d3e7e3", "substance": "#e9dccd", "cognition": "#e4dff2",
    "possession": "#f2d9d3", "field-of-study": "#dfe9f2",
}
ROOT_FILL = "#cfc6b6"


def load():
    par, ch = {}, defaultdict(list)
    for l in open(ROOT / "build/core.od"):
        if l.startswith("#"):
            continue
        f = shlex.split(l)
        par[f[0]] = [p for p in f[1:] if p != "*"]
        for p in par[f[0]]:
            ch[p].append(f[0])
    return par, ch


def cones(par, ch):
    memo = {}
    def size(n):
        if n in memo:
            return memo[n]
        seen, st = set(), [n]
        while st:
            x = st.pop()
            for c in ch[x]:
                if c not in seen:
                    seen.add(c); st.append(c)
        memo[n] = len(seen)
        return memo[n]
    return size


def branches_of(par, roots):
    """name -> set of roots above it (memoised upward walk)."""
    memo = {}
    def up(n):
        if n in memo:
            return memo[n]
        if not par[n]:
            memo[n] = {n}
            return memo[n]
        s = set()
        for p in par[n]:
            s |= up(p)
        memo[n] = s
        return s
    return up


def dot(par, keep, size, up, roots, *, big_labels=True):
    ids = {n: f'"{n}"' for n in keep}
    lines = ["digraph core {", "  rankdir=TB; ranksep=0.8; nodesep=0.22; splines=true; outputorder=edgesfirst;",
             '  node [shape=box, style="rounded,filled", color="#8a7f70", fontname=Helvetica, fontsize=11];',
             '  edge [color="#a89c8c", arrowsize=0.55];']
    for n in sorted(keep):
        bs = up(n)
        fill = ROOT_FILL if n in roots else (BRANCH_COLOURS[next(iter(bs))] if len(bs) == 1 else "#f2efe9")
        label = f"{n}\\n{size(n)}" if (big_labels or n in roots) and size(n) else n
        extra = ' fontsize=13 penwidth=1.6' if n in roots else ''
        lines.append(f'  {ids[n]} [label="{label}" fillcolor="{fill}"{extra}];')
    lines.append("  { rank=min; " + " ".join(ids[r] for r in roots if r in keep) + " }")
    for n in keep:
        for p in par[n]:
            if p in keep:
                lines.append(f"  {ids[p]} -> {ids[n]};")
    lines.append("}")
    return "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    par, ch = load()
    roots = [n for n, ps in par.items() if not ps]
    size, up = cones(par, ch), branches_of(par, roots)

    def cut(k, depth):
        keep, frontier = set(roots), list(roots)
        for _ in range(depth):
            nxt = []
            for n in frontier:
                for c in sorted(ch[n], key=lambda c: -size(c))[:k]:
                    if c not in keep:
                        keep.add(c); nxt.append(c)
            frontier = nxt
        return keep

    (OUT / "top.dot").write_text(dot(par, cut(3, 1), size, up, roots))
    (OUT / "upper.dot").write_text(dot(par, cut(4, 2), size, up, roots))
    (OUT / "core.dot").write_text(dot(par, set(par), size, up, roots, big_labels=False))
    print("top", len(cut(3, 1)), "upper", len(cut(4, 2)), "core", len(par))


if __name__ == "__main__":
    main()
