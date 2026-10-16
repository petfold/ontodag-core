# Core review, 2026-10-16 — a v14 candidate

Peter asked for every item in core to be read again, against the rule that
transitivity makes explicit: if Y is below Z and X is below Y, then X is
below Z, so an edge is wrong whenever any ancestor it brings in is false of
the child. Clearly wrong edges were to be removed onto a removed list;
doubtful ones listed, at most 200; the yardstick is the one core was built
for, generally accepted knowledge that is certain and unlikely to change.
Claude did the reading. Peter then ruled on four of the findings, and the
closure check was run on the eleven packs as well (both below). Nothing here
is shipped: `ontodag` still carries v13, and nothing is committed.

## How it was read

A review sheet listed all 4,992 concepts of `build/core.od` in depth-first
order from the roots, so that a parent was read before its children. Each
entry carried the concept's WordNet synset and full gloss, its parents with
the sources behind each edge, and its complete ancestor set. That set is the
point: `chicken ⊑ poultry` is harmless on its own; the line that also showed
`mammal` among the chicken's ancestors is what made the error visible. The
sheet was read in twenty batches of 250, and the results were saved after
each one (`align/review-v14-progress.tsv`).

A second sweep then crossed every concept's WordNet lexicographer file
(food, artifact, act, state, and so on) with the branches it now lands in,
and re-read the rare pairings. That found eight more.

## The files

| file | what |
|---|---|
| `align/rulings-v14-removed.tsv` | **the removed list**: 279 core rows and 454 pack rows (the concept pass included), applied by `tools/step7.py` like the v13 rulings |
| `align/renames-step7.tsv` | the bank renames (Peter, below) join the earlier renames |
| `align/rulings-v14-peter.tsv` | Peter's rulings of 2026-10-16 (sugars, art, music's works) |
| `align/doubtful-v14.tsv` | **the doubtful list**, with Peter's answers in its third column (2026-10-16) |
| `align/name-traps-v14.tsv` | 153 names under which a true edge reads false (below) |
| `align/review-v14-progress.tsv` | one row per batch |
| `tools/closure.py`, `build/closure.tsv`, `packs/*/build/closure.tsv` | the closure check (below) |

`tools/step7.py` gained two actions for rulings files: `cut` drops one
edge and refuses if it is the node's only parent, and `drop` removes a node
whose children have already been moved. No row uses `drop`: every
correction is an edge. A rulings row may also name a parent that an `add`
row of the same run brought into core. `sh tools/build.sh` replays the list after
consensus, so a rebuild reproduces this core.

## What changed

260 edges were removed from core. 248 came from the reading (below); 12 more came from the closure check (its own section). The numbers in the list below are the reading's:

- **79 cuts** where the concept keeps other parents (`cigar ⊑ device`,
  `coin ⊑ information`, `game ⊑ information`).
- **100 moves to an existing ancestor**: the wrong parent goes and the
  concept keeps the coarser claim the old edge already implied
  (`host: adult → person`, `livestock: mammal → animal`). Nothing new is
  asserted.
- **66 moves to a new parent**, where no ancestor was true either
  (`ingredient: component → substance`, `cloud: natural-event →
  natural-object`, `clock-time: cognition → time`). These are new claims,
  each with its reason in the note column; they are the rows to check first.
- **3 moves to the top level**: `amount`, `relation` and `part` (below).

Two edges were added to keep true knowledge (`hand-saw ⊑ hand-tool` once
`saw` was widened to `tool`; `stopper ⊑ artifact` once `occlusion` left
`structure`). Four cuts only restore the transitive reduction after the
moves.

Core now has fourteen top-level branches: the eleven of v13, plus `amount`,
`relation` and `part`. There are no missing parents and no cycles, and the
only redundant edge is the one v13 already shipped (`egg-white ⊑ food`, from
the v12 roles rewrite). `odag -f build/core.od` loads it, and spot checks
answer as intended (`chicken ⊑ bird` is true and `chicken ⊑ mammal` false,
`afternoon ⊑ cognition` false, `honey ⊑ food` true). The packs are
untouched: no core name was dropped, so every pack parent still resolves.

## What the errors were

