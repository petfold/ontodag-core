"""ontodag's shipped `core` pack -> Graph, so it can be compared like the rest.
Root is a synthetic `*`; the pack's top-level branches hang from it."""
import sys
from graph import Graph
from ontodag.packs import pack_entries

ROOT = "*"


def extract():
    nodes = {ROOT: ("*", [])}
    for name, parents in pack_entries("core"):
        nodes[name] = (name, list(parents) or [ROOT])
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    g = extract()
    g.save(sys.argv[1])
    print(len(g.nodes) - 1, "categories")
