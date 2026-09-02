"""WordNet 3.0 noun hypernym DAG (data.noun) -> Graph.  Ids are synset offsets,
labels the first lemma.  `@` hypernyms only; `@i` instance links are dropped
(instances are not categories)."""
import sys
from pathlib import Path
from graph import Graph

SRC = Path(__file__).resolve().parent.parent / "sources/wordnet/dict/data.noun"
ROOT = "00001740"   # entity


def extract(path=SRC):
    nodes = {}
    for line in open(path, encoding="latin-1"):
        if line.startswith("  "):
            continue
        head, _, gloss = line.partition("|")
        f = head.split()
        sid, nw = f[0], int(f[3], 16)
        lemmas = [f[4 + 2 * i] for i in range(nw)]
        i = 4 + 2 * nw
        npts = int(f[i]); i += 1
        parents = []
        for _ in range(npts):
            sym, tgt, pos, _ = f[i:i + 4]; i += 4
            if sym == "@" and pos == "n":
                parents.append(tgt)
        nodes[sid] = (lemmas[0], parents)
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    g = extract()
    g.save(sys.argv[1])
    print(len(g.nodes), "synsets;", sum(1 for s in g.nodes if len(g.parents(s)) > 1), "with 2+ hypernyms")
