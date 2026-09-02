"""ontodag's shipped `core` pack -> Graph, so it can be compared like the rest.
Root is a synthetic `*`; the pack's top-level branches hang from it."""
import sys
from graph import Graph
from ontodag.packs import pack_entries

ROOT = "*"


def extract(od=None):
    """From an .od file when given — the FROZEN core v1 (tops/core.od) is the
    common-sense witness; reading the installed ontodag would make the pack
    its own second witness once v2 shipped there."""
    nodes = {ROOT: ("*", [])}
    if od:
        import shlex
        for l in open(od):
            if not l.startswith("#"):
                f = shlex.split(l)
                nodes[f[0]] = (f[0], [p if p != "*" else ROOT for p in f[1:]])
        return Graph(nodes, ROOT)
    for name, parents in pack_entries("core"):
        nodes[name] = (name, list(parents) or [ROOT])
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    g = extract(sys.argv[2] if len(sys.argv) > 2 else None)
    g.save(sys.argv[1])
    print(len(g.nodes) - 1, "categories")
