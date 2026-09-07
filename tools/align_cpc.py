"""UN CPC 2.1, the goods sections -> the goods layer's second witness and its
coverage check (2026-09-07, UPPER.md §12).

The services pass (§11) aligned CPC by hand: 79 synsets, one code each, in
align/services.tsv.  The goods half is 2,713 codes (sections 0-4 and division
53), too many for a hand list, and its titles are qualified phrases —
"Pumpkins, squash and gourds", "Barley, seed", "Meat of bovine animals, fresh
or chilled", "Other cereals" — so this tool reads the kind names OUT of the
titles and aligns those to WordNet noun synsets the way tools/align_gpt.py
aligns the Google Product Taxonomy's labels:

  * a title is split at ';' and ','; the pieces before the first qualifier
    ("fresh or chilled", "seed", "n.e.c.", "of a kind used ...", anything
    opening with a preposition or a participle) are the kinds, each split
    again at 'and'/'or'; "other X" and "the like" are residual bins, not
    kinds, and are skipped; "X of Y" keeps X ("Meat of pigs" -> meat) unless
    X is a generic word (article, product, part ...);
  * a kind is a WordNet noun lemma (singularised, multiword allowed: "juniper
    berries" -> juniper_berry) with a sense under the section's hinge —
    artifact, organism, substance, natural object, food; never person;
  * several senses: a hand pick (align/cpc-picks.tsv), else the sense under the
    nearest aligned CPC ancestor's synset, else — at a 5-digit subclass only —
    the sense core already has; a group or class stays ambiguous for a human,
    because it is the upper end of every edge CPC will witness through it;
  * a synset named by several codes takes the shortest (the class "Wheat",
    not the subclass "Wheat, seed"), then the title with fewest kinds.

Writes:
  align/cpc-goods.tsv     offset  name  code  note — GENERATED; read by align.py
                          like services.tsv: the code is CPC's witness for the
                          synset.  A synset core already has keeps an empty
                          name (align.py's read_names skips it; read_cpc_map
                          does not), so CPC becomes a second witness for the
                          goods layer's edges; a synset core lacks gets a name
                          and joins core's candidates — the coverage check.
  build/cpc-ambiguous.tsv label  senses...   for a pick into align/cpc-picks.tsv
  build/cpc-unmatched.tsv code  title  kinds WordNet has no noun for
  build/cpc-upper.tsv     every aligned code of at most 4 digits, for reading:
                          these are the superclass ends of CPC's witness edges.
"""
import collections
import csv
import re
import sys
from pathlib import Path
from graph import Graph, normalise
from extract_gpt import singular

ROOT = Path(__file__).resolve().parent.parent
ART, ORG, SUBST, PERSON, NATOBJ = "00021939", "00004475", "00019613", "00007846", "00019128"
MATTER = "00020827"               # WordNet files solid/liquid/gas, fuel, glass, ice under `matter`, beside `substance`
PHENOM, MEDIUM, SOFTWARE, WRITING = "00034213", "06254669", "06566077", "06362953"
FOOD = {"00021265", "07555863", "07566340", "07881800"}       # nutrient, solid food, foodstuff, beverage
BASE = {ART, ORG, SUBST, MATTER, NATOBJ} | FOOD
HINGE = {"1": BASE | {PHENOM}, "53": {ART}}                  # by longest matching code prefix; default BASE
HINGE_EXTRA = {"32": {MEDIUM, WRITING}, "478": {SOFTWARE}}   # printed matter; packaged software

