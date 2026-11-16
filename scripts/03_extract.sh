#!/usr/bin/env bash
# Cut the extract to the outline (smart strategy keeps multipolygons complete), then filter by tag.
source "$(dirname "$0")/config.sh"
clip="$WORK/outline.geojson"
if [[ -n "$BBOX" ]]; then
  osmium extract -O -s smart -b "$BBOX" -o "$WORK/region.osm.pbf" "$SRC/ukraine-latest.osm.pbf"
else
  osmium extract -O -s smart -p "$clip"  -o "$WORK/region.osm.pbf" "$SRC/ukraine-latest.osm.pbf"
fi
log "water filter"
osmium tags-filter -O -o "$WORK/water.osm.pbf" "$WORK/region.osm.pbf" \
  wa/natural=water wa/water wa/waterway=riverbank wa/landuse=reservoir \
  w/waterway=river,canal,stream
for s in "$ROOT"/scripts/sources/settlements_"$SETTLEMENT_SOURCE".sh; do source "$s"; settlements_extract; done
