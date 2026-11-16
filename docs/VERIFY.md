# Phase 1 verification — 2026-11-16

Build: `scripts/build.sh` with `CLIP_SOURCE=osm VARIANT=clustered` (MINZOOM_PX2=4, CLUSTER_M=30), 9 min 14 s on 4 cores.
Source: OSM France `europe/ukraine.osm.pbf`, replication timestamp 2026-11-15T01:19:34Z, md5 verified.
Land: osmdata.openstreetmap.de `land-polygons-split-4326` (2026-11-16). Outline: OSM relation 60199 (containment test passed).

## Output
`data/out/the_map.pmtiles` — 183,348,349 bytes (175 MiB), z0–14, 317,321 addressed tiles, 226,471 unique tile contents, gzip MVT.

## Feature counts (input to tippecanoe, after clipping)
| layer | geometry | count | breakdown |
|---|---|---|---|
| ground | polygon | 454 | mainland + islands |
| water | polygon | 151,206 | water 93,523 · pond 30,049 · reservoir 10,346 · lake 8,269 · river 4,737 · other 4,006 · canal 276 |
| water | line | 129,629 | stream 106,844 · river 15,876 · canal 6,909 |
| water | `intermittent=true` | 32,633 | across polygons and lines |
| settlements | polygon | 205,681 | residential/osm; 58,548 clusters (30 m) |

Tile-level counts (tilestats, features summed over tiles): ground 322,206 · water 1,638,762 · settlements 1,807,648.
Size-limit fallback (`--drop-smallest-as-needed`) triggered in **no** tile.

## Metadata vs SCHEMA.md (`scripts/07_verify.sh`)
Layers exactly {ground, water, settlements}. Fields: ground {} · water {kind, intermittent} · settlements {kind, source}. PASS.

## No-loss check (decoded tiles vs input with minzoom ≤ z)
| tile | settlements in tile / expected | water in tile / expected |
|---|---|---|
| Kyiv 12/2395/1381 | 308 / ≥300 | 58 / ≥53 |
| Simferopol 10/608/368 | 926 / ≥778 | 113 / ≥99 |
| Poltava rural 9/304/174 | 358 / ≥325 | 166 / ≥156 |
| Kyiv 7/74/43 | 10,375 / ≥9,540 | 1,553 / ≥1,498 |
Extras = features in the tile buffer. PASS.

## Visual checks (`docs/img/verify/phase1-2026-11-16.png`)
- Kyiv z11 — dense block-level residential, Dnipro channels and islands. OK.
- Rural Poltava oblast z10 — village polygons present across the frame. Completeness vs reality: see settlement spike.
- Crimea z7.3 — included, coastline intact; Syvash lagoons as water polygons.
- Sevastopol z11/z12 — straight-looking edge north of the bay is the real Lyubimovka–Kacha beach (checked at z12), not an artefact.
- Kerch Strait z11 — Kerch and Tuzla Is. present; no Taman/Chushka land; bridge not drawn (not in schema).
- Danube delta z10 — ground ends at the Chilia branch (RO border). OK.
- Kherson coast z10 — the 39 km² OSM/COD difference is a large lake/lagoon complex mapped as water; consistent within OSM.
- Overview z5.3 — settlements very sparse: consequence of the approved 4 px² rule. Knob: `MINZOOM_PX2`.

## Kakhovka reservoir (as OSM maps it on 2026-11-15)
No reservoir polygon remains. The former reservoir is mapped as:
- the Dnipro channel: one 117.5 km² `natural=water` polygon (no `water=*`) spanning 33.36–35.06° E → `kind=water`, not intermittent;
- the drained bed: `natural=wetland` + `wetland=marsh` + `intermittent=yes` (98 km² of a 430 km² sample window at 33.85–34.15° E, 47.25–47.42° N;
  rest of window mostly bank-side farmland/wood).
Consequence under schema v1.0 (no wetland): the former reservoir renders as ground with a narrow river channel. Not altered.

## Not done / open
- tippecanoe 2.79.0 test (OPEN.md §7) — blocked by the session permission check.
- Settlement coverage vs GHSL/WSF — `docs/briefs/settlement-coverage-spike.md`.
