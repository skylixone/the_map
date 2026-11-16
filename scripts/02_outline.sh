#!/usr/bin/env bash
# Build the clip outline -> $WORK/outline.geojson (single (Multi)Polygon, EPSG:4326),
# then run the containment test (Crimea, Kerch, Kyiv inside; Taganrog, Chisinau outside).
source "$(dirname "$0")/config.sh"
case "$CLIP_SOURCE" in
  geoboundaries)
    cp "$SRC/boundary/geoBoundaries-UKR-ADM0.geojson" "$WORK/outline.src.geojson" ;;
  osm)
    osmium getid -r -O -o "$WORK/outline.osm.pbf" "$SRC/ukraine-latest.osm.pbf" "r$OSM_UKRAINE_RELATION"
    osmium export -O -f geojson --geometry-types=polygon -o "$WORK/outline.src.geojson" "$WORK/outline.osm.pbf" ;;
  *) echo "unknown CLIP_SOURCE=$CLIP_SOURCE" >&2; exit 1 ;;
esac
"$PY" -I "$ROOT/scripts/lib/outline.py" "$WORK/outline.src.geojson" "$WORK/outline.geojson" "$CLIP_SOURCE"
