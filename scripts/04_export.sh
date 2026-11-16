#!/usr/bin/env bash
# OSM -> GeoJSONSeq (raw tags kept only for the keys the normaliser reads). Land polygons -> GeoJSONSeq.
source "$(dirname "$0")/config.sh"
cfg="$ROOT/scripts/lib/osmium-export.json"
log "export water"
osmium export -O -c "$cfg" -f geojsonseq -x print_record_separator=false \
  -o "$WORK/water.raw.geojsonseq" "$WORK/water.osm.pbf"
for s in "$ROOT"/scripts/sources/settlements_"$SETTLEMENT_SOURCE".sh; do source "$s"; settlements_export; done
log "export land polygons (outline bbox only)"
spat=$("$PY" -I -c 'import json,sys
from shapely.geometry import shape
g=json.load(open(sys.argv[1]))["features"][0]["geometry"]; print(*shape(g).bounds)' "$WORK/outline.geojson")
[[ -n "$BBOX" ]] && spat="${BBOX//,/ }"
ogr2ogr -f GeoJSONSeq -spat $spat "$WORK/land.raw.geojsonseq" \
  "/vsizip/$SRC/land-polygons-split-4326.zip/land-polygons-split-4326/land_polygons.shp"
