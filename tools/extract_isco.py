"""ILO International Standard Classification of Occupations, ISCO-08 (sources/isco/ISCO-08 EN.csv) -> Graph.

The ILO's classification of *jobs*: 10 major groups, 43 sub-major, 130 minor,
436 unit groups, a strict tree by code prefix (1 / 2 / 3 / 4 digits). It is the
WITNESS for the occupations pack (docs/OCCUPATIONS.md, 2026-09-23), the way CPC
is for the services layer (UPPER.md §11): it says which occupations the labour
market recognises and how they group; WordNet defines them; it is never
imported. Its group titles are phrases ("Building and related trades workers,
excluding electricians"), so it is aligned by synset through the ILO's index of
occupational titles (tools/align_isco.py -> packs/occupations/align/occupations.tsv),
never by label.

Node ids are the codes themselves ("7", "71", "712", "7126") under a synthetic
`isco-root`; the armed forces' major group is "0" ("01", "011", "0110").
"""
import csv
import sys
from pathlib import Path
from graph import Graph

SRC = Path(__file__).resolve().parent.parent / "sources/isco/ISCO-08 EN.csv"
ROOT = "isco-root"


def extract(path=SRC):
    nodes = {ROOT: ("isco-08 occupations", [])}
    for r in csv.DictReader(open(path, encoding="latin-1")):
        if r["ISCO_version"] != "ISCO-08":       # the file carries ISCO-88, -68 and -58 too
            continue
        levels = [(r["major"], r["major_label"]), (r["sub_major"], r["sub_major_label"]),
                  (r["minor"], r["minor_label"]), (r["unit"], r["description"])]
        parent = ROOT
        for width, (code, title) in enumerate(levels, 1):
            code = code.strip().zfill(width)     # the armed forces' codes lost their leading 0 ("110" is 0110)
            if code not in nodes:
                nodes[code] = (title.strip().lower(), [parent])
            parent = code
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    g = extract()
    g.save(sys.argv[1])
    by_len = {}
    for code in g.nodes:
        if code != ROOT:
            by_len[len(code)] = by_len.get(len(code), 0) + 1
    print(len(g.nodes), "nodes:", ", ".join(f"{n} of {k} digit(s)" for k, n in sorted(by_len.items())))
