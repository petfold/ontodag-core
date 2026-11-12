"""The cross-connection trial on the animal branch (docs/UPPER.md §17,
question 52, option B).

    python3 tools/cross_trial.py [--standard strict|everyday] [--alone]

Reads align/trial-cross-classes.tsv (the classes named by a shared
quality), align/trial-cross-animal.tsv (one row per candidate edge, with
what Wikidata, WordNet's tree and the WordNet gloss say and how Claude read
it) and align/trial-cross-rulings.tsv (Peter's yes or no on the edges no
source speaks for), counts the candidates by what speaks for them, applies
the accepted ones to core and the biology pack in memory, and prints what
the branch then looks like and answers. Nothing is written and nothing is
shipped.

An edge is accepted when the reading says yes under the chosen standard
and a source says it too, Wikidata by its subclass statements, WordNet by
its tree or the gloss outright: two witnesses, as everywhere here. The
standard is strict unless `--standard everyday` asks for the other: a pack
states no edge that has a counterexample (Peter, 2026-11-12). Peter's
ruling stands above both: an edge he ruled yes is applied under either
standard, and one he ruled no never is. `--alone` also applies the edges
only the reading speaks for and he has not ruled on.
"""
import argparse
import csv
from pathlib import Path

from ontodag import packs, prelude
from ontodag.dag import OntoDAG

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = [
    ("mammals that live in water", ["aquatic-animal", "mammal"]),
    ("invertebrates of the sea", ["marine-animal", "invertebrate"]),
    ("warm-blooded animals that lay eggs",
     ["warm-blooded-animal", "egg-laying-animal"]),
    ("cold-blooded vertebrates", ["cold-blooded-animal", "vertebrate"]),
    ("birds that hunt", ["predator", "bird"]),
    ("birds that cannot fly", ["flightless-bird"]),
    ("domestic animals that eat plants", ["domestic-animal", "herbivore"]),
    ("fish that eat animals", ["carnivore", "fish"]),
    ("animals that chew the cud", ["ruminant"]),
    ("shellfish", ["shellfish"]),
]


