# The occupations pack — plan

Status: plan for review, 2026-09-23; first build the same day (§10), unreviewed. Written from loopmarket's
need (a wanter requiring "a licensed plumber") and measured against the
shipped core (v9) and WordNet 3.0; to be folded into `UPPER.md` as a section
once decided, as §10–§14 were.

## 1. The gap

Core is **activity-rich and person-poor.** The services layer (§11) gave it
the work — `plumbing-work`, `carpentry`, `roofing-work`, `wiring`,
`hairdressing`, `massage`, `cleaning`, `gardening`, `tutoring`,
`babysitting`, `accounting` — but not the people who do it. Measured
2026-09-23: 77 concepts sit under `worker`, `professional` and `occupation`,
and of a sample of 69 everyday trades and professions **15 are present and
54 missing**: electrician, plumber, carpenter, mechanic, hairdresser, baker,
gardener, cleaner, teacher, tutor, translator, pharmacist, physiotherapist,
veterinarian, midwife, nanny, caregiver, programmer, locksmith, tiler,
optician …

**The words are not missing from the source.** WordNet has 52 of the 53
tested (all but `chimney-sweep`, spelled differently there); its `worker`
cone (09632518) holds 1,130 synsets, `skilled_worker` (10605985) 694,
`professional` (10480253) 299. Core's cut — Princeton Core WordNet, the
~5,000 most frequent synsets — simply left them out. So this is §11's
situation again: the concepts exist in WordNet; what is needed is a
**selection** and **witnesses**.

Why it matters beyond loopmarket: an occupation is what a credential, a
licence, a professional body and a job advertisement name. Trade (the
service) and occupation (the person) are different kinds, and the catalogue
needs both.

## 2. Pack, not core

§7's test: a concept belongs in core when we could not conceivably be wrong
about it *and* a non-specialist files under it. `plumber` passes the second
half, but there are hundreds of occupations, they have their own classifying
sources (ISCO, ESCO) with their own versioning, and many names need
qualifiers (`pilot`, `conductor`, `driver`, `cleaner`, `mover`). **A pack:
`packs/occupations`**, merged onto core's existing hinges.

**Hinges already in core:** `occupation` (00582388), `worker` (09632518),
`professional` (10480253), `craftsman` (09974648), `laborer` (10241300),
`person`, and the everyday practitioners core already holds (`dentist`,
`doctor`, `nurse`, `lawyer`, `engineer`, `pilot`, `cook`, `painter`,
`driver`, `accountant`, `architect`, `photographer`, `musician`). No new
core hinge is proposed; `skilled-worker` (10605985) is the candidate if the
pack's structure asks for one, decided at review.

**The medicine pack already holds health practitioners** (its `health
professional` cone and Wikidata's physician / health professional roots,
§8). They stay there. The occupations pack references them through
`tools/crosspack.py` rather than re-deriving them, and ISCO's health groups
(22, 32) become their witness. Two packs, one concept each.

## 3. Sources — witnesses, never imported

As with CPC for services (§11) and the Google Product Taxonomy for goods
(§10): concept identity stays WordNet's synset; the classifications witness
edges and check coverage; their titles are phrases, so they are matched by
code carried beside each synset, never by label.

| source | what | role | licence | status |
|---|---|---|---|---|
| **WordNet 3.0** noun.person | the `worker`, `skilled_worker`, `professional` cones | concept identity + hypernym witness | Princeton | have |
| **ISCO-08** (ILO) | 10 major, 43 sub-major, 130 minor, 436 unit groups; structure + index of occupational titles | structure witness + coverage check | ILO; free download | to fetch (xlsx) |
| **ESCO v1.2.1** (European Commission) | occupations below ISCO unit groups (each maps to exactly one; levels 5+), with alternative labels in 28 languages | fine-grained witness, coverage, labels | reuse under the Commission's policy (Decision 2011/833/EU) — **exact terms to verify** | **needs a registered download** (email; Peter) |
| **Wikidata** | bounded P279 walks under *occupation* and *profession* | the independent second witness | CC0 | roots to verify by label |

