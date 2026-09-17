"""The IANA Media Types registry -> the file-format layer's witness and its
coverage check (2026-09-17, UPPER.md §14).

The goods pass (§12) read kind names out of CPC's titles because CPC's labels
are phrases.  The registry's labels are the opposite problem: a subtype is a
bare token — `text/calendar`, `model/step`, `application/index`, `image/example`
— and a quarter of them are ordinary English words that mean something else
(`directory`, `collection`, `report`, `passport`, `news`, `slate`, `sofa`,
`tone`).  Matching those against our whole vocabulary would align the calendar
in someone's head to a file format.  So the match is fenced twice:

  * only a concept the pack ALREADY places under `file-format` may take a
    media type (plus the handful of family concepts named in the picks);
  * the key is the concept's name with a format suffix stripped
    (`zip-file-format` -> zip, `turtle-syntax` -> turtle, `bmp-file-format` ->
    bmp), and a subtype registered under more than one top-level type
    (`mp4`, `ogg`, `xml`, `jpeg`) is never guessed — it needs a pick.

`align/iana-picks.tsv` is the hand table: the six family alignments that make
the registry witness anything at all (`image` -> `image-file-format`), the
formats whose registered name is not their common one (mp3 -> audio/mpeg, svg
-> image/svg+xml, epub -> application/epub+zip), and `-` for the formats IANA
has never registered — 7z, wav, webm, avi, tar, rss, avro, gpx — which is the
coverage check pointing the other way.

Only the top level is ever aligned to a concept, so what the registry entails
about a format is exactly `X ⊑ <family>-file-format`.  Nothing is aligned to
the registry's root: `png ⊑ media-type` would be false, because `image/png` is
the NAME of png's type, not a kind above png.  `application`, `example`,
`multipart` and `model` stay unaligned — the first is the residual bin (1,800
of 2,347 entries, three quarters of them vendor trees), the second is RFC
4735's reserved fake, the third classifies message structure rather than a
file, and the fourth has no concept in the pack yet.

Writes:
  <pack>/align/media-types.tsv   name  media-type  note — GENERATED; read by
                                 align.py into the `iana` column, the way
                                 cpc-goods.tsv is read into `cpc`.
  <pack>/build/iana-unmatched.tsv  registered subtypes with no concept, the
                                 vendor and personal trees folded into a count
  <pack>/build/iana-families.tsv   what the alignment will make the registry
                                 witness, for reading before it is believed
"""
import collections
import csv
import shlex
import sys
from pathlib import Path
from graph import Graph

ROOT = Path(__file__).resolve().parent.parent
PACK = "computing"
SUFFIXES = ("-file-format", "-coding-format", "-format", "-syntax", "-file")
FAMILY_ROOT = "file-format"


def read_od(path):
    par = {}
    for line in open(path):
        if line.startswith("#"):
            continue
        f = shlex.split(line)
        if f:
            par[f[0]] = [x for x in f[1:] if x != "*"]
    return par


def cone(par, root):
    """Every name below `root` in a parents map."""
    kids = collections.defaultdict(set)
    for a, bs in par.items():
        for b in bs:
            kids[b].add(a)
    seen, stack = set(), [root]
    while stack:
        for c in kids[stack.pop()]:
            if c not in seen:
                seen.add(c)
                stack.append(c)
    return seen


