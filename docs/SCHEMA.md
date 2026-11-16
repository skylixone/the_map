# Tile schema — DRAFT v0.1 (awaiting owner OK)

This is the contract between the pipeline and every future control: a style can only use what is listed here.
Status: **proposed, not approved.** No full build until the owner signs off.

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
| both | `intermittent` | `true` (omitted otherwise) | `intermittent=yes` or `seasonal=yes`. **Proposed — needs OK.** Relevant to Kakhovka and southern steppe streams. |

Precedence when tags conflict: `water=*` → `landuse=reservoir` → `waterway=riverbank` → untyped.
Excluded: `waterway=ditch|drain` and any waterway segment with `tunnel=*` other than `no` (culverts and underground streams would draw as surface water).
`natural=wetland` is **not** included in phase 1.

## Layer `settlements`
| geometry | attribute | values | meaning |
|---|---|---|---|
| Polygon | `kind` | `residential` | `landuse=residential` |
|  | `source` | `osm` | provenance; future: `ghsl`, `wsf` |

`kind` exists so that other sources and landuses can join without a schema break. Candidates, **not included unless approved**:
`industrial`, `commercial`, `retail` (they fill visible holes in city cores, Kyiv especially).
`place`/`name`: **recommend omitting.** Joining place nodes to residential polygons is ambiguous: one village spans several polygons, and one polygon can hold several places.
Names are the heaviest attribute class. Phase 2 can add a separate `places` point layer for labels instead.

## Generalisation (affects what the tiles contain, so it lives in the contract)
Per-feature minzoom is computed in the pipeline and passed to tippecanoe as `"tippecanoe":{"minzoom":n}`; it costs no tile bytes.
- Polygons (`water`, `settlements`): minzoom = first zoom at which the feature covers ≥ `MINZOOM_PX2` screen px²
  (512 px tiles, latitude-corrected). Default `MINZOOM_PX2=4` (≈2×2 px). `ground` is always 0.
- Lines: by kind — `river` 6, `canal` 8, `stream` 11.
- Tippecanoe flags are per layer and documented in `scripts/06_tiles.sh`. Two candidate generalisation variants
  will be compared on a sample region before the full build (see `docs/OPEN.md` §4).

## Verification hooks
`pmtiles show` must report exactly the layers `ground`, `water`, `settlements`, and in `vector_layers`,
fields ⊆ {`kind`, `intermittent`, `source`}. `scripts/07_verify.sh` checks this mechanically.
