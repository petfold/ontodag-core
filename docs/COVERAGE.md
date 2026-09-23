# Widening the cut — plan

Status: plan for review, 2026-09-23. Peter: core and the packs should hold
more than Core WordNet's ~5,000 synsets — raise the cut, and add by
judgement what ontodag's consumers (loopmarket, factbond, the assurance
layer) will need even where frequency does not reach. The occupations pack
(`docs/OCCUPATIONS.md`) is the first instance of this plan, not a separate
problem.

## 1. What the cut leaves out — measured 2026-09-23

Core today: 4,974 WordNet noun synsets; core and all ten packs together
8,987 of WordNet's 82,115.

**By sense frequency** (SemCor tag counts, WordNet `index.sense`): of the
5,974 noun synsets tagged at least three times, **3,474 are in neither core
nor any pack**; at ten or more tags, 911. Many of these are *other senses*
of words core has (`time`, `child`, `man`) — core took one sense — so the
sharper measure is by word:

| threshold | senses whose words appear nowhere in core or the packs |
|---|---|
| SemCor ≥ 3 | 1,760 |
| SemCor ≥ 5 | 897 |
| SemCor ≥ 10 | 315 |

(numbers and units excluded: they are values, §7.)

**By modern word frequency** (`wordfreq`, Zipf scale over subtitles,
Wikipedia, news and web): single-word nouns absent everywhere — 229 at Zipf
≥ 5, 562 at ≥ 4.5, **1,331 at ≥ 4.0** (about once per 100,000 words). This
list is noisy — it counts word forms, not parts of speech, so `have`,
`great`, `white` appear — but it finds what SemCor, a 1960s corpus, cannot.

**What is really missing** — words a person reaches for daily, confirmed by
both measures or plainly needed:

| kind | examples absent from core and every pack |
|---|---|
| people and family | girl, boy, son, mom, guy, companion; the occupations (54 of 69 sampled — `OCCUPATIONS.md`) |
| buildings and rooms | barn, porch, stairs, living-room, hut, cafeteria, steeple, campus, downtown, neighborhood |
| food and meals | sandwich, pizza, biscuit, supper, loaf |
| animals | kitten, puppy, chick, bull, honeybee, dairy-cattle, robin |
| plants | pine, willow, apple-tree, bud, vine, pollen |
| time | the months and weekdays; today; half-hour |
| communication | song, story, description, tv |
| feelings | hate, horror, delight, boredom, longing |
| body | teeth, back |

SemCor also over-weights its era: military ranks (lieutenant, colonel,
regiment, brigade), laboratory chemistry and thyroid physiology rank high.
Frequency alone is a poor cut in both directions.

## 2. The method — frequency proposes, judgement disposes

1. **A candidate queue from two frequency sources**, intersected with
   WordNet's noun senses:
   - SemCor sense counts ≥ 3 (the sense is attested as a noun);
   - `wordfreq` Zipf ≥ 4.0, restricted to lemmas whose **noun** use
     dominates (WordNet's tagged noun count ≥ its verb and adjective counts,
     or no competing part of speech) — removes `have`, `great`, `white`;
   - the sense taken is the lemma's most frequent tagged noun sense; a
     second sense enters only when it is itself frequent.

   Estimated size after the part-of-speech filter: 1,500–2,500 new concepts.
   Written as `build/queue-wide.tsv`, one line per candidate with both
   frequencies, the WordNet gloss and the nearest placed ancestor.
2. **Judgement lists** (§3): domain lists for what consumers need
   regardless of frequency, each with a witness where one exists.
3. **The existing machinery decides**: views, consensus (two independent
   witnesses per edge, or a ruling), `review.tsv` for Peter,
   `claude-ruling.tsv` under standing permission. Nothing bypasses review
   because it was frequent.
4. **Placement by §7's test**: the everyday word a layperson files under,
   unambiguous → core; specialist, qualified or large families → a pack.

## 3. Judgement lists — what the consumers need

