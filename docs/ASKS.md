# Vocabulary asks filed by consumers

Status: filed 2026-09-25 from the credentials, cover and options plan
(loopmarket's and factbond's `docs/plans/credentials-cover-and-options.md`;
the drafts' `ontodag-asks.md`). Nothing here is built; each ask names its
consumer and the evidence. The kinds asks (an identifier kind, the ordinal
tripwire) are ontodag's and sit in its `ROADMAP.md`; this file holds what
belongs to packs.

## 1. General vocabulary missing from core v11 and the packs

Checked against `build/core.od` (v11) and the shipped domain packs on
2026-09-25. Absent, and general enough for core rather than a specialist
pack:

| term | sense wanted | consumer |
|---|---|---|
| `warranty` | a seller's undertaking about a good's condition or performance | loopmarket options and cover |
| `inspection` | the act of examining a thing and reporting on it | loopmarket `inspect` legs (`surveying` exists as an activity in geography; `survey` in the building/vehicle sense does not) |
| `certification`, `qualification`, `diploma`, `accreditation` | the credential vocabulary's nouns (`certificate`, `license`, `academic-degree` exist) | the counterparty gate |
| `theft`, `stolen-goods` | `larceny` exists; the everyday word and the goods themselves do not | the stolen-goods register absence proof |
| `recall` | withdrawal of a lot from the market | `lot(h)` and recall registers |
| `serial-number` | a maker-assigned identifier of one item | `item(h)` derived ids |
| the batch sense of lot | `lot → region` is the land-plot sense; v11's `batch → indefinite-quantity` covers the quantity, not the recall unit | `lot(h)` |
| `surety-bond` | a third party's guarantee of another's performance (`performance-bond → bond` is in the economics pack; only the surety form is absent) | cover and the mutual |

Present and sufficient, for the record: `insurance-coverage`,
`certificate`, `license`, `academic-degree`, `appraisal`,
`appraisal-report`, `option`, `purchase-option`, `reservation`, `right`,
`deed`, `warrant`, `larceny` in core; `insurance`, `insurance-policy`,
`guaranty`, `collateral`, `escrow`, `property-title`, `performance-bond`
in economics.

## 2. The legal vocabulary check (Peter, 2026-09-25)

The plan's decisions on cover, indemnity, subrogation, discretionary
mutual payouts and private adjudication will need legal terms the
catalogue almost certainly lacks. A first look at v11: `contract`,
`liability`, `indemnity` and `negligence` are present; `tort`,
`arbitration`, `mediation`, `jurisdiction`, `subrogation`, `warranty` and
`surety-bond` are not. The question to settle, in `OCCUPATIONS.md`'s
manner (a selection with a standard classification as witness, never an
import): whether a **legal pack** is warranted, covering private
arbitration and privately produced law (lex mercatoria, trade-association
rules, mutuals' by-laws, standard-form contracts) beside state law.
Candidate witnesses: WordNet's legal synsets, EuroVoc's law domain, a
legal ontology such as LKIF. The plan's `commercial-practice-review.md` in
loopmarket lists the concepts the mechanisms actually use (indemnity,
insurable interest, subrogation, retention, deductible, certificate-final,
contra proferentem, expert determination, arbitration, dispute board,
notice and cure, finality, look-back) and is the requirements list for the
selection. Not started.

## 3. What is not asked

- **Occupations**: unchanged. The pack built under `OCCUPATIONS.md`
  already holds the trades the plan's examples need (electrician,
  plumber, dentist, translator, locksmith, teacher, …); the plan's earlier
  note that they needed an ISCO/ESCO import was withdrawn on 2026-09-25 in
  favour of the pack's own method.
- **The credential layer** (licensing status per occupation, recognition
  edges such as EU Annex V, the door scale, evidence-basis names,
  `scheme` per category) is the assurance repository's own pack, not
  core's; it depends on core and the occupations pack and adds nothing to
  them.
- **Per-key or per-item nodes**: never in a shared pack (the identifier
  kind exists so that `item(h)` needs no node).
