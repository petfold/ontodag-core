# The top of the ontology — design record

Status: discussion draft, 2026-09-02. Nothing here is decided.

## 1. What a version commits us to

OntoDAG's structure decides this before any taxonomy question does. Items
attach to categories *by name*; nothing stored about an item changes when
the structure above it changes. Under complete transitive reduction and
merge-as-union (ontodag EVOLUTION.md §1), the changes to a pack fall in two
classes:

| change | propagates by merge? | why |
|---|---|---|
| add a node anywhere | yes | plain addition |
| insert a level between existing nodes (`dog ⊑ canid ⊑ mammal`) | yes | the old edge becomes redundant; reduction drops it on every replica |
| deepen the top (put `continuant` above today's roots) | yes | addition again |
| retract a false edge | **no** | a peer still holding it re-adds it; needs `move` in every store |
| rename | **no** | names are identity; it is a new node plus refiling |

So a version commits exactly **the names** and **the truth of every edge**.
It never commits coverage or granularity. Consequences for how to build:

1. A small pack is the *safe* pack. "Too small" is fixed additively forever;
   "wrong" is not.
2. When unsure of an edge, leave siblings under a coarser parent. Refinement
   later is free; retraction is not.
3. Names are the real one-way door. Spend the review time there: plain,
   singular, unambiguous, disambiguated in the name where the word is
   polysemous (`bank` never appears; `river-bank` may).
4. Versions should be **monotone** (v(n+1) ⊇ v(n)). A retraction, when one
   is unavoidable, ships as an explicit list that `odag pack` applies with
   `reclassify` — a mechanism to build, not yet built.

## 2. The sources, extracted

`tools/build.sh` produces four tops as `.od` files. First numbers:

| top | categories | shared names with `core` | cut |
|---|---|---|---|
| core (ontodag 0.18.1 + review) | 194 | — | whole pack |
| WordNet 3.0 nouns | 44 | 7 | depth ≤ 3, cone ≥ 300 |
| SUMO `Merge.kif` | 43 | 2 | depth ≤ 3 |
| OpenCyc 4.0 OWL | 169 | 9 | depth ≤ 2, cone ≥ 1500 |

No name is shared by all three sources at the top. That is the vocabulary
problem in one line: the sources agree on the *split* far more than on the
words, so the comparison has to be done on structure, by aligning nodes, not
on names.

**WordNet** (82,115 noun synsets, 1,422 with two hypernyms): complete, a real
DAG, lexicon-first. The top two levels are philosophy (`entity` →
`physical_entity` / `abstraction`), with known oddities (`event` under
`psychological_feature`, `person` under `causal_agent` and `organism`).
Everything from level three down is good, and Core WordNet gives a
principled 3,299-noun cut of it.

**SUMO** (845 subclass claims in the upper file, 2,117 more in the mid-level,
82,173 noun synsets mapped): a designed top — `Entity` → `Physical`
(`Object`, `Collection`, `Process`, `PhysicalSystem`) / `Abstract`
(`Quantity`, `Attribute`, `SetOrClass`, `Relation`, `List`, `Proposition`).
Half of its top is *logic's* furniture (relations by arity, sets, lists,
propositions), which OntoDAG has no use for as categories. The WordNet
mapping is the asset: it lets WordNet's breadth hang under a designed top.

**OpenCyc** (116,822 classes, 52,422 multi-parent, 94 roots): the designed
upper ontology is in there but the export buries it under generated union
classes ("the union of { valve prostheses, information }"), the AURA biology
import and underspecified-location scaffolding. Contains mutual-subclass
pairs (`human`/`person`). Read Cyc's published upper-level diagram for its
decisions; do not quarry this file for nodes.

## 3. Open questions

1. Which top split: BFO/SUMO's physical/abstract, WordNet's, or the current
   seven branches with a deepenable top? (§1 says deepening later is free,
   which argues for shipping branches and deciding the top above them
   slowly.)
2. What is the cut for coverage: Core WordNet's 3,299 nouns filtered by the
   admission rule? SUMO's mid-level? Both aligned?
3. Alignment method for the comparison: by name (fails, see §2), by SUMO's
   WordNet mapping, by hand for the top 50?
4. Naming convention: WordNet lemma, SUMO term, or our own, and the
   polysemy rule.
5. The retraction mechanism for pack versions (§1 item 4).

## 4. Still to fetch

schema.org (JSON-LD, ~800 types), YAGO 4 taxonomy (schema.org top over
cleaned Wikidata classes — the plan already built by someone else), BFO
(~35 classes), DOLCE (~100), Princeton Core WordNet noun cut as a `.od`.
