"""Print a source's top as a tree, or write it as an importable .od file.

    python3 tools/top.py cache/wordnet.pkl --depth 3 --min 300
    python3 tools/top.py cache/wordnet.pkl --depth 3 --min 300 --od tops/wordnet.od
"""
import argparse
from graph import Graph

ap = argparse.ArgumentParser()
ap.add_argument("pkl")
ap.add_argument("--depth", type=int, default=3)
ap.add_argument("--min", type=int, default=1, help="minimum cone size to include")
ap.add_argument("--od", help="write the cut as an OntoDAG .od file instead of printing")
a = ap.parse_args()

g = Graph.load(a.pkl)
if a.od:
    ids = g.top(a.depth, a.min)
    g.write_od(ids, a.od)
    print(f"{a.od}: {len(ids)} categories (depth <= {a.depth}, cone >= {a.min})")
else:
    g.print_tree(a.depth, a.min)
