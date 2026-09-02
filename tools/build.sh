#!/bin/sh
# Extract every source once (cache/), then write the four tops (tops/).
# The cut parameters are the record of what "the top" means for each source;
# change them here, not by hand in the .od files.
set -e
cd "$(dirname "$0")/.."
mkdir -p cache tops
[ -f cache/wordnet.pkl ] || python3 tools/extract_wordnet.py cache/wordnet.pkl
[ -f cache/opencyc.pkl ] || python3 tools/extract_opencyc.py cache/opencyc.pkl
[ -f cache/sumo.pkl ]    || python3 tools/extract_sumo.py    cache/sumo.pkl Merge.kif
[ -f cache/sumo-mid.pkl ]|| python3 tools/extract_sumo.py    cache/sumo-mid.pkl Merge.kif Mid-level-ontology.kif
python3 tools/extract_core.py cache/core.pkl      # always fresh: it is the thing under review
python3 tools/top.py cache/wordnet.pkl --depth 3 --min 300  --od tops/wordnet.od
python3 tools/top.py cache/sumo.pkl    --depth 3 --min 1    --od tops/sumo.od
python3 tools/top.py cache/opencyc.pkl --depth 2 --min 1500 --od tops/opencyc.od
python3 tools/top.py cache/core.pkl    --depth 99 --min 0   --od tops/core.od
[ -f cache/bfo.pkl ]       || python3 tools/extract_owl.py sources/bfo/bfo.owl BFO_0000001 cache/bfo.pkl
[ -f cache/dolce.pkl ]     || python3 tools/extract_owl.py sources/dolce/DOLCE-Lite.owl particular cache/dolce.pkl
[ -f cache/dul.pkl ]       || python3 tools/extract_owl.py sources/dolce/DUL.owl Entity cache/dul.pkl
[ -f cache/schemaorg.pkl ] || python3 tools/extract_schemaorg.py cache/schemaorg.pkl
[ -f cache/yago.pkl ]      || python3 tools/extract_yago.py cache/yago.pkl
python3 tools/top.py cache/bfo.pkl       --depth 99 --min 0   --od tops/bfo.od        # all 35
python3 tools/top.py cache/dolce.pkl     --depth 99 --min 0   --od tops/dolce.od      # all of DOLCE-Lite
python3 tools/top.py cache/dul.pkl       --depth 3  --min 1   --od tops/dul.od
python3 tools/top.py cache/schemaorg.pkl --depth 2  --min 3   --od tops/schemaorg.od
python3 tools/top.py cache/yago.pkl      --depth 2  --min 200 --od tops/yago.od