def table(name):
    """The rows of a table in align/. A comment line starts with `#`; a
    spreadsheet that saved the file may have put a quote before it."""
    with open(ROOT / "align" / name, encoding="utf-8") as handle:
        lines = [line for line in handle
                 if not line.lstrip('"').startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def rulings():
    """(sub, sup) -> True, False or None for every edge of the ruling sheet:
    Peter's yes, his no, or no ruling yet. A ruling is `yes` or `no` (`y`,
    `n`), in any case, with anything after it as his remark; any other
    answer is a remark alone, and the edge waits."""
    sheet = {}
    for row in table("trial-cross-rulings.tsv"):
        words = (row["ruling"] or "").split()
        word = words[0].strip(".,;:!").lower() if words else ""
        sheet[row["sub"], row["sup"]] = (
            word[0] == "y" if word in ("yes", "y", "no", "n") else None)
    return sheet


def branch(dag):
    """The animal kinds: the cone of `animal` without the people filed
    under `human`, whose second parents are roles of persons."""
    cone = {n.name for n in dag.get_descendants(dag.nodes["animal"],
                                                computed=False)}
    people = {n.name for n in dag.get_descendants(dag.nodes["human"],
                                                  computed=False)}
    return cone - people


def parents(dag, name):
    return {p.name for p in dag.nodes[name].parents
            if dag.nodes.get(p.name) is p}


def several(dag, names):
    return sum(1 for name in names if len(parents(dag, name)) > 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--standard", choices=["strict", "everyday"],
                        default="strict")
    parser.add_argument("--alone", action="store_true",
                        help="apply the reading's own edges as well")
    args = parser.parse_args()
    classes, rows = table("trial-cross-classes.tsv"), table("trial-cross-animal.tsv")
    sheet = rulings()
    ruled = {edge: answer for edge, answer in sheet.items()
             if answer is not None}

    def sourced(row):
        return "y" in (row["wikidata"], row["tree"], row["gloss"])

    print(f"candidate edges: {len(rows)} onto {len(classes)} classes")
    print(f"  Wikidata's subclass statements say it: "
          f"{sum(r['wikidata'] == 'y' for r in rows)}; WordNet's tree: "
          f"{sum(r['tree'] == 'y' for r in rows)}; the gloss outright: "
          f"{sum(r['gloss'] == 'y' for r in rows)}; the gloss with a hedge: "
          f"{sum(r['gloss'] == 'hedged' for r in rows)}; no source: "
          f"{sum(not sourced(r) and r['gloss'] != 'hedged' for r in rows)}")
    for standard in ("strict", "everyday"):
        yes = [r for r in rows if r[standard] == "y"]
        print(f"  read {standard}: {len(yes)} hold; with a source as second "
              f"witness {sum(sourced(r) for r in yes)}, the reading alone "
              f"{sum(not sourced(r) for r in yes)}")
    print(f"  a source says it and the reading does not (everyday): "
          f"{sum(sourced(r) and r['everyday'] != 'y' for r in rows)}")
    print(f"  said of the kind but not true of all of it (typical, not "
          f"everyday): {sum(r['typical'] == 'y' and r['everyday'] != 'y' for r in rows)}")
    print(f"  true in the everyday sense, with a known exception (everyday, "
          f"not strict): {sum(r['everyday'] == 'y' and r['strict'] != 'y' for r in rows)}")
    alone = {(r["sub"], r["sup"]) for r in rows
             if r["everyday"] == "y" and not sourced(r)}
    yes = sum(answer for edge, answer in ruled.items() if edge in alone)
    print(f"  Peter's rulings on the {len(alone)} edges the everyday reading "
          f"alone speaks for: {yes} yes, {len(alone & set(ruled)) - yes} no, "
          f"{len(alone - set(ruled))} waiting")
    candidates = {(r["sub"], r["sup"]) for r in rows}
    for edge in sorted((set(ruled) - alone) & candidates):
        print(f"  and on another candidate: {edge[0]} ⊑ {edge[1]}, "
              f"{'yes' if ruled[edge] else 'no'}")
    if alone - set(sheet) or set(sheet) - candidates:
        print(f"  the ruling sheet and the table have parted: missing from "
              f"the sheet {sorted(alone - set(sheet))}, in the sheet and no "
              f"candidate {sorted(set(sheet) - candidates)}")

    dag = OntoDAG()
    prelude.apply(dag)
    for name in ("core", "biology"):
        dag.merge(packs.adoption_dag(dag, name))
    before = branch(dag)
    print(f"\nthe branch before: {len(before)} kinds, "
          f"{several(dag, before)} with several parents")

    for row in classes:
        dag.put(row["name"], row["parents"].split())

    def accepted_by(row):
        answer = ruled.get((row["sub"], row["sup"]))
        if answer is not None:
            return answer
        return row[args.standard] == "y" and (args.alone or sourced(row))

    accepted = [r for r in rows if accepted_by(r)]
    for row in accepted:
        dag.put(row["sub"], [row["sup"]])
    for (sub, sup), answer in sorted(ruled.items()):
        if not answer and sup in {a.name for a in dag.get_ancestors(
                sub, computed=False)}:
            print(f"ruled no, yet it follows from the edges applied: "
                  f"{sub} ⊑ {sup}")
    stored = [r for r in accepted if r["sup"] in parents(dag, r["sub"])]
    after = branch(dag)
    names = {row["name"] for row in classes}
    kinds = after - names
    reached = sum(1 for name in kinds if names & {
        a.name for a in dag.get_ancestors(name, computed=False)})
    how = "the reading alone included" if args.alone else "two witnesses"
    if ruled:
        how += ", with Peter's rulings"
    print(f"applied ({args.standard}, {how}): {len(accepted)} edges, "
          f"{len(stored)} stored and "
          f"{len(accepted) - len(stored)} implied by others")
    print(f"the branch after: {len(after)} nodes, {several(dag, after)} with "
          f"several parents; {reached} of the {len(kinds)} kinds now stand "
          f"under a class named by a quality")
    for row in classes:
        cone = {n.name for n in dag.get_descendants(dag.nodes[row["name"]],
                                                    computed=False)}
        print(f"  {row['name']}: {len(cone & kinds)} kinds below")
    print("\nten questions the branch could not be asked before:")
    for text, terms in QUESTIONS:
        found = sorted({n.name for n in dag.get(terms)} & kinds)
        print(f"  {text} ({' '.join(terms)}): "
              f"{', '.join(found) if found else 'nothing'}")


if __name__ == "__main__":
    main()
