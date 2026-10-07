# Roles audit of core and the domain packs

Draft analysis, 2026-10-07, for ROLES.md §9 step 7; nothing here is applied.
Decisions taken the same day are in the section "Decisions" at the end, and
the edge-by-edge rewrites in `align/roles-rewrites.tsv`.

The question, from ontodag's contract 0.2: which shipped edges are not
inclusion? Under 0.2 every name is a class of items and `x ⊑ y` says every
item in x is in y. Parts, places and things related to an entity fail that
test and belong under `in(...)`, `about(...)` or `for(...)`. The full list,
machine-readable, is `align/audit-roles.tsv`.

## In short

- **45 of the 12,960 shipped edges fail the test**: 22 with high
  confidence, 16 medium, 7 low. 24 are part-of, 8 use an entity as a
  quality, 13 are wrong in some other way. None is located-in.
- **They cluster.** Economics has 27, all hand-asserted and nearly all
  crypto terms. Geography has 10, four of them around the Earth's own
  structure. Core has 5, where WordNet filed a part as a kind of its
  whole. Computing has 2, both under `internet`, and mathematics 1. ai,
  biology, chemistry, medicine, physics and space have none.
- **20 of the 45 hang under an entity**: bitcoin, ethereum, ether, the
  Lightning Network, Swarm, Earth's atmosphere and structure, GPS, the
  Internet. The other 18 edges under entities are fine: versions, variants
  and family members (`ipv6 ⊑ internet-protocol`, `android ⊑ linux`).
- **Spelling: 22 British names, not 17, and one typo.** Eight of them,
  not six, are told apart from another sense only by their spelling:
  civilisation/civilization and judgement/judgment join ROLES' list.
- **Every finding is still in ontodag-core HEAD** (dca08d1, core v11), and
  HEAD's 949 new edges add only one weak case. The fixes can go into
  whichever core version ships with step 7.

## Method

