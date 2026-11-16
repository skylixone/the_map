# Decisions

Format: `YYYY-MM-DD — decision — reason`. Append only; supersede with a new line that references the old one.

- 2026-11-16 — Renderer: MapLibre GL JS + `pmtiles` protocol, one vanilla HTML viewer, no build step — minimal surface; framework choice deferred past phase 1.
- 2026-11-16 — Primary source: Geofabrik "Ukraine (with Crimea)" extract (~836 MB `.osm.pbf`) — Crimea is included; single country-sized download.
- 2026-11-16 — Land/sea from osmdata.openstreetmap.de pre-processed polygons, not from the extract — coastline assembly is error-prone and already solved upstream.
- 2026-11-16 — Phase 1 scope: `ground`, `water`, `settlements` only — controls/export/styling wait until tiles are verified.
- 2026-11-16 — Data lives in `data/` (gitignored); repo holds scripts, docs, viewer only — pbf and pmtiles are too large and fully reproducible.
- 2026-11-16 — Cloud environment `the_map` (personal) with allowlist: geofabrik, osmdata, geoboundaries, github (+raw/media), HDX — keeps project-only hosts off the Default environment.
- 2026-11-16 — Toolchain: osmium-tool 1.16, gdal-bin 3.8, tippecanoe 2.49 (Ubuntu 24.04 apt), go-pmtiles v1.31.2, shapely 2 in `.venv` — all available via allowed package channels; no source builds.
- 2026-11-16 — Not planetiler — clipping to a country polygon needs a custom Java profile (`--polygon` only limits tile coverage), its generalisation lacks tippecanoe's density-driven dropping, and its release jar is not on Maven Central (only GitHub releases).
- 2026-11-16 — Tag mapping, clipping and minzoom in one Python step (`scripts/lib/normalize.py`) — the schema becomes one readable table; shapely prepared-geometry clip skips intersection for fully-inside features.
- 2026-11-16 — One tippecanoe run per layer, then tile-join → mbtiles → `pmtiles convert` — generalisation flags must differ per layer (ground must never drop).
- 2026-11-16 — Visibility via per-feature `tippecanoe.minzoom` from screen area (512 px tiles, lat-corrected) — explicit, deterministic, zero tile bytes. Provisional until the A/B in OPEN.md §4.
- 2026-11-16 — `--detect-shared-borders` on water and settlements — adjacent polygons simplify identically; no hairline seams.
- 2026-11-16 — Viewer pins maplibre-gl 5.24.0 + pmtiles 4.5.0 from unpkg — 6.x API unchecked; 5.24.1 is under two weeks old.
- 2026-11-16 — Local serving via `scripts/serve.py` (Range-capable) — `python -m http.server` ignores Range, PMTiles needs it.
- 2026-11-16 — Schema: `water.intermittent` (true|omitted) in; `settlements.kind` stays `residential` only (no industrial/commercial/retail); no `natural=wetland` — owner decision.
- 2026-11-16 — PBF from OSM France mirror (`download.openstreetmap.fr/extracts/europe/ukraine.osm.pbf`, 970 MB) — Geofabrik resets every TLS handshake from the cloud env for 30+ min; OSM-FR cut polygon verified to contain 100% of the COD-AB outline incl. Crimea. Supersedes the Geofabrik line above for this environment.
- 2026-11-16 — Clip outline: compare COD-AB (Kartographia, HDX) as a third candidate — owner decision; analysis in OPEN.md §1.
- 2026-11-16 — Clip outline candidates measured (OSM 60199, geoBoundaries, COD-AB); recommendation OSM 60199 + containment guard, COD-AB as reference — evidence in OPEN.md §1. Provisional default `CLIP_SOURCE=osm` pending owner OK.
- 2026-11-16 — Do not use tippecanoe feature `"tippecanoe":{"minzoom"}` with tippecanoe 2.49 (Ubuntu noble) — synthetic test: minzoom 5 first appears z14, minzoom 12 at z13; first sample build lost ~99 % of polygons (Kyiv z12 tile: 1 of 300). Workaround: `scripts/lib/bucket.py` splits by minzoom, one run per bucket with `-Z<n>`, tile-join merges same-named layers (verified: no loss). Unverified whether upstream 2.79.0 fixes it; building from source was not approved.
- 2026-11-16 — Verification includes decoding sample tiles and comparing feature counts with the input (not only metadata) — the minzoom loss passed every metadata check.
- 2026-11-16 — Added generalisation variant `clustered` (default, provisional): settlement minzoom from cluster area (polygons < 30 m apart) — per-polygon area inverted urban density at z≤8 because OSM block-maps cities. Pending owner eyeball, OPEN.md §4.
- 2026-11-16 — Owner approved: clip to OSM relation 60199 (guarded) with COD-AB as reference; generalisation variant `clustered` (MINZOOM_PX2=4, CLUSTER_M=30); schema v1.0; name/place omitted.
- 2026-11-16 — Phase 1 built and verified: 175 MiB PMTiles, counts/metadata/no-loss/visual checks in docs/VERIFY.md. Kakhovka left as OSM maps it (bed = intermittent marsh, excluded by schema).
