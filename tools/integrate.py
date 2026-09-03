"""Integration build: core plus every pack, merged into one store, checked.

    python3 tools/integrate.py [--ontodag PATH]

Each pack is built against core alone; this is the first time they meet.
What is checked: every merge is accepted (a cycle or a refused edge would
raise), every pack concept reaches the root in the union, the cross-pack
edges resolve (a geography format under computing's file-format), the union
root is the same whatever order the packs are merged in (I7 in practice),
and the roots under both addressings are printed so they can be pinned."""
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ontodag_path = HERE.parent / "ontodag"
if "--ontodag" in sys.argv:
    ontodag_path = Path(sys.argv[sys.argv.index("--ontodag") + 1])
sys.path.insert(0, str(ontodag_path / "src"))

import ontodag                                   # noqa: E402
from ontodag.__main__ import _load_native        # noqa: E402
from ontodag.packs import apply                  # noqa: E402
from recordstore import MemoryBytesStore, RecordStore, DirBytesStore  # noqa: E402
import tempfile                                  # noqa: E402

PACKS = ["physics", "mathematics", "chemistry", "biology", "medicine", "ai",
         "economics", "computing", "geography", "space"]


def load(name):
    return _load_native(str(HERE / "packs" / name / "build" / f"{name}.od"))


def build(order, blobs=None):
    dag = ontodag.EagerOntoDAG(RecordStore(blobs if blobs is not None else MemoryBytesStore()))
    apply(dag, "core")
    for name in order:
        dag.merge(load(name))
    return dag


def main():
    t = time.time()
    packs = {n: load(n) for n in PACKS}
    origin_of = {}
    dag = build(PACKS)
    root = dag.commit()
    print(f"union: {len(dag.nodes) - 1} categories, "
          f"{sum(len(n.neighbors) for n in dag.nodes.values())} edges, "
          f"built in {time.time() - t:.1f}s; sha256 root {root}")

    # every pack concept is present and reaches the root (merge keeps only what it can attach)
    root_node = dag.nodes["*"]
    reach = {x.name for x in dag.get_descendants(root_node)}
    for name, p in packs.items():
        missing = [x for x in p.nodes if x != "*" and x not in dag.nodes]
        stranded = [x for x in p.nodes if x != "*" and x in dag.nodes and x not in reach]
        print(f"  {name:12} {len(p.nodes) - 1:5} concepts; missing {len(missing)}, stranded {len(stranded)}",
              (missing + stranded)[:5] if missing or stranded else "")

    # cross-pack edges: the claims one pack makes about another's names
    checks = [("shapefile", "file-format"), ("geojson", "geographic-data-format"), ("merkle-dag", "directed-acyclic-graph"),
              ("swarm-storage", "decentralized-storage"), ("celestial-coordinate-system", "coordinate-system"),
              ("mount-everest", "landform"), ("hurricane", "natural-event"), ("python-language", "language"),
              ("bitcoin", "cryptocurrency"), ("ethereum", "blockchain"), ("quicksort", "algorithm"), ("pulsar", "celestial-body"),
              ("wgs-84", "geodetic-datum"), ("global-positioning-system", "navigational-system"), ("geohash", "geocode"),
              ("elliptic-curve-cryptography", "cryptography"), ("hash-table", "data-structure"), ("dijkstra-algorithm", "algorithm")]
    for sub, sup in checks:
        if sub not in dag.nodes or sup not in dag.nodes:
            print(f"  ? {sub} ⊑ {sup}: absent ({'sub' if sub not in dag.nodes else 'sup'})")
        else:
            print(f"  {'✓' if dag.is_below(sub, sup) else '✗'} {sub} ⊑ {sup}")

    # top-level categories in the union that are not core's roots: borrowed names
    # nobody filed, or a pack's own hinge that reaches nothing above
    core_roots = {x.name for x in root_node.neighbors if all(o == "core" for o in [origin_of.get(x.name, "core")])}
    tops = sorted(x.name for x in root_node.neighbors)
    print(f"  top level: {len(tops)} categories: {' '.join(tops)}")

    # every pack alone onto core merges cleanly
    for name in PACKS:
        d = ontodag.EagerOntoDAG(RecordStore(MemoryBytesStore()))
        apply(d, "core"); d.merge(packs[name])
        alone = sorted(x.name for x in d.nodes["*"].neighbors)
        extra = [t for t in alone if t not in tops]
        print(f"  {name:12} alone: {len(d.nodes) - 1} categories, top level adds {extra}")

    # one name in several packs with different parents: a sense worth a look
    shared = {}
    for name, p in packs.items():
        for x, node in p.nodes.items():
            if x == "*": continue
            shared.setdefault(x, {})[name] = tuple(sorted(n.name for n in node.parents))
    diffs = {x: v for x, v in shared.items() if len(v) > 1 and len(set(v.values())) > 1}
    print(f"  names in several packs with different parents: {len(diffs)}")
    for x, v in sorted(diffs.items())[:60]:
        print(f"    {x}: " + "; ".join(f"{k}:{'/'.join(par) or '*'}" for k, par in v.items()))

    # order independence
    for seed in (1, 2, 3):
        order = PACKS[:]
        random.Random(seed).shuffle(order)
        r = build(order).commit()
        print(f"  order {seed}: {'same root' if r == root else 'DIFFERENT ROOT ' + r}")
    r = build(list(reversed(PACKS))).commit()
    print(f"  reversed: {'same root' if r == root else 'DIFFERENT ROOT ' + r}")

    # idempotence: merging everything again changes nothing
    for name in PACKS:
        dag.merge(packs[name])
    print(f"  re-merge: {'same root' if dag.commit() == root else 'DIFFERENT ROOT'}")

    # Swarm (BMT) addressing
    with tempfile.TemporaryDirectory() as d:
        try:
            sroot = build(PACKS, DirBytesStore(d, addressing="swarm")).commit()
            print(f"  swarm root {sroot}")
        except Exception as exc:
            print(f"  swarm addressing unavailable: {exc}")

    # a few timings on the union
    t = time.time(); n = len(dag.get(["landform"])); print(f"  get landform: {n} in {1000*(time.time()-t):.0f} ms")
    t = time.time(); n = len(dag.get(["software", "free-software"])); print(f"  get software free-software: {n} in {1000*(time.time()-t):.0f} ms")
    t = time.time(); n = len(dag.get([])); print(f"  get (everything): {n} in {1000*(time.time()-t):.0f} ms")


if __name__ == "__main__":
    main()
