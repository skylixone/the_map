# Open questions — state as of 2026-11-16

Each item: evidence, recommendation, what is needed from the owner. Resolved items move to DECISIONS.md.

## 0. RESOLVED — Geofabrik unreachable from this container (using OSM France mirror, see DECISIONS.md)
`download.geofabrik.de` is on the environment allowlist (the proxy accepts CONNECT), but every TLS handshake is
reset ~3 s after ClientHello (`ws_closed_mid_exchange`), consistently over ~10 min. osmdata.openstreetmap.de,
added in the same change, works. Cause unconfirmed — likely Geofabrik refusing this egress range. Unsure.
Options: (a) retry later; (b) another mirror of a Ukraine-with-Crimea extract (needs a new host + a check that its
cut polygon includes Crimea); (c) owner downloads the pbf locally and runs `scripts/` there.

## 1. RESOLVED 2026-11-16 — Clip outline: OSM 60199 + containment guard, COD-AB as reference
Three candidates measured (2026-11-16; scripts in `scripts/02_outline.sh`, `scripts/lib/outline.py`):

| | OSM relation 60199 (extract 2026-11-15) | geoBoundaries gbOpen UKR ADM0 | OCHA COD-AB admin0 (Kartographia) |
|---|---|---|---|
| Crimea, Sevastopol, Kerch, Tuzla, Zmiinyi inside | yes | yes | yes |
| Taman, Taganrog, Chișinău, Tulcea, Brest outside | yes | yes | yes |
| Lineage | live OSM | OSM snapshot 2017 (Wambacher) | UA state cartography, valid_on 2025-09-01 |
| Vertices | 81,655 | 28,714 | 168,956 (158 parts) |
| Seaward extent | 12 nmi territorial sea | 12 nmi territorial sea | land only, own coastline |
| Land border vs COD (p50/p90/p99/max) | 9 / 60 / 397 / 2,257 m | 15 / 109 / 418 / 1,957 m | — |

OSM policy history: DWG 2014 kept Crimea in both UA and RU relations (disputed); DWG 2018-11 moved it to RU only; OSMF board
2018-12 granted the appeal and kept the exception. The 2026-11-15 data confirms relation 60199 still contains Crimea.

COD-AB as a clip needs a coastal patch: its coast differs from the OSM coast (OSM land beyond COD coast: 556 km² in ~6,700
slivers, 98 % within 2 km; COD land that OSM maps as sea: 1,753 km², mostly limans/bays). A plain coastal band pulls in
foreign land (Taman/Chushka at Kerch, Romanian Danube delta), so it needs guards. OSM 60199 needs none: same mappers as the coastline.
Largest OSM–COD land-border gap: 2.26 km on the Dnipro (Belarus border) at 30.575,51.644 — river channel interpretation, unsure which is right.
Largest area gap: 39 km² at 33.93,46.16 (Kherson coast) inside OSM outline, outside COD — visual check pending.

**Recommendation:** OSM 60199, guarded by the containment test (build fails if a future edit drops Crimea); keep COD-AB as the
verification reference. `CLIP_SOURCE=osm` is the default provisionally; `geoboundaries` remains selectable.

## 2. Settlement shape source
Start: OSM `landuse=residential`. Modular seam: `scripts/sources/settlements_<name>.sh` + `SETTLEMENT_SOURCES` in
`scripts/lib/normalize.py`; output contract `data/work/settlements.raw.geojsonseq`. Spike brief: `docs/briefs/settlement-coverage-spike.md`.

## 3. Max zoom
`-z14`, MapLibre overzooms. Revisit if print becomes real.

## 4. RESOLVED 2026-11-16 — Generalisation: variant C `clustered`
Sample: Kyiv + rural Kyiv/Zhytomyr oblast (`BBOX=29.2,49.6,31.8,51.3`, `scripts/sample.sh`), three variants:
- A `explicit`: polygon visible from the first zoom where *its own* area ≥ 4 px². **Flaw:** OSM maps cities as many
  block-sized polygons and villages as one, so at z6–8 Kyiv is sparser than its exurbs (inverted density).
- C `clustered`: same, but area = sum over the cluster of polygons < 30 m apart (≈ street width). 14,674 polygons → 4,200
  clusters. Real geometry only; Kyiv reads as the densest area again. **Recommended.**
- B `tippecanoe-default`: tiny-polygon reduction (pixel squares) + drop-densest. Densest texture at z≤6, partly synthetic.
From z10 up all three are visually identical (`docs/img/generalisation/ab-kyiv-z12.png`, `ab-rural-z10.png`).
Sizes for the sample: A 13 MB, B 14 MB, C 13 MB.
Open knobs: `MINZOOM_PX2` (4), `CLUSTER_M` (30).
Hairlines between residential blocks at z12 — measured (central Kyiv, 2,052 neighbour pairs < 40 m): 12.5 % share an edge,
62 % are 5–30 m apart. So they are mostly real streets (OSM maps residential per block); a 10 m street is < 1 px at z12 and
renders as an antialiased hairline. Style question for phase 2 (e.g. closing gaps), not a data defect. Edge-sharing pairs are
always in the same cluster -> same minzoom bucket -> `--detect-shared-borders` still applies to them.

## 5. RESOLVED 2026-11-16 — Schema v1.0 signed off (docs/SCHEMA.md)
Needs OK: `intermittent` flag; whether `settlements.kind` adds `industrial|commercial|retail`; omission of `place`/name;
exclusion of `natural=wetland`; exclusion of tunnelled waterways and ditches/drains; line minzooms (river 6, canal 8, stream 11).

## 6. RESOLVED 2026-11-16 — Kakhovka reservoir recorded (docs/VERIFY.md)
OSM maps the drained bed as intermittent marsh (`natural=wetland`, excluded by schema v1.0) and the channel as untyped
`natural=water`. On our map the former reservoir is ground with a narrow river. If the bed should be visible, the lever is
adding `wetland` to the water layer (schema change, owner decision).

## 8. Low-zoom density (overview z5–6 is sparse)
Consequence of MINZOOM_PX2=4 with clustered areas. Options if unwanted: lower MINZOOM_PX2 at low zoom only, or per-zoom px²
thresholds. Owner eyeball.

## 7. tippecanoe upstream (2.79.0) — does it fix feature minzoom?
Owner approved building it in the cloud container; the session's permission check blocked the clone/build twice.
Not needed for phase 1 (bucketing workaround verified). Test elsewhere or after adding a permission rule.