# a piece opening with one of these is a qualifier: it and everything after it are not kinds
QUAL = {"not", "whether", "except", "excluding", "other", "of", "for", "in", "from", "with", "by",
        "containing", "including", "n.e.c.", "n.e.c", "nec", "fresh", "frozen", "chilled", "live", "dried",
        "dry", "raw", "seed", "seeds", "shelled", "cooked", "uncooked", "processed", "prepared", "preserved",
        "salted", "smoked", "roasted", "crude", "refined", "unrefined", "unrendered", "rendered", "worked",
        "unworked", "uncoated", "coated", "knitted", "woven", "new", "used", "greasy", "whole", "husked",
        "unhusked", "milled", "semi-", "semi", "wholly", "otherwise", "but", "and", "or", "the", "similar",
        "inedible", "edible", "unfit", "fit", "primary", "secondary", "natural", "artificial", "synthetic",
        "man-made", "electric", "electrical", "mechanical", "hand-operated", "self-propelled", "assembled",
        "packaged", "printed", "obtained", "resulting", "derived", "sparkling", "still", "hulled", "broken",
        "ground", "unground", "carded", "combed", "bleached", "unbleached", "dyed", "crocheted", "tanned",
        "dressed", "wild", "farmed", "hot", "cold", "liquid", "solid", "powdered", "granulated", "in-shell",
        "roughly", "sawn", "sliced", "peeled", "treated", "untreated", "impregnated", "reinforced", "laminated",
        "veneered", "agglomerated", "vulcanized", "unvulcanized", "hardened", "unhardened", "cut", "polished",
        "unpolished", "shaped", "continuously", "plated", "clad", "coated", "galvanized", "rolled", "cast",
        "forged", "stamped", "drawn", "extruded", "moulded", "molded", "glazed", "unglazed", "fired",
        "unfired", "exposed", "unexposed", "developed", "undeveloped", "recorded", "unrecorded", "mounted",
        "unmounted", "framed", "unframed", "loaded", "unloaded", "ready", "denatured", "undenatured",
        "sweetened", "unsweetened", "flavoured", "concentrated", "unconcentrated", "fermented", "unfermented",
        "pasteurized", "homogenized", "reconstituted", "expanded", "compressed", "liquefied", "gaseous",
        "at", "on", "under", "over", "to", "as", "than", "if", "when", "which", "that", "whose", "each",
        "all", "any", "some", "no", "per", "less", "more", "exceeding", "weighing", "measuring", "having",
        "made", "being", "put", "up", "sold", "suitable", "designed", "specially", "principally", "mainly",
        "solely", "wholly", "partly", "partially", "fully", "completely", "single", "double", "multiple",
        "two", "three", "four", "one", "two-", "three-", "four-", "sterile", "sterilized", "non-sterile",
        "adhesive", "self-adhesive", "gummed", "surface-coloured", "surface-decorated", "impregnated"}
STRIP = ("other ", "live ", "fresh or chilled ", "fresh or dried ", "fresh ", "chilled ", "frozen ", "wild ", "farmed ",
         "edible ", "raw ", "prepared and preserved ", "prepared or preserved ", "processed ", "prepared ", "preserved ",
         "unmanufactured ", "new ", "whole ", "similar ", "certain ", "dried ", "cooked ", "salted ", "smoked ")
GENERIC = {"article", "product", "good", "goods", "item", "material", "equipment", "apparatus", "part",
           "preparation", "residue", "substance", "thing", "type", "kind", "matter", "component", "accessory",
           "thereof", "fraction", "derivative", "mixture", "piece", "quantity", "weight", "content", "use", "form",
           "consumption", "purpose", "sale", "planting", "industry", "manufacture", "extraction", "treatment",
           "other", "like", "n.e.c.", "section", "profile", "unit", "set", "assembly", "system", "machinery"}


def read_wordnet():
    lem, lemmas, gloss, lexfile = collections.defaultdict(list), {}, {}, {}
    for line in open(ROOT / "sources/wordnet/dict/data.noun", encoding="latin-1"):
        if line.startswith("  "):
            continue
        head, _, gl = line.partition("|"); f = head.split(); sid, nw = f[0], int(f[3], 16)
        lemmas[sid] = [f[4 + 2 * i] for i in range(nw)]; gloss[sid] = gl.strip().split(";")[0][:90]
        lexfile[sid] = f[1]
        for l in lemmas[sid]:
            lem[l.lower()].append(sid)
    return lem, lemmas, gloss, lexfile


def kinds(title):
    """The kind names a CPC title names, in order.  See the module docstring."""
    t = title.lower().replace('"', "")
    t = re.sub(r"\([^)]*\)", "", t)
    t = re.sub(r"\bn\.e\.c\.?", "", t)
    t = re.sub(r"\s+", " ", t)
    out = []
    for seg in t.split(";"):
        seg = seg.strip(" ,.")
        if not seg:
            continue
        for i, piece in enumerate(p.strip() for p in seg.split(",")):
            if not piece:
                continue
            first = piece.split()[0]
            if i > 0 and first in QUAL and first != "other":
                break                       # a qualifier after the head: it and the rest describe, not name
            if piece.startswith(("the like", "similar")):
                break
            # a coordination of kinds; a clause after a preposition is trimmed off first ("meat of pigs")
            head = re.split(r" (?:of|for|from|with|by|containing|including|in|on|at|to|used|obtained|derived|"
                            r"whether|except|other than|not|weighing|measuring|having|made|put up|exceeding) ", piece)[0]
            for item in re.split(r" and | or ", head):
                item = item.strip(" -")
                if not item or item.startswith(("other ", "the like", "similar ", "like ")):
                    continue
                if all(w in QUAL for w in item.split()):
                    continue                # "fresh", "chilled": modifiers left over from a split coordination
                out.append(item)
            if head != piece:                # the trimmed clause was the last thing named
                break
    seen, res = set(), []
    for k in out:
        if k not in seen:
            seen.add(k); res.append(k)
    return res


