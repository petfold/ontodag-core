"""Turn the everyday-sense review's decisions into step7 rulings.

    python3 tools/sense_rulings.py

Reads `align/sense-review-v14.tsv`, one decision per row: pack, name,
action, args, confidence, reason, reviewer, apply, check. It writes
`align/rulings-v14-ysenses.tsv`, the last rulings file step7 replays, and
the generated section of `align/glosses-v14.tsv`. Only rows with
`apply = yes` are written; the others stay on the sheet for Peter.

Actions, in the review's vocabulary (see tools/sense_audit.py):

- `move OLD NEW...`: a parent is replaced.
- `cut OLD`: a parent is removed.
- `parent+ NEW...`: parents are added.
- `resense WN30 NEW...`: the node takes another sense. Its parents become
  NEW, and its gloss becomes WN30's.
- `split Q | WN30 NEW...`: the node's sense moves to the new name Q, which
  takes its parents and children. The plain name takes WN30 under NEW.
- `rename NEW`: the same sense under a new name. Its parents and children
  move, and the old name is dropped.
- `drop`: the node leaves.

The decisions are applied, in order, to a copy of the built graphs as
they were before the pass (`BASE`), and
every row is written from the state at that point, as step7 will meet it.
The order:
1. Renames and splits come first, each after the row that frees the name it
   takes: the drop of a rare-sense holder, or another rename
   (`pot` → marijuana before cooking-pot → pot).
2. Then the moves, cuts and resenses.
3. Then the remaining drops, once their children have moved.

A later row that names a renamed node follows it to its new name, and a
row that no longer applies is reported, not written. Splits and renames
are written as rulings (add, move, drop), not renames, because renames run
before every rulings file and the earlier files name the old senses.
"""
import argparse
import csv
import json
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "align/sense-review-v14.tsv"
OUT = ROOT / "align/rulings-v14-ysenses.tsv"
GLOSSES = ROOT / "align/glosses-v14.tsv"
MARK = "# --- the everyday-sense pass, 2026-10-22 (tools/sense_rulings.py writes this section) ---"


# The built files the pass starts from: the commit before its first rulings.
# The decisions were read against them, and step7 replays the rulings on top
# of everything before them, so the rows are written from this state.
BASE = "5c21408"


def built(store):
    return "build/core.od" if store == "core" else f"packs/{store}/build/{store}.od"


