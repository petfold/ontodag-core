"""Google Product Taxonomy (taxonomy-with-ids.en-US.txt) -> Graph.

A shopping taxonomy, not an ontology: 21 departments, a strict tree, plural
labels, and a quarter of the nodes are union bins ("Toasters & Grills").  It is
used as a WITNESS for the everyday goods layer of core — coverage and a second
source for edge truth — never imported verbatim.  So the extractor makes it
alignable by name: labels are singularised ("Toasters" -> "toaster"), and every
"A & B" bin keeps its own node (the path through it stays intact for its
children) and gains two sibling kind nodes A and B under the same parent, ids
<bin>a and <bin>b, so `toaster` and `grill` exist as kinds.  "X Accessories" and
"X Parts" stay as they are (`bicycle part` is a fine category).  Root: a
synthetic `gpt-root` above the 21 departments.
"""
import re
import sys
from pathlib import Path
from graph import Graph

SRC = Path(__file__).resolve().parent.parent / "sources/gpt/taxonomy-with-ids.en-US.txt"
ROOT = "gpt-root"

# words whose plural is the kind (or that are not plurals at all)
KEEP = {"glasses", "sunglasses", "scissors", "jeans", "pants", "trousers", "shorts", "tights",
        "leggings", "binoculars", "headphones", "earphones", "goggles", "pliers", "tongs", "tweezers",
        "overalls", "pajamas", "clothes", "bellows", "dice", "chess", "dominoes", "darts", "billiards",
        "athletics", "electronics", "optics", "supplies", "goods", "accessories", "cosmetics", "series",
        "species", "physics", "mathematics", "gymnastics", "aerobics", "graphics", "canvas", "bass",
        "brass", "glass", "dress", "mattress", "harness", "compass", "lens", "chassis", "gas", "iris",
        "tennis", "waders", "suspenders", "braces", "leftovers", "sweets", "forceps", "shears", "clippers", "chopsticks", "earmuffs", "handcuffs", "bagpipes", "briefs", "boxers", "dungarees", "coveralls", "spectacles", "bifocals", "linens", "textiles", "furnishings", "fixtures", "condiments", "spices", "herbs", "arts", "crafts", "notions", "greens", "grits", "oats",
        "noodles", "preserves", "spirits", "molasses", "hummus", "couscous", "lettuce"}
IRREGULAR = {"children": "child", "men": "man", "women": "woman", "feet": "foot", "teeth": "tooth",
             "geese": "goose", "mice": "mouse", "knives": "knife", "shelves": "shelf", "leaves": "leaf",
             "loaves": "loaf", "scarves": "scarf", "halves": "half", "calves": "calf", "wolves": "wolf",
             "lives": "life", "wives": "wife", "hooves": "hoof", "dies": "die", "cookies": "cookie",
             "movies": "movie", "ties": "tie", "pies": "pie", "cacti": "cactus", "fungi": "fungus",
             "media": "medium", "data": "data", "vertebrae": "vertebra", "antennae": "antenna",
             "shoes": "shoe", "canoes": "canoe", "potatoes": "potato", "tomatoes": "tomato",
             "pianos": "piano", "cellos": "cello", "banjos": "banjo", "videos": "video", "radios": "radio",
             "photos": "photo", "memos": "memo", "logos": "logo", "kimonos": "kimono", "tacos": "taco",
             "burritos": "burrito", "gazebos": "gazebo", "bikinis": "bikini", "skis": "ski", "taxis": "taxi",
             "menus": "menu", "tutus": "tutu", "cactuses": "cactus", "buses": "bus", "gases": "gas",
             "lenses": "lens", "canvases": "canvas", "mattresses": "mattress", "dresses": "dress",
             "harnesses": "harness", "compasses": "compass", "glasses": "glass", "brushes": "brush",
             "watches": "watch", "benches": "bench", "torches": "torch", "boxes": "box", "quizzes": "quiz"}


def singular(word):
    w = word.lower()
    if w in KEEP:
        return w
    if w in IRREGULAR:
        return IRREGULAR[w]
    if w.endswith("ties") and w[:-4] in ("neck", "bow", "hog", ""):
        return w[:-1]                      # neckties -> necktie
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("ches", "shes", "sses", "xes", "zes")):
        return w[:-2]
    if w.endswith("oes") and len(w) > 4:
        return w[:-2]
    if w.endswith("ves") and len(w) > 4:
        return w[:-1]                      # gloves -> glove, valves -> valve; f-plurals are in IRREGULAR
    if w.endswith("s") and not w.endswith("ss") and not w.endswith("us") and not w.endswith("is"):
        return w[:-1]
    return w


def singular_label(label):
    """'Kitchen Appliances' -> 'kitchen appliance'; only the head noun changes."""
    words = label.lower().replace(",", "").split()
    if not words:
        return label.lower()
    words[-1] = singular(words[-1])
    return " ".join(words)


