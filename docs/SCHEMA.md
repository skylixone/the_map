# Tile schema — v1.0 (approved by owner 2026-11-16)

This is the contract between the pipeline and every future control: a style can only use what is listed here.
Status: approved 2026-11-16. Changes need owner sign-off and a version bump here.

## Container
- One file: `data/out/the_map.pmtiles`, MVT, gzip-compressed tiles, EPSG:3857.
- Zooms 0–14 (`-Z0 -z14`); MapLibre overzooms beyond 14.
- Tile extent 4096 (tippecanoe default, detail 12). Tiles are addressed as 512 px tiles by MapLibre, so zoom N in the viewer = tile zoom N.
- Coverage: everything clipped to the Ukraine outline (see `docs/OPEN.md` §1). Outside the outline the tiles are empty;
  the sea and neighbouring countries are just the style's `background`.
- Attribute policy: an attribute exists only if a phase-1 style or check needs it. Absent attribute = default, never `null`.
  No feature IDs (`--generate-ids` off). No names in phase 1.

## Layer `ground`
| geometry | attributes | minzoom |
|---|---|---|
| Polygon | — none — | 0 |

Source: osmdata.openstreetmap.de `land-polygons-split-4326`, unioned and intersected with the outline.
Inland water is **not** cut out of ground; `water` draws on top.

## Layer `water`
Mixed geometry in one layer; style filters on `$type` (`Polygon` / `LineString`).

| geometry | attribute | values | meaning |
|---|---|---|---|
| Polygon | `kind` | `river` | `waterway=riverbank`, `water=river\|stream` |
|  |  | `canal` | `water=canal` |
|  |  | `lake` | `water=lake\|oxbow\|lagoon` |
|  |  | `reservoir` | `water=reservoir`, `landuse=reservoir` |
|  |  | `pond` | `water=pond\|fishpond` |
|  |  | `water` | `natural=water` with no `water=*` (untyped) |
|  |  | `other` | any other `water=*` (basin, wastewater, lock, moat, ditch, …) |
| LineString | `kind` | `river` \| `canal` \| `stream` | `waterway=*` |
| both | `intermittent` | `true` (omitted otherwise) | `intermittent=yes` or `seasonal=yes`. Approved 2026-11-16. Relevant to Kakhovka and southern steppe streams. |

Precedence when tags conflict: `water=*` → `landuse=reservoir` → `waterway=riverbank` → untyped.
Excluded: `waterway=ditch|drain` and any waterway segment with `tunnel=*` other than `no` (culverts and underground streams would draw as surface water).
`natural=wetland` is **not** included in phase 1 (owner decision 2026-11-16).

## Layer `settlements`
| geometry | attribute | values | meaning |
|---|---|---|---|
| Polygon | `kind` | `residential` | `landuse=residential` |
|  | `source` | `osm` | provenance; future: `ghsl`, `wsf` |

`kind` exists so that other sources and landuses can join without a schema break.
`industrial`/`commercial`/`retail`: **excluded** (owner decision 2026-11-16); city cores will show holes where OSM has no residential.
`place`/`name`: **omitted** (approved 2026-11-16). Joining place nodes to residential polygons is ambiguous: one village spans several polygons, and one polygon can hold several places.
Names are the heaviest attribute class. Phase 2 can add a separate `places` point layer for labels instead.

## Generalisation (affects what the tiles contain, so it lives in the contract)
Per-feature minzoom is computed in the pipeline (`tippecanoe.minzoom` in the normalised GeoJSONSeq); it costs no tile bytes.
It is realised by bucketing (one tippecanoe run per minzoom with `-Z<n>`, then tile-join), not by tippecanoe's own feature
minzoom, which is broken in the installed 2.49 (see DECISIONS.md).
- Polygons (`water`, `settlements`): minzoom = first zoom at which the feature covers ≥ `MINZOOM_PX2` screen px²
  (512 px tiles, latitude-corrected). Default `MINZOOM_PX2=4` (≈2×2 px). `ground` is always 0.
- Lines: by kind — `river` 6, `canal` 8, `stream` 11.
- Settlements: minzoom uses the summed area of the cluster of polygons < `CLUSTER_M`=30 m apart, applied to every member
  (variant `clustered`, approved 2026-11-16; rationale in OPEN.md §4 / DECISIONS.md).
- Tippecanoe flags are per layer and documented in `scripts/06_tiles.sh`.

## Verification hooks
`pmtiles show` must report exactly the layers `ground`, `water`, `settlements`, and in `vector_layers`,
fields ⊆ {`kind`, `intermittent`, `source`}. `scripts/07_verify.sh` checks this mechanically.