def main():
    pack_dir = ROOT / "packs" / PACK
    iana = Graph.load(ROOT / "cache/iana.pkl")
    par = read_od(pack_dir / "build" / f"{PACK}.od")
    formats = cone(par, FAMILY_ROOT)

    picks, refused = {}, {}
    p = pack_dir / "align/iana-picks.tsv"
    for row in csv.reader(open(p), delimiter="\t"):
        if not row or row[0].startswith("#") or len(row) < 2:
            continue
        name, mt = row[0].strip(), row[1].strip()
        (refused if mt == "-" else picks)[name] = (mt, row[2] if len(row) > 2 else "")

    # subtype -> the full types registered under it; a subtype under two top-level
    # types is ambiguous and is never taken automatically
    by_sub = collections.defaultdict(list)
    for node in iana.nodes:
        if "/" in node:
            by_sub[node.split("/", 1)[1].lower()].append(node)

    rows, auto, ambiguous = [], 0, []
    for name in sorted(formats | set(picks)):
        if name in refused:
            continue
        if name in picks:
            mt, note = picks[name]
            if mt not in iana.nodes:
                print(f"pick {name} -> {mt}: not in the registry", file=sys.stderr)
                continue
            rows.append((name, mt, note or f"pick — {iana.label(mt)}"))
            continue
        keys = [name] + [name[: -len(s)] for s in SUFFIXES if name.endswith(s) and len(name) > len(s)]
        hit = next((k for k in keys if k.lower() in by_sub), None)
        if not hit:
            continue
        cands = by_sub[hit.lower()]
        if len(cands) > 1:
            ambiguous.append((name, cands))
            continue
        auto += 1
        rows.append((name, cands[0], f"by name — {iana.label(cands[0])}"))

    out = pack_dir / "align/media-types.tsv"
    with open(out, "w") as fh:
        fh.write("# name\tmedia-type\tnote — GENERATED by tools/align_iana.py from the IANA Media Types registry; do not edit "
                 "(hand picks and refusals go in iana-picks.tsv). Read by align.py into the `iana` column: the registry is a "
                 "witness for the format families, never imported. UPPER.md §14.\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")

    taken = {mt for _, mt, _ in rows}
    vendor = collections.Counter()
    unmatched = []
    for node in sorted(iana.nodes):
        if "/" not in node or node in taken:
            continue
        top, sub = node.split("/", 1)
        if sub.startswith(("vnd.", "prs.", "x-")):
            vendor[top] += 1
            continue
        unmatched.append((top, node, iana.label(node)))
    with open(pack_dir / "build/iana-unmatched.tsv", "w") as fh:
        fh.write("# top-level\tmedia-type\tlabel — registered subtypes no concept in the pack claims: the coverage check. "
                 "Vendor (vnd.), personal (prs.) and unregistered (x-) trees are counted in the footer, not listed.\n")
        for t, node, label in unmatched:
            fh.write(f"{t}\t{node}\t{label}\n")
        fh.write("# vendor/personal/x- subtypes left out: "
                 + ", ".join(f"{t} {n}" for t, n in sorted(vendor.items())) + f"; total {sum(vendor.values())}\n")

    fam = {mt: name for name, mt, _ in rows if "/" not in mt}
    with open(pack_dir / "build/iana-families.tsv", "w") as fh:
        fh.write("# media-type\tconcept\tfamily\twhat the registry will witness (concept ⊑ family) — read this before believing it\n")
        for name, mt, _ in sorted(rows):
            if "/" in mt:
                f = fam.get(mt.split("/", 1)[0])
                fh.write(f"{mt}\t{name}\t{f or '-'}\t" + (f"{name} ⊑ {f}" if f else "top level unaligned: witnesses nothing") + "\n")
    with open(pack_dir / "build/iana-ambiguous.tsv", "w") as fh:
        fh.write("# name\tcandidates — the subtype is registered under several top-level types; pick one into iana-picks.tsv\n")
        for name, cands in ambiguous:
            fh.write(name + "\t" + " ".join(cands) + "\n")

    witnessed = sum(1 for _, mt, _ in rows if "/" in mt and mt.split("/", 1)[0] in fam)
    print(f"IANA: {len(formats)} concepts under {FAMILY_ROOT}; {len(rows)} aligned "
          f"({auto} by name, {len(picks)} by pick, {len(refused)} refused as unregistered); "
          f"{len(fam)} of {sum(1 for n in iana.nodes if '/' not in n) - 3} top-level types aligned to a family, "
          f"so {witnessed} formats get a witnessed family edge; "
          f"{len(ambiguous)} ambiguous; {len(unmatched)} registered subtypes unclaimed "
          f"(+{sum(vendor.values())} vendor/personal)")


if __name__ == "__main__":
    main()
