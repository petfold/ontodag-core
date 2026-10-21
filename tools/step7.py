"""Apply the step-7 decisions to the built .od files (ontodag ROLES.md §9
step 7): the renames of align/renames-step7.tsv, the role rewrites of
align/roles-rewrites.tsv, the unit heads core declares for the quantity
names it owns (align/core-heads.tsv, ROLES.md §8 item 23), and the
unit-family pins of every dimension head (ROLES.md §8 item 21), and the
rulings of align/rulings-v*.tsv (a later core version's edge decisions:
move, parent+, add, cut, drop, refine, refine-cross, promote, disown).

    python3 tools/step7.py            # rewrite build/core.od and packs/*/build/*.od
    python3 tools/step7.py --check    # report only

The stores are written as ontodag's canonical `.od` (`native.dumps`): built
the way ontodag builds a pack, the prelude first, so the files carry the
`#:canonical` marker that lets a load trust them, the prelude's declarations
and the relation terms' nodes, and each node's gloss as `#:meta` (WordNet
3.0's definition of its synset, align/glosses-v14.tsv where a ruling
changed the sense; on a name's owner only). Canonical files keep only the
transitive reduction, so a ruling's edge another path implies is not
stored and the checks read what is implied.

These are rulings made after consensus, and consensus never produces an
`in(...)` or `about(...)` parent, so they are applied to its output, as the
last stage of tools/build.sh. The stage is idempotent: every row reports
whether it was applied now, was already applied, or does not match the
build (an error, so the build stops rather than ship half a decision).

A name is a name in every pack: a rename rewrites it wherever it occurs, as
a node or a parent. A drop removes a node that must have no children.
A merge whose target is a core name moves the entry's parents into core.
A pack may carry an entry for a core name only to refine it (the rulings
actions `refine` and `refine-cross`): it adds a parent from the pack, never
removes or renames anything, and core keeps its own edge.
"""
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENAMES = ROOT / "align/renames-step7.tsv"
CORE_HEADS = ROOT / "align/core-heads.tsv"
RULINGS = sorted(ROOT.glob("align/rulings-v*.tsv"))
REWRITES = ROOT / "align/roles-rewrites.tsv"

# A pinned head's family is its own name when the registry has a family of
# that name; otherwise it is listed here (ontodag dimensions._UNITS).
FAMILY_OF = {"amount-of-substance": "amount"}
PINNABLE = ("linear-dimension", "count-dimension")


sys.path.insert(0, str(ROOT.parent / "ontodag" / "src"))


def _prelude():
    from ontodag.packs import pack_entries
    return {n: set(p) for n, p in pack_entries("prelude")}


PRELUDE = _prelude()


def read_od(path):
    """A store's lines, without what ontodag adds when it writes them
    canonical (`write_od`): the relation terms' nodes and the prelude's own
    declarations. A prelude name a store says more about (core's
    `linear-dimension ⊑ attribute`) keeps its line. Canonical files store
    only the reduction, so an implied edge is not there: the checks read
    `implied`, and a ruling on a prelude name brings its node back."""
    order, par = [], {}
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        fields = shlex.split(line)
        name, parents = fields[0], fields[1:]
        if "(" in name:
            continue                                  # a term's node: ontodag's
        if name in PRELUDE and set(parents) <= PRELUDE[name] | {"*"}:
            continue                                  # the prelude's own declaration
        if name not in par:
            order.append(name)
        par[name] = list(parents)
    return order, par


def write_od(path, order, par, meta):
    """Write a store as ontodag's canonical `.od`: built the way ontodag builds
    a pack (the prelude first, every node, then the edges), with each node's
    gloss as `#:meta`, and written by `native.dumps`, which adds the
    `#:canonical` marker that lets the next load trust the file."""
    from ontodag import native
    from ontodag.dag import Item, OntoDAG
    from ontodag.packs import _hung, pack_entries
    dag = OntoDAG()
    prelude = pack_entries("prelude")
    for node, parents in prelude:
        if node not in dag.nodes:
            dag.put(node, list(parents))
    for node, parents in prelude:
        if parents:
            dag.put(node, list(parents))
    entries = [(n, [x for x in par[n] if x != "*"]) for n in order if n in par]
    for node, parents in entries:
        for parent in parents:
            hung = _hung(parent)
            for stub in ((parent,) if hung is None else hung):
                if stub not in dag.nodes:
                    dag.put(stub, [])
    for node, _ in entries:
        if node not in dag.nodes:
            dag.put(node, [])
    for node, values in meta.items():                 # a prelude name core glosses too
        if node in dag.nodes and values:
            dag.nodes[node].metadata.update(values)
    for node, parents in entries:
        if parents:
            dag.put(node, parents)
    with open(path, "w") as out:
        out.write(native.dumps(dag))


