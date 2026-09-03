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
8. **Cognition** (Peter, 2026-09-02): a tenth root, WordNet's `cognition`
   ("the psychological result of perception and learning and reasoning"):
   belief, concept, idea, attitude, skill, method, memory, the senses.
   Mythical beings and legal rights, which WordNet files under belief and
   concept, stay out. `field-of-study ⊑ cognition` is true and held back:
   it would fold one root under another; Peter's call.

## 7. Policy: the sciences — hinges in core, contents in packs

A concept belongs in core when we could not conceivably be wrong about it
*and* a non-specialist files under it. Applied to a science, that puts the
**hinge** in core — the highest node of the domain that ordinary documents
get filed under — and the **content** in a pack. The hinge is in core so
that the domain pack merges onto a shared anchor instead of inventing its
own top; the content is in a pack because it has its own source, its own
versioning, and specialist names.

| science | in core (hinges) | in a pack (content) | source for the pack |
|---|---|---|---|
| mathematics | `mathematics`, `logic`, `number`, `set` | structures and theorems, **all qualified** (`mathematical-group`, never `group`) | hand-written; small |
| physics | `physics`, `particle`, `atom`, `electron`, `radiation`, `process` | particles, fields, laws | Wikidata P279 (physics) |
| chemistry | `substance`, `material`, `chemical`, `compound`, `chemical-element`, `chemical-reaction`, `water`, `metal`, the everyday elements | the 118 elements, compounds | IUPAC / PubChem |
| biology | `organism`, `animal`, `plant`, `fungus`, `bacterium`, `virus`, `cell`, `species`, `body-part`, the everyday animals and plants | the tree of life | WordNet's organism cone, or NCBI taxonomy |
| medicine | `medicine`, `disease`, `illness`, `symptom`, `injury`, `medication`, `drug`, `doctor`, `nurse`, `hospital`, `surgery`, `therapy`, `diagnosis`, `infection`, `wound`, `cancer`, `fever`, `health` — all already in core | specialties, diseases, symptoms, procedures, instruments, drugs, practitioners | WordNet medicine/pathology/psychiatry topics and the bounded cones + **Wikidata** (27 verified roots); ICD/SNOMED stay a possible later pack |
| AI / machine learning | `computer-science`, `algorithm`, `software`, `automaton`, `agent`, `information`, `concept` — all in core | the field's own vocabulary: paradigms, models, algorithms, architectures, agents, robots, alignment | Wikidata P279 from a verified label list; WordNet is nearly silent |
| economics / finance / logistics / crypto | `commerce`, `trade`, `money`, `currency`, `payment`, `price`, `cost`, `debt`, `loan`, `bank`, `contract`, `insurance`, `merchant`, `market`, `transport`, `delivery`, `container` — all in core | instruments, markets, accounting, logistics, Bitcoin and Ethereum | WordNet's commerce cones + Wikidata + hand-asserted crypto/logistics vocabulary; the macroeconomic half of the field deliberately left out |
| computing | `computer-science`, `software`, `computer-program`, `application`, `hardware`, `computer`, `computer-network`, `internet`, `web-site`, `code`, `information`, `interface`, `chip` — all in core | the field's vocabulary: paradigms, languages (the major ones as categories, on Peter's list), compilers and tools, data types and structures, algorithms, OS and Linux, hardware, networks and protocols, the web, databases incl. functional/immutable and decentralized storage, distributed systems and P2P, IR, information theory, semantic web and KR, open source, Wikipedia/Wikidata, file formats | WordNet's computer-science topic and ~60 cones; ~970 Wikidata items resolved by exact-label SPARQL and typed lookups; ~70 hand-asserted classes and Swarm/recordstore-shaped concepts |

Two things are not categories at all and belong to neither: **quantities**
(energy, force, temperature, length) are dimensions, owned by the unit
registry and reaching `attribute` through the three kind-level edges of §6.7;
and **numbers** are values, never nodes.

