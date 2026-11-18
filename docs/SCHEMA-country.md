# Country tile schema — v0.1 DRAFT (needs owner sign-off before C3 starts)

Second product next to the detail file (`docs/SCHEMA.md`, unchanged). Purpose and the numbers behind it are in
`docs/ROADMAP.md` (§1, §6). Owner choices this encodes (2026-11-18): screen targets with print later (bands to z8);
settlements = option (b), areas plus dots; rivers = only those ≥ 200 km; a separate file.

## Container
- `data/out/the_map-country.pmtiles`, MVT, gzip, EPSG:3857, **z0–8**, extent 4096.
- Same clip outline as phase 1 (OSM relation 60199, guarded). Outside it, tiles are empty.
- Attribute policy as in phase 1: an attribute exists only if a style needs it; absent means default; no IDs, no names.
- Size: expected ≤ 15 MB, so it publishes to the phone page as one file. **Unsure** until the first sample build.

## Zoom bands
Every areal layer is generalised **per zoom**: one geometry set per z = 0…8, each tiled into its own zoom only
(`-Z z -z z`), then joined. This avoids tippecanoe 2.49's broken feature minzoom, as in phase 1. Pixel size at 48.5°N with 512 px
tiles: 1 px ≈ 51,862 / 2^z m.

| z | 1 px | closing gap (< 1 px) | min area (4 px²) | simplify (0.5 px) |
|---|---|---|---|---|
| 4 | 3.24 km | 3.24 km | 42 km² | 1.62 km |
| 5 | 1.62 km | 1.62 km | 10.5 km² | 810 m |
| 6 | 810 m | 810 m | 2.6 km² | 405 m |
| 7 | 405 m | 405 m | 0.66 km² | 203 m |
| 8 | 203 m | 203 m | 0.16 km² | 101 m |

z0–3 reuse the z4 parameters. **Areal generalisation G(z)**, done in a metric CRS (UTM 36N, EPSG:32636):
1. union the inputs;
2. buffer +½ gap, then −½ gap. This is a morphological closing: features less than 1 px apart merge and sub-pixel gaps close;
3. drop parts smaller than the min area;
4. simplify to 0.5 px with topology preserved;
5. clip to the outline.

The three parameters (gap 1 px, area 4 px², simplify 0.5 px) are the knobs for C4. The values above are the starting set.

## Layer `ground`
| geometry | attributes | zooms |
|---|---|---|
| Polygon | none | 0–8 |

The phase-1 `ground` with steps 3–4 of G(z): islands smaller than 4 px² dropped, simplified to 0.5 px. No closing, because merging
coastline gaps would fill real bays and spits.

## Layer `water`
| geometry | attributes | zooms | content |
|---|---|---|---|
| Polygon | none | 0–8 | G(z) over every phase-1 water polygon except `intermittent` ones |
| LineString | none | 0–8 | rivers ≥ 200 km, one merged line per river, simplified 0.5 px |

- `kind` is dropped: one water colour at country scale. Intermittent polygons are excluded. That covers dry beds and seasonal lakes, and Kakhovka
  keeps its permanent channel only. **Owner check.**
- River selection is by **length inside the outline**: ~36 rivers by the name-merge estimate (ROADMAP §6). Members are merged by
  `waterway=river` relation first, then by name plus connectivity, so that rivers sharing a name don't add up. C3 reports the exact list for review.
- Border rivers (Danube's Kiliia branch, Prut, Tysa, parts of the Dniester) run *along* the outline, so clipping can
  shred them. Lines are clipped to the outline buffered by 1 px at z8, about 200 m. **Unsure** whether that is enough; check in C4.

## Layer `builtup`
| geometry | attributes | zooms |
|---|---|---|
| Polygon | none | 0–8 |

G(z) over phase-1 `settlements` polygons (OSM `landuse=residential`). Expected readable areas: about 183 at z5,
2,533 at z6 and 10,724 at z7 (cluster counts ≥ 4 px², ROADMAP §6). The real numbers after closing will be higher; C3 reports them.

## Layer `places`
| geometry | attribute | values | meaning |
|---|---|---|---|
| Point | `place` | `city` \| `town` \| `village` | OSM `place=*` (admin status: місто / смт or town / село). Hamlets excluded. |
|  | `pop` | `5` ≥ 1 M · `4` 100 k–1 M · `3` 10 k–100 k · `2` 1 k–10 k · `1` < 1 k | OSM `population`, parsed (spaces and thin spaces removed); omitted if missing or unparseable |

- Counts inside the outline (2026-11-18): `pop` 5 / 4 / 3 / 2 / 1 = 4 / 41 / 373 / 5,264 / 20,743; 38 have no population.
  By status: city 47, town 1,261, village 25,117.
- **Per-zoom suppression:** at zoom z a place is left out if it lies inside a `builtup` polygon of the z band. Dots mark
  places that are too small to show as areas, and a dot disappears once its town becomes an area. So the
  dot/area handover follows the data rather than a fixed rule.
- Population figures are undated, probably an old census (unsure) and pre-war. `pop` is a size class, not a figure.
- Labels are not in this schema. A names phase would add `name` here.

## Verification hooks
- `pmtiles show`: exactly the layers `ground`, `water`, `builtup`, `places`; fields ⊆ {`place`, `pop`}; zooms 0–8.
- Decode check per band: features in the tile = features in that band's input (no tippecanoe loss).
- Area accounting per z: built-up area after G(z) ÷ phase-1 residential area, which states the exaggeration.
- Visual: contact sheet at phone z3.9 and desktop z5.5, plus z7.6 as the print preview.