**Independence.** ESCO is built on ISCO: above the unit group they are *one*
witness, not two. An edge `plumber ⊑ building-trades-worker` witnessed by
ISCO and ESCO counts once; the second independent source is WordNet's own
hypernym or Wikidata's P279. This is the consensus rule's crux for this pack
and `consensus.py` must be told the pairing.

**Wikidata roots** (to verify by label before any walk — §8's lesson, four
of thirty-three were wrong): *occupation* and *profession* are candidates,
walked at depth 1 with the 3,000-children cap; *occupation* files job titles
by the thousand, so depth 0 (label only) may be all it can bear.

## 4. Selection — what goes in

**In:** a WordNet synset in the three cones that ISCO or ESCO witnesses — an
occupation a labour-market classification recognises — plus the everyday
occupations the §1 sample names. Expected size **500–900 concepts** (436 unit
groups, several synsets for some, none for the phrase-only ones), under the
core's own 4,992.

**Out** (a scope rule in economics' spirit, "if in doubt, leave it out"):

- titles, ranks and offices (`baron`, `presidentship`, military ranks) —
  positions, not occupations;
- historical and obsolete trades WordNet keeps (the lamplighter kind), unless
  ISCO still classifies them;
- criminal "occupations" and slurs WordNet files under person;
- employer- or country-specific job titles (ESCO's narrowest level often
  is): an ESCO occupation enters only when it is a kind a person in another
  country would also recognise;
- **no instances** — no named professional bodies, no licences, no degrees
  as nodes (those are credentials, loopmarket's and the assurance layer's).

**ESCO-only occupations** with no WordNet synset (`data-scientist`,
`web-developer`, `blockchain-developer`, `solar-panel-installer`): through
Wikidata where it has an item, hand-asserted in `align/extra-edges.tsv`
otherwise, as economics did for its ~80 crypto concepts — each with its ISCO
code.

## 5. Structure — how deep

ISCO's four levels are the obvious skeleton, but its group titles are
phrases ("Building and related trades workers, excluding electricians").
Rule: **an ISCO group becomes a node only where a plain name exists**
(`building-trades-worker`, `health-professional`, `teacher`); otherwise it
stays a witness code, and its unit groups hang from the nearest named
ancestor. The pack will be shallow — typically occupation → one or two named
groups → hinge — which is what matching needs: a wanter requiring
`building-trades-worker` accepts a plumber, a tiler and a roofer.

## 6. Names

§10's rule: the everyday word where it is unambiguous (`plumber`,
`electrician`, `hairdresser`, `baker`); qualified where core or another pack
already uses the word for something else — `driver` (software, golf) →
core's existing sense checked first; `conductor` → `music-conductor` /
`rail-conductor`; `cleaner` (the product) → `cleaner-person` or ESCO's
`cleaning-worker`; `mover`, `pilot` (core's is the aviator — keep), `nurse`
(core's — keep). Every qualification goes in `align/names.tsv` with its
reason, as medicine's do.

## 7. What the pack does not do — the occupation ↔ activity link

The useful fact "a plumber does plumbing-work" is **not** a subsumption:
`plumber ⊑ plumbing-work` is false, and ontodag's graph carries only ⊑. The
pack therefore places occupations and does not link them to activities.
Two ways to add the link later, both outside this plan:

- a **graph-kind head** in ontodag (`practitioner(plumbing-work)` — the kind
  of person who performs X), with `plumber ⊑ practitioner(plumbing-work)`
  asserted — needs checking against DIMENSIONS.md §15 (can a node be filed
  below a graph term?) and Peter's ruling;
- **loopmarket's own mapping** (the credential layer reads "occupation O
  performs activity A" from ESCO's occupation–skill relations) — no catalogue
  change.

Recommendation: ship the occupations first; decide the link when a consumer
needs it (loopmarket's counterparty gate can require `plumber` directly).

**Multilingual labels** (ESCO's 28 languages) are also out of the first
version: ontodag's names are identity; whether a pack may carry labels for
lookup is an ontodag question, not a pack one.

## 8. Steps and gates

| # | step | files / tools | gate |
|---|---|---|---|
| O0 | sources and licences: ISCO-08 xlsx from the ILO; **ESCO v1.2.1 CSV via the registered download (Peter)**; ESCO's reuse terms read and recorded in NOTICE; Wikidata roots verified by label | `sources/isco/`, `sources/esco/`, `tools/fetch.sh`, NOTICE | licences written down; every root QID's label checked |
| O1 | extractors: `extract_isco.py` (code tree → Graph), `extract_esco.py` (occupations + their ISCO unit group) | `tools/`, `cache/` | ISCO: 10/43/130/436 nodes exactly; every ESCO occupation under exactly one unit group |
| O2 | candidate set: WordNet cones + ISCO/ESCO code map per synset | `packs/occupations/align/{sources,occupations,drop}.tsv`, `align.py` gains `read_isco_map` like `read_cpc_map` | every one of the §1 sample's 54 resolves to a synset or an extra edge |
| O3 | names | `align/names.tsv` | no pack name equals a core or other-pack name of a different sense (`crosspack.py`) |
| O4 | views, consensus, review | `views.py`, `consensus.py --pack occupations` (ISCO+ESCO counted as one witness above the unit group); `review.tsv` for Peter, `claude-ruling.tsv` under standing permission | every edge two independent witnesses or a ruling; the queue empty |
| O5 | integrate: core + medicine + occupations as one store | `regen_ontodag_core.py`, `regen_ontodag_packs.py`, `integrate.py` | one coherent root; health practitioners once (medicine's) |
| O6 | coverage check | a script over ISCO's 436 unit groups | each has a concept or a recorded reason for none |
| O7 | ship | ontodag `domain/occupations.py`, golden root; `odag pack occupations` | loopmarket resolves `plumber`, `electrician`, `building-trades-worker` after `odag pack core` + the pack |

O0 needs Peter (the ESCO registration); O1–O6 are mechanical plus review; the
review load is §11-sized (hundreds of lines, not thousands).

## 9. Decisions for Peter

1. A pack (`packs/occupations`), not core — agreed?
2. Scope rule (§4): recognised occupations only; no titles, ranks, obsolete
   trades, instances — and ESCO's narrowest titles only when portable across
   countries?
3. Health practitioners stay in medicine (§2)?
4. ISCO groups as nodes only where a plain name exists (§5)?
5. The occupation ↔ activity link deferred (§7) — or wanted now, which makes
   it an ontodag design question first?
6. The ESCO download: register and fetch v1.2.1 CSV (only you can do the
   registration).

## 10. Progress

**2026-09-23 — first build, unreviewed.** `tools/extract_isco.py` (ISCO-08:
exactly 10/43/130/436 groups; the armed forces' codes had lost their leading
zero in the ILO's CSV) and `tools/align_isco.py`, registered in `align.py` and
`views.py` as the `isco` source, aligned by synset. Three findings changed §3–§4:

- **The pool is every WordNet person synset**, not the worker/professional
  cones: WordNet files occupations all over (tailor under garment-maker), so the
  cones held only 21 of the 54 sampled. 7,272 non-instance person synsets; ISCO
  selects.
- **The index inverts its titles** ("Sitter, baby", "Engineer, civil"): the
  qualifier put back in front is matched first; the bare head only for the
  lemma's most frequent person sense (the artist's sitter is not a baby sitter).
- **Instances out** — Samuel Barber was *barber*'s first person sense.

Result: **714 new concepts selected**, 88 core concepts given an ISCO code, 214
queued (`align/queue-isco.tsv`: codes across major groups, armed forces, synsets
held by medicine); of the 54 sampled, 40 selected, 4 already in core v11, 8
queued with a reason, 2 absent (caregiver — ISCO says "care worker";
chimney-sweep — WordNet's `chimneysweep`). Consensus: **588 placed**, 129
unplaced, 92 disputed. Placements mostly sound (plumber, carpenter, welder,
tailor ⊑ craftsman; chef ⊑ cook); visible errors for review (optician ⊑
organization and place — label sources naming the shop; translator ⊑
scientist).

Not in `integrate.py`'s or `regen_ontodag_packs.py`'s pack lists: nothing ships
until reviewed. Next: Wikidata roots (occupation, profession) as the second
witness; names; the queue; the medicine overlap through `crosspack.py`.
