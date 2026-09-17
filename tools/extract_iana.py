"""IANA Media Types registry (the ten assignment CSVs) -> Graph.

The registry of internet media types — what RFC 2045 called MIME types and
RFC 6838 renamed.  A media type is a two-part label, `image/png`: a top-level
*type* from a closed list of ten, and a *subtype* registered under it.  The
registry is therefore already a one-level classification of every format that
travels over the wire or sits in a mail part, maintained by IANA and pinned to
an RFC for each entry.

It is the WITNESS for the file-format layer of `packs/computing` (2026-09-17,
UPPER.md §14), the way the Google Product Taxonomy is for goods and the UN CPC
for services: it says which families the formats fall into and it is never
imported.  Only the top level is aligned to concepts — `image` to
`image-file-format`, `audio` to `audio-file-format` and so on
(packs/computing/align/iana-picks.tsv) — so what it entails about a format we
have is exactly `X ⊑ <family>-file-format`, which is what the pack had been
asserting by hand.  The individual subtype is carried on the concept as the
witness's id, the way a CPC code is carried on a good; it never becomes a
concept of its own, because `image/png` is the NAME of png's type, not a kind
of thing above png.

Three top-level types are deliberately left unaligned by the picks:
`application` is the residual bin ("everything not one of the others", 1,800
of the 2,347 entries, three quarters of them vendor trees), `example` is the
reserved fake type of RFC 4735, and `multipart` classifies message structure
rather than any file.  `model` and the rest are aligned only if a pick names
a concept for them.

Structure: `media-type` root -> `discrete-media-type` / `composite-media-type`
(RFC 2046's split; message and multipart are the composites) -> the ten types
-> one node per registered subtype, id and label both the full `type/subtype`.
Labels are never matched against our names — a registry subtype is a token
(`text/calendar`, `model/step`, `application/index`) that collides with
unrelated everyday words — so alignment is by the generated pick table only,
as CPC's is.
"""
import csv
import sys
from pathlib import Path
from graph import Graph

SRC = Path(__file__).resolve().parent.parent / "sources/iana"
ROOT, DISCRETE, COMPOSITE = "media-type", "discrete-media-type", "composite-media-type"
# RFC 2046 §1: discrete types carry a single body, composite types enclose others.
# `font` (RFC 8081), `model` (RFC 2077) and `example` (RFC 4735) came later; all discrete.
TYPES = {"application": DISCRETE, "audio": DISCRETE, "example": DISCRETE, "font": DISCRETE,
         "image": DISCRETE, "message": COMPOSITE, "model": DISCRETE, "multipart": COMPOSITE,
         "text": DISCRETE, "video": DISCRETE}
DEAD = ("DEPRECAT", "OBSOLET", "RETIRED", "(OBSOLETE)")


def extract(src=SRC):
    nodes = {ROOT: ("media type", []),
             DISCRETE: ("discrete media type", [ROOT]),
             COMPOSITE: ("composite media type", [ROOT])}
    for t, kind in TYPES.items():
        nodes[t] = (t, [kind])
    n_dead = 0
    for t in TYPES:
        path = src / f"{t}.csv"
        if not path.exists():
            print(f"missing {path}", file=sys.stderr)
            continue
        for r in csv.DictReader(open(path, encoding="utf-8")):
            name, tmpl = (r.get("Name") or "").strip(), (r.get("Template") or "").strip()
            if not tmpl or "/" not in tmpl:
                continue                            # a row with no template is a placeholder, not a type
            dead = any(m in name.upper() for m in DEAD)
            n_dead += dead
            # the template is authoritative: the Name column carries prose
            # ("font-sfnt - DEPRECATED in favor of font/sfnt")
            nodes[tmpl] = (tmpl + (" [deprecated]" if dead else ""), [tmpl.split("/", 1)[0]])
    return Graph(nodes, ROOT), n_dead


if __name__ == "__main__":
    g, dead = extract()
    g.save(sys.argv[1])
    print(f"{len(g.nodes)} nodes: {len(TYPES)} top-level types, "
          f"{len(g.nodes) - len(TYPES) - 3} registered subtypes ({dead} deprecated or obsolete); "
          + ", ".join(f"{t} {g.descendants(t)}" for t in sorted(TYPES)))
