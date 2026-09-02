# ontodag-core

Construction site for OntoDAG's upper ontology: the `core` pack.

[OntoDAG](https://github.com/petfold/ontodag) ships `core` as a pack (a small
ontology adopted by idempotent merge, pinned by a golden root). This repo is
where that pack is *built*: the reference ontologies are extracted into one
comparable shape, their tops are cut to importable `.od` files, and the design
of our own top is argued in `docs/UPPER.md`. Nothing here is installed by
anyone; the product is a published store root that `odag pack core` adopts.

## State (2026-09-02)

`build/core.od` is the `core` pack (v3 shipped in ontodag 0.19.1; v4, the
Wikidata-confirmed rebuild, is in ontodag's main branch unreleased): ~2,930
concepts, ten branches, every edge carried by two independent sources or by
Peter's ruling. It is a strict superset of the hand-written v1 (194 concepts,
nothing lost). `docs/UPPER.md` §6 records every decision, §7 the policy for
the sciences, §8 the science packs built beside it — `packs/physics`,
`packs/mathematics`, `packs/chemistry`, `packs/biology`, each a
`build/<pack>.od` that merges onto core's hinges (`odag pack core`, then
`odag merge packs/<pack>/build/<pack>.od`). Rebuild core from the review
files with `sh tools/build.sh`; a pack with
`python3 tools/{align,views,consensus}.py --pack NAME`.

## Pictures

`docs/img/top.svg` is the top of the pack (roots and their largest children,
cone sizes on the labels); `docs/img/upper.svg` goes two levels down.
`tools/picture.py` writes the DOT files, `tools/atlas.py` the pan-and-zoom
page `docs/img/core.html` (whole pack, radial, coloured by branch, with
search and a parents/children panel) — regenerable, not tracked:

    python3 tools/picture.py
    dot   -Tsvg docs/img/top.dot   -o docs/img/top.svg
    dot   -Tsvg docs/img/upper.dot -o docs/img/upper.svg
    twopi -Tsvg -Granksep=2.4 -Goverlap=false -Gsplines=line docs/img/core.dot -o docs/img/core.svg
    python3 tools/atlas.py

## Layout

    sources/   the downloaded ontologies (not tracked; see below)
    tools/     extractors, one per source, all producing tools/graph.py's Graph
    cache/     extracted graphs as pickles (not tracked; tools/build.sh fills it)
    tops/      the top of each source as an OntoDAG .od file — tracked, diffable
    align/     the review files: overrides, names, drops, extra edges, Peter's and Claude's judgements
    views/     each source's entailments over our vocabulary (built)
    build/     the consensus pack, its evidence table and review queue (built)
    docs/      UPPER.md, the design record

## Sources

`sources/` holds symlinks or checkouts; `tools/build.sh` expects:

| path | what | licence |
|---|---|---|
| `sources/wordnet/dict/` | WordNet 3.0 database files (`data.noun` is what we read) | Princeton WordNet licence |
| `sources/wordnet/core-wordnet.txt` | Princeton Core WordNet, ~5,000 frequent synsets | same |
| `sources/opencyc/opencyc-latest.owl/owl-export-unversioned.owl` | OpenCyc 4.0 OWL export, 240 MB | CC-BY 3.0 (per file header) |
| `sources/sumo/` | SUMO checkout: `Merge.kif`, `Mid-level-ontology.kif`, `WordNetMappings/` | IEEE licence (ontology), GPL (tools) |
| `sources/schemaorg/schemaorg-current-https.jsonld` | schema.org, latest release, JSON-LD | CC-BY-SA 3.0 |
| `sources/yago/yago-wd-{schema,class}.nt.gz` | YAGO 4 (2020-02-24) taxonomy: schema.org top, Wikidata classes below | CC-BY-SA 3.0 |
| `sources/bfo/bfo.owl` | BFO 2020 (ISO/IEC 21838-2), from purl.obolibrary.org | CC-BY 4.0 |
| `sources/dolce/DOLCE-Lite.owl`, `DUL.owl` | DOLCE-Lite and DOLCE+DnS Ultralite (Turtle despite the name) | CC-BY 4.0 |

Fetch commands are in `tools/fetch.sh`. YAGO 4.5 was not found at any public
path on 2026-09-02; YAGO 4 is what we have.

## Use

    sh tools/build.sh                                   # extract + write tops/
    python3 tools/top.py cache/wordnet.pkl --depth 3 --min 300   # print a tree
    odag -f tops/sumo.od get                            # browse a top with odag
    odag -f tops/core.od diff tops/opencyc.od           # compare two tops

The cut parameters in `tools/build.sh` *are* the definition of "the top" for
each source; change them there. Ids stay the sources' own (synset offsets,
Cyc concept ids, SUMO terms); the `.od` names are normalised labels with
`.2`, `.3` on collisions. OpenCyc contains mutual-subclass pairs (OWL
equivalence); the exporter breaks them and says where.

Requires `ontodag` (`pip install ontodag`; the tools import it to write files it
can read back) and `rdflib` for the three small OWL files.
