"""OpenCyc 4.0 OWL export -> Graph, streaming (the file is 240 MB).  Ids are
Cyc's opaque concept ids, labels the rdfs:label; the root is owl:Thing, which
is what the export's top-level classes actually point at (Cyc's own `thing`
class is present but has no OWL children)."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from graph import Graph

SRC = Path(__file__).resolve().parent.parent / "sources/opencyc/opencyc-latest.owl/owl-export-unversioned.owl"
OWL = "{http://www.w3.org/2002/07/owl#}"
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"
ROOT = "owl#Thing"


def extract(path=SRC):
    nodes = {ROOT: ("Thing", [])}
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag != OWL + "Class":
            continue
        cid = el.get(RDF + "about")
        if cid is not None:
            label, parents = None, []
            for ch in el:
                if ch.tag == RDFS + "label" and label is None:
                    label = (ch.text or "").strip()
                elif ch.tag == RDFS + "subClassOf":
                    r = ch.get(RDF + "resource")
                    if r:
                        parents.append(r.rsplit("/", 1)[-1])
            nodes[cid.rsplit("/", 1)[-1]] = (label, parents)
        el.clear()
    # keep only edges whose target is a class we saw (drops XSD datatypes etc.)
    for s, (lab, ps) in nodes.items():
        nodes[s] = (lab, [p for p in ps if p in nodes])
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    g = extract()
    g.save(sys.argv[1])
    print(len(g.nodes), "classes;", sum(1 for s in g.nodes if len(g.parents(s)) > 1), "with 2+ parents")
