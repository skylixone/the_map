# the_map

Layered vector web map of Ukraine. Source data → one PMTiles file → bare MapLibre viewer.
The repo is the only shared memory between sessions: decisions go into files, not chat.

## Phase 1 (current)
Three semantic layers — `ground`, `water`, `settlements` — clipped to Ukraine's internationally
recognised border (incl. Crimea), built into `data/out/the_map.pmtiles`, shown in `viewer/index.html`.
Out of scope until phase 1 is verified: settings sheet, styling controls, print/PNG export, framework choice.

## Stack
- Viewer: one vanilla HTML file, MapLibre GL JS + `pmtiles` protocol, no build step.
- Sources: OSM via Geofabrik "Ukraine (with Crimea)" `.osm.pbf`; land/water from osmdata.openstreetmap.de
  pre-processed coastline polygons (never build sea from the extract).
- Pipeline: `scripts/` — download → osmium tags-filter → GeoJSONSeq → clip → tippecanoe → PMTiles. Rerunnable.
- Settlement shape source must stay swappable (see `docs/briefs/settlement-coverage-spike.md` when written).

## Pointers
- `docs/SCHEMA.md` — tile schema. **The contract.** Changes need owner sign-off.
- `docs/DECISIONS.md` — dated one-line decisions with reasons. Append, don't rewrite.
- `docs/OPEN.md` — open questions and their current state.
- `docs/briefs/<topic>.md` — self-contained briefs for split-off sessions.
- `data/` — all downloaded and generated data. Gitignored.

## Working rules
- Owner is a senior UI/UX designer: dense, explicit, say "unsure" rather than smooth over.
- Ask before anything slow, large, or hard to undo (big downloads, full builds, schema changes).
- Line widths in MapLibre are screen px; no `vector-effect`.
