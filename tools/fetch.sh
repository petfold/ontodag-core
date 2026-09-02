#!/bin/sh
# Fetch the sources that are plain downloads into ../ (beside this repo), the
# way the first four were obtained on 2026-09-02.  WordNet 3.0 and OpenCyc were
# downloaded by hand; SUMO is a shallow git clone.  Re-run to refresh.
set -e
cd "$(dirname "$0")/../.."
mkdir -p schemaorg yago bfo dolce wordnet
curl -sSL -o schemaorg/schemaorg-current-https.jsonld https://schema.org/version/latest/schemaorg-current-https.jsonld
curl -sSL -o bfo/bfo.owl http://purl.obolibrary.org/obo/bfo.owl
curl -sSL -o dolce/DUL.owl http://www.ontologydesignpatterns.org/ont/dul/DUL.owl
curl -sSL -o dolce/DOLCE-Lite.owl http://www.loa.istc.cnr.it/ontologies/DOLCE-Lite.owl
for f in yago-wd-class.nt.gz yago-wd-schema.nt.gz; do
  curl -sSL -o yago/$f https://yago-knowledge.org/data/yago4/full/2020-02-24/$f
done
curl -sSL -o wordnet/core-wordnet.txt https://wordnetcode.princeton.edu/standoff-files/core-wordnet.txt
[ -d sumo ] || git clone -q --depth 1 https://github.com/ontologyportal/sumo.git sumo
