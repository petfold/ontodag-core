"""Apply the step-7 decisions to the built .od files (ontodag ROLES.md §9
step 7): the renames of align/renames-step7.tsv, the role rewrites of
align/roles-rewrites.tsv, the unit heads core declares for the quantity
names it owns (align/core-heads.tsv, ROLES.md §8 item 23), and the
unit-family pins of every dimension head (ROLES.md §8 item 21).

    python3 tools/step7.py            # rewrite build/core.od and packs/*/build/*.od
    python3 tools/step7.py --check    # report only

These are rulings made after consensus, and consensus never produces an
`in(...)` or `about(...)` parent, so they are applied to its output, as the
last stage of tools/build.sh. The stage is idempotent: every row reports
whether it was applied now, was already applied, or does not match the
build (an error, so the build stops rather than ship half a decision).

A name is a name in every pack: a rename rewrites it wherever it occurs, as
a node or a parent. A drop removes a node that must have no children.
A merge whose target is a core name moves the entry's parents into core,
since a pack never carries entries for core names.
"""
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENAMES = ROOT / "align/renames-step7.tsv"
CORE_HEADS = ROOT / "align/core-heads.tsv"
REWRITES = ROOT / "align/roles-rewrites.tsv"

# A pinned head's family is its own name when the registry has a family of
# that name; otherwise it is listed here (ontodag dimensions._UNITS).
FAMILY_OF = {"amount-of-substance": "amount"}
PINNABLE = ("linear-dimension", "count-dimension")


def read_od(path):
    order, par = [], {}
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        fields = shlex.split(line)
        if fields[0] not in par:
            order.append(fields[0])
        par[fields[0]] = [x for x in fields[1:]]
    return order, par


def write_od(path, order, par, header):
    with open(path, "w") as out:
        out.write(header)
        written = set()
        for name in order:
            if name in par and name not in written:
                written.add(name)
                out.write(" ".join(shlex.quote(x) for x in [name, *par[name]]) + "\n")


def header_of(path):
    return "".join(l for l in open(path) if l.startswith("#"))


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
                for n, ps in par.items() if name in ps]

    def rename(old, new):
        for k, (order, par) in graphs.items():
            if old in par:
                if new in par:
                    par[new] = sorted(set(par[new]) | set(par.pop(old)))
                else:
                    par[new] = par.pop(old)
                    order[order.index(old)] = new
            for n, ps in par.items():
                if old in ps:
                    par[n] = [new if x == old else x for x in ps]

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
            return core_names
        return {n for _, par in graphs.values() for n in par}
    for pack, sub, old_sup, action, new_parents, relation in table(REWRITES):
        if action == "keep":
            continue
        order, par = graphs[pack]
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
            if set(new) <= set(par[sub]):
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

    # A sibling's name a rewrite brought into a pack is written there as a
    # stub, as the build writes every borrowed name (UPPER.md §8.1).
    for pack, (order, par) in graphs.items():
        if pack == "core":
            continue
        used = set()
        for ps in par.values():
            for x in ps:
                if x.startswith(tuple(k + "(" for k in PINNABLE)):
                    continue                          # a family pin, not a name
                used |= {x[x.index("(") + 1:-1]} if "(" in x else {x}
        for name in sorted(used - set(par) - core_names - {"*"}):
            if any(name in g[1] for k, g in graphs.items() if k != pack):
                par[name] = ["*"]
                order.append(name)
                log.append(f"applied  {pack} borrows {name}")

    core = graphs["core"][1]
    for name, family, drop, *note in table(CORE_HEADS):
        pin = f"linear-dimension({family})"
        if name not in core:
            errors.append(f"core-heads: core has no {name!r}")
            continue
        if pin in core[name] and drop not in core[name]:
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
        for k, path in files.items():
            write_od(path, *graphs[k], header=header_of(path))


def _families():
    sys.path.insert(0, str(ROOT.parent / "ontodag" / "src"))
    from ontodag import dimensions
    return dimensions.known_families()


if __name__ == "__main__":
    main()