def ensure(par, sub, parents):
    """Store edges a ruling asks for even when another path implies them
    now: a later ruling may remove that path (banknote ⊑ artifact outlives
    currency ⊑ artifact). The canonical writer drops any that stay implied,
    so a rerun writes the same bytes."""
    keep = [x for x in par.get(sub, []) if x != "*"]
    par[sub] = sorted(set(keep) | set(parents)) or ["*"]


def glosses(renamed):
    """name -> {"gloss", "wn30"}: WordNet 3.0's definition (examples dropped)
    for the synset each name is aligned to, through the renames, with
    align/glosses-v14.tsv for the senses a v14 ruling changed or added."""
    import csv
    defs = {}
    for line in open(ROOT.parent / "wordnet/dict/data.noun", encoding="latin-1"):
        if line[:1].isdigit():
            offset, text = line.split(" ", 1)[0], line.split(" | ", 1)[-1]
            defs[offset] = text.split('; "')[0].strip().rstrip(";").strip()
    syn = {}
    homes = [ROOT] + sorted(d for d in (ROOT / "packs").iterdir() if (d / "align/concepts.tsv").exists())
    for home in homes:
        for r in csv.DictReader(open(home / "align/concepts.tsv"), delimiter="\t"):
            if not r.get("wordnet"):
                continue
            name = renamed(r["name"])
            # the row of the name itself wins over a row renamed into it
            if name not in syn or r["name"] == name:
                syn[name] = r["wordnet"]
    out = {n: {"gloss": defs[s], "wn30": f"{s}-n"} for n, s in syn.items() if s in defs}
    for row in table(ROOT / "align/glosses-v14.tsv"):
        name, offset, gloss = row[0], row[1], (row[2] if len(row) > 2 else "")
        if offset == "-" and not gloss:
            out.pop(name, None)                # a new sense no synset fits: no gloss
            continue
        out[name] = ({"gloss": defs[offset], "wn30": f"{offset}-n"} if offset != "-"
                     else {"gloss": gloss})
    return out


def table(path):
    rows = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        rows.append(line.rstrip("\n").split("\t"))
    return rows[1:]                                   # the header row


def parents_of(text):
    """The parents column: names and terms, before any note."""
    text = text.split(";")[0]
    if "(" in text:
        # cut a trailing note "(...)" but keep terms like in(x)
        out, depth, word = [], 0, ""
        for ch in text:
            if ch == "(" and not word.strip():
                break                                 # a note, not a term
            word += ch
            depth += ch == "("
            depth -= ch == ")"
            if ch == " " and depth == 0:
                out.append(word.strip())
                word = ""
        if word.strip():
            out.append(word.strip())
        return [w for w in out if w]
    return text.split()