**Abstractions filed as thoughts.** v11 hung WordNet's `measure, quantity,
amount` under core's `quantity`, which is a different synset ("the concept
that something has a magnitude"), and `relation` under `concept`; `part`
sits under `relation`, and rights sat under `concept`. Through `concept ⊑
idea ⊑ cognition`, an afternoon, a century, a coin, a teardrop, kinship,
north, a parking space, blood and fur were all psychological results of
perception and reasoning. WordNet holds measure and relation as top-level
abstractions, and removing the edges leaves them that way (doubtful list:
Peter may prefer `attribute`, which is how ontodag reads its dimensions).
`clock-time` and the times of day moved under `time`, and rights under
`attribute`, WordNet's own lexicographer file for them.

**Two senses in one node.** The rule "one reading where a word has two"
(CORE.md) was broken wherever a later source attached its own sense to a
WordNet node. schema.org's CreativeWork brought `game`, `play`, `course`,
`review` and `collection` into `information`, so tennis and a pile of
stones became information. Cyc and Wikidata gave the choice sense of
`option` the parent `contract`, so a default option was a legal document.
`acquisition` ("something acquired") under `event` made every gift and
prize an event. `alliance`, `conspiracy`, `wardrobe`, `aquarium` and
`sunlight ⊑ light` (the lamp) were the same fault. The building-or-
institution pairs (hospital, hotel, restaurant, library, factory) and
`country` are on the doubtful list, because which reading keeps the name is
a sense decision.

**Information that became an object.** CORE.md says a document is
information only. SUMO's and Cyc's artifact edges had come back on letters,
wills, charters, diaries, articles, tickets, diagrams and photographs. A
photo file was a physical object, and through `recording` (WordNet's
storage device) a podcast or a film was a device.

**WordNet chains carried too far.** These were true in WordNet's lexicon
but false in a store that is closed under transitivity:
- `livestock ⊑ mammal`: chickens, ducks and turkeys were mammals.
- `ingredient ⊑ component ⊑ device`: honey, sugar, yeast and vinegar were
  man-made devices.
- `wood ⊑ tissue ⊑ body-part`: firewood and sawdust were body parts.
- `water ⊑ liquid`: ice and steam were liquids.
- `symptom ⊑ evidence ⊑ information`: a fever was information.
- `natural-event` held clouds, smoke, pressure, electric charge, gravity
  and the states of matter, so all of them were happenings.
- `saw` is the hand saw, so table saws and band saws were hand tools.
- `generator ⊑ engine`.
- WordNet's associate ⊑ peer made every member, participant and stand-in a
  person of equal standing.
- The wheeled-vehicle ⊑ container chain, which CORE.md records as rejected,
  had come back through Cyc.

**Edges thrown out before.** UPPER.md §15.2 threw out `crop ⊑ industry`,
`backlog ⊑ income` and `reception ⊑ storage-medium` and caught `planner`
under `notebook-computer`. All four were in v13 all the same, the planner
under `machine`.

**Role nouns stated too strongly.** The glosses themselves say "a person or
institution" (`defendant`, `trustee`). Manufacturers, retailers and sellers
are mostly firms. Children host parties and are princes. Most hunters,
cooks and pilots are not doing a job.

**Chemistry.** Mixtures sat under `compound` ("formed by chemical union ...
in definite proportion"): toothpaste, shampoo, paper pulp, bitumen. Asphalt
sat under `mineral`, and beach sand under `soil`.

## The closure check

The two-source rule confirms one edge at a time. Two witnesses for X ⊑ Y and
two for Y ⊑ Z do not add up to any witness for X ⊑ Z, because each source may
hold Y in a different sense. `tools/closure.py` tests the composed result
instead. It takes every (concept, ancestor) pair in core's closure and asks
which sources entail it in their own graphs (`views/*.tsv`). Its class
`0-testable` marks pairs that some source aligns at both ends and none
entails.

| | pairs | 0-testable |
|---|---|---|
| v13 as shipped | 19,571 | 1,667 |
| after the reading | 18,288 | 1,034 |
| after the closure fixes | 18,196 | 976 |
| after Peter's rulings | 18,217 | 996 |

The last row is higher because Peter's re-hangings (carbohydrate, art,
music's works, lighting) are claims no source states in those words.

Most of the 976 that remain are not errors. Sources often file the same
thing under a different synset: WordNet's fruit leads to "solid food", not
to core's food, so no source confirms `apple ⊑ food`. Others are WordNet
instances the views do not walk (Mars, Europe), Peter's rulings, or the
review's own re-hangings, which no source states by construction.

The chains whose links each have support but whose whole has none were read
again. Twelve more edges came out:
- Seven fixtures sat under `plumbing`, "the utility consisting of the pipes
  and fixtures": a toilet or a tap is part of the utility, not the utility.
- `commercial-enterprise` sat under `commerce`, "sales and purchases", which
  made construction and farming into transactions.
- The chemical sugars (fructose, glucose, lactose) sat under core's `sugar`,
  which is refined table sugar and a seasoning.
- `cut-rate-sale` (WordNet's "an occasion for buying at reduced prices")
  sat under `opportunity`, a state, so every garage sale was a state. It is
  now an event. This one was found through the packs.

A cut of the chandelier and the oil lamp from `lighting` was withdrawn on
Peter's ruling (below).

About 9,400 pairs (half the closure) rest on one source, nearly always
WordNet. Those are the next place to look.

## Peter's rulings, 2026-10-16

`align/rulings-v14-peter.tsv`, replayed after the removed list:

- **Sugars.** Fructose, glucose and lactose are sugars in the chemistry
  sense, not core's `sugar` (table sugar). The chemistry pack has no
  carbohydrate concept, and core may lean on no pack, so core gains
  `carbohydrate ⊑ compound` (WordNet 14792703), and the three sugars and
  starch move under it. `monosaccharide` and `disaccharide` (WordNet
  14954284, 14836642) could follow.
- **Lighting** should be more general than stage lighting. The chandelier
  and oil-lamp edges stay. The node's WordNet synset is still 03667235
  (stage lighting apparatus); re-sensing it would change alignment and
  consensus, so only the edges were restored.
- **Art** is a cultural practice that is sometimes the subject of a field of
  study: `art` moves from `field-of-study` to `practice`. Its works do not
  become practices: `musical-composition` and `tune` move from `music` to
  `information`, and `musical-harmony` to `attribute`. The genres stay
  under music. This settles the doubtful row on `music ⊑ art`.

A second round, after the pack check:

- **Bank** names the bank that keeps money. WordNet's sloping land beside
  water becomes `river-bank`, and geography's `riverbank` merges into it
  (`align/renames-step7.tsv`). Its edge to geography's `shore` is cut,
  because core may lean on no pack. The old `depository-financial-institution`
  takes the name `bank`, and `custodian-bank` sits under it. This departs
  from UPPER.md's principle 3 ("`bank` never appears") by Peter's decision.
- **Currency is not a physical object.** It moves from `artifact` to
  `possession`, where WordNet files the medium of exchange. That settles the
  doubtful row on `money ⊑ currency`, and cryptocurrency stays under
  currency. Coins, bills, banknotes and token money keep `artifact` as a
  parent of their own.
- **A hardware wallet** is a special-purpose computer: `hardware-wallet ⊑
  computer`, not software.
- **Monosaccharide and disaccharide** are added to the chemistry pack under
  core's `carbohydrate`. Core's glucose, fructose and lactose cannot sit
  under them, since core may lean on no pack.

A third round settled more of the doubtful list:

- **Money** is the wider class (`money ⊑ possession`), and `currency ⊑
  money` holds fiat currency, cryptocurrency and cash. Core's `bill` is
  renamed `banknote`, since `bill` is also an invoice, a beak and a draft
  law, and economics' `banknote` merges into it. A banknote and a coin are
  physical objects and money at once, the way a hospital is a building and
  an organization. Token money is coins.
- **A publication is not physical**: `publication` moves from `product`
  to `information`, and `printed-publication ⊑ publication, product` is
  the copy a shop sells.
- **Owner** is dropped: it is a role, a relation to a filler, not a
  category. If ownership is wanted, the fitting form is a head on the
  possession, `owned-by(...)`, like `in`, `about` and `shared-with`. None
  is declared yet.
- **Pharmacy** is the shop (organization and place), not a field; the
  field is pharmacology.

## The concept pass

Peter: "concept is quite bad, everything in ontodag is a concept", and "we
should try to eliminate concept". 313 nodes sat directly under `concept ⊑
idea ⊑ cognition`, 302 of them in packs (economics 99, ai 85, computing 42,
mathematics 34). Through that chain a data structure, a stock market, a
law of nature and the Black-Scholes model were all psychological states.
Each node was re-filed by what it is:

- **Statements** go to `information`, as `theorem ⊑ proposition` already
  did. `hypothesis` and `principle` go under `proposition`, and core gains
  `law-of-nature ⊑ proposition` (WordNet 05872982), under which physics'
  `physical-law` and the chemical, biological and astronomical laws now
  sit. `theory` (physics) and `rule` go under `information`.
- **Models, data structures, data types, data models and protocol
  layers** go to `information`, as Peter ruled for `ai-model`.
- **Mathematical objects** go to a new `mathematical-object`, at the top
  of the mathematics pack, since core holds no abstract objects.
  `mathematical-relation` goes under core's `relation`, as WordNet has it,
  and `mathematical-set` goes under `collection` as well.
- **Measures, rates and values** go to `amount`. Core's `quantity` ("the
  concept that something has a magnitude") merges into `amount`, so
  humidity and the earth's radius sit with temperature and mass.
- **Situations and conditions** go to `state`: moral hazard, market
  failure, the Nash equilibrium, technical debt.
- **Designs and techniques** go to `method`: software architectures,
  design patterns, programming paradigms.
- **Properties** go to `attribute`. Core's `property` moves there, with the
  software quality attributes.

`concept` is then empty and is dropped. `idea` stays under `cognition` for
what really is a thought (`category`, `notion`, `web3`). Peter's rulings on
the pass: `goods-and-services` is dropped, since it joins two categories
(a query says `goods or service`). `mathematical-object` stays at the top
of the mathematics pack rather than becoming a core node. The pass also
found three more name traps. `date` is the fruit, so expiration and
settlement dates go under `day`. `style` is editorial directions, so
programming paradigms are cut from it. `risk` is a venture, so financial
risk goes under `danger`.

The closure check counts fell where the pass reached: the testable pairs
no source supports went from 2,260 to 1,868 in ai, 2,915 to 2,362 in
computing, 1,585 to 1,272 in economics, and 1,126 to 659 in mathematics.
The chain to `cognition` was most of what no source stated.

`tools/step7.py` now accepts a v13 role rewrite whose edge a later ruling
has changed again (the concept pass moves `account-abstraction` off
`concept`). Replaying every rename and ruling on the committed v13 files
reproduces the working tree; four pack files differ only in the order of
their borrowed-name lines.

## The about() pass

Peter: "maybe we should have a lot more about() in core". `about` is the
prelude's subject-matter relation, and it follows the graph: `about(heart) ⊑
about(organ) ⊑ about(body-part)`. A field of study or a kind of information
is filed under `about(X)` for what it is about, beside its kind
(`cardiology ⊑ medical-specialty about(heart)`). So `get field-of-study
'about(body-part)'` finds cardiology, dermatology, dentistry and the rest.
The edges are in `align/rulings-v14-subjects.tsv` (288 rows, `parent+`),
applied after the other rulings files.

- **Batch 1, core's fields** (18). Examples: linguistics about language,
  biology about organisms, astronomy about celestial bodies, medicine
  about health, geography about place, economics about core's
  `economic-system`. Core's `economy` is frugality, so it is not used.
- **Batch 2, the packs' fields** (111): the earth sciences (seismology,
  glaciology, petrology...), the medical specialties (cardiology about the
  heart, psychiatry about mental disorders), the branches of biology,
  physics and mathematics, and robotics, cryptography and software
  engineering.
- **Batch 3, kinds of information** (38): a biography and a portrait about
  a person, a map about place, a dictionary about words, a menu about
  food, a prescription about a drug, star catalogues about stars, a bill
  of lading about a shipment.
- **Batch 4, the packs' remaining fields** (31): computability theory
  about computational problems, computer vision and image processing about
  images, affective computing about emotion, network science about complex
  networks, game theory about games, the ontology fields about ontologies,
  electromagnetism about electricity and magnetism.
- **Batch 5, the packs' information** (89): the theories and laws that the
  concept pass made information (the gas laws about gas, Kepler's laws
  about planets, the periodic law and table about chemical elements, cell
  theory about cells, germ theory about disease, the theories of mind
  about the mind), datasets, financial models (Black-Scholes about
  options), contracts (an employment contract about employment), and
  improvement proposals about Bitcoin and Ethereum.

Most of the packs' 1,363 kinds of information have no subject in this
sense: software, file formats, protocols, data structures and AI models.
They were left alone.

Each row's note opens with its witnesses:

| witnesses | rows |
|---|---|
| the WordNet gloss names the subject | 138 |
| Claude's reading only (mostly pack concepts that have no gloss) | 104 |
| Wikidata P2578 and the gloss | 18 |
| Wikidata P2578 only | 14 |
| WordNet topic domain and gloss | 8 |
| all three | 5 |

The topic-domain check adds little. For each edge it counts how many of
the words WordNet files in the field's domain sit under the subject. Only
13 edges get any support that way. The 104 rows with Claude's reading
alone are rulings under CORE.md's "two witnesses or a ruling", and they
are the ones for Peter to read first.

The witnesses are Wikidata's "studies" (P2578, fetched 2026-10-16 for the
1,696 aligned fields and information kinds), the WordNet gloss ("the
branch of biology that studies animals"), and Claude's reading. Because a
subfield inherits its field's subject, each edge was checked against
everything below it. Some were left out for that reason:
- `geology` about the lithosphere: hydrology and glaciology sit under
  geology.
- `physics` about matter: acoustics.
- `logic` about inference: computability theory.
- `social-science` about society: psychology.

The pass also ran into name traps, and avoided them:
- core's `light` is a lamp, `crystal` glassware and `joint` a disreputable
  place;
- `dish` is dishware and `signal` a gesture, so signal processing has no
  subject;
- `fire` is a fireplace and `portfolio` a carrying case;
- `solution` is "the successful action of solving", `wave` a ridge on
  water, and `marriage` the ceremony;
- `motion` is an act, so mechanics and kinematics have no subject;
- `sound` is a sensation, so acoustics has none.

They join the naming pass. Two pairs of duplicate nodes turned up across
physics and space: `hubble's-law`/`hubbles-law` and
`kepler's-law`/`keplers-laws`. They are candidates for a merge.

Two notes for ontodag:
- Adopting the store the way `odag pack` does (put, then merge) answers
  `get` correctly.
- Loading or `merge`-ing the plain `.od` file with the CLI does not:
  `get field-of-study 'about(body-part)'` comes back empty although `below
  cardiology 'about(body-part)'` is true. The computed links between terms
  are missing when a term arrives before its argument's edges.

Left without a subject on purpose:
- the broad fields (engineering, philosophy, physics, the formal
  sciences);
- most of AI's techniques, which are ways of computing rather than studies
  of something;
- the fields whose subject is a name trap (above).

## Packs that refine core

Peter asked whether the packs integrate with core and with each other.
The measurements:
- About 4,000 of the 8,800 pack edges hang directly from a core node, and
  `odag pack` brings core first. So the packs do depend on core, and only
  in that direction.
- Only about 110 edges cross into a sibling pack.
- 145 names are entries in two or more packs, and 95 of them have
  different parents there. Adopting both packs merges the parents into an
  unreviewed union.

A pack could not refine an intermediate step. step7 enforced "a pack never
carries entries for core names", so a pack could hang new kinds under a
core node but never insert a tier above one. ontodag's merge supports
exactly that: a pack that says `glucose ⊑ monosaccharide ⊑ carbohydrate`,
merged into a store whose core says `glucose ⊑ carbohydrate`, leaves
`glucose ⊑ monosaccharide`, and the direct edge goes as implied.

Peter: "allow refinement rows and review the 258 candidates".
`tools/step7.py` gained two rulings actions:
- `refine`: a pack adds a parent to a core name. The new parent must lie
  under one of the core node's own parents, so the row inserts a tier.
- `refine-cross`: a reviewed claim that crosses branches.

Neither removes or renames anything, and core keeps its own edge, since
core may lean on no pack. `tools/regen_ontodag_packs.py` now writes these
entries into the generated pack modules instead of dropping them.

The candidates were the core ⊑ pack-node pairs that two or more sources
entail and the graph lacked: 266, or 258 when only the lowest pack concept
per core node is kept. `align/rulings-v14-tiers.tsv` holds the 79 taken:
- 75 of the 258, plus `botanical-fruit ⊑ plant-part`, which stands in for
  the 25 fruits the sources list one by one;
- glucose and fructose under chemistry's monosaccharide, and lactose under
  disaccharide, which core could not use this morning.

Examples: laptops and notebooks under portable-computer; printers and input
devices under peripheral; viruses and worms under malware; species under
taxonomic-group; chemical reactions under chemical-process; rain and snow
under precipitation; settlements, fields, parks and territories under
geographical-area; hills and mountains under natural-elevation;
pneumonia under respiratory-disease; the electron under lepton; triangles
under polygon. The rows are 57 insertions and 22 cross-branch claims.
Chemistry's `mixture` moved from `chemical` to `substance`, as WordNet
has it. Otherwise blood, air and toothpaste would have become "a material
used in or produced by a reaction".

`align/refinements-v14-rejected.tsv` holds the other 183, each with its
reason:
- **115 are `X ⊑ goods`** (shirt, bicycle, soup). In core, goods is a
  possession, which makes it a role: a shirt is a garment whether or not
  anyone sells it. OpenCyc and Wikidata agree on these, so the two-source
  rule does not catch them.
- **SUMO's mental and medical states as organic processes**: judgment,
  analogy, nightmare, nausea.
- **Beverages and dishes as chemical mixtures**: true, but fine-but-arguable.
- **Rows already implied** through a parent that was refined.

Adopting core and then a pack in ontodag shows the result:
- glucose's stored parent becomes monosaccharide, a laptop's
  portable-computer, and a settlement's geographical-area;
- the cross-branch rows add a second parent, so an alloy is a material and
  a mixture.

### Hinges promoted into core

`odag put glucose carbohydrate` fails when `carbohydrate` is undefined, as
an import does. A pack seems to adopt without core only because ontodag's
`pack_dag` enters every core name the pack hangs from as an empty
placeholder before the pack's own entries. `odag pack` and the organiser
page bring core along first. The REST route `/dag/pack` does not, which
leaves those placeholders unfilled. It should go through `packs.apply`, as
the CLI does (a change for ontodag).

So that packs depend on core alone, Peter had the general names that
sibling packs borrowed from one another promoted into core:
`align/rulings-v14-xhinges.tsv`, 14 names. Science's `theory`, `theorem`,
`physical-law`, `physical-phenomenon`, `magnetism` and `hormone`;
computing's `data-structure`, `data-processing`, `data-storage`,
`database`, `file-format`, `classification-scheme` and
`communications-protocol`; geography's `time-standard`.

A new step7 action, `promote`, moves the entry into core with core
parents. The pack keeps any parent of its own as a refinement entry:
computing keeps `data-storage ⊑ computer-operation` and
`classification-scheme ⊑ knowledge-organization-system`.

Biology, chemistry, medicine and occupations now depend on core alone.
What remains is left in its packs by CORE.md's policy:
- the mathematical structures, which computing and ai build on;
- computing's crypto infrastructure, which economics builds on;
- `temperature`, a registry quantity, which geography uses;
- single uses of `coordinate-system` and `solar-system`.

Mathematics and computing lean on each other.

### One owner per name, duplicates merged, soft dependencies

Peter: "So do these open things".

**Duplicates under different names**, merged by `renames-step7.tsv`:
- `unmanned-aerial-vehicle` into `drone-aircraft`;
- `planet-earth` into `earth`;
- `random-access-memory` into `ram`;
- `image-scanner` into `scanner`;
- `data-input-device` into `input-device`;
- `hard-disk-drive` into `hard-disk`;
- `shareholder` into `stockholder`;
- space's `hubbles-law` and `keplers-laws` into physics' entries.

A new rename kind, `refine-merge`, leaves a pack's own parent with the pack
as a refinement instead of pushing it into core: computing keeps
`hard-disk ⊑ non-volatile-storage`, and economics keeps
`stockholder ⊑ stakeholder`. Renames now also rewrite relation terms
(`in(planet-earth)` becomes `in(earth)`).

**One owner per name.** 144 names were entries in two or more packs. Each
now has one owner, chosen by subject:
- astronomy: space;
- the theory of computation, algorithms and data structures: computing;
- graph and order theory: mathematics;
- people: occupations;
- blockchain and game theory: economics;
- taxonomy: biology.

The other packs disown their copy with a new step7 action, `disown`. They
keep a placeholder, plus any parent from their own vocabulary as a
refinement of the owner's name: ai keeps `a-star-search ⊑
best-first-search` under computing's name. A parent the owner could state
without a new dependency (a core name, or its own) moved to the owner: 36
of them. 150 copies were disowned, and 30 of them keep a refinement.
`algorithm`, which three packs defined, is a hinge and went to core,
making 15 promoted names.

**Soft dependencies.** What packs still borrow from siblings is declared:
`tools/regen_ontodag_packs.py` writes `USES` into each generated module.
The regenerated packs will have:
- physics: mathematics, space;
- mathematics: computing;
- ai: computing, mathematics;
- economics: computing, mathematics, occupations;
- computing: mathematics;
- geography: physics;
- space: geography;
- chemistry, biology, medicine and occupations: none.

The regen tool also counts a name used only inside a term (`about(galaxy)`)
as mentioned, so it is listed as borrowed.

In ontodag (working tree, uncommitted):
- `packs.uses()` and `packs.unplaced_borrowings()`;
- `odag pack NAME` notes each sibling whose names are still unfiled, an
  offer and never an automatic adoption;
- `POST /dag/pack` adopts through `packs.apply`, so core comes along as
  with the CLI, and names those siblings under `uses`;
- three tests, the CHANGELOG and REFERENCE entries, the README test count,
  and a qualifier on ROLES.md item 23 (packs may now refine core names).

The pack and web tests, the invariants, boundaries and reference tests,
and the lint all pass.

**Peter's doubtful-list answers** (column 3) applied:
- machine learning moves from artificial intelligence to computer science;
- championship and meeting are events only;
- academy moves from school to institution;
- interest rate moves from charge rate to ratio.


## The packs

`tools/closure.py --packs` runs the same test on every pack. A pack's
concepts climb into core and into sibling packs, so the graph is the union
of core and every pack's own entries, and each source's evidence is the
union of its views in core and in every pack. The pairs reported for a pack
are those whose subject is that pack's own entry.

| pack | pairs | 0-testable before | 0-testable after |
|---|---|---|---|
| ai | 3,747 | 2,322 | 2,260 |
| biology | 1,281 | 170 | 170 |
| chemistry | 953 | 85 | 76 |
| computing | 6,241 | 3,039 | 2,915 |
| economics | 5,038 | 1,672 | 1,585 |
| geography | 4,209 | 1,514 | 1,372 |
| mathematics | 2,956 | 1,151 | 1,126 |
| medicine | 7,236 | 1,928 | 1,790 |
| occupations | 3,711 | 216 | 223 |
| physics | 746 | 97 | 105 |
| space | 1,343 | 529 | 530 |

The counts say less here than in core. Most pack concepts are aligned to
Wikidata alone, and the Wikidata views rarely climb as far as core's names,
so a sound pack edge such as `foundation-model ⊑ ai-model` has no source
behind it. Pack edges mostly rest on Claude's rulings (`claude-ruling.tsv`)
instead. Where a count rose, the new parent is one no source states in those
words (a monsignor under `priest`, voltage under `attribute`).

So the packs were read a second way: every pack concept whose ancestors span
two unrelated top-level branches (a field of study and an event, a document
and a physical object) was listed with the chain behind each branch, and
small single-branch groups were read by name. 127 pack edges came out, from
122 concepts, plus 7 cuts that restore the transitive reduction. Most are
the faults core had:

- **A core name in a different sense.** `custodian-bank ⊑ bank` (then the
  river slope); compass points under `direction` (an inclination, so northeast was
  an attitude); `log-file ⊑ record` (a best performance); the Beaufort and
  Richter scales under `measure` ("a step toward a goal") and under the
  fish's `scale`; bonds and shares under core's `asset` ("a useful
  quality"); call and put options under `option` (a choice); the Gulf Stream
  under `motion` (an act); thunder under `sound` (a sensation);
  `tree-structure ⊑ hierarchy ⊑ organization`, so a data structure was an
  agent.
- **A thing filed as a field.** Random forests, Q-learning, t-SNE, the RSA
  cryptosystem, a brute-force attack, confusion matrices and F1 scores,
  rhinoplasty and lobotomy (through `plastic-surgery` and `neurosurgery`),
  and SaaS and IaaS (through `parallel-computing ⊑ computer-science`) were
  fields of study.
- **Software or information that became an object, and the reverse.**
  Bitcoin under `currency` (then an artifact, now a possession), a Turing
  machine under `computer`,
  virtual memory under computer memory, a GUI window and a text cursor
  under `device`, a SPARQL endpoint under `computer`; and the other way, a
  hardware wallet under software (now `computer`). Globes and armillary spheres were maps
  (documents).
- **Quantities filed as happenings**, as core's pressure and electric
  charge were: voltage, capacitance, inductance, inertia, mechanical work
  and stress, amplitude.
- **Plain errors.** `space-probe ⊑ weapon`; alum under `chemical-element`;
  `smartphone ⊑ telephony` (now `cellular-telephone`); an organelle as an
  organ; a cough and a nosebleed as knowledge (`clinical-sign ⊑ evidence`,
  cut from core's `symptom` for the same reason); the bridegroom and a
  libertine filed as organisms and monsignor and vicar as attributes in
  occupations.

The ai pack's field branch needs a separate decision: about 250 entries are
filed as fields of study, and while most are subfields, some are tasks or
techniques. Only the clear algorithms and measures were moved; the rest is
a doubtful row.

## The doubtful list, in short

Thirty-eight rows, each a question for Peter rather than an error. The
thirty core rows:

- **One reading per name**: the building/organization pairs, `country`,
  `meeting` (people or event), `championship`, `railway`/`metro`, `book`
  (the work or the printed copy), `profile`.
- **The new top**: `amount`, `relation` and `part` as top-level branches.
- **Peter's own rulings that transitivity strains**: `vehicle ⊑ machine`
  (a canoe), `body-of-water ⊑ natural-object` (a reservoir).
- **Policy**: `pet`, `child`, `adult` and `owner` are in core although
  CORE.md names them as roles that are not kinds.
- **Contested or partial**: `virus ⊑ microorganism`; the services layer filing acts that are often
  done for oneself (`housework ⊑ service`); the phenomena under `process`;
  `bait`; `sample`.

The eight pack rows: `pharmacy` (field, shop and business in one node);
`ai-model ⊑ concept` (a trained model is software); the ai pack's field
branch; `computer-server` (hardware and software); `interest-rate`
under a price charged; core's `problem` as a topic; radio telescopes
under `telescope ⊑ magnifier`; and web resources under `dictionary ⊑ book`.

## Name traps

The shipped core has names and edges but no glosses, so an edge that is true
of WordNet's sense can read false under the name. `pig ⊑ person` is
WordNet's greedy person, `hand ⊑ assist` is "give me a hand", `fire ⊑
fireplace`, `head ⊑ artifact` is the side of a coin,
`pupil ⊑ hole`, `pound ⊑ enclosure`, `reservation ⊑ information` is a
qualification (ASKS.md lists `reservation` as present for loopmarket's
bookings), and `item ⊑ cognition`. These 153 are not removals and not
doubts. They are candidates for a naming pass, and a rename rides a version
as the v9 sense list did.

## Not done

- The packs were not read item by item as core was; they were read through
  the closure check, by their mixed-branch concepts and small groups.
- `ontodag`'s modules were not regenerated, so `CORE_VERSION` is unchanged.
- Nothing is committed.
