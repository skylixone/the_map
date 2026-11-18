#!/usr/bin/env bash
# Country inputs not in the phase-1 layers: place nodes and river ways + waterway relations (from the clipped region extract).
source "$(dirname "$0")/config.sh"
R="$WORK/region.osm.pbf"; [[ -f "$R" ]] || { echo "missing $R: run scripts/03_extract.sh" >&2; exit 1; }
log "places"
osmium tags-filter -O -o "$CWORK/places.osm.pbf" "$R" n/place=city,town,village
osmium export -O -f geojsonseq -x print_record_separator=false -c "$ROOT/scripts/country/lib/export-places.json" \
  -o "$CWORK/places.raw.geojsonseq" "$CWORK/places.osm.pbf"
log "rivers"
# Relations bring their member ways (also stream/canal members); -R variant gives the relations alone for membership.
osmium tags-filter -O -o "$CWORK/rivers.osm.pbf" "$R" w/waterway=river r/waterway=river r/type=waterway
osmium tags-filter -O -R -o "$CWORK/river-rels.osm.pbf" "$CWORK/rivers.osm.pbf" r/waterway=river r/type=waterway
osmium cat -O -f opl -o "$CWORK/river-rels.opl" "$CWORK/river-rels.osm.pbf"
osmium export -O -f geojsonseq -x print_record_separator=false -c "$ROOT/scripts/country/lib/export-rivers.json" \
  -o "$CWORK/rivers.raw.geojsonseq" "$CWORK/rivers.osm.pbf"
log "places $(wc -l < "$CWORK/places.raw.geojsonseq"), river features $(wc -l < "$CWORK/rivers.raw.geojsonseq"), relations $(grep -c '^r' "$CWORK/river-rels.opl")"