The test at the boundary is the **name**. If the plain English word is
unambiguous and a layperson reaches for it, the concept may sit in core
(`planet`, `cell`, `disease`). If the word needs a qualifier to be safe, it
belongs in a pack where the qualifier is the convention. The change
asymmetry (§1) makes the choice forgiving in one direction only: a hinge
left out of core can be added later, additively; a wrong one shipped is a
one-way door. **When unsure, pack.**

Packs derived from a source live in `packs/<name>/` in this repo, built by
the same tools (extract → align to the core hinge → consensus where a
second source exists, review where not), each with its own golden root.
The first should be chemistry from IUPAC: small, authoritative, and it
proves the pattern before biology's tree of life tests its scale.


## 8. Packs built so far (2026-09-03)

| pack | concepts | sources | hinges in core |
|---|---|---|---|
| physics | 197 | WordNet physics/astronomy topics, the particle cone; 12 new unit heads under `linear-dimension` | particle, concept (physical-law, theory), natural-event (physical-phenomenon), event, place, attribute |
| mathematics | 614 | WordNet mathematics/statistics/geometry/logic topics and cones; **Wikidata** (bounded P279 pulls, `tools/fetch_wikidata.py`, 227 roots) for the skeleton: algebraic structures, number types, relations, sets, spaces, graph theory, mathematical logic, order theory and Formal Concept Analysis, **discrete mathematics** (combinatorics, number theory, automata, coding theory, designs) and **cryptography** (primitives, ciphers, hash functions incl. SHA-2/Keccak, signatures incl. ECDSA, MACs, KDFs, key exchange, zero-knowledge proofs, commitments, Merkle trees, content addressing, blockchain, cryptanalysis) — the vocabulary ontodag's own certificates, provenance and Swarm layer are described in | concept (mathematical-set, mathematical-relation, mathematical-structure, expression, algorithm), cognition (statistic), event/procedure (mathematical-operation), shape, mathematics, number, cryptography ⊑ field-of-study |
| chemistry | 248 | WordNet chemistry topic, the element cone, hinge synsets (molecule, compound, solution, material, ion, polymer, mixture, alloy, catalyst, bond); **Wikidata** for 16 roots (element, reaction, bond, functional group, molecule, ion, acid, base, polymer, state of matter, mixture, alloy, mineral — and `chemical compound`, `chemical substance`, `medication` label-only, since each has tens of thousands of direct subclasses); 2 new unit heads (`amount-of-substance`, `catalytic-activity`) | substance, material, chemical, compound, chemical-element, natural-event (chemical-bond), collection (chemical-group), information (periodic-table), concept (theories), number (equilibrium-constant), attribute |
| biology | 345 | WordNet biology/genetics/botany/physiology/ecology topics, the cell and gene cones, hinge synsets (enzyme, nucleic acid, DNA, chromosome, metabolism, ecosystem, hormone, biological process, taxonomic group, plant part); **Wikidata** for 17 roots (organism, cell to depth 2, enzyme, the kingdoms, virus, chromosome, metabolism, biological process to depth 2, strain, taxon, ecosystem, nucleic acid — `gene` and `protein` label-only: 453,793 and 769,212 direct subclasses, every named gene and protein) | organism, cell, body-part (plant-part hangs here: "any part of an organism"), nucleic-acid, taxonomic-group ⊑ concept, natural-event, attribute, group (ecosystem; `system` is unplaced in core), physical-object |
| medicine | 1048 | WordNet topics (medicine, pathology, psychiatry, surgery, dentistry, pharmacology, immunology, epidemiology), bounded cones (medical science, medical procedure, therapy, injury, infection, mental illness, syndrome, cancer, medical instrument, antibiotic, vaccine, health professional, hospital), and the **`children` source kind** — a synset plus its direct hyponyms — for the three cones too big to take whole (disease 605, symptom 468, medication 512); **Wikidata** for 27 roots verified by label (disease, symptom, clinical sign, syndrome, infectious disease, cancer, mental disorder, cardiovascular disease, injury, medicine, medical specialty to depth 2, procedure, surgery, test, diagnosis, imaging, therapy, anaesthesia, medication, vaccine, antibiotic, analgesic, medical device, physician, health professional, hospital) | medicine, disease, illness, symptom, injury, medication, drug, doctor, nurse, hospital, condition, state, information, act, procedure, person, natural-event, physical-object, tissue |
| ai | 676 | **Wikidata-driven** — WordNet's `artificial intelligence` cone has four nouns, so WordNet contributes only the hinges it has (AI, robotics, machine translation, NLP, cybernetics, information science, computational linguistics, algorithm, heuristic, data mining, control system, sensor, servo, game theory, the CS ontology); ~440 Wikidata roots resolved from a label list by two search passes, every QID checked against its description (the search returned a cichlid fish for "medical device", a warship for "therapy", the Google OS for "android"), then ~220 descendants picked from the fetched neighbourhood. GOFAI (symbolic AI, expert systems, logic programming, planning, search, knowledge representation, the frame problem, situation calculus, blackboard and subsumption architectures, GOFAI vs. Nouvelle AI), machine learning (paradigms, models, algorithms, learning theory, evaluation, training internals), neural networks (architectures from perceptron to transformer, Hopfield and Boltzmann, sparse distributed memory), robotics, NLP, computer vision, agents and multi-agent systems, alignment and safety, ethics and governance, cognitive-science positions (connectionism, embodied cognition), network science, control theory, artificial life. Instances excluded (ChatGPT, Deep Blue, ELIZA, WordNet, GPT-3). | artificial-intelligence ⊑ computer-science (WordNet), then hubs by ruling: `ai-model ⊑ concept` (every model architecture hangs there), `statistical-model ⊑ concept`, `algorithm ⊑ procedure`, `dataset ⊑ information`, `intelligent-agent ⊑ agent`, `automaton` (core) for robots, `software` for systems, `field-of-study`/`mathematics`/`engineering`/`law`/`management` for the disciplines |
| economics | 1125 | Markets, finance, trading, investing, accounting, payments, insurance, contracts, logistics, Bitcoin and the Ethereum ecosystem. **Scope rule (Peter): only the universally accepted parts — no macroeconomics, no government-driven economics (tax, monetary policy, welfare), no Solana or other shitcoins; if in doubt, leave it out.** WordNet: the commerce, payment, cost, income, debt, loan, credit, security, bond, stock, share, insurance, fund, price, fee, contract, merchant, carrier, transport and delivery cones (~150 agriculture/industry/government/gambling/illicit-trade leftovers dropped by hand); **Wikidata**: ~520 roots resolved by exact-label SPARQL (the search API had slowed to 4 s a term) and read against descriptions; **hand-asserted** via `extra-edges.tsv` the ~80 concepts Wikidata has no item for — mempool, hash rate, halving, block reward, Lightning channels, gas, ERC-721, rollups, validators, the Beacon Chain, MEV, account abstraction, and Swarm's postage batches and chunks. | financial-services, commerce, commercial-trade, monetary-exchange, trading, investing, contract, legal-document, payment, payment-amount, purchase-price, income, expense, fee, debt, loan, credit, share-capital, bond, fund, merchant, transportation, transport, possession, information, concept, procedure, act, event, state, organization, company, software, device, container, vehicle, ship, aircraft, building, crime, fraud, agent, person, professional, management, economics, law |
| computing | 1370 | Peter's list (2026-09-03): computing, CS, software engineering, programming languages and concepts, databases incl. functional and Swarm, distributed systems and P2P, web, IR, information theory, networks, Internet, semantic web, KR, knowledge graphs, algorithms outside AI, open source, Linux, Wikipedia/Wikidata, ontologies, data structures, protocols, file formats. WordNet: the computer-science topic plus ~60 cones (software, program, language, code, database, computer, network, hardware, memory device, peripheral, file, data processing, telecommunication, protocol, subroutine, instruction, UI, compiler, OS, email …); everyday lists, telephony, broadcasting, writing systems, recorded music and arithmetic that the cones drag in dropped by hand (~130). **Wikidata**: ~970 items resolved by exact-label SPARQL, the ambiguous ones by type-constrained lookups and the entity-search API; **instances deliberately included** as categories where Peter asked (Linux, Git, Wikipedia, the major languages, protocols, formats) — they hang by P31 in Wikidata, so every one of them, and most abstract concepts whose Wikidata parent is unnamed here, is placed by ruling (~1,150). **Hand-asserted** (`extra-edges.tsv`): the intermediate classes Wikidata lacks or names only as instances' types (image/audio/document/archive/serialization/font file formats, system and server software, networking hardware, the protocol layers, `technical-standard`, `knowledge-organization-system`, `model-of-computation`), and the storage vocabulary this project lives in — `authenticated-data-structure`, `merkle-dag`, `content-identifier`, `append-only-log`, `immutable-database`, `versioned-database`, `functional-database`, `local-first-software`, `decentralized-storage` (shared with economics' `swarm-storage`). | software, computer-program, application, hardware, computer, digital-computer, computer-network, internet, web-site, code, information, interface, chip, document, message, symbol, list, collection, dataset, record, method, procedure, process, activity, practice, skill, property, quantity, concept, rule, law, organization, machine, device, artifact, engineering, mathematics, communication, telecommunication (WordNet) |

Three lessons from the Wikidata stage. **Verify every root QID by label
before walking it**: four of the first thirty-three were wrong (metabolism
was biotechnology, ecosystem a Swiss district, nucleic acid methane, base
inorganic chemistry) and the walk gives no warning — it just pulls the wrong
cone. **Some roots cannot be walked**: `chemical compound` returned 89 MB of
direct subclasses, `gene` 453,793 and `protein` 769,212 — Wikidata files
every named instance-class under them; such roots get depth 0 (label only)
and `tools/fetch_wikidata.py` now caps a level at 3,000 children and says so.
**Wikidata's label collides with the everyday word more often than WordNet's
sense does**: `clique`, `edge`, `filter`, `region`, `diameter` all arrived
under the taxonomic rank `subclass`; a chemical `indicator` under `sign`;
`forest`, `desert`, `marsh` under `ecosystem` — every such edge was rejected
on the WordNet gloss, never on the label.

Two lessons from the mathematics pack. **Wikidata's habit is the reverse of
WordNet's**: WordNet files parts as kinds, Wikidata inherits by forgetting
structure (a field is an abelian group, complex numbers are a totally ordered
set); every such edge was rejected — a thing is filed as what it is. And
**mathematics never takes an everyday word**: `mathematical-set`,
`mathematical-group`, `mathematical-graph`, `graph-clique`, `logical-negation`.
Rulings proposed for Peter sit in each pack's `align/review.tsv`.

## 9. The second pass (2026-09-03, with Peter)

Peter noticed `acyclic-graph ⊑ undirected-graph` in the mathematics pack. The
edge is Wikidata's definition of Q3115453 (an undirected graph without
cycles, i.e. a forest) and the ruling behind it was Claude's, written into
`review.tsv` — nominally Peter's file. Three things followed.

