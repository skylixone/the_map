# Open questions — state as of 2026-11-16

Each item: evidence, recommendation, what is needed from the owner. Resolved items move to DECISIONS.md.

## 0. BLOCKER — Geofabrik unreachable from this container
`download.geofabrik.de` is on the environment allowlist (the proxy accepts CONNECT), but every TLS handshake is
reset ~3 s after ClientHello (`ws_closed_mid_exchange`), consistently over ~10 min. osmdata.openstreetmap.de,
added in the same change, works. Cause unconfirmed — likely Geofabrik refusing this egress range. Unsure.
Options: (a) retry later; (b) another mirror of a Ukraine-with-Crimea extract (needs a new host + a check that its
cut polygon includes Crimea); (c) owner downloads the pbf locally and runs `scripts/` there.

## 1. Clip outline
Evidence:
- OSM policy history: DWG 2014 — Crimea in both UA and RU admin relations, marked disputed. DWG 2018-11 — move to RU only.
  OSMF board 2018-12 — appeal granted, the exception (Crimea in UA relation) kept. Current state of relation 60199: **unverified**,
  test from the extract (`CLIP_SOURCE=osm scripts/02_outline.sh` fails loudly if Crimea is outside).
- geoBoundaries gbOpen UKR ADM0 (build 2023-12, `boundaryYearRepresented: 2017`) is **itself OSM-derived** (Wambacher export).
  Tested: one polygon, includes Crimea, Sevastopol, Kerch, Arabat Spit, Zmiinyi, Tuzla; excludes Taganrog, Chișinău, Brest, Tulcea, Taman.
  Includes the 12 nmi territorial sea (640,065 km² vs ~603,600 km² land).
  Weakness: 28,714 vertices / 9,315 km perimeter ≈ 324 m mean spacing → visible facets on river borders (Danube, Dniester, Prut) at z12+.
  Kerch Strait line near Chushka Spit to be checked visually.
- OCHA COD-AB (source: Kartographia, UA state enterprise) has Crimea UA01 and Sevastopol UA85. Not fetched. Likely land-only with a
  coarser coastline than OSM — unsure.
Why territorial sea matters: ground = land polygons ∩ outline, so the coastline comes from OSM land polygons, not the outline.
An outline that stops at its own (coarser) coastline would shave the OSM coast.
**Recommendation:** OSM relation 60199 from the extract if it passes the containment test (densest, current, same source as the
rest); otherwise geoBoundaries. Default in `config.sh` is `geoboundaries` until the test has run.

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
