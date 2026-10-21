"""The everyday-sense audit of a store (Peter, 2026-10-22): a pre-filled
sheet, one row per name, for the rule "a plain name means its everyday,
most frequent sense; qualify or drop the others; core is for clear and
unchanging things".

    python3 tools/sense_audit.py                 # core -> build/sense-audit.tsv
    python3 tools/sense_audit.py --pack NAME     # packs/NAME/build/sense-audit.tsv

Signals, per name, from WordNet 3.0:
  - the sense the node holds (its `wn30` gloss), that sense's rank for the
    name's lemma and its SemCor tag count;
  - the everyday sense: the lemma's sense in Princeton's core WordNet (the
    ~5,000 most frequently used word senses; `wordnet/core-wordnet.txt`),
    else its first (most frequent) sense, and the nearest name of this store
    a hypernym walk from it reaches (the parent the everyday sense would take);
  - the node's parents, children, and whether a pack or a term uses it.

Flags (several may hold):
  rare-sense   the node holds another sense than the everyday one, and the
               everyday one is more frequent (tags) or in core WordNet
  held-by      the everyday sense is another name's in this store
  disjoint     two or more parents with no common ancestor below the top
               branches: several parents mean AND, so the node is claimed
               to be both
  off-wordnet  a parent the node's WordNet hypernyms do not reach (it came
               from another source; WordNet may still be wrong)
  shrink       a leaf no pack or term uses, whose word is rare (not in core
               WordNet, at most one SemCor tag over all its senses)
  no-synset    no WordNet sense recorded

`recommendation` is pre-filled from the flags; `decision` is left for the
reviewer (Claude's pass, then Peter).
"""
import argparse
import csv
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WN = ROOT.parent / "wordnet"
LEXFILES = {
    3: "Tops", 4: "act", 5: "animal", 6: "artifact", 7: "attribute", 8: "body",
    9: "cognition", 10: "communication", 11: "event", 12: "feeling", 13: "food",
    14: "group", 15: "location", 16: "motive", 17: "object", 18: "person",
    19: "phenomenon", 20: "plant", 21: "possession", 22: "process",
    23: "quantity", 24: "relation", 25: "shape", 26: "state", 27: "substance",
    28: "time",
}


def wordnet():
    """(index: lemma -> [offsets by sense rank], data: offset -> dict,
    tags: (lemma, offset) -> tag count, everyday: lemma -> [offsets])."""
    index = {}
    for line in open(WN / "dict/index.noun", encoding="latin-1"):
        if line.startswith(" "):
            continue
        parts = line.split()
        lemma, n_ptr = parts[0], int(parts[3])
        synset_cnt = int(parts[2])
        offsets = parts[4 + n_ptr + 2:]
        index[lemma] = offsets[:synset_cnt]
    data = {}
    for line in open(WN / "dict/data.noun", encoding="latin-1"):
        if not line[:1].isdigit():
            continue
        head, _, gloss = line.partition(" | ")
        parts = head.split()
        offset, lexfile, w_cnt = parts[0], int(parts[1]), int(parts[3], 16)
        words = [parts[4 + 2 * i].lower() for i in range(w_cnt)]
        p = 4 + 2 * w_cnt
        p_cnt = int(parts[p])
        hypers = []
        for i in range(p_cnt):
            sym, target, pos = parts[p + 1 + 4 * i: p + 4 + 4 * i]
            if sym in ("@", "@i") and pos == "n":
                hypers.append(target)
        data[offset] = {"lexfile": LEXFILES.get(lexfile, str(lexfile)), "words": words,
                        "hypers": hypers,
                        "gloss": gloss.split('; "')[0].strip().rstrip(";").strip()}
    tags, keys = {}, {}
    for line in open(WN / "dict/index.sense", encoding="latin-1"):
        key, offset, _rank, count = line.split()
        lemma, _, rest = key.partition("%")
        if rest.startswith("1:"):
            tags[(lemma, offset)] = int(count)
            keys[key] = (lemma, offset)
    everyday = defaultdict(list)
    for line in open(WN / "core-wordnet.txt", encoding="latin-1"):
        if not line.startswith("n "):
            continue
        for key in re.findall(r"\[([^\]]+%1:[^\]]*)\]", line):
            if key in keys:
                lemma, offset = keys[key]
                everyday[lemma].append(offset)
    return index, data, tags, everyday


def load(pack):
    from ontodag import native, prelude
    path = ROOT / ("build/core.od" if pack == "core" else f"packs/{pack}/build/{pack}.od")
    dag = native.load(str(path))
    own = set(prelude.prelude_dag().nodes)
    return dag, own