The shipped modules (ontodag's `core_ontology.py` v9 and `domain/*.py`)
match the build at ontodag-core 4830925 edge for edge, plus the five
economics additions of 845d789. The evidence was read at that commit.
That is 12,960 edges: 5,226 in core and 7,734 in the packs.

Every edge was tested four ways:

1. **WordNet 3.0** (`data.noun`): a part, member or substance holonym
   between the two synsets, in either direction, along the holonym chain,
   or inherited through the child's hypernyms; and `@i` for instances. The
   parser was checked on toe #p foot, finger #p hand, and Tokyo @i national
   capital #p Japan.
2. **Wikidata**, queried live for the 7,445 QIDs in the concept tables:
   P361 and P527 (part), P131, P706, P30, P17 and P276 (location), P1269
   and P921 (facet, subject), P144 and P400 (based on, platform), P279 and
   P31. A P361 target whose label matches the parent's name also counted.
3. **Glosses**: the child's WordNet gloss or Wikidata description says it
   is a part, portion, layer, region or component of the parent, or is
   located in it.
4. **Reading**: all 239 hand-asserted edges (`extra-edges.tsv`), every
   edge under an entity (23 parents, 38 edges), and every hit from 1–3.

The ~12,000 edges with no signal were not read one by one. A part-of
edge among them would have to be one that neither WordNet nor Wikidata
describes as a part. That is possible, and it is exactly what happened in
the hand-asserted edges, which is why all of those were read.

Proposals use `⊑` for the edges that replace the old one. `in(...)`
presumes the prelude declares `in`, as step 7 plans. Where the old parent
was the child's only one, a kind parent is proposed too. Several are
computing names (`peer-node`, `computer-network`, `data-block`); economics
would borrow them, as geography already borrows `file-format`.

## Counts

Edges by class, with (high/medium/low); spelling counts names.

| pack | part-of | located-in | entity-as-quality | wrong | edges | spelling |
|---|---|---|---|---|---|---|
| core | 5 (1/4/0) | — | — | — | 5 | 14 + 2 optional |
| ai | — | — | — | — | 0 | 1 |
| biology | — | — | — | — | 0 | 2 (one a typo) |
| chemistry | — | — | — | — | 0 | — |
| computing | — | — | 2 (1/1/0) | — | 2 | 1 |
| economics | 11 (8/3/0) | — | 5 (5/0/0) | 11 (2/6/3) | 27 | 2 |
| geography | 8 (4/1/3) | — | 1 (0/1/0) | 1 (1/0/0) | 10 | 1 |
| mathematics | — | — | — | 1 (0/0/1) | 1 | 1 |
| medicine | — | — | — | — | 0 | 2 optional |
| physics | — | — | — | — | 0 | — |
| space | — | — | — | — | 0 | 1 + 2 optional |
| **total** | **24** | **0** | **8** | **13** | **45** | **23 + 6 optional** |

## High confidence

| edge | pack | evidence | proposal |
|---|---|---|---|
| `beacon-chain ⊑ ethereum` | economics | hand-asserted: "the proof-of-stake consensus layer" | `⊑ in(ethereum)`, `⊑ blockchain` |
| `bitcoin-network ⊑ bitcoin` | economics | hand-asserted: "the peer-to-peer network of nodes"; `bitcoin ⊑ cryptocurrency`, so the network is filed as a currency | `⊑ in(bitcoin)`, `⊑ computer-network` |
| `mempool ⊑ bitcoin` | economics | hand-asserted: "the pool of unconfirmed transactions" | `⊑ in(bitcoin-network)`, `⊑ collection` |
| `full-node ⊑ bitcoin-network` | economics | hand-asserted: "a node that validates every block"; every chain has full nodes | `⊑ peer-node` |
| `light-client ⊑ bitcoin-network` | economics | hand-asserted: "a node that trusts headers" | `⊑ peer-node` |
| `payment-channel ⊑ lightning-network` | economics | hand-asserted: "a two-party channel settled on chain" | `⊑ in(lightning-network)` and a kind; `smart-contract` is the nearest |
| `payment-channel-network ⊑ lightning-network` | economics | hand-asserted: "channels routed into a network"; the wrong way round, since Lightning is one payment-channel network | `lightning-network ⊑ payment-channel-network ⊑ layer-2` |
| `chunk-storage ⊑ swarm-storage` | economics | hand-asserted: "content-addressed 4 KB units"; `swarm-storage` is Swarm itself | `⊑ in(swarm-storage)`, `⊑ content-addressable-storage` |
| `postage-batch ⊑ swarm-storage` | economics | hand-asserted: "prepaid storage rent on Swarm" | `⊑ in(swarm-storage)`, `⊑ prepayment` |
| `ethereum-gas ⊑ ether` | economics | hand-asserted: "the unit of computation paid for in ether"; gas is priced in ether, it is not ether | `⊑ in(ethereum)`, `⊑ quantity` |
| `account-abstraction ⊑ ethereum` | economics | hand-asserted: "smart-contract accounts as first-class users" | `⊑ in(ethereum)`, `⊑ concept` |
| `maximal-extractable-value ⊑ ethereum` | economics | hand-asserted: "value extracted by ordering transactions in a block" | `⊑ in(ethereum)`, `⊑ income` |
| `bitcoin-halving ⊑ bitcoin` | economics | hand-asserted: "the block subsidy halves every 210,000 blocks" | `⊑ in(bitcoin)`, `⊑ event` |
| `timestamp-server ⊑ bitcoin` | economics | hand-asserted: "the whitepaper's framing of the chain"; the chain is a timestamp server, not the reverse | `⊑ computer-system`; if wanted, `bitcoin-network ⊑ timestamp-server` |
| `blockchain-block ⊑ blockchain` | economics | hand-asserted: "a batch of transactions chained by hash" | `⊑ in(blockchain)`, `⊑ data-block` |
| `atmospheric-layer ⊑ earth-atmosphere` | geography | hand-asserted; Wikidata: troposphere, stratosphere, mesosphere, thermosphere, ionosphere all P361 atmosphere of Earth; WordNet troposphere #p atmosphere | `⊑ in(earth-atmosphere)`, `⊑ layer` |
| `earth-sphere ⊑ earth-structure` | geography | hand-asserted: "the concentric shells"; `earth-structure` is Wikidata's "internal structure of Earth"; most of the spheres are P361 Earth | drop; `⊑ in(planet-earth)` (keeps `⊑ layer`) |
| `mohorovicic-discontinuity ⊑ earth-structure` | geography | WordNet: an instance of boundary, "between the Earth's crust and the underlying mantle"; no other parent | `⊑ in(planet-earth)`, `⊑ place` |
| `air-mass ⊑ atmosphere` | geography | Wikidata P361 troposphere; core's `atmosphere` is "the envelope of gases surrounding any celestial body" | drop; `⊑ in(atmosphere)` (keeps `⊑ atmospheric-state`) |
| `geographic-line ⊑ geographic-point` | geography | hand-asserted: "loci of points"; a line is made of points, it is not one | `⊑ place`, as `geographic-point` is |
| `egg-white ⊑ egg` | core | WordNet egg_white #p egg; Wikidata P361 bird egg, P279 food | `⊑ in(egg)`, `⊑ food` |
| `satellite-internet ⊑ internet` | computing | Wikidata: "satellite Internet access", P279 wireless communication | drop (keeps `⊑ wireless-communication`) |

## Medium and low

| edge | pack | class | conf. | evidence | proposal |
|---|---|---|---|---|---|
| `colon ⊑ intestine` | core | part-of | medium | WordNet gloss "the part of the large intestine"; Wikidata (aligned to large intestine) P361 intestine; but WordNet's hypernym says is-a | `⊑ in(intestine)`, `⊑ organ` |
| `thigh ⊑ limb` | core | part-of | medium | WordNet #p leg, "the part of the leg between the hip and the knee"; Wikidata P361 leg | `⊑ in(limb)`, `⊑ body-part` |
| `roadway ⊑ street` | core | part-of | medium | aligned to WordNet's "the part of a thoroughfare between the sidewalks"; Wikidata P361 street, P279 road. Peter's review accepted it, before 0.2 | `⊑ in(street)`, `⊑ road` |
| `leaf-blade ⊑ leaf` | core | part-of | medium | WordNet "the broad portion of a leaf as distinct from the petiole" (its hypernym is leaf) | `⊑ in(leaf)`, `⊑ body-part` |
| `humus ⊑ soil` | geography | part-of | medium | WordNet "the organic component of soil"; Wikidata P361 soil, P279 organic matter | `⊑ in(soil)`, `⊑ material` |
| `world-wide-web ⊑ internet` | computing | entity-as-quality | medium | Wikidata P279 "service on Internet": it runs over the Internet | `⊑ in(internet)` (keeps `⊑ computer-network`) |
| `differential-gps ⊑ global-positioning-system` | geography | entity-as-quality | medium | "enhancements to the GPS"; but Wikidata does give P279 GPS | drop (keeps `⊑ gnss-augmentation`) |
| `liquidity-pool ⊑ automated-market-maker` | economics | part-of | medium | hand-asserted; the AMM's own note: "prices set by a formula over a liquidity pool" | `⊑ in(automated-market-maker)`, `⊑ pooled-fund` |
| `staking ⊑ proof-of-stake` | economics | part-of | medium | hand-asserted: "locking ether to validate" | `⊑ in(proof-of-stake)`, `⊑ activity` |
| `incoterms ⊑ sales-contract` | economics | part-of | medium | hand-asserted: "the standard trade delivery terms"; terms in a contract | `⊑ contract-condition` |
| `validator ⊑ staking` | economics | wrong | medium | hand-asserted: "a staking node"; a node under an activity | `⊑ peer-node` |
| `hash-rate ⊑ cryptocurrency-mining` | economics | wrong | medium | "the network's hashing throughput": a quantity | `⊑ quantity` |
| `mining-difficulty ⊑ cryptocurrency-mining` | economics | wrong | medium | "the target adjusted every 2016 blocks" | `⊑ quantity` |
| `difficulty-adjustment ⊑ cryptocurrency-mining` | economics | wrong | medium | "the retargeting rule" | `⊑ rule` |
| `block-reward ⊑ cryptocurrency-mining` | economics | wrong | medium | "new coins plus fees paid to the block's miner" | `⊑ payment-amount` |
| `cross-chain ⊑ blockchain` | economics | wrong | medium | "between chains": an adjective, with nothing below it | drop, or a quality under `attribute` |
| `reorder-point ⊑ inventory-management` | economics | wrong | low | a stock level under an activity | `⊑ quantity` |
| `layer-2 ⊑ blockchain` | economics | wrong | low | "a protocol that settles on a base chain"; some are chains | `⊑ communications-protocol`, or keep |
| `blockchain-bridge ⊑ layer-2` | economics | wrong | low | a bridge links chains; it is not a layer 2 | `⊑ decentralized-application` |
| `floodhead ⊑ flash-flood` | geography | part-of | low | WordNet "a wall of water rushing ahead of the flood" | keep as a phase, or `⊑ in(flash-flood)` |
| `rapids ⊑ stream`, `rapids ⊑ waterway` | geography | part-of | low | WordNet #p river, "a part of a river" | keep (a stretch of river is water); maybe add `⊑ in(river)` |
| `secp256k1 ⊑ elliptic-curve-cryptography` | mathematics | wrong | low | one named curve, filed under the technique that uses it | drop (keeps `⊑ concept`) |

## Checked and kept

- **Wikidata's 150 part-of hits are almost all noise.** P361 links
  sub-disciplines (`statistics ⊑ mathematics`, `neurosurgery ⊑ surgery`),
  P527 links subtypes (`husband ⊑ spouse`, `capital-market ⊑
  financial-market`). A branch of a field is a kind of the field under the
  item reading, so these stay.
- **WordNet holonymy that is still inclusion.** `fishing-rod ⊑
  fishing-tackle` (a rod is a piece of tackle); `syndrome ⊑ disease`
  (Wikidata and OpenCyc say is-a); the four trades under `construction`
  (`house-painting`, `masonry-work`, `plumbing-work`, `roofing-work`: CPC
  files them as construction services); and `ice ⊑ water`, `dna ⊑
  nucleic-acid`, `cyclone ⊑ low`, where WordNet points the other way.
- **Mass nouns.** `toilet` and `urinal ⊑ plumbing`, `bacon` and `ham ⊑
  pork`, foods under `food`: a toilet is a piece of plumbing as a table is
  a piece of furniture. The retail reading keeps `headboard`, `footboard`
  and `mattress ⊑ furniture`.
- **Under entities.** Versions (`http-2`, `http-3 ⊑
  hypertext-transfer-protocol`; `ipv4`, `ipv6 ⊑ internet-protocol`; `wgs-84
  ⊑ world-geodetic-system`; `iers-reference-meridian ⊑ prime-meridian`),
  variants (`https`, `web-mercator-projection`), family members (`android ⊑
  linux`, `freebsd ⊑ berkeley-software-distribution ⊑ unix`, `clojure` and
  `scheme-language ⊑ lisp`), formats built on others (`svg` and
  `gps-exchange-format ⊑ xml`, `office-open-xml ⊑ zip-file-format`),
  `semantic-web ⊑ world-wide-web` (Wikidata P279) and `free-on-board ⊑
  incoterms`.

## Entities

Proper names among the shipped names, found from WordNet `@i`, from a
Wikidata item with P31 but no P279, or from a capitalized Wikidata label,
then read by hand. A name in two packs is listed once per pack.

**core (2):** bible, internet.

**economics (20).** Networks and systems: bitcoin, bitcoin-network,
beacon-chain, ethereum, ethereum-name-service, ethereum-virtual-machine,
ipfs, lightning-network, swarm-storage. Currencies and tokens: ether, dai,
xdai, usdc, bzz, xbzz. Upgrades and software: segwit, bitcoin-taproot,
bitcoin-core, solidity. Rule sets: incoterms.

**computing (203).**
- Organizations: apache-software-foundation, free-software-foundation,
  gnu-project, internet-engineering-task-force, linux-foundation,
  mozilla-foundation, open-source-initiative, wikimedia-foundation,
  world-wide-web-consortium.
- Sites, knowledge bases and datasets: cyc, dbpedia, freebase, github,
  openstreetmap, stack-overflow, wikidata, wikidata-query-service,
  wikimedia-commons, wikipedia, wiktionary, wordnet, yago.
- Networks and systems: internet-protocol-suite, semantic-web,
  world-wide-web.
- Operating systems and software: android, apache-hadoop, apache-kafka,
  apache-spark, apache-subversion, arch-linux, bash-shell,
  berkeley-software-distribution, datomic, debian, docker, fedora-linux,
  freebsd, git, ios, kubernetes, latex, linux, linux-kernel, macos,
  mediawiki, memcached, mercurial, microsoft-windows, mysql, openssh,
  postgresql, raspberry-pi, redis, sqlite, systemd, tex, ubuntu, unix,
  wayland, wikibase, x-window-system, zfs.
- Languages (44): ada-language, algol, apl, c-language, c-plus-plus,
  c-sharp, clojure, cobol, datalog, elixir-language, elm-language,
  erlang-language, f-sharp, forth-language, fortran, go-language, haskell,
  java-language, javascript, julia-language, kotlin, lisp, lua, matlab,
  nim-language, ocaml, pascal-language, perl, php, prolog, python-language,
  r-language, ruby-language, rust-language, scala, scheme-language,
  smalltalk, solidity, sparql, sql, swift-language, typescript, vyper,
  zig-language.
- Protocols, standards and architectures (56): 5g, activitypub, amqp,
  arm-architecture, bittorrent, bluetooth, border-gateway-protocol, dhcp,
  domain-name-system, dublin-core, ethernet, file-transfer-protocol,
  gnutella, graphql, hdmi, http-2, http-3, https,
  hypertext-transfer-protocol, internet-protocol, ipv4, ipv6, kademlia,
  kerberos-protocol, ldap, libp2p, mime, mqtt, network-time-protocol,
  nvm-express, oauth, openid-connect, osi-model, pci-express, posix, quic,
  rdf-schema, resource-description-framework, risc-v, saml, schema-org,
  serial-ata, simple-mail-transfer-protocol, skos,
  transmission-control-protocol, transport-layer-security, uefi, unicode,
  usb, user-datagram-protocol, utf-8, web-ontology-language, webassembly,
  webrtc, wi-fi, x86.
- File formats (37): 7z, avif, csv, epub, flac, geojson, gif,
  gps-exchange-format, gzip, html, jpeg, json, json-ld,
  keyhole-markup-language, markdown, matroska, mp3, mp4, n-triples,
  office-open-xml, ogg, opendocument, pdf, png, postscript, rar,
  rich-text-format, svg, tar-file-format, toml, turtle-syntax, wav, webm,
  webp, xml, yaml, zip-file-format.
- Licenses: apache-license, gnu-general-public-license, mit-license.

**geography (120).**
- Continents, oceans and landmasses: africa, afro-eurasia, americas,
  antarctica, arctic-ocean, asia, atlantic-ocean, australian-continent,
  eurasia, europe, greenland, indian-ocean, north-america, oceania,
  pacific-ocean, south-america, southern-ocean.
- Named features: alps, amazon-river, andes, antarctic-ice-sheet,
  dead-sea, gobi-desert, great-barrier-reef, great-rift-valley,
  greenland-ice-sheet, gulf-stream, himalayas, lake-baikal, mariana-trench,
  mount-everest, nile, north-equatorial-current, sahara,
  south-equatorial-current.
- Lines, poles and hemispheres: antarctic-circle, arctic-circle,
  eastern-hemisphere, equator, iers-reference-meridian,
  international-date-line, north-pole, northern-hemisphere, prime-meridian,
  south-pole, southern-hemisphere, tropic-of-cancer, tropic-of-capricorn,
  western-hemisphere.
- The Earth and its parts: planet-earth, earth-atmosphere,
  earth-structure, earth-crust, earth-mantle, earth-inner-core,
  earth-outer-core, mohorovicic-discontinuity, biosphere, cryosphere,
  geosphere, hydrosphere, pedosphere, earth-magnetic-field, earth-rotation.
- Climate patterns: el-nino-southern-oscillation, la-nina.
- Geologic time (21): hadean, archean, proterozoic, phanerozoic,
  paleozoic, mesozoic, cenozoic, cambrian, ordovician, silurian, devonian,
  carboniferous, permian, triassic, jurassic, cretaceous, paleogene,
  neogene, quaternary, pleistocene, holocene.
- Datums, systems and standards: beaufort-scale, beidou,
  coordinated-universal-time, epsg-geodetic-parameter-dataset, etrs89,
  galileo-navigation-system, geonames, getty-thesaurus-of-geographic-names,
  global-positioning-system, glonass, gps-time, gregorian-calendar,
  international-atomic-time, international-terrestrial-reference-system,
  koppen-climate-classification, military-grid-reference-system,
  north-american-datum, open-location-code, richter-magnitude-scale,
  unix-time, utm-coordinate-system, wgs-84, wide-area-augmentation-system,
  world-geodetic-system.
- Map projections: albers-projection, gall-peters-projection,
  lambert-conformal-conic-projection, mercator-projection,
  mollweide-projection, polyconic-projection, robinson-projection,
  web-mercator-projection, winkel-tripel-projection.

**space (56).**
- The Solar System: solar-system, mercury-planet, venus, mars, jupiter,
  saturn, uranus, neptune, pluto, ceres, eris, phobos, deimos, io, europa,
  ganymede, callisto, titan, enceladus, triton, charon, asteroid-belt,
  kuiper-belt, scattered-disc, oort-cloud.
- Beyond: milky-way, andromeda-galaxy, large-magellanic-cloud,
  small-magellanic-cloud, magellanic-clouds, local-group,
  virgo-supercluster, laniakea-supercluster, orion, trapezium-cluster.
- Craft, missions and programs: apollo-11, apollo-program, falcon-9,
  hubble-space-telescope, international-space-station,
  james-webb-space-telescope, saturn-v, soyuz-spacecraft, space-shuttle,
  sputnik-1, voyager-1, voyager-2.
- Organizations and catalogues: nasa, european-space-agency, isro, cnsa,
  spacex, international-astronomical-union, new-general-catalogue.
- Events and epochs: big-bang, j2000.

**physics (1):** oort-cloud. **mathematics (2):** aes, secp256k1.
**ai, biology, chemistry, medicine:** none.

Borderline, not counted above: named methods, laws and results, which are
individuals but behave as kinds. ai 17 (dijkstra-algorithm, pagerank,
dbscan, chinese-room, turing-test, goodharts-law, …), computing 19
(paxos, mapreduce, cap-theorem, moores-law, huffman-coding, turing-machine,
…), mathematics 9 (godel-incompleteness-theorem, zorn's-lemma, ecdsa,
diffie-hellman, …), economics 3 (black-scholes-model, nash-equilibrium,
fama-french-three-factor-model), space 3 (hubbles-law, keplers-laws,
lambda-cdm-model).

## Spelling

| British name | pack | proposed | note |
|---|---|---|---|
| `centre` | core | `center-point` | pair: `center` is "a building dedicated to a particular activity"; this is "a point equidistant from the ends of a line" |
| `civilisation` | core | `historical-civilization`, or drop | pair, not in ROLES §8: this is "a particular society at a particular time and place", `civilization` "a society in an advanced state of social development". Both ⊑ society with no children, so it may be a near-synonym to drop |
| `draught` | core | `draft-of-air` | pair: `draft` is a version of a written work. Not `air-draft`, which is a ship's clearance height. Its children `downdraft` and `updraft` are already US |
| `honour` | core | `honored-status` | pair: `honor` is the quality of being honorable; this is "the state of being honored", over fame, glory, good-name, good-repute |
| `judgement` | core | `court-judgment` (or `judicial-decision`) | pair, not in ROLES §8: `judgment` is the act of judging; this is a court's determination, over verdict and judgment-of-conviction |
| `labour` | core | `working-class` | pair: `labor` is the work; this is the social class |
| `mould` | core | `casting-mold` | pair: `mold` is the fungus |
| `programme` | core | `broadcast-program` | pair: `program` is the printed program of an event (not software, which is `computer-program`). Its children include `news-program` |
| `storey` | core | `building-story` | `story` is free as a name but is the everyday word for a tale |
| `hard-disc` | computing | `hard-disk` | a duplicate, not a variant: core's `hard-disk` is WordNet's "hard disc, hard disk". The rename merges them and gives the edge the ruling meant, `hard-disk ⊑ magnetic-disk` |
| `ash-grey` | core | `ash-gray` | |
| `axe-head` | core | `ax-head` | core already spells the tool `ax` |
| `fibreboard` | core | `fiberboard` | |
| `mollusc` | core | `mollusk` | many children (`abalone`, …) |
| `orange-colour` | core | `orange-color` | |
| `bodily-humour` | biology | `bodily-humor` | |
| `division-of-labour` | economics | `division-of-labor` | |
| `grey-market` | economics | `gray-market` | |
| `graph-colouring` | mathematics | `graph-coloring` | |
| `levelling` | geography | `leveling` | |
| `predictive-modelling` | ai | `predictive-modeling` | |
| `star-catalogue` | space | `star-catalog` | its parent is already `astronomical-catalog` |
| `hematopoeitic-stem-cell` | biology | `hematopoietic-stem-cell` | a typo, not British |

No proposed name exists in the shipped data or in HEAD, except the two
noted: `civilization` and `hard-disk`.

Optional, since US usage has both forms: `analogue` (core) → `analog`;
`circumstellar-disc` and `scattered-disc` (space) → `-disk`, as US
astronomy writes it and as core's own `disk` does; `herniated-disc` and
`cervical-disc-syndrome` (medicine) → `-disk`. `dialogue` (core) is valid
US spelling, but spelling alone separates it from `dialog` ("a
conversation between two persons"), the same trap as the pairs;
`scripted-dialogue` would end it. Proper names keep their spelling:
`new-general-catalogue`, `vincenty-formulae`.

## Surprises

1. **WordNet files parts as kinds, so its pointers miss them.** Only 7
   shipped edges carry a direct WordNet holonym, and only `egg-white` is a
   finding. `colon`, `thigh`, `humus` and `leaf-blade` have WordNet
   hypernyms to their wholes; the glosses ("the part of the large
   intestine") caught them.
2. **`hard-disc` is a duplicate.** A ruling created `hard-disc ⊑
   magnetic-disk`, and a review line (`removable-disk ⊑ hard-disc`) gives
   `hard-disc` the WordNet offset of core's `hard-disk`. So the computing
   pack shipped a second name for one concept. Computing's
   `hard-disk-drive` and core's `hard-disk` also share a Wikidata item
   (Q4439).
3. **ROLES §8's `program` is not software.** Core's `program` is the
   printed program of an event; software is `computer-program`. The pair
   still needs the rename.
4. **Knowing a name is an entity.** WordNet `@i` marks only 7 shipped
   names, because the build drops instance links. Wikidata's P31 without
   P279 marks 852 of the 7,445 items, but it is noisy: every genus is an
   instance of taxon, and in core 33 of the 34 capitalized hits are
   misalignments (`accountant` is aligned to Gogol's play *The Government
   Inspector*, `cologne` to the city, `island` to a Hong Kong district).
   Core holds just two entities, bible and internet; the 400-odd are in
   the packs. So the surface layer can't learn entities from core; the
   packs would have to declare them.
5. **Most proposed `in(...)` are parts of abstract systems**: a node in a
   network, a layer of a protocol, a term in a contract, a feature of
   Ethereum. ROLES §5 allows "places and parts", but this is the first
   large use of `in` for non-spatial parts. For features like
   `account-abstraction`, `about(ethereum)` is the alternative. Worth
   deciding before step 7.
6. **`bitcoin` names two things.** It is filed as a currency (`bitcoin ⊑
   cryptocurrency`) while its children are parts of the Bitcoin system;
   Wikidata's item is both. `in(bitcoin)` reads it as the system.
7. **No located-in edges at all.** Geography files its named places under
   kinds (`africa ⊑ continent`, `nile ⊑ river`), never under each other,
   and it has no countries or cities. The only place-in-place pressure is
   Earth's own structure (atmosphere, spheres, the Moho).
8. **Not covered:** the occupations pack in ontodag-core HEAD (not
   shipped); and a reading of HEAD's 949 new edges beyond the same
   automatic checks, which found one weak case, HEAD's `blade ⊑ tool`
   ("the flat part of a tool or weapon").

## Decisions (2026-10-07, Peter)

1. **Option B for parts of systems.** Components go under `in(...)`
   (a node, a mempool, a beacon chain, a block, a chunk, a postage
   batch). Mechanisms, rules, measures and features go under `about(...)`
   (gas, account abstraction, MEV, the halving, staking, hash rate,
   difficulty, the block reward). Peter's caveat: the line will not
   always be easy, so the hard cases are marked `borderline` in the TSV
   rather than decided.
2. **A generic part names the kind of whole.** Under the one meaning,
   `in(X)` is "things in some X", so `mempool ⊑ in(bitcoin-network)`
   would say every mempool is in the Bitcoin network. Generic parts
   therefore go under `in(blockchain)`, `in(atmosphere)`,
   `in(automated-market-maker)`; only a part specific to one system names
   it (`beacon-chain ⊑ in(ethereum)`, `earth-sphere ⊑ in(planet-earth)`).
3. **`bitcoin` is the coin, `bitcoin-network` the system**, matching
   `ether` and `ethereum`. `bitcoin-network ⊑ bitcoin` becomes
   `bitcoin-network ⊑ blockchain`, as `ethereum` is filed. The
   distinction is made by words, not case: names are case-sensitive
   (`Bitcoin` and `bitcoin` would be two nodes), but every shipped name
   is lowercase, and a case-only distinction would also collide on
   case-insensitive filesystems through ontodag-fs.

4. **The borderline cases**, decided the same day on Claude's leanings:
   a coin is not `in` its network (they stay related by name only);
   `payment-channel ⊑ smart-contract` and `incoterms ⊑
   contract-condition` (kind only, since neither is always inside one
   particular whole); `world-wide-web` drops `⊑ internet` and keeps `⊑
   computer-network` (it runs over the Internet through HTTP, which is
   neither `in` nor `about`; an `information-system` kind would fit it
   better and doesn't exist yet); `floodhead ⊑ in(flash-flood)` (`in`
   covers the parts of events too).
5. **Spelling** (the same day): every rename is listed in
   `align/renames-step7.tsv`. Group 1 respellings as proposed, plus the
   `hard-disc` merge. The pairs as proposed, except `draught` →
   `air-current`. Two names change sense on Peter's ruling: `civilization`
   is the historical society (the Romans, the Maya), taking over
   `civilisation`, and the advanced-state sense leaves; `floor` is a level
   of a building, taking over `storey`, while the walking surface becomes
   `floor-surface`. `story` stays a tale. The optional variants are taken
   (`analog`, the four `-disk`, `scripted-dialogue`).
