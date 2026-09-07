"""UN Central Product Classification, Ver. 2.1 (CPC_Ver_2_1_english_structure.txt) -> Graph.

The UN's classification of *products* — goods in sections 0-4, services in
sections 5-9 — a strict tree by code prefix (5 digits: section / division /
group / class / subclass).  It is the WITNESS for the services layer of core
(2026-09-07), the way the Google Product Taxonomy is for goods: it says which
kinds of work a market trades and where they sit; WordNet defines them; it is
never imported.  Its titles are phrases ("Hairdressing and barbers' services"),
so it is aligned by hand (align/services.tsv, align/overrides.tsv) and never by
label.

Goods (2026-09-07, UPPER.md §12): tools/align_cpc.py reads the kind names out
of the goods titles.  A code with children whose title names several kinds
("Fruits and nuts", "Sheep and goats, live") is a union bin: as the Google
Product Taxonomy extractor does, each kind gets its own leaf beside the bin
(`013a` fruit, `013b` nut, under the bin's parent), so the bin's children are
never made subclasses of one half of it, and the kind still inherits what the
parent witnesses (sheep ⊑ animal through 021 "Live animals").

Two synthetic nodes make the sections' meaning explicit: `cpc-services` above
sections 5-9 — less division 53 "Constructions", the buildings themselves,
which CPC files beside the construction services — and `cpc-goods` above the
rest; `cpc-root` above both.  Aligning `service` to `cpc-services` is what lets
CPC witness `X ⊑ service` for every service it lists.
"""
import csv
import sys
from pathlib import Path
from graph import Graph

SRC = Path(__file__).resolve().parent.parent / "sources/cpc/CPC_Ver_2_1_english_structure.txt"
ROOT, SERVICES, GOODS = "cpc-root", "cpc-services", "cpc-goods"


def extract(path=SRC):
    nodes = {ROOT: ("cpc root", []), SERVICES: ("services (cpc sections 5-9)", [ROOT]),
             GOODS: ("goods (cpc sections 0-4 and division 53)", [ROOT])}
    rows = list(csv.reader(open(path, encoding="latin-1")))[1:]          # header: CPC21code, CPC21title
    for code, title in rows:
        code = code.strip()
        if len(code) == 1:
            parent = SERVICES if code in "56789" else GOODS
        elif code == "53":
            parent = GOODS
        else:
            parent = code[:-1]
        nodes[code] = (title.strip().lower(), [parent])
    from align_cpc import kinds, is_union                       # union bins in the goods sections: one leaf per kind, beside the bin
    has_children = {p for _, (_, ps) in nodes.items() for p in ps}
    for code, (title, ps) in list(nodes.items()):
        if code in has_children and code[0].isdigit() and (code[0] in "01234" or code.startswith("53")):
            ks = kinds(title)
            if is_union(title, ks):
                for i, k in enumerate(ks):
                    nodes[f"{code}{chr(97 + i)}"] = (f"{k} (from {code})", ps)
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    g = extract()
    g.save(sys.argv[1])
    print(len(g.nodes), "nodes;", g.descendants(SERVICES), "under", SERVICES, ";", g.descendants(GOODS), "under", GOODS)
