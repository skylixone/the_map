# Open questions — state as of 2026-11-16

Each item: evidence, recommendation, what is needed from the owner. Resolved items move to DECISIONS.md.

## 0. RESOLVED — Geofabrik unreachable from this container (using OSM France mirror, see DECISIONS.md)
`download.geofabrik.de` is on the environment allowlist (the proxy accepts CONNECT), but every TLS handshake is
reset ~3 s after ClientHello (`ws_closed_mid_exchange`), consistently over ~10 min. osmdata.openstreetmap.de,
added in the same change, works. Cause unconfirmed — likely Geofabrik refusing this egress range. Unsure.
Options: (a) retry later; (b) another mirror of a Ukraine-with-Crimea extract (needs a new host + a check that its
cut polygon includes Crimea); (c) owner downloads the pbf locally and runs `scripts/` there.

## 1. Clip outline — recommendation ready, needs owner OK
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

## 4. Generalisation — needs an eyeball decision before the full build
Two variants, both implemented (`VARIANT=` in `scripts/06_tiles.sh`, rationale per flag in its header):
- `explicit`: per-feature minzoom = first zoom where area ≥ 4 screen px²; no tiny-polygon reduction. Only real geometry; sparse at z5–8.
- `tippecanoe-default`: tiny-polygon reduction (sub-pixel polygons → area-preserving pixel squares) + drop-densest. Keeps the
  village-grid texture at low zoom but as synthetic squares.
Plan: sample build over Kyiv + rural Kyiv/Zhytomyr oblast (`BBOX=29.2,49.6,31.8,51.3`), both variants, screenshots at z6/z8/z10/z12.

## 5. Schema sign-off (docs/SCHEMA.md)
Needs OK: `intermittent` flag; whether `settlements.kind` adds `industrial|commercial|retail`; omission of `place`/name;
exclusion of `natural=wetland`; exclusion of tunnelled waterways and ditches/drains; line minzooms (river 6, canal 8, stream 11).

## 6. Kakhovka reservoir
To record after extraction: how OSM tags the former reservoir area today (reservoir / intermittent / wetland / river + scrub).
Not to be "fixed" in the pipeline.
