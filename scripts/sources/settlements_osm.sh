# Settlement source module: OSM landuse=residential.
# Contract for every settlement module: define settlements_extract and settlements_export;
# settlements_export must write $WORK/settlements.raw.geojsonseq (polygons; tags as properties),
# which lib/normalize.py maps via its SETTLEMENT_SOURCES["<name>"] entry.
settlements_extract() {
  log "settlements filter (osm)"
  osmium tags-filter -O -o "$WORK/settlements.osm.pbf" "$WORK/region.osm.pbf" wa/landuse=residential
}
settlements_export() {
  log "export settlements (osm)"
  osmium export -O -c "$ROOT/scripts/lib/osmium-export.json" -f geojsonseq -x print_record_separator=false \
    --geometry-types=polygon -o "$WORK/settlements.raw.geojsonseq" "$WORK/settlements.osm.pbf"
}
