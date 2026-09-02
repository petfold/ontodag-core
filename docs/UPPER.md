# The top of the ontology — design record

Status: 2026-09-02, evening. §1 and the decisions in §6 are agreed with
Peter; the pack in `build/core.od` is the current candidate for core v2.

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

| top | categories | names shared with `core` | cut |
|---|---|---|---|
| core | 194 | — | whole pack |
| wordnet | 44 | 7 | depth ≤ 3, cone ≥ 300 |
| sumo | 43 | 2 | `Merge.kif`, depth ≤ 3 |
| opencyc | 169 | 9 | depth ≤ 2, cone ≥ 1500 |
| bfo | 34 | 1 | whole (BFO 2020) |
| dolce | 36 | 3 | whole (DOLCE-Lite) |
| dul | 19 | 4 | DUL, depth ≤ 3 |
| schemaorg | 66 | 7 | depth ≤ 2, cone ≥ 3 |
| yago | 14 | 5 | YAGO 4, depth ≤ 2, cone ≥ 200 |

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

**BFO 2020** (34 classes, a tree): `entity` → `continuant` (independent /
specifically dependent / generically dependent) and `occurrent` (process,
temporal region, spatiotemporal region, process boundary). Rigorous, and
everything we would file is one of four leaves: `object`, `object
aggregate`, `process`, `generically dependent continuant` (information).
The rest is about boundaries, regions and qualities. A top for scientists,
not filers; useful as a check on our branch *claims*, useless as branches.

**DOLCE-Lite** (36 classes) and **DUL** (79): `particular` →
`endurant` / `perdurant` / `quality` / `abstract`; DUL flattens that to
`Object` (physical, social, agent) / `Event` / `Situation` /
`InformationEntity` / `Abstract`. DUL's top is the closest of the
philosophical tops to the current seven branches, and it is where the
`agent` and `information` readings come from. Note DOLCE-Lite hides its own
top edge inside an `owl:equivalentClass` intersection — the extractor reads
those, otherwise the ontology falls into four pieces.

**schema.org** (926 classes, 48 multi-parent): `Thing` → `Intangible` (277),
`Place` (208), `CreativeWork` (176), `Organization` (166), `Action` (115),
`MedicalEntity`, `Event`, `Product`, `Person`. Business-shaped and flat;
`Intangible` is where everything without a home went. Its middle level
(tickets, invoices, events, places, organizations) is the best-worded of
all the sources for the things people actually file.

**YAGO 4** (10,146 classes, 2,512 multi-parent): schema.org's top with
Wikidata classes cleaned and hung under it — the "schema.org top, Wikidata
below" plan, already executed by someone else, and a real DAG. Its five
roots are schema.org's; `Place` alone has 3,092 descendants.

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

## 4. Not yet extracted

Princeton Core WordNet's 3,299 nouns as a `.od` (the file is downloaded; the
cut needs the WordNet graph restricted to those synsets plus their ancestors).
SUMO's mid-level with the WordNet mapping applied. YAGO 4.5 if a public
download reappears.

## 5. First reading of the tops together

Three families of top exist, and they answer different questions:

- **Philosophical** (BFO, DOLCE, SUMO's upper file): *what kinds of thing
  exist* — continuant/occurrent, endurant/perdurant, physical/abstract.
  Small, defensible, and almost nobody files under them directly.
- **Lexical** (WordNet): *what words mean* — complete and multi-parent,
  with a top chosen for the dictionary, not for filing.
- **Practical** (schema.org, YAGO, DUL's middle): *what people describe* —
  places, organizations, events, creative works, products, persons.

The current `core` is a practical top with a philosophical excuse. §1 says
the top above the branches can be added later without cost, which suggests
shipping the practical branches now, worded from schema.org where it has
the word, checked for truth against BFO/DOLCE, and deciding the
philosophical roof slowly — or never.


## 6. Decisions taken (2026-09-02, with Peter)

Recorded in `align/review.tsv` (Peter's rulings), `align/claude-review.tsv`
(Claude's per-edge judgements), `align/overrides.tsv` (alignment),
`align/names.tsv` (names by synset) and `align/drop.tsv` (concepts left out).

1. **Single-witness edges**: Claude reads both glosses and votes; the vote is
   a witness like SUMO's, never a veto (two sources still carry an edge past
   a dissent), and Peter's `review.tsv` outranks everyone. Every direct
   WordNet-only edge in or into the pack was read (about 1,900 judgements,
   roughly one in six rejected). Cyc-only, YAGO-only and SUMO-only edges are
   *not* reviewed: those sources are second witnesses, nothing more.
2. **Roots**: the seven branches as aligned in `overrides.tsv`, plus
   `attribute` (with `state` and `feeling` beneath) and `possession`;
   `body-part ⊑ physical-object` and the physical `process ⊑ event` by
   ruling. `time` and `quantity` stay out: they are registry territory.
3. **Top-level claims**: vehicles, tools and instruments under `device`;
   documents are information only (the one-reading rule), never artifacts;
   vehicles are not containers; `organism ⊑ agent` rejected (a plant is not
   an agent); a conversation is communication, not information.
4. **Core v1's own claims** all kept on review; `business` is the enterprise,
   `business-studies` the subject.
5. **Disputes**: synonym pairs get no edge and lose one name (aim/goal,
   emotion/emotional-state, spirit/soul, ...); `field` and `yard` differ;
   `boat ⊑ watercraft`, `human ⊑ person`, `street ⊑ road`, `myth ⊑ fiction`,
   `program ⊑ software`, `note ⊑ document`, `city ⊑ settlement`,
   `collection ⊑ group`, `battle ⊑ military-action`, `line ⊑ text` rescued;
   `state ⊑ district`, `cheek ⊑ feature`, war/fight, cognition/property,
   universe/object, convention/situation all out.
6. **Names**: a sense that shares its word with another gets a hand-chosen
   name (`book-copy`, `prepared-dish`, `capital-city`), never a numbered or
   field-suffixed one; where the more-filed sense was the qualified one, it
   took the plain word (`accident`, `injection`, `match`, `notebook`,
   `seat`, `staff`, `claim`, `sign`, `mine`, `association`, `state`,
   `feeling`, `possession`, `process`, `procedure`). Review lines carry
   WordNet offsets so renames never strand a judgement.
7. **Quantities and the prelude** (Peter, 2026-09-02): the unit registry
   owns every dimension head (`weight`, `length`, `temperature`, ...) and
   every unit spelling (`mile`, `gallon`, `calorie`); the pack ships none of
   them as categories. It asserts the connection at kind level instead —
   `linear-dimension`, `count-dimension` and `calendar-dimension` are
   attributes (`align/extra-edges.tsv`), so every head and every value
   inherits it; `geo-dimension` is left out because a geo value is a place.
   The pack therefore presumes the prelude. Currency denominations
   (`dollar`, `penny`) are synonyms of the fiat pack's unit spellings and
   leave the pack too; `money`, `cash`, `coin` stay as kinds of possession.
   WordNet's `dimension` sense is renamed `spatial-extent` so it cannot
   merge with the registry's kind root.