ADJ = {"fresh", "frozen", "dried", "canned", "hot", "cold", "wet", "dry", "indoor", "outdoor", "men's", "women's",
       "boys'", "girls'", "baby", "kids'", "toddler", "adult", "electric", "manual", "portable", "disposable", "reusable",
       "wired", "wireless", "digital", "analog", "fixed", "mobile", "standard", "specialty", "raw", "cooked", "sweet", "savory"}


def shared_head(label):
    """'Fresh & Frozen Vegetables' -> 'frozen vegetable' is wrong and 'fresh' is junk: when the first
    half is a lone modifier the halves share the head, and the bin IS that kind (a subset of it) —
    return the singular head phrase, else None."""
    if " & " not in label or label.count(" & ") > 1:
        return None
    a, b = label.split(" & ")
    if len(a.split()) == 1 and (a.lower() in ADJ or a.lower().endswith(("ed", "ing", "'s", "s'"))):
        return singular_label(" ".join(b.split()[1:]) if len(b.split()) > 1 else b)
    return None


def split_bin(label):
    """'Toasters & Grills' -> ['toaster', 'grill']; 'Fresh & Frozen Vegetables' -> [] (shared head:
    the modifiers are alternatives, not kinds).  Only a two-noun-phrase union splits."""
    label = label.replace(" and ", " & ")
    if " & " not in label or label.count(" & ") > 1:
        return []
    a, b = label.split(" & ")
    if len(a.split()) > 2 or len(b.split()) > 2:
        return []
    return [singular_label(a), singular_label(b)]


def extract(path=SRC):
    nodes = {ROOT: ("gpt root", [])}
    by_path = {}
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        gid, _, path_s = line.rstrip("\n").partition(" - ")
        parts = path_s.split(" > ")
        by_path[tuple(parts)] = gid
    for parts, gid in by_path.items():
        parent = by_path[tuple(parts[:-1])] if len(parts) > 1 else ROOT
        raw = parts[-1]
        is_bin = " & " in raw or " and " in raw
        head = shared_head(raw.replace(" and ", " & ")) if is_bin else None
        nodes[gid] = (head if head else raw.lower().replace(" and ", " & ") if is_bin else singular_label(raw), [parent])
        for i, kind in enumerate([] if head else split_bin(raw)):
            nodes[f"{gid}{'ab'[i]}"] = (kind, [parent])
    # GPT is a tree, so one kind appears once per department ("Gloves" under Apparel and under
    # Baseball; "Fruit" three times).  Our concepts are DAG nodes: merge equal labels into one node
    # whose parents are the union — the alignment then finds one node per label, and the merged
    # node carries every department's claim as a witness.
    first, merged = {}, {}
    for gid, (label, ps) in list(nodes.items()):
        if gid == ROOT or " & " in label:
            continue
        if label in first:
            merged[gid] = first[label]
        else:
            first[label] = gid
    for gid, keep in merged.items():
        lab, ps = nodes.pop(gid)
        klab, kps = nodes[keep]
        nodes[keep] = (klab, sorted(set(kps) | set(ps)))
    for gid, (label, ps) in nodes.items():
        nodes[gid] = (label, sorted({merged.get(p, p) for p in ps}))
    # One label, one kind: GPT files gloves under Apparel and under Baseball, and three bins read
    # "fruit" once their shared head is taken.  Alignment is by label and needs the match unique,
    # so same-label kind nodes merge into one node with the union of their parents (a multi-parent
    # node — exactly the DAG's improvement on the tree) and their children reattached.
    by_label = {}
    for gid, (label, _) in nodes.items():
        if " & " not in label and gid != ROOT:
            by_label.setdefault(label, []).append(gid)
    alias = {}
    for label, ids in by_label.items():
        if len(ids) > 1:
            keep = ids[0]
            parents = []
            for i in ids:
                for q in nodes[i][1]:
                    if q not in parents:
                        parents.append(q)
                if i != keep:
                    alias[i] = keep
            nodes[keep] = (label, parents)
    for i in alias:
        del nodes[i]
    for gid, (label, ps) in nodes.items():
        ps2 = []
        for q in ps:
            q = alias.get(q, q)
            if q != gid and q not in ps2:
                ps2.append(q)
        nodes[gid] = (label, ps2)
    # A merge can put a kind above itself ("fruit" as a bin head under a "fruit" bin): drop any
    # parent link whose target already reaches the node — the finer placement stays, the loop goes.
    def reaches(a, b):
        seen, stack = set(), [a]
        while stack:
            x = stack.pop()
            if x == b:
                return True
            for q in nodes[x][1]:
                if q not in seen:
                    seen.add(q); stack.append(q)
        return False
    for gid, (label, ps) in list(nodes.items()):
        keep = [q for q in ps if not reaches(q, gid)]
        if len(keep) != len(ps):
            nodes[gid] = (label, keep)
    return Graph(nodes, ROOT)


if __name__ == "__main__":
    g = extract()
    g.save(sys.argv[1])
    bins = sum(1 for s, (l, _) in g.nodes.items() if " & " in l)
    print(len(g.nodes), "nodes;", bins, "union bins kept as paths;",
          sum(1 for s in g.nodes if s[-1] in "ab" and s[:-1] in g.nodes), "kinds split out of them")