def is_union(title, ks):
    """A code with children whose title names several kinds, or one kind beside a residual
    ("furniture; other transportable goods", "horses and other equines", "margarine and
    similar preparations"), is a union bin: none of its kinds is the class of its children."""
    t = re.sub(r"\([^)]*\)", "", title.lower())
    return len(ks) > 1 or bool(re.search(r";|\bother\b|\bsimilar\b|the like|\bparts\b", t))


def variants(item):
    """Lookup keys for one kind phrase, in order: the phrase, its singular, a bare plural
    strip, then the same with a leading food/agriculture modifier removed."""
    outs = []

    def add(s):
        s = s.strip()
        if not s:
            return
        words = s.split()
        forms = [" ".join(words[:-1] + [singular(words[-1])])]       # the singular first: "clocks" is also a weed
        if words[-1].endswith("s") and not words[-1].endswith("ss"):
            forms.append(" ".join(words[:-1] + [words[-1][:-1]]))
        forms.append(s)
        for cand in forms:
            for key in (cand.replace(" ", "_"), cand.replace(" ", "_").replace("-", "_"), cand.replace(" ", "-")):
                if key not in outs:
                    outs.append(key)
    add(item)
    s = item
    changed = True
    while changed:
        changed = False
        for m in STRIP:
            if s.startswith(m) and len(s) > len(m):
                s = s[len(m):]; changed = True
    if s != item:
        add(s)
    return outs


