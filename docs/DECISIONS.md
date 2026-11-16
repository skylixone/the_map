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
