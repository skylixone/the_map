#!/usr/bin/env bash
# Per-layer tippecanoe runs (flags differ per layer), joined into one PMTiles.
#
# Why each flag (see also docs/DECISIONS.md):
#   -Z0 -z14                     schema zoom range; MapLibre overzooms past 14.
#   -P                           parallel read; inputs are newline-delimited GeoJSONSeq.
#   --detect-shared-borders      adjacent polygons (residential blocks, riverbank pieces meeting a reservoir)
#                                simplify identically -> no hairline gaps/overlaps between neighbours.
#   ground: --no-feature-limit --no-tile-size-limit
#                                ground must never be dropped; it is ~1 polygon per tile.
#   VARIANT=explicit (default)
#     --no-tiny-polygon-reduction  no synthetic squares: visibility is decided by the per-feature minzoom
#                                  (area >= MINZOOM_PX2 screen px^2) computed in 05; what you see is real geometry.
#     --drop-smallest-as-needed    safety net only, for tiles over 500 KB; a log line means the minzoom rule
#                                  was not enough for that tile and the threshold should be revisited.
#   VARIANT=tippecanoe-default
#     (tiny-polygon reduction on)  sub-pixel polygons accumulate into pixel-sized squares: area-preserving
#                                  dot texture, synthetic geometry.
#     --drop-densest-as-needed     when tiles overflow, drop features from the most crowded areas first:
#                                  density evens out; dense cores thin more than rural areas.
source "$(dirname "$0")/config.sh"
L="$WORK/layers"; T="$WORK/tiles-$VARIANT"; mkdir -p "$T"
common=(-Z0 -z"$MAXZOOM" -P --force --quiet)
case "$VARIANT" in
  explicit)           gen=(--no-tiny-polygon-reduction --drop-smallest-as-needed) ;;
  tippecanoe-default) gen=(--drop-densest-as-needed) ;;
  *) echo "unknown VARIANT=$VARIANT" >&2; exit 1 ;;
esac
log "tippecanoe ground";      tippecanoe "${common[@]}" -l ground --no-feature-limit --no-tile-size-limit --no-tiny-polygon-reduction -o "$T/ground.mbtiles" "$L/ground.geojsonseq"
log "tippecanoe water";       tippecanoe "${common[@]}" -l water --detect-shared-borders "${gen[@]}" -o "$T/water.mbtiles" "$L/water.geojsonseq"
log "tippecanoe settlements"; tippecanoe "${common[@]}" -l settlements --detect-shared-borders "${gen[@]}" -o "$T/settlements.mbtiles" "$L/settlements.geojsonseq"
log "tile-join"
tile-join --force --no-tile-size-limit -n "the_map" -N "Ukraine: ground, water, settlements (schema v0.1, $VARIANT, px2=$MINZOOM_PX2)" \
  -A '© OpenStreetMap contributors' -o "$T/the_map.mbtiles" "$T/ground.mbtiles" "$T/water.mbtiles" "$T/settlements.mbtiles"
rm -f "$TILES"; pmtiles convert "$T/the_map.mbtiles" "$TILES"
log "wrote $TILES ($(du -h "$TILES" | cut -f1))"