**Attribution.** Rulings Claude made under Peter's standing permission now
live in `claude-ruling.tsv` per pack and count as the witness `claude-ruling`;
`review.tsv` holds only Peter's lines (in the packs: `theory ⊑ concept` and
`elementary-particle ⊑ particle`). Peter's line wins where both speak. A
ruling may also place a concept that core left unplaced (`gene`). In
`claude-review.tsv` the last verdict on a pair wins, so a second reading can
overturn a first.

**A second reading of every single-source edge** — 1,109 edges whose only
independent source was one of WordNet, Wikidata or SUMO, read against both
glosses. Forty were rejected and re-ruled, four concepts dropped, ~105
renamed. The kinds of error found, so the next pass knows where to look:

- *WordNet's own slips*: `heterozygote ⊑ zygote` (an organism, not a cell),
  `leukocyte ⊑ free-phagocyte` (lymphocytes are neither), `covariance ⊑
  variance`, `standard-deviation ⊑ variance`, `mathematical-analysis ⊑
  calculus` (inverted), `antiproton ⊑ nucleon`, `erythroblast ⊑
  embryonic-cell`, `nerve-fiber ⊑ fiber` (the textile one).
- *Claude's coarse rulings that were wrong rather than coarse*: `chemical-chain
  ⊑ concept` (atoms are physical), `actinide-series ⊑ chemical-group` (a
  series of elements is not a functional group), `brute-force-attack ⊑
  cryptanalysis` (a method under a field), `gene ⊑ dna` (Peter: genes were
  known before DNA), `ecosystem ⊑ group` (true only abstractly).
- *Wrong sense behind a right name*: the physics unit heads `charge`, `power`,
  `resistance`, `force` had aligned to the payment, the person and the act of
  opposing; `disease-vector` was WordNet's cloning vector; a `domain` row
  survived a rename as an orphan.

**The everyday-word rule now covers every pack, not only mathematics.** A
pack concept whose plain word has an everyday sense is qualified: `cone-cell`,
`rod-cell`, `pitcher-leaf`, `flower-spike`, `mechanical-stress`,
`magnetic-dip`, `statistical-mode`, `function-domain`, `gene-expression`,
`rna-translation`, `chemical-indicator` — because a bare `cone` or `stress`
in a merged store would file everyone's ice creams and deadlines under retina
cells and physics. The same rule resolved fifteen cross-pack collisions
(`polymorphism`, `decomposition`, `relaxation`, `transformation`,
`translation` each meant something different in two packs). `parity` in
physics is `parity-conservation`. The names that stay plain are the ones
whose only common sense is the pack's: `enzyme`, `quark`, `theorem`,
`genus`, `mixture`.

**Medicine (2026-09-03, same day).** Built with the second-pass rules in
force from the start: everyday-word names qualified as they appeared
(`whitlow` for WordNet's `felon`, `furuncle` for `boil`, `common-cold` stays
core's, `symptomatic-effect`, `tissue-graft`, `medical-imaging`,
`psychological-repression`, `surgical-taxis`), slang and pejoratives dropped
(`crud`, `craziness`, `bedlam`, `monster`), the `anemia` sense overridden to
the blood disorder (WordNet's hub sense is "a lack of vitality"), and one
Wikidata alignment corrected at the source: P8814 maps Q12140 *medication*
onto WordNet's *act of medicating*, so every drug arrived as a kind of
treatment until `medicating` was cleared and `medication` pinned. Wikidata's
noise here was louder than in the sciences — `patent-medicine ⊑ crime`,
`forensic-medicine ⊑ law`, `intern ⊑ servant`, every specialty under
`practice-of-medicine` (the profession) — 85 of 151 Wikidata-only edges
rejected. Medicine has had **one** reading, not two; its single-source
edges are the natural next target for the bounty of factbond
INTEGRATION.md §11.

**AI and machine learning (2026-09-03, afternoon).** The first pack where
Wikidata is the primary source rather than a witness: WordNet has almost
nothing after 2000. That changes the failure modes. Wikidata files
*everything* under `artificial intelligence` — a vehicle, an agent, a
heuristic, a technique — so "is a subfield of" and "is an instance of the
field's subject matter" had to be separated by hand (a boosting algorithm is
not a subfield; `intelligence amplification` is the *alternative* to AI). It
also inverts freely (`AI model ⊑ artificial neural network`), and its P8814
WordNet links can land on the wrong sense (the medication case above). Two
label-search passes over ~840 terms took 45 minutes at the API's rate; every
hit was read before use. Placement needed ~280 hand rulings for roots
Wikidata gives no parent to, the hubs being `ai-model` and `statistical-model`
(both ⊑ concept — a model is an abstract object here, as mathematical objects
are), `algorithm ⊑ procedure`, and core's `automaton` for robots (Wikidata's
`robot` aligned to it). Everyday-word renames as elsewhere: `transformer-model`,
`attention-mechanism`, `vector-embedding`, `boosting-algorithm`,
`minimax-rule`, `game-of-life`, `android-robot`, `robotic-manipulator`.
Two readings of nothing yet — one pass, like medicine.

**Economics (2026-09-03, afternoon).** The first pack with an explicit
*exclusion* rule, and it needed one: WordNet's commerce cone reaches farming,
mining, printing and roller coasters, its payment cone reaches bribes, ransom,
alimony and welfare, and Wikidata files a slave, a kite and a torch under
`goods`. About 150 WordNet concepts and 60 Wikidata edges were dropped or
rejected on the scope rule alone. Two core senses surfaced: core's `dividend`
was WordNet's hub sense ("a bonus; something extra") and is now the company
dividend (override in `align/overrides.tsv`; the rename does not propagate to
published v3; Peter ruled the same afternoon: dividend is the company dividend by default); `cold` and
`operation` remain flagged, unchanged. Renames on the everyday-word rule as
usual (`price-charged`, `payment-amount`, `dues`, `bitcoin-taproot` — the
plant root is biology's). One reading only.

**Computing (2026-09-03, evening).** Peter's list was long and mostly
*instances* — Linux, Git, Python, PNG, HTTP, Wikipedia — which Wikidata holds
by P31, not P279, so the fetch returned no parent for 850 of the 970 items and
the pack is placed by ruling to a degree no earlier pack was (~1,150 rulings,
all in `claude-ruling.tsv`). Two tool changes fell out. `tools/crosspack.py`
checks identity across packs — one QID or WordNet offset must carry one name
everywhere, and one name one identity — and found nine pre-existing
collisions the packs could not see alone (`content-addressing` vs
`content-addressable-storage`, `satisfiability` on the Boolean SAT item,
`pencil-of-rays`/`pencil-of-lines`, `error-correction-code`, `logic-operation`,
economics' everyday `storage` vs computing's), plus thirteen inside the pack
where P8814 had given a WordNet synset the same item as a Wikidata override
(`push-down-storage` = `stack`, `browser` = `web browser`, `binary` =
`executable`); each is now one name. And `consensus.py` had bolted
`extra-edges.tsv` on *after* the placement fixpoint, so a concept whose only
parent was a hand-asserted class never reached a root — 180 computing concepts
hung from `image-file-format` and friends, and economics gains 70 concepts it
had silently left out (1055 → 1125; the other packs moved by a handful for the
same reason). The everyday-word rule renamed `router`, `instruction`,
`buffer`, `dump`, `sort`, `seek`, `telephone` (→ `telephony`), `basic`,
`ontology` (→ `computational-ontology`: the philosophers keep the word) and
the like; programming languages are qualified only where the bare word is
one (`python-language`, `rust-language`, `go-language`, `c-language`,
`java-language`; `haskell`, `fortran`, `prolog` stay). Core's `graph` is the
chart sense while aligned to Wikidata's mathematical graph, `interface` is the
UI-program sense, `hierarchy` and `terminal` are fine; `standard`, `system`,
`design`, `pattern`, `principle`, `time-period` are *unplaced in core*, so
nothing here hangs from them (`technical-standard ⊑ document` instead).
One reading only, like medicine, AI and economics.

**Still doubtful, left for Peter** (kept as they stand, WordNet's readings):
iron products under the element (`cast-iron`, `pig-iron`, `wrought-iron ⊑
iron`; likewise `green-gold ⊑ gold`, `calcium-ion ⊑ calcium`); gaseous
elements under `fluid`; `animal-egg ⊑ ovum` and `ovule ⊑ ovum`;
`plant-part ⊑ body-part`; `astronomer ⊑ physicist`; `ph-value ⊑
concentration`; `stoichiometry ⊑ ratio`; `probability ⊑ statistic`;
`sample-distribution ⊑ statistical-distribution`; `computational-complexity-
theory ⊑ computability-theory`; `chemical-bond ⊑ natural-event` (correct by
WordNet's chain, but core's name `natural-event` for *natural phenomenon*
misleads here); the `-blast` precursor cells under `embryonic-cell`.
