# Brief: settlement coverage spike

Read `CLAUDE.md` first. This brief is self-contained otherwise.

## Question
Is OSM `landuse=residential` complete and consistent enough across Ukraine to be the `settlements` layer,
or should a 10 m built-up raster (GHSL GHS-BUILT-S, or WSF 2019) replace or complement it?

## Why it matters
At low zoom the settlement layer's spatial pattern *is* the map's aesthetic. Mapper-activity bias in OSM
(dense, well-mapped west and cities vs sparse villages elsewhere) would show up as a fake regional pattern.

## Method (suggested)
1. Grid Ukraine (e.g. 10 km cells or hromada polygons if available). Per cell: OSM residential area vs GHSL/WSF built-up area.
2. Map the ratio. Flag cells where raster built-up > 0 and OSM residential = 0 (missing villages) and the inverse.
3. Spot-check 5 oblasts across regions, including one frontline/occupied area (mapping may be stale or deliberately sparse) and Crimea.
4. Prototype a raster source: threshold → `gdal_polygonize` → simplify → output that matches the contract below. Report
   polygon count and file size versus OSM.

## Contract to plug in (do not change without HQ)
- Add `scripts/sources/settlements_<name>.sh` defining `settlements_extract` and `settlements_export`.
- `settlements_export` writes `data/work/settlements.raw.geojsonseq`: polygons, EPSG:4326, one feature per line.
- Add `<name>` to `SETTLEMENT_SOURCES` in `scripts/lib/normalize.py`; output attributes must stay `kind`, `source` (docs/SCHEMA.md).
- Select with `SETTLEMENT_SOURCE=<name>`.

## Deliverable
`docs/spikes/settlement-coverage.md`: method, numbers per region, 4–6 screenshots, a recommendation
(osm | raster | hybrid with rule), and the source module if raster wins. Record licences (GHSL: CC BY 4.0; WSF: check).
