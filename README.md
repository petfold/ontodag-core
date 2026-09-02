# ontodag-core

Construction site for OntoDAG's upper ontology: the `core` pack.

[OntoDAG](https://github.com/petfold/ontodag) ships `core` as a pack (a small
ontology adopted by idempotent merge, pinned by a golden root). This repo is
where that pack is *built*: the reference ontologies are extracted into one
comparable shape, their tops are cut to importable `.od` files, and the design
of our own top is argued in `docs/UPPER.md`. Nothing here is installed by
anyone; the product is a published store root that `odag pack core` adopts.

## Layout

    sources/   the downloaded ontologies (not tracked; see below)
    tools/     extractors, one per source, all producing tools/graph.py's Graph
    cache/     extracted graphs as pickles (not tracked; tools/build.sh fills it)
    tops/      the top of each source as an OntoDAG .od file — tracked, diffable
    docs/      UPPER.md, the design record

## Sources

`sources/` holds symlinks or checkouts; `tools/build.sh` expects:

| path | what | licence |
|---|---|---|
| `sources/wordnet/dict/` | WordNet 3.0 database files (`data.noun` is what we read) | Princeton WordNet licence |
| `sources/wordnet/core-wordnet.txt` | Princeton Core WordNet, ~5,000 frequent synsets | same |
| `sources/opencyc/opencyc-latest.owl/owl-export-unversioned.owl` | OpenCyc 4.0 OWL export, 240 MB | CC-BY 3.0 (per file header) |
| `sources/sumo/` | SUMO checkout: `Merge.kif`, `Mid-level-ontology.kif`, `WordNetMappings/` | IEEE licence (ontology), GPL (tools) |

Still to fetch: schema.org (JSON-LD), YAGO 4 taxonomy, BFO, DOLCE.

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

Requires `ontodag` installed (`pip install ontodag`); the tools import it to
write files it can read back.