| area | why | where | witness |
|---|---|---|---|
| **occupations** | credentials, licences, professional bodies, jobs (loopmarket's counterparty gate, the assurance layer) | pack `occupations` | ISCO-08, ESCO (`OCCUPATIONS.md`) |
| **family and person roles** | who a service is for (child care, a son's tutoring), everyday speech | core | WordNet + Wikidata |
| **buildings, rooms, parts of a home** | renting, repairing, cleaning, inspecting a place (the apartment case) | core | GPT's home categories, Wikidata, OSM building tags |
| **places of business and amenities** | factbond's first domain (POI liveness: existence, opening hours) and loopmarket's handover points — bakery, pharmacy, café, garage, post office, parcel locker | core (the everyday ones), a `places` pack for the long tail | **OpenStreetMap tags** (`shop=*`, `amenity=*`) as a new witness |
| **food, dishes, meals** | the most traded everyday goods | core (dishes), goods layer | GPT food categories, CPC 21–23 |
| **animals: pets and livestock** | pet-sitting, veterinary care, farm trade | core | WordNet + Wikidata |
| **plants: garden and trees** | gardening, landscaping, nurseries | core (everyday), biology pack (the rest) | WordNet + Wikidata |
| **vehicles and their parts** | repair, inspection (the car case) | core | GPT vehicles & parts, CPC |
| **legal and property documents** | title, deed, lease, lien, warranty, certificate, diploma, licence, inspection report — the assurance layer's vocabulary | core (everyday), economics (the rest) | WordNet + Wikidata + CPC |
| **condition and quality words** | an item "used", "damaged", "new", "refurbished" — describing what is sold | core, under `attribute` / `state` | GPT's condition field, schema.org `OfferItemCondition` |
| **calendar names** | months, weekdays | **decision first** — as categories (`november`) or as values of the parked *periodic* kind (DIMENSIONS.md §13)? a "every Monday" offer needs the latter | — |

Consumers other than loopmarket's line should add their lists here before
the build (ontodag's own demos, factbond's domains, swarm-ai-data-exchange
catalogue terms).

## 4. What stays out

Numbers and units (values, §7); proper names and instances beyond §8's
policies; slurs and obscenities (WordNet and the frequency lists carry them —
excluded by list); function-word artefacts of the frequency source; senses
only a specialist uses (they go to packs or nowhere); the dated senses
SemCor over-weights unless a consumer needs them (military ranks stay out of
core; a `military` pack is not proposed).

## 5. Versions and size

The widened core is **v12**; the change is additive (§1's asymmetry makes
adding safe and removal a one-way door), so nothing present moves unless
review says it must. Expected: core from 4,992 to roughly 7,000–8,000;
packs grow by their judgement lists; the whole store (core + packs, 11,842
categories at v11's integration) toward 15,000–18,000.

## 6. Steps and gates

| # | step | gate |
|---|---|---|
| W0 | decisions (§8) | agreed |
| W1 | `tools/queue_wide.py`: the two-source candidate queue with the part-of-speech filter; `wordfreq` data (CC BY-SA 4.0) recorded in NOTICE as a selection witness, never imported | the queue reproduces from sources; `have`/`great`/`white` absent from it |
| W2 | judgement lists as `align/lists/*.tsv` (one per area, with the witness per line); OSM tags added as a witness for places (`tools/extract_osm_tags.py` over the tag wiki's `shop`/`amenity` values) | each list reviewed once by its consumer |
| W3 | build: views, consensus, review — in batches by area, as §10–§14 were | review queue empty per batch |
| W4 | integrate (core + packs one store), regenerate the shipped modules | `integrate.py`: nothing missing or stranded |
| W5 | coverage gate | ≥ 95 % of noun-dominant Zipf ≥ 4.5 lemmas present or excluded with a recorded reason; every word in §1's table present or excluded |
| W6 | consumer gate | loopmarket's example lines and the assurance drafts' terms resolve (`plumber`, `barn`, `sandwich`, `warranty`, `inspection`, `bakery`, `used`) |

The occupations pack (O0–O7) runs as W2–W4's first batch.

## 7. Cost

Review is the cost: §11 (services) was 79 selected synsets plus witnesses,
§12 (CPC goods) 374. This plan is several times §12 — spread over batches
by area, most edges carried by two witnesses automatically, the ruling
load concentrated in placement (which core node a word hangs under) and
sense choice.

## 8. Decisions for Peter

1. The method (§2): two frequency sources as a candidate queue, the
   part-of-speech filter, review as today — or a fixed larger list (e.g.
   the 10,000 most frequent) taken whole?
2. The judgement areas (§3) — add or strike any.
3. OpenStreetMap tags as a new witness for places of business.
4. Calendar names: categories, or values of a periodic kind (an ontodag
   question first)?
5. v12 as one release or per batch (occupations first)?

## 9. Progress

**2026-09-23 — W1 built.** `tools/queue_wide.py` writes `build/queue-wide.tsv`:
**3,658 candidates, 1,960 whose words are nowhere yet** in core or the packs,
most frequent first, each with its SemCor count, Zipf frequency, the nearest
placed ancestor and flags. The noun-dominance filter removes `have` and
`great`; WordNet's own usage domains remove disparaging, obscene, profane,
archaic and trade-name senses without a hand list (slang and colloquial senses
stay, flagged). The known gaps land where §3 expects: `sandwich` under
`snack-food`, `pizza` under `prepared-dish`, `barn` under `building`, `puppy`
under `dog`, `pine` and `willow` under `tree`, `november` under
`calendar-month`, `son` under `child`, `neighborhood` under `community`.
Occupations run as their own batch (`OCCUPATIONS.md` §10). Next: W2's
judgement lists, then the queue read area by area into review batches.
