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