def main():
    lem, lemmas, gloss, lexfile = read_wordnet()
    wn = Graph.load(ROOT / "cache/wordnet.pkl")
    cpc = Graph.load(ROOT / "cache/cpc.pkl")
    goods = [c for c in cpc.nodes if c.isdigit() and (c[0] in "01234" or c.startswith("53"))]
    goods.sort(key=lambda c: (len(c), c))
    picks, skip = {}, set()          # label -> offset or '-';  an 8-digit key with '-' is a synset never proposed as new
    p = ROOT / "align/cpc-picks.tsv"
    if p.exists():
        for row in csv.reader(open(p), delimiter="\t"):
            if row and not row[0].startswith("#") and len(row) >= 2:
                if row[0].strip().isdigit() and len(row[0].strip()) == 8:
                    skip.add(row[0].strip())
                else:
                    picks[row[0].strip()] = row[1].strip()
    # the baseline: core's concepts without this tool's own previous output (or a second run finds nothing new)
    prev = set()
    gp = ROOT / "align/cpc-goods.tsv"
    if gp.exists():
        prev = {r[0] for r in csv.reader(open(gp), delimiter="\t") if r and not r[0].startswith("#") and len(r) >= 2 and r[1].strip()}
    rows_ = [r for r in csv.DictReader(open(ROOT / "align/concepts.tsv"), delimiter="\t") if r.get("wordnet") not in prev]
    core = {r["wordnet"]: r["name"] for r in rows_ if r.get("wordnet")}
    taken = {r["name"] for r in rows_}

    def hinge(code):
        h = BASE
        for k, v in HINGE.items():
            if code.startswith(k):
                h = v
        for k, v in HINGE_EXTRA.items():
            if code.startswith(k):
                h = h | v
        return h

    anc_cache = {}
    def anc(s):
        if s not in anc_cache:
            anc_cache[s] = wn.ancestors(s)
        return anc_cache[s]

    chosen = {}                     # code -> {label: offset}; a union bin's kinds go to `union` (they are siblings, not ancestors)
    union = {}
    ambiguous = {}                  # label -> (code, cands)
    unmatched = []                  # (code, title, label)
    nonsense = []                   # label matched WordNet but only in non-goods senses
    for code in goods:              # short codes first: an ancestor's alignment guides its descendants
        title = cpc.label(code)
        ks = kinds(title)
        into = union if cpc.children.get(code) and is_union(title, ks) else chosen
        for label in ks:
            key = f"{label}@{code}"
            if key in picks or label in picks:
                pk = picks.get(key, picks.get(label))
                if pk != "-":
                    into.setdefault(code, {})[label] = pk
                continue
            hits = []
            for v in variants(label):
                if v in lem:
                    hits = lem[v]; break
            if not hits:
                if label.split()[-1] in GENERIC or label in GENERIC:
                    continue
                unmatched.append((code, title, label)); continue
            if label in GENERIC or singular(label) in GENERIC:
                continue
            h = hinge(code)
            cand = [x for x in hits if anc(x) & h and PERSON not in anc(x)]
            if not cand:
                nonsense.append((code, title, label, hits)); continue
            if len(cand) > 1:
                q, guide = cpc.parents(code)[0], set()
                while q and q not in ("cpc-root", "cpc-goods"):
                    if q in chosen:
                        guide = set(chosen[q].values()); break
                    q = cpc.parents(q)[0] if cpc.parents(q) else None
                if guide:
                    c2 = [x for x in cand if anc(x) & guide]
                    if c2:
                        cand = c2
            if len(cand) > 1 and len(code) == 5:
                c3 = [x for x in cand if x in core]
                if len(c3) == 1:
                    cand = c3
            if len(cand) == 1:
                into.setdefault(code, {})[label] = cand[0]
            else:
                ambiguous.setdefault(label, (code, cand))

    # one code per synset: the shortest, then the title naming fewest kinds
    best = {}
    label_of = collections.defaultdict(set)
    for code, m in list(chosen.items()) + list(union.items()):
        n = len(m)
        ks = kinds(cpc.label(code))
        for label, off in m.items():
            if off in skip and off not in core:
                continue
            label_of[off].add(label)
            target = f"{code}{chr(97 + ks.index(label))}" if code in union else code       # the union bin's kind leaf (extract_cpc.py)
            if target not in cpc.nodes:
                continue
            k = (len(code), n, code)
            if off not in best or k < best[off][0]:
                best[off] = (k, target)
    rows = []
    collisions = 0
    for off, (_, code) in sorted(best.items(), key=lambda kv: kv[1][1]):
        labels = sorted(label_of[off])
        if off in core:
            rows.append((off, "", code, f"core: {core[off]} — cpc {code} {cpc.label(code)[:60]}"))
            continue
        name = None
        for l in labels:
            if l.replace(" ", "_") in [x.lower() for x in lemmas[off]] or l.replace(" ", "-") in [x.lower() for x in lemmas[off]]:
                name = normalise(l); break
        name = name or normalise(lemmas[off][0])
        if name in taken:
            alts = [normalise(l) for l in lemmas[off][1:] if normalise(l) not in taken and "." not in normalise(l)]
            if alts:
                name = alts[0]
            else:
                name += ".cpc"; collisions += 1
        taken.add(name)
        rows.append((off, name, code, f"cpc {code} {cpc.label(code)[:50]}: {'; '.join(labels)} — {gloss[off]}"))
    with open(gp, "w") as f:
        f.write("# offset\tname\tcpc\tnote — GENERATED by tools/align_cpc.py from the UN CPC 2.1 goods sections (0-4, 53); do not edit "
                "(sense picks in cpc-picks.tsv, hand names in names.tsv). An empty name is a synset core already has: the code is "
                "CPC's witness for it; a named row is a good or material core lacked. UPPER.md §12.\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    with open(ROOT / "build/cpc-ambiguous.tsv", "w") as f:
        f.write("# label\tcode\tsenses (offset: gloss) — pick one into align/cpc-picks.tsv as `label<TAB>offset` (or `-` to skip; `label@code` for one code)\n")
        for l, (code, cand) in sorted(ambiguous.items()):
            f.write(l + "\t" + code + "\t" + "\t".join(f"{c}: {gloss[c]}" + (" [core]" if c in core else "") for c in cand) + "\n")
    with open(ROOT / "build/cpc-unmatched.tsv", "w") as f:
        f.write("# code\ttitle\tkind — kinds WordNet has no noun for (or only non-goods senses, marked)\n")
        for code, title, l in unmatched:
            f.write(f"{code}\t{title[:80]}\t{l}\n")
        for code, title, l, hits in nonsense:
            f.write(f"{code}\t{title[:80]}\t{l}\t[non-goods senses: " + "; ".join(gloss[h][:40] for h in hits[:3]) + "]\n")
    with open(ROOT / "build/cpc-upper.tsv", "w") as f:
        f.write("# code\ttitle\tlabel\toffset\tname\tgloss — every aligned code with children: the upper ends of CPC's witness edges (union bins' kinds are leaves beside the bin and are not listed)\n")
        for code in sorted(chosen, key=lambda c: (len(c), c)):
            if not cpc.children.get(code):
                continue
            for l, off in chosen[code].items():
                nm = core.get(off) or next((r[1] for r in rows if r[0] == off), "")
                f.write(f"{code}\t{cpc.label(code)[:60]}\t{l}\t{off}\t{nm}\t{gloss[off][:60]}\n")
    new = sum(1 for r in rows if r[1])
    print(f"CPC goods: {len(goods)} codes; {sum(len(m) for m in chosen.values())} kinds aligned in {len(chosen)} codes "
          f"(+{sum(len(m) for m in union.values())} in {len(union)} union bins, as sibling leaves) -> "
          f"{len(best)} synsets ({len(best) - new} core already has: CPC becomes their witness; {new} new to core); "
          f"{len(ambiguous)} ambiguous labels; {len(unmatched)} unmatched kinds, {len(nonsense)} with only non-goods senses; "
          f"{collisions} names collide with core (marked .cpc)")


if __name__ == "__main__":
    main()