def main():
    check = "--check" in sys.argv
    files = {"core": ROOT / "build/core.od"}
    for d in sorted((ROOT / "packs").iterdir()):
        od = d / "build" / f"{d.name}.od"
        if od.exists():
            files[d.name] = od
    graphs = {k: read_od(p) for k, p in files.items()}
    log, errors = [], []

    def where(name):
        return [k for k, (_, par) in graphs.items() if name in par]

    def mentions(name):
        return [(k, n) for k, (_, par) in graphs.items()
                for n, ps in par.items()
                if name in ps or any(x.endswith(f"({name})") for x in ps)]

    def renamed(x, old, new):
        if x == old:
            return new
        if "(" in x and x[x.index("(") + 1:-1] == old:      # in(old), about(old)
            return x[:x.index("(") + 1] + new + ")"
        return x

    def rename(old, new):
        for k, (order, par) in graphs.items():
            if old in par:
                if new in par:
                    joined = set(par[new]) | set(par.pop(old))
                    par[new] = sorted(joined - {"*"}) or ["*"]   # into a stub: the stub fills
                else:
                    par[new] = par.pop(old)
                    order[order.index(old)] = new
            for n, ps in par.items():
                if any(renamed(x, old, new) != x for x in ps):
                    par[n] = [renamed(x, old, new) for x in ps]
            if new in par.get(new, []):               # a child merged into its parent
                par[new] = [x for x in par[new] if x != new]

    def union_ancestors(name):
        """Every name above `name` in core and all packs together; a term
        (`linear-dimension(pressure)`) leads to its head."""
        seen, todo = set(), [name]
        while todo:
            n = todo.pop()
            for x in PRELUDE.get(n, ()):              # the prelude's declared parents
                if x not in seen:
                    seen.add(x)
                    todo.append(x[:x.index("(")] if "(" in x else x)
            for k, (_, par) in graphs.items():
                for x in par.get(n, []):
                    if x == "*":
                        continue
                    if x not in seen:
                        seen.add(x)
                        todo.append(x[:x.index("(")] if "(" in x else x)
                        if "(" in x:
                            seen.add(x[:x.index("(")])
        return seen

    def implied(sub, pack):
        """What `sub` is below in `pack` and the stores beside it: stored or
        implied, since the canonical files keep only the reduction."""
        return set(graphs[pack][1].get(sub, [])) | union_ancestors(sub)

    rows = table(RENAMES)
    for i, (pack, old, new, kind, *note) in enumerate(rows):
        # A chain: `floor -> floor-surface`, then `storey -> floor`. Once the
        # later row has run, `floor` is the new sense, so this row is done.
        reused = [r for r in rows[i + 1:] if r[2] == old]
        if reused and not where(reused[0][1]) and not mentions(reused[0][1]):
            log.append(f"already  {kind} {old} -> {new} (the name is reused)")
            continue
        if kind == "drop":
            if not where(old):
                log.append(f"already  drop {old}")
                continue
            children = mentions(old)
            if children:
                errors.append(f"drop {old}: it has children {children}")
                continue
            for k in where(old):
                del graphs[k][1][old]
            log.append(f"applied  drop {old}")
            continue
        if not where(old) and not mentions(old):
            log.append(f"already  {kind} {old} -> {new}")
            continue
        # refine-merge: a pack's duplicate of a core name keeps its own parent
        # as a refinement in the pack (plain rename); merge moves it into core
        if kind == "merge" and new in graphs["core"][1] and pack != "core":
            moved = graphs[pack][1].pop(old, [])
            core = graphs["core"][1]
            core[new] = sorted(set(core[new]) | set(moved))
        rename(old, new)
        log.append(f"applied  {kind} {old} -> {new}")

    core_names = set(graphs["core"][1])

    def known_to(pack):
        """The names a pack's claims may use: its own and core's. A pack
        borrowing a sibling's name is its .od's business (written as a stub);
        core may lean on no pack."""
        if pack == "core":
            return core_names | set(graphs["core"][1]) | set(PRELUDE)
        return {n for _, par in graphs.values() for n in par} | set(PRELUDE)
    # A rewritten edge that a later ruling changes again (the concept pass
    # moved account-abstraction off concept) is done, not missing.
    ruled = {(r[0], r[1]) for path in RULINGS for r in table(path)}
    dropped = {(r[0], r[1]) for path in RULINGS for r in table(path) if r[2] == "drop"}
    for pack, sub, old_sup, action, new_parents, relation in table(REWRITES):
        if action == "keep":
            continue
        order, par = graphs[pack]
        if sub not in par and (pack, sub) in dropped:
            log.append(f"already  {sub}: {old_sup} -> (rewritten, then dropped by a ruling)")
            continue
        if (pack, sub) in ruled and sub in par and old_sup not in par[sub]:
            log.append(f"already  {sub}: {old_sup} -> (rewritten, then ruled on)")
            continue
        if "(drop the name" in new_parents:
            if sub not in par:
                log.append(f"already  drop {sub}")
            elif mentions(sub):
                errors.append(f"drop {sub}: it has children {mentions(sub)}")
            else:
                del par[sub]
                log.append(f"applied  drop {sub}")
            continue
        new = parents_of(new_parents)
        for term in new:
            for constraint in ([term[term.index("(") + 1:-1]] if "(" in term else [term]):
                if constraint not in known_to(pack):
                    errors.append(f"{sub}: no node {constraint!r} ({new_parents})")
        if sub not in par:
            errors.append(f"{pack}: no node {sub!r}")
            continue
        stale = [x for x in par[sub] if x not in known_to(pack) and "(" not in x]
        if old_sup not in par[sub] and stale and set(new) - set(par[sub]):
            par[sub] = sorted((set(par[sub]) - set(stale)) | set(new))
            log.append(f"applied  {sub}: {' '.join(stale)} -> {' '.join(new)} (revised)")
            continue
        if old_sup not in par[sub]:
            if set(new) <= implied(sub, pack):
                log.append(f"already  {sub}: {old_sup} -> {' '.join(new)}")
            else:
                errors.append(f"{sub} ⊑ {old_sup} is not in {pack}, and the rewrite is not there either")
            continue
        par[sub] = sorted((set(par[sub]) - {old_sup}) | set(new))
        log.append(f"applied  {sub}: {old_sup} -> {' '.join(new)}")
        if "; and " in new_parents:                   # a second edge, `a ⊑ b`
            extra = new_parents.split("; and ", 1)[1].split()
            child, parent = extra[0], extra[2]
            par[child] = sorted(set(par.get(child, [])) | {parent})
            log.append(f"applied  {child} ⊑ {parent}")

    disowned = {(r[0], r[1]): set(r[4].split()) or {"*"}
                for path in RULINGS for r in table(path) if r[2] == "disown"}
    # A later ruling supersedes what it undoes (the everyday-sense pass,
    # 2026-10-22, re-files and drops names earlier files placed). Replayed on
    # its own output, an earlier row must not re-add an edge a later row
    # removes, nor stumble on a node a later row drops: it is done.
    sequence = [(path, r) for path in RULINGS for r in table(path)]
    later_rows = {}
    for i, (_, r) in enumerate(sequence):
        later_rows.setdefault((r[0], r[1]), []).append((i, r[2], r[3], r[4].split()))

    def later(i, pack, sub):
        return [(a, o) for j, a, o, _ in later_rows.get((pack, sub), []) if j > i]

    def readded(i, pack, sub):
        return {x for j, a, _, n in later_rows.get((pack, sub), []) if j > i
                and a in ("move", "parent+", "add") for x in n}

    def dropped_later(i, pack, name):
        return any(a == "drop" for k in (pack, "core") for a, _ in later(i, k, name))

    def superseded(i, pack, sub, targets):
        """The targets a later row removes (moves or cuts away), or drops."""
        gone = {o for a, o in later(i, pack, sub) if a in ("move", "cut")}
        return {x for x in targets if x in gone or dropped_later(i, pack, x)}

    generated = RULINGS[-1]                  # rows written from a simulated graph
    for i, (path, (pack, sub, action, old, new, *note)) in enumerate(sequence):
        if True:
            order, par = graphs[pack]
            if sub in PRELUDE and sub not in par and action not in ("add", "drop"):
                par[sub] = sorted(PRELUDE[sub]) or ["*"]   # a declaration, read back
                order.append(sub)
            if (action != "disown" and (pack, sub) in disowned
                    and set(par.get(sub, [])) == disowned[(pack, sub)]):
                log.append(f"already  {action} {sub} ({pack} has disowned its copy)")
                continue
            if action != "drop" and sub not in par and dropped_later(i, pack, sub):
                log.append(f"already  {action} {sub} (a later ruling drops it)")
                continue
            if action not in ("disown", "add", "refine", "refine-cross", "promote") \
                    and sub not in par and any(a == "disown" for a, _ in later(i, pack, sub)):
                log.append(f"already  {action} {sub} ({pack} disowns its copy later)")
                continue
            want = new.split()
            undone = superseded(i, "core" if action == "promote" else pack, sub, want) \
                if action in ("add", "parent+", "move", "promote", "refine", "refine-cross") else set()
            if undone:
                want = [x for x in want if x not in undone]
                if action == "promote" and not want and sub in graphs["core"][1]:
                    log.append(f"already  promote {sub} ({pack}; a later ruling places it)")
                    continue
                if action == "move" and not want and old in readded(i, pack, sub):
                    log.append(f"already  {sub}: {old} -> {new} (a later ruling puts it back)")
                    continue
                if action == "move" and not want:
                    if old in par.get(sub, []):
                        rest = [x for x in par[sub] if x != old and x != "*"]
                        # the only parent: the move is made, a later row moves on from it
                        par[sub] = rest or sorted(new.split())
                        log.append(f"applied  {sub}: {old} -> "
                                   + ("(a later ruling places it)" if rest else new))
                    else:
                        log.append(f"already  {sub}: {old} -> {new} (a later ruling places it)")
                    continue
                if action in ("refine", "refine-cross") and not want:
                    if sub in par:
                        log.append(f"already  {pack} refines {sub} ⊑ {new} (a later ruling changes it)")
                        continue
                    want = new.split()               # the entry a later row re-files
                if action == "parent+" and not want:
                    log.append(f"already  {sub} ⊑ {new} (a later ruling changes it)")
                    continue
                if action == "add" and not want:
                    want = ["*"]
            if action == "add":
                if sub in par and want == ["*"]:
                    log.append(f"already  add {sub} (a later ruling places it)")
                    continue
                if sub in par:
                    log.append(f"already  add {sub}" if set(want) <= implied(sub, pack)
                               else f"ERROR    add {sub}: exists with {par[sub]}")
                    if not set(want) <= implied(sub, pack):
                        errors.append(f"add {sub}: it exists with other parents {par[sub]}")
                    else:
                        ensure(par, sub, want)
                    continue
                par[sub] = sorted(want)
                order.append(sub)
                log.append(f"applied  add {sub} ⊑ {' '.join(want)}")
            elif action == "parent+":
                if sub not in par:
                    errors.append(f"{pack}: no node {sub!r}")
                elif set(want) <= implied(sub, pack):
                    log.append(f"already  {sub} ⊑ {' '.join(want)}")
                    ensure(par, sub, want)
                else:
                    par[sub] = sorted((set(par[sub]) - {"*"}) | set(want))
                    log.append(f"applied  {sub} ⊑ {' '.join(want)}")
            elif action == "move":
                if sub not in par:
                    errors.append(f"{pack}: no node {sub!r}")
                    continue
                target = [] if want == ["*"] else want
                if old not in par[sub]:
                    # a name promoted into core later carries its parents there
                    have = implied(sub, pack)
                    done = set(target) <= have and (target or par[sub] in ([], ["*"]))
                    if done:
                        log.append(f"already  {sub}: {old} -> {new}")
                        if target and par[sub] != ["*"]:
                            ensure(par, sub, target)
                    elif path == generated and target:
                        # the old parent went with a row this pass supersedes
                        ensure(par, sub, target)
                        log.append(f"applied  {sub}: ({old} already gone) -> {new}")
                    else:
                        errors.append(f"{sub} ⊑ {old} is not in {pack}, and the move is not there either")
                    continue
                rest = (set(par[sub]) - {old}) | set(target)
                par[sub] = sorted(rest) if rest else ["*"]
                log.append(f"applied  {sub}: {old} -> {new}")
            elif action == "cut":
                # drop the edge sub ⊑ old; the node keeps its other parents
                if sub not in par:
                    errors.append(f"{pack}: no node {sub!r}")
                elif old not in par[sub]:
                    log.append(f"already  cut {sub} ⊑ {old}")
                elif old in readded(i, pack, sub):
                    log.append(f"already  cut {sub} ⊑ {old} (a later ruling puts it back)")
                elif not set(par[sub]) - {old, "*"}:
                    errors.append(f"cut {sub} ⊑ {old}: it is {sub}'s only parent (use move)")
                else:
                    par[sub] = sorted(set(par[sub]) - {old})
                    log.append(f"applied  cut {sub} ⊑ {old}")
                want = []
            elif action in ("refine", "refine-cross"):
                # A pack adds a parent to a core name: refinement by merge.
                # core keeps its own edge (it leans on no pack); merging the
                # pack drops that edge as implied. `refine` must insert a
                # level: the new parent lies under one of the core node's
                # parents. `refine-cross` is a reviewed cross-branch claim.
                core = graphs["core"][1]
                if pack != "core" and sub not in core and dropped_later(i, "core", sub):
                    log.append(f"already  {pack} refines {sub} (core drops it later; {pack} keeps it)")
                    want = []
                elif pack == "core" or sub not in core:
                    errors.append(f"{action} {sub}: not a core name refined by a pack")
                    want = []
                elif set(want) <= set(par.get(sub, [])) or (
                        sub in par and set(want) <= implied(sub, pack) and par[sub] != ["*"]):
                    log.append(f"already  {pack} refines {sub} ⊑ {' '.join(want)}")
                    ensure(par, sub, want)
                else:
                    for x in want:
                        if "(" in x:
                            errors.append(f"{action} {sub} ⊑ {x}: a refinement adds a kind, never a "
                                          f"relation or a unit pin (whoever owns a name declares its head)")
                        elif x in core:
                            errors.append(f"{action} {sub} ⊑ {x}: a core-to-core edge belongs in core")
                        elif action == "refine" and not any(
                                c in union_ancestors(x) for c in core[sub] if c != "*" and "(" not in c):
                            errors.append(f"refine {sub} ⊑ {x}: {x} is not under any of "
                                          f"{sub}'s core parents (a cross-branch claim: refine-cross)")
                    if sub not in par:
                        order.append(sub)
                    par[sub] = sorted((set(par.get(sub, [])) - {"*"}) | set(want))
                    log.append(f"applied  {pack} refines {sub} ⊑ {' '.join(want)}")
            elif action == "promote":
                # A pack's general name moves into core (a hinge several packs
                # use), with the core parents in `new`. The pack keeps any
                # parent of its own as a refinement, which must insert a tier
                # under one of the core parents; otherwise its entry becomes a
                # stub, as for every core name it hangs from.
                core_order, core = graphs["core"]
                if pack == "core":
                    errors.append(f"promote {sub}: name a pack")
                    want = []
                elif any(x not in core for x in want):
                    errors.append(f"promote {sub}: core parents only, got {want}")
                    want = []
                elif sub in core and set(want) <= set(core[sub]) and all(
                        x == "*" or x not in core for x in par.get(sub, ["*"])):
                    log.append(f"already  promote {sub} ⊑ {' '.join(want)} ({pack})")
                    want = []
                elif sub not in par and sub not in core:
                    errors.append(f"{pack}: no node {sub!r} to promote")
                    want = []
                else:
                    if sub not in core:
                        core_order.append(sub)
                    core[sub] = sorted((set(core.get(sub, [])) - {"*"}) | set(want))
                    keep = [x for x in par.get(sub, []) if x != "*" and x not in core]
                    for x in keep:
                        if "(" in x or not any(c in union_ancestors(x) for c in want):
                            errors.append(f"promote {sub}: {pack} keeps {x}, which is not under {want}")
                    if sub not in par:
                        order.append(sub)
                    par[sub] = sorted(keep) if keep else ["*"]
                    log.append(f"applied  promote {sub} ⊑ {' '.join(want)} into core"
                               + (f"; {pack} refines it ⊑ {' '.join(keep)}" if keep else ""))
                want = []
            elif action == "disown":
                # One owner per name: a pack gives up its copy of a name that
                # core or a sibling pack owns, keeping a stub (a borrowed name).
                others = [k for k, (_, p) in graphs.items()
                          if k != pack and p.get(sub) not in (None, ["*"])]
                have = set(par.get(sub) or ["*"]) - {"*"}
                if not others and any(a == "drop" for k in graphs for a, _ in later(i, k, sub)):
                    log.append(f"already  {pack} disowns {sub} (a later ruling drops it)")
                elif not others:
                    errors.append(f"disown {sub}: no other store owns it")
                elif have == set(want) or (have and have <= set(want) <= implied(sub, pack)):
                    log.append(f"already  {pack} disowns {sub}")
                elif not set(want) <= set(par.get(sub, [])) | implied(sub, pack):
                    errors.append(f"disown {sub}: {pack} can keep only parents it has, not {want}")
                else:
                    # `new` lists the parents the pack's own vocabulary adds:
                    # it keeps them as a refinement of the owner's name
                    par[sub] = sorted(want) or ["*"]
                    log.append(f"applied  {pack} disowns {sub} (owned by {', '.join(others)})"
                               + (f", keeping ⊑ {' '.join(want)}" if want else ""))
                want = []
            elif action == "drop":
                # remove the node; its children must have been moved first
                if sub not in par:
                    log.append(f"already  drop {sub}")
                elif mentions(sub):
                    errors.append(f"drop {sub}: it has children {mentions(sub)}")
                else:
                    del par[sub]
                    log.append(f"applied  drop {sub}")
                want = []
            else:
                errors.append(f"{path.name}: unknown action {action!r}")
            for x in want:
                name = x[x.index("(") + 1:-1] if "(" in x else x   # about(x), in(x): the argument
                if x != "*" and name not in known_to(pack):
                    errors.append(f"{sub}: no node {name!r} for {pack}")

    removed = ({r[1] for path in RULINGS for r in table(path) if r[2] == "drop"}
               | {r[1] for r in table(RENAMES)})
    # A name from core or a sibling that a rewrite or a ruling brought into
    # a pack is written there as a stub, as the build writes every borrowed
    # name (UPPER.md §8.1).
    for pack, (order, par) in graphs.items():
        if pack == "core":
            continue
        used = set()
        for ps in par.values():
            for x in ps:
                if x.startswith(tuple(k + "(" for k in PINNABLE)):
                    continue                          # a family pin, not a name
                used |= {x[x.index("(") + 1:-1]} if "(" in x else {x}
        for name in sorted(used - set(par) - set(PRELUDE) - {"*"}):   # the prelude is in every store
            if any(name in g[1] for k, g in graphs.items() if k != pack):
                par[name] = ["*"]
                order.append(name)
                log.append(f"applied  {pack} borrows {name}")
        # and a stub nothing in the pack uses goes: a borrowed name another
        # store holds, or one a ruling dropped or renamed away. (A pack's own
        # top-level name is written the same way, so it is never touched.)
        for name in sorted(n for n, ps in par.items() if ps == ["*"] and n not in used):
            held = name in graphs["core"][1] or any(
                g[1].get(name, ["*"]) != ["*"] for k, g in graphs.items() if k != pack)
            if name not in PRELUDE and (held or name in removed):
                del par[name]
                order.remove(name)
                log.append(f"applied  {pack} no longer borrows {name} (nothing in it uses it)")

    core = graphs["core"][1]
    for name, family, drop, *note in table(CORE_HEADS):
        pin = f"linear-dimension({family})"
        if name not in core:
            errors.append(f"core-heads: core has no {name!r}")
            continue
        if pin in core[name] and drop not in core[name] or (
                drop not in core[name] and pin in union_ancestors(name)):
            log.append(f"already  head {name} ⊑ {pin}")
            continue
        core[name] = sorted((set(core[name]) - {drop}) | {pin})
        log.append(f"applied  head {name} ⊑ {pin}" + (f" (drops ⊑ {drop})" if drop else ""))

    from_registry = _families()
    for pack, (order, par) in graphs.items():
        for name, ps in par.items():
            for kind in PINNABLE:
                if kind in ps:
                    family = FAMILY_OF.get(name, name)
                    if family not in from_registry:
                        errors.append(f"{pack}: {name} ⊑ {kind} names no unit family")
                        continue
                    par[name] = sorted((set(ps) - {kind}) | {f"{kind}({family})"})
                    log.append(f"applied  pin {name} ⊑ {kind}({family})")

    print("\n".join(log))
    if errors:
        print("\n".join("ERROR    " + e for e in errors), file=sys.stderr)
        sys.exit(1)
    if not check:
        # glosses go on each name's owner: core's names in core; a pack's own
        # names in the pack, never on a stub, a refinement of a core name or a
        # sibling's name it has disowned (merge keeps the first gloss it sees)
        rows = [r for r in table(RENAMES) if len(r) > 3 and r[3] != "drop"]

        def renamed(name):
            for _, old, new, *_rest in rows:
                if name == old:
                    name = new
            return name
        gloss = glosses(renamed)
        core = graphs["core"][1]
        disowned_by = {(r[0], r[1]) for path in RULINGS for r in table(path) if r[2] == "disown"}
        for k, path in files.items():
            order, par = graphs[k]
            meta = {n: gloss[n] for n in par if n in gloss and par[n] != ["*"]
                    and (k == "core" or (n not in core and (k, n) not in disowned_by))}
            if k == "core":                           # the prelude's names core has senses for
                meta.update({n: gloss[n] for n in PRELUDE if n in gloss})
            write_od(path, order, par, meta)


def _families():
    sys.path.insert(0, str(ROOT.parent / "ontodag" / "src"))
    from ontodag import dimensions
    return dimensions.known_families()


if __name__ == "__main__":
    main()
