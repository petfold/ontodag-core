"""Any small OWL/RDF file -> Graph via rdflib: BFO, DOLCE-Lite, DUL.
Ids are the class URIs' local names, labels from rdfs:label (English if
tagged) else the local name.  Anonymous superclasses are read one
level deep: A ⊑ (B ⊓ R) entails A ⊑ B, so the named members of an
owl:intersectionOf count as parents; restrictions themselves are axioms,
not categories, and are ignored.

    python3 tools/extract_owl.py sources/bfo/bfo.owl BFO_0000001 cache/bfo.pkl
"""
import sys
import rdflib
from rdflib.namespace import OWL, RDF, RDFS
from graph import Graph


def local(uri):
    s = str(uri)
    return s.rsplit("#", 1)[-1] if "#" in s else s.rsplit("/", 1)[-1]


def extract(path, root):
    g = rdflib.Graph()
    with open(path, "rb") as fh:                       # DUL.owl is Turtle despite its name
        fmt = "turtle" if fh.read(64).lstrip().startswith(b"@prefix") else "xml"
    g.parse(path, format=fmt)
    classes = {c for c in g.subjects(RDF.type, OWL.Class) if isinstance(c, rdflib.URIRef)}
    nodes = {}
    for c in classes:
        label = None
        for lab in g.objects(c, RDFS.label):
            if getattr(lab, "language", None) in (None, "en") or label is None:
                label = str(lab)
        parents = []
        # equivalentClass to an intersection entails subsumption by each
        # member too (DOLCE-Lite's spatio-temporal-particular is defined so).
        supers = list(g.objects(c, RDFS.subClassOf)) + list(g.objects(c, OWL.equivalentClass))
        for p in supers:
            if isinstance(p, rdflib.URIRef) and p in classes:
                parents.append(local(p))
            elif isinstance(p, rdflib.BNode):
                for lst in g.objects(p, OWL.intersectionOf):
                    parents += [local(m) for m in g.items(lst)
                                if isinstance(m, rdflib.URIRef) and m in classes]
        parents = sorted(set(parents))
        nodes[local(c)] = (label or local(c), parents)
    if root not in nodes:
        raise SystemExit(f"root {root!r} not among {len(nodes)} classes; roots are "
                         f"{sorted(n for n, (_, ps) in nodes.items() if not ps)[:20]}")
    return Graph(nodes, root)


if __name__ == "__main__":
    path, root, out = sys.argv[1:4]
    gr = extract(path, root)
    gr.save(out)
    print(len(gr.nodes), "classes;", sum(1 for s in gr.nodes if len(gr.parents(s)) > 1), "with 2+ parents;",
          "roots:", sorted(gr.label(n) for n, (_, ps) in gr.nodes.items() if not ps))