def lines(store):
    import subprocess
    return subprocess.run(["git", "show", f"{BASE}:{built(store)}"], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.splitlines()


def graphs():
    """{store: {name: [parents]}} of the built files, terms included."""
    stores = ["core"] + [p.parent.parent.name for p in sorted((ROOT / "packs").glob("*/build/*.od"))]
    out = {}
    for store in stores:
        par = {}
        for line in lines(store):
            if line.startswith("#") or not line.strip():
                continue
            tokens = shlex.split(line)
            par[tokens[0]] = tokens[1:]
        out[store] = par
    return out


def metas(store):
    out = {}
    for line in lines(store):
        if line.startswith("#:meta "):
            _, name, blob = shlex.split(line)
            out[name] = json.loads(blob)
    return out


class Sim:
    """The graphs as the rulings change them, and the rows that do it."""

    def __init__(self):
        self.g = graphs()
        self.rows, self.glosses, self.errors = [], [], []
        self.meta = {}

    def exists(self, name):
        # a pack's "*" line is a stub or the pack's own top-level name: either way the name is there
        return any(name in par for par in self.g.values())

    def owner(self, name):
        return next((s for s, par in self.g.items() if name in par and par[name] != ["*"]), None)

    def plain(self, store, name):
        return [p for p in self.g[store].get(name, []) if p != "*"]

    def children(self, name):
        """(store, child, parent-as-written) for every filing under `name`,
        a term naming it included (about(name), in(name))."""
        out = []
        for store, par in self.g.items():
            for n, ps in par.items():
                for x in ps:
                    if x == name or ("(" in x and x.endswith(f"({name})")):
                        out.append((store, n, x))
        return out

    def emit(self, store, sub, action, old, new, note):
        self.rows.append((store, sub, action, old or "-", new or "-", note))
        par = self.g[store]
        if action == "add":
            par[sub] = new.split()
        elif action == "move":
            ps = [p for p in par[sub] if p != old] + [x for x in new.split() if x not in par[sub]]
            par[sub] = [p for p in ps if p != "*"] or ["*"]
        elif action == "cut":
            par[sub] = [p for p in par[sub] if p != old]
        elif action == "parent+":
            par[sub] = [p for p in par[sub] if p != "*"] + [x for x in new.split() if x not in par[sub]]
        elif action == "drop":
            del par[sub]

    def gloss_of(self, store, name):
        if store not in self.meta:
            self.meta[store] = metas(store)
        return self.meta[store].get(name, {})

    def reparent(self, store, name, new, note):
        """The node's parents become `new` (its terms stay)."""
        plain = [p for p in self.plain(store, name) if "(" not in p]
        gone = [p for p in plain if p not in new]
        added = [x for x in new if x not in plain]
        if not gone:
            if added:
                self.emit(store, name, "parent+", "", " ".join(added), note)
            return
        if added:
            self.emit(store, name, "move", gone[0], " ".join(added), note)
        else:
            self.emit(store, name, "cut", gone[0], "", note)
        for p in gone[1:]:
            self.emit(store, name, "cut", p, "", "the old sense's parent")

    def take_over(self, store, name, holder, note, keep_terms):
        """`holder` (a rare sense with nothing under it) takes `name`'s sense
        in place: its parents become name's, name's children move to it.
        Re-sensing the holder, not dropping and re-adding it, keeps the rows
        idempotent: a rerun finds every one done."""
        self.reparent(store, holder, self.plain(store, name) or ["*"], note)
        for st, child, written in self.children(name):
            if "(" in written:
                if keep_terms:
                    continue
                head = written[:written.index("(")]
                self.emit(st, child, "move", written, f"{head}({holder})", f"{name} is renamed {holder}")
            elif child != holder:
                self.emit(st, child, "move", name, holder, f"follows {name}'s sense to {holder}")
        old = self.gloss_of(store, name)
        if old:
            wn = old.get("wn30", "")
            self.glosses.append((holder, wn[:-2] if wn else "-", "" if wn else old.get("gloss", "")))

    def drop(self, store, name, note):
        if name not in self.g[store]:
            self.errors.append(f"drop {name}: not in {store} any more")
            return False
        kids = self.children(name)
        if kids:
            self.errors.append(f"drop {name}: it has children {[k[1] for k in kids][:4]}")
            return False
        self.emit(store, name, "drop", "", "", note)
        return True

    def relocate(self, store, name, qualified, note, keep_terms):
        """`name`'s sense, parents and children move to `qualified`."""
        self.emit(store, qualified, "add", "", " ".join(self.plain(store, name)) or "*", note)
        for st, child, written in self.children(name):
            if "(" in written:
                if keep_terms:
                    continue
                head = written[:written.index("(")]
                self.emit(st, child, "move", written, f"{head}({qualified})", f"{name} is renamed {qualified}")
            elif child != qualified:
                self.emit(st, child, "move", name, qualified, f"follows {name}'s old sense to {qualified}")
        old = self.gloss_of(store, name)
        if old:
            wn = old.get("wn30", "")
            self.glosses.append((qualified, wn[:-2] if wn else "-", "" if wn else old.get("gloss", "")))


def main():
    argparse.ArgumentParser(description=__doc__.split("\n")[0]).parse_args()
    sim = Sim()
    sheet = [r for r in csv.DictReader((l for l in open(SHEET) if not l.startswith("#")),
                                       delimiter="\t") if r.get("apply") == "yes"]
    for r in sheet:
        r["pack"] = r.get("pack") or "core"
    drops = {(r["pack"], r["name"]): r for r in sheet if r["action"] == "drop"}
    renames = [r for r in sheet if r["action"] in ("rename", "split")]
    by_source = {(r["pack"], r["name"]): r for r in renames}
    moved = {}                                   # old name -> new name (renames)
    done = set()

    def target(r):
        if r["action"] == "rename":
            return r["args"].split()[0]
        return r["args"].split("|")[0].strip()

    retaken = {(r["pack"], target(r)) for r in renames}
    vacated = set()                              # names whose sense moved away, node kept

    def apply_rename(r, path=()):
        key = (r["pack"], r["name"])
        if key in done or key in path:
            return
        done.add(key)
        store, s, q = r["pack"], r["name"], target(r)
        over = False                             # q is a holder that takes s's sense
        if sim.exists(q):
            holder = sim.owner(q) or "core"
            if (holder, q) in by_source:         # the holder's own rename frees it
                apply_rename(by_source[(holder, q)], path + (key,))
                over = (holder, q) in vacated and holder == store
            elif (holder, q) in drops and holder == store and not sim.children(q):
                done.add((holder, q))            # the drop's holder is re-sensed instead
                over = True
            elif (holder, q) in drops and not sim.children(q):
                done.add((holder, q))            # another store's holder goes first
                sim.drop(holder, q, drops[(holder, q)]["reason"])
            if not over:
                sim.errors.append(f"{r['action']} {s}: {q} exists")
                return
        if s not in sim.g[store]:
            sim.errors.append(f"{r['action']} {s}: not in {store} any more")
            return
        note = f"{s}'s {'old ' if r['action'] == 'split' else ''}sense, under the name {q}"
        if over:
            sim.take_over(store, s, q, note, keep_terms=r["action"] == "split")
        else:
            sim.relocate(store, s, q, note, keep_terms=r["action"] == "split")
        if r["action"] == "rename":
            moved[s] = q
            if (store, s) in retaken:            # another rename takes the name: keep the node
                vacated.add((store, s))
            else:
                sim.drop(store, s, f"renamed {q}: {r['reason']}")
        else:
            tail = r["args"].split("|")[1].split()
            wn30, new = tail[0], tail[1:]
            sim.reparent(store, s, new, r["reason"])
            sim.glosses.append((s, wn30, ""))   # "-": no synset fits, so no gloss

    for r in renames:
        apply_rename(r)

    def follow(name):
        seen = set()
        while name in moved and name not in seen:
            seen.add(name)
            name = moved[name]
        return name

    for r in sheet:
        action = r["action"]
        if action in ("rename", "split", "drop"):
            continue
        store, name = r["pack"], follow(r["name"])
        args = [follow(a) if not a.isdigit() else a for a in r["args"].split()]
        if name not in sim.g[store]:
            sim.errors.append(f"{action} {name}: not in {store} any more")
            continue
        have = sim.plain(store, name)
        targets = (args[1:] if action in ("move", "resense") else args if action == "parent+" else [])
        missing = [t for t in targets if not sim.exists(t[t.index("(") + 1:-1] if "(" in t else t)]
        if missing:
            sim.errors.append(f"{action} {name}: {missing} no longer exist")
            continue
        if action == "move":
            if args[1:] == [args[0]]:
                continue                         # a rename made it a move to itself
            if args[0] not in have:
                sim.errors.append(f"move {name}: {args[0]} is no longer a parent ({have})")
                continue
            sim.emit(store, name, "move", args[0], " ".join(args[1:]), r["reason"])
        elif action == "cut":
            if args[0] not in have or not [p for p in have if p != args[0]]:
                sim.errors.append(f"cut {name} ⊑ {args[0]}: not a parent, or the only one ({have})")
                continue
            sim.emit(store, name, "cut", args[0], "", r["reason"])
        elif action == "parent+":
            sim.emit(store, name, "parent+", "", " ".join(args), r["reason"])
        elif action == "resense":
            sim.reparent(store, name, args[1:], r["reason"])
            sim.glosses.append((name, args[0], ""))   # "-": no synset fits, so no gloss
        else:
            sim.errors.append(f"{name}: unknown action {action!r}")

    for key, r in sorted(drops.items()):
        if key in done:
            continue
        store, name = key
        if name in sim.g[store]:
            sim.drop(store, name, r["reason"])

    with open(OUT, "w") as f:
        f.write("# The everyday-sense pass (Peter, 2026-10-22): a plain name means its everyday sense; several parents\n"
                "# mean AND; an edge is wrong when any ancestor it brings in is false; core keeps clear, unchanging things.\n"
                "# Written by tools/sense_rulings.py from align/sense-review-v14.tsv (the rows marked apply = yes).\n")
        f.write("pack\tsub\taction\told\tnew\tnote\n")
        for row in sim.rows:
            f.write("\t".join(row) + "\n")
    text = open(GLOSSES).read()
    text = text.split("\n" + MARK)[0].rstrip("\n") + "\n"
    if sim.glosses:
        text += MARK + "\n" + "".join(f"{n}\t{w}\t{g}\n" for n, w, g in sim.glosses)
    open(GLOSSES, "w").write(text)
    print(f"{OUT.relative_to(ROOT)}: {len(sim.rows)} rows from {len(sheet)} decisions; "
          f"{len(sim.glosses)} glosses; {len(sim.errors)} decisions not applied", file=sys.stderr)
    for e in sim.errors:
        print("SKIPPED", e, file=sys.stderr)


if __name__ == "__main__":
    main()
