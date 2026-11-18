# Roadmap — country-level map

Status 2026-11-18: owner answered §4 (see §6); Q2 awaits a pick after the advice in §6. Nothing here is built yet.

## 1. Problem
Goal: one map where all of Ukraine fits in a single view and still reads as Ukraine — built-up areas, rivers and water at
country scale. Phase 1 delivered a **detail base** instead: z0–14 tiles whose only generalisation is *selection by size*
(a polygon appears once its cluster covers ≥4 px²). There is no aggregation and no simplification beyond tippecanoe's
default. At country zoom, that leaves almost nothing (owner on the phone artifact, 2026-11-17: built-up areas pop in on zoom-in and vanish on zoom-out).

Where "country view" is (Ukraine ≈ 1,335 km E–W at 48.5°N; 512 px tiles; m/px ≈ 51,862 / 2^z):

| target | width px | zoom that fits Ukraine | 1 px on the ground |
|---|---|---|---|
| phone portrait | ~400 | ≈ 3.9 | ≈ 3.3 km |
| desktop window | ~1200 | ≈ 5.5 | ≈ 1.1 km |
| A3 landscape, 300 dpi (if print comes) | 4961 | ≈ 7.6 | ≈ 270 m |
| A2 landscape, 300 dpi | 7016 | ≈ 8.1 | ≈ 190 m |

How much of phase 1 survives at those zooms (`data/work/layers/settlements.geojsonseq.stats.json`):

| zoom ≤ | settlement polygons present | share of 205,681 |
|---|---|---|
| 4 | 375 | 0.2 % |
| 5 | 11,110 | 5.4 % |
| 6 | 50,871 | 24.7 % |
| 7 | 104,469 | 50.8 % |
| 8 | 143,189 | 69.6 % |

Water lines start at z6 (river), z8 (canal) and z11 (stream), so a phone-sized or desktop-sized country view has **no river
lines at all**, only large water polygons (Dnipro reservoirs, Danube).

## 2. Fundamental truths
- At z4–6 one pixel covers 1–3 km. A typical village polygon is far smaller (unmeasured: compute the area
  distribution in C3), so any per-polygon depiction is either invisible or aliasing noise.
- What a reader perceives at that scale is *aggregate*: where built-up land is dense, how big the towns are, and how the river network runs.
  Producing that needs three operations phase 1 doesn't have:
  1. **aggregation** — merge neighbouring polygons into built-up areas;
  2. **simplification** — vertex density matched to the pixel;
  3. **selection by importance** — rivers by length or rank, not by drawn width; settlements by aggregate size.
- Tile-level tricks (dropping, coalescing) cannot do aggregation correctly. Doing it in the pipeline, in a metric CRS, is
  the only controllable route.
- The detail base stays valid for the planned oblast-level and settlement-level maps. The country map is a **different
  product**, not a fix to phase 1.

## 3. Phases
**C0 — Freeze the detail base (now).** Record phase 1 as the detail base. Code state: commit `9911c10` (phase 1 verified), plus
the viewers after it. What is retained and where: §5.

**C1 — Owner decisions (§4).** Target sizes, settlement depiction, river selection, product shape. Blocks C2.

**C2 — Schema `country` v0.1 (`docs/SCHEMA-country.md`), owner sign-off.** Proposed layers:
- `ground` — the outline land, simplified per zoom band.
- `water` — large lake and reservoir polygons above an area threshold; river lines selected by importance (§4 Q3), one
  merged line per river, simplified.
- `builtup` — aggregated settlement polygons: buffer +d → union → buffer −d (morphological closing) → simplify(tol) →
  drop < min area. Attribute `size` as an area bucket, so style can scale emphasis. No names (as in phase 1).
- (optional, Q2) `places` — points for settlements that are too small to read as areas, if dots are wanted.

**C3 — Pipeline `scripts/country/`.** Input is the phase-1 normalised layers (`data/work/layers/*.geojsonseq`), so
no re-extract is needed. Work in a metric CRS: EPSG:3035 LAEA Europe or UTM 36N, to be decided. Parameters come from the pixel size
of each zoom band: closing distance d ≈ 1–2 px, tolerance ≈ 0.5 px, min area ≈ 4 px². Before choosing values, measure the
size distribution of settlement clusters and of the gaps between them. Output: `data/out/the_map-country.pmtiles`, z0–8.

**C4 — Sample and compare.** Build 2–3 parameter sets. Show each as a contact sheet at phone z3.9, desktop z5.5 and print z7.6 (if
print is in scope), next to the phase-1 render. The owner picks.

**C5 — Build, verify, publish.**
- Verification: counts per layer; built-up area before/after aggregation (the share kept,
  to make the exaggeration explicit); a decode check like phase 1; visual checks.
- Publish: if the file is ≤15 MB (expected, unsure until built), it goes into the artifact as one file with no
  piece-splitting.

**Later (out of scope here):** the oblast map and the settlement map, both from the detail base, each with its own
viewport and print targets; the settlement-coverage spike (`docs/briefs/settlement-coverage-spike.md`) feeds both.

## 4. Owner decisions needed
1. **Targets.** Screen only (phone and desktop), or print too, and at what size? Print at A3/A2 pushes the country map
   to z7.6–8.1, which means four times finer geometry.
2. **Settlements at country scale:**
   - (a) aggregated footprints only, so small villages vanish;
   - (b) footprints for towns and cities plus dots for villages, which needs `places` points and population or status;
   - (c) a built-up density surface (GHSL-derived), which overlaps with the coverage spike.
   Recommendation: (a) first, add dots if it reads empty.