def pack_uses():
    """name -> the packs (and terms) that name it as a parent or argument."""
    uses = defaultdict(set)
    for path in sorted((ROOT / "packs").glob("*/build/*.od")):
        pack = path.parent.parent.name
        for line in open(path, encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            import shlex
            tokens = shlex.split(line)
            for t in tokens[1:]:
                uses[t].add(pack)
                m = re.match(r"^[a-z-]+\((.*)\)$", t)
                if m:
                    uses[m.group(1)].add(pack)
    return uses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default="core")
    args = ap.parse_args()
    index, data, tags, everyday = wordnet()
    dag, own = load(args.pack)
    uses = pack_uses()
    names = sorted(n for n in dag.nodes
                   if n != "*" and n not in own and "(" not in n)
    by_offset = defaultdict(list)
    for n in names:
        wn30 = (dag.nodes[n].metadata or {}).get("wn30", "")
        if wn30:
            by_offset[wn30[:-2]].append(n)
    # term arguments used in this store: about(x), in(x)
    for n in dag.nodes:
        m = re.match(r"^[a-z-]+\((.*)\)$", n)
        if m and dag.nodes[n].neighbors:
            uses[m.group(1)].add("term")

    def parents(n):
        return sorted(p.name for p in dag.nodes[n].parents
                      if dag.nodes.get(p.name) is p and p.name != "*")

    def ancestors(n):
        seen, todo = set(), deque([n])
        while todo:
            for p in parents(todo.popleft()):
                if p not in seen:
                    seen.add(p)
                    todo.append(p)
        return seen

    tops = {p.name for p in dag.root.neighbors}

    def nearest_core(offset, exclude):
        """The nearest store name a hypernym walk from `offset` reaches."""
        seen, todo = {offset}, deque([(offset, 0)])
        while todo:
            o, d = todo.popleft()
            if d:
                hits = [n for n in by_offset.get(o, []) if n != exclude]
                if hits:
                    return hits[0]
            for h in data.get(o, {}).get("hypers", []):
                if h not in seen:
                    seen.add(h)
                    todo.append((h, d + 1))
        return ""

    def wn_reach(offset):
        """Store names the node's WordNet hypernyms reach."""
        out, seen, todo = set(), {offset}, deque([offset])
        while todo:
            o = todo.popleft()
            for h in data.get(o, {}).get("hypers", []):
                if h not in seen:
                    seen.add(h)
                    out.update(by_offset.get(h, []))
                    todo.append(h)
        return out

    rows = []
    for n in names:
        node = dag.nodes[n]
        meta = node.metadata or {}
        cur = meta.get("wn30", "")[:-2] if meta.get("wn30") else ""
        lemma = n.replace("-", "_")
        senses = index.get(lemma, [])
        rank = senses.index(cur) + 1 if cur in senses else ""
        cur_tags = tags.get((lemma, cur), "") if cur else ""
        daily = [o for o in everyday.get(lemma, [])]
        ref = daily[0] if daily else (senses[0] if senses else "")
        ref_tags = tags.get((lemma, ref), 0) if ref else ""
        total_tags = sum(tags.get((lemma, o), 0) for o in senses)
        flags = []
        if not cur:
            flags.append("no-synset")
        if cur and ref and cur != ref and cur not in daily and (
                daily or (ref_tags or 0) > (cur_tags or 0)):
            flags.append("rare-sense")
        holder = [h for h in by_offset.get(ref, []) if h != n] if ref and ref != cur else []
        if holder:
            flags.append("held-by")
        ps = parents(n)
        if len(ps) >= 2:
            branches = []
            for p in ps:
                anc = ancestors(p) | {p}
                branches.append(anc - tops - {"*"})
            if any(not (branches[i] & branches[j])
                   for i in range(len(ps)) for j in range(i + 1, len(ps))):
                flags.append("disjoint")
        off = []
        if cur and ps:
            reach = wn_reach(cur)
            off = [p for p in ps if p not in reach]
            if off:
                flags.append("off-wordnet")
        leaf = not any(dag.nodes.get(c.name) is c for c in node.neighbors)
        used = sorted(uses.get(n, set()) - {args.pack})
        if leaf and not used and not daily and total_tags <= 1 and senses:
            flags.append("shrink")
        rec = ""
        if "rare-sense" in flags:
            where = nearest_core(ref, n)
            rec = (f"re-sense to the everyday {ref} (held by {holder[0]}: rename one)" if holder
                   else f"re-sense to the everyday {ref} under {where or '?'}")
        elif "disjoint" in flags:
            rec = "keep one parent (several mean AND)"
        elif "shrink" in flags:
            rec = "drop from core (rare leaf)" if args.pack == "core" else "review: rare leaf"
        rows.append({
            "name": n, "parents": " ".join(ps), "children": sum(
                1 for c in node.neighbors if dag.nodes.get(c.name) is c),
            "descendants": node.descendant_count, "used_by": " ".join(used),
            "wn30": cur, "lexfile": data.get(cur, {}).get("lexfile", "") if cur else "",
            "rank": rank, "senses": len(senses), "tags": cur_tags,
            "gloss": meta.get("gloss", ""),
            "everyday": ref if ref != cur else "", "everyday_tags": ref_tags if ref != cur else "",
            "everyday_lexfile": data.get(ref, {}).get("lexfile", "") if ref and ref != cur else "",
            "everyday_gloss": data.get(ref, {}).get("gloss", "") if ref and ref != cur else "",
            "everyday_parent": nearest_core(ref, n) if ref and ref != cur else "",
            "off_wordnet": " ".join(off), "flags": " ".join(flags),
            "recommendation": rec, "decision": "", "note": "",
        })
    out = ROOT / ("build/sense-audit.tsv" if args.pack == "core"
                  else f"packs/{args.pack}/build/sense-audit.tsv")
    with open(out, "w", newline="") as f:
        f.write(f"# The everyday-sense audit of {args.pack} (tools/sense_audit.py, 2026-10-22). "
                "See the tool's docstring for the columns and flags.\n")
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    counts = defaultdict(int)
    for r in rows:
        for fl in r["flags"].split():
            counts[fl] += 1
    print(f"{out.relative_to(ROOT)}: {len(rows)} names; " +
          ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), file=sys.stderr)


if __name__ == "__main__":
    main()