3. **River selection:**
   - length of the named river (OSM `waterway` relations or merged ways);
   - named only;
   - Strahler order, which needs network topology and is slower.
   Recommendation: length of the named river, with a threshold set per zoom band.
4. **Product shape:**
   - a separate `the_map-country.pmtiles` (z0–8) next to the detail file, or
   - one file with zoom bands (country layers at z0–8, detail at z9+).
   Recommendation: separate. They are different products with different schemas, and a small file publishes to a phone as a single file.
5. **Retention of the raw OSM extract** (§5): where should 970 MB live, or is re-downloading (newer data) acceptable?

## 5. Retention — what survives this cloud container
The container is ephemeral and `data/` is gitignored.

| what | size | durable copy | how to get it back |
|---|---|---|---|
| code, docs, schema | small | git, branch `claude/the-map-hq-kickoff-utk6v8` | clone |
| phase-1 tiles `the_map.pmtiles` | 175 MiB | private artifact https://claude.ai/artifact/Qonz2CqpPaqXzKk7KijLMx, 175 base64 pieces `t/cNNN.txt` | Claude: Artifact `read` with `paths` for all 175 pieces, then `base64 -d` each and `cat` them in order; md5 below |
| OSM extract `ukraine-latest.osm.pbf`, 2026-11-15T01:19:34Z | 970 MB | GitHub, Git LFS, data-only branch `data/osm-2026-11-15` (pushed 2026-11-18, LFS oid sha256 `89589465c34e…936c`); to be copied to the owner's Mac | `git fetch origin data/osm-2026-11-15` + `git lfs pull`, or a worktree of that branch; check md5 below |
| land polygons, geoBoundaries, COD-AB | 1.3 GB | none needed | re-download (`scripts/01_download.sh`); sources are versioned upstream |
| normalised layers `data/work/layers/` | 404 MB | none | regenerate from the PBF: `scripts/02–05`, ~10 min |

Checksums: PBF md5 `6a81a0abe569f39e155d945bb8aa68d2`; PMTiles md5 `05dafa74ff90ffd811cae0d1c0dffe26` (183,348,349 bytes).

## 6. Owner answers 2026-11-18 and measurements behind the open one
1. **Targets: screen** (phone z≈3.9 – desktop z≈5.5). Print later, from the same pipeline. Mechanism: print must be
   rendered as a *large viewport at the print zoom* (A3 300 dpi ≈ z7.6), not as a high `pixelRatio` at screen zoom —
   MapLibre picks tiles by zoom, so a 3× pixelRatio at z5.5 would print z5-band geometry (simplified to 0.5 screen px =
   1.5 print px, visibly coarse). Therefore the country file keeps bands up to **z8** even though screen needs ≤ z6.
2. **Settlements: (b) or (c) — open, advice below.**
3. **Rivers: (b) named rivers, with a togglable level.** Interpretation (assumption, confirm): only named rivers enter
   the country file, each carrying a `rank` (length class), and the viewer gets a control for how many ranks show.
4. **Product: separate file** `the_map-country.pmtiles`.
5. **Raw extract:** a newer download is acceptable; keep the 2026-11-15 snapshot on GitHub (Git LFS, data-only branch
   `data/osm-2026-11-15`) until it can be copied to the owner's Mac.

### Measurements (2026-11-18, phase-1 data, scripts in session scratchpad, numbers reproducible from data/work)
Settlement clusters (CLUSTER_M=30): 58,548; area p10 0.002 / p50 0.055 / p90 1.34 / p99 6.07 / max 66.0 km².
The median cluster (~235 × 235 m) is ≈1.3 px² even at z8.

| zoom | 1 px | clusters ≥ 4 px² (readable as area) | clusters ≥ 1 px² |
|---|---|---|---|
| 4 | 3.2 km | 5 | 183 |
| 5 | 1.6 km | 183 | 2,533 |
| 6 | 810 m | 2,533 | 10,724 |
| 7 | 405 m | 10,724 | 21,611 |
| 8 | 203 m | 21,611 | 31,363 |

OSM place nodes inside the outline vs residential polygons:

| place | count | `population` tagged | residential polygon within 300 m |
|---|---|---|---|
| city | 47 | 100 % | 96 % |
| town | 1,261 | 100 % | 82 % |
| village | 25,155 | 100 % | 69 % |
| hamlet | 3,290 | 97 % | 49 % |

Population provenance: 99 % have neither `population:date` nor `source:population`; likely an old census import
(2001?) — **unsure**, and pre-war in any case. Usable for size *classes*, not as current figures.
Named rivers: 32,133 `waterway=river` ways, 83 % named, 67,717 km; 2,466 distinct names; 806 `waterway=river`
relations. Names with merged length ≥ 500 / 200 / 100 / 50 / 20 km: 6 / 36 / 102 / 287 / 782. Merging by name
conflates same-named different rivers (common names like Суха Балка) — C3 merges by relation first, by name + connectivity second.

### Advice on Q2: (b), with (c) as a later optional underlay
- At desktop country zoom only ~200–2,500 clusters can read as areas; ~26k villages exist. Footprints alone cannot
  carry the country picture — something point-like is needed for the rest.
- (b) needs no new source: place nodes are complete for city/town/village with population on ~100 %, and they cover
  the 31 % of villages / 18 % of towns that have no residential polygon nearby (OSM coverage gaps). Footprints of the
  big clusters plus population-classed dots read as "where the places are" and lead straight into a later labels phase.
- (c) answers a different question ("how dense is building"): needs GHSL (new source, JRC host not allowed yet), a raster
  or contour pipeline, and its epochs are pre-war like the OSM populations. It is exactly what the settlement-coverage
  spike evaluates, so decide (c) from the spike's result, as a togglable underlay — it doesn't block (b).
