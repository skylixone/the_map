#!/usr/bin/env bash
# Per-layer, per-minzoom-bucket tippecanoe runs, joined into one PMTiles.
#
# Feature minzoom is NOT passed to tippecanoe as "tippecanoe":{"minzoom"}: tippecanoe 2.49 mishandles it
# (minzoom 5 -> first appears z14). Instead lib/bucket.py splits each layer by minzoom, each bucket is tiled
# with -Z<bucket>, and tile-join merges same-named layers. Side effect: --detect-shared-borders only acts
# within a bucket, so neighbours in different buckets simplify independently.
#
# Why each flag (see also docs/DECISIONS.md):
#   -z14                         schema max zoom; MapLibre overzooms past 14.
#   -P                           parallel read; inputs are newline-delimited GeoJSONSeq.
#   --detect-shared-borders      adjacent polygons simplify identically -> no hairline gaps between neighbours.
#   ground: --no-feature-limit --no-tile-size-limit --no-tiny-polygon-reduction
#                                ground must never be dropped or turned into squares; it is ~1 polygon per tile.
#   VARIANT=clustered (default) — as explicit, but settlement minzoom uses the area of the cluster of polygons
#                                closer than CLUSTER_M (30 m): cities are block-mapped, villages single-polygon.
#   VARIANT=explicit
#     --no-tiny-polygon-reduction  no synthetic squares: visibility = per-feature minzoom (area >= MINZOOM_PX2 px^2).
#     --drop-smallest-as-needed    safety net for tiles over 500 KB; any non-empty "strategies" entry in the
#                                  metadata means the minzoom rule was not enough there.
#   VARIANT=tippecanoe-default
#     (tiny-polygon reduction on)  sub-pixel polygons accumulate into pixel-sized squares: area-preserving dot
#                                  texture, synthetic geometry.
#     --drop-densest-as-needed     on overflow, drop from the most crowded areas first.
source "$(dirname "$0")/config.sh"
L="$WORK/layers"; T="$WORK/tiles-$VARIANT"; rm -rf "$T"; mkdir -p "$T/buckets"
common=(-z"$MAXZOOM" -P --force --quiet)
case "$VARIANT" in
  explicit|clustered) gen=(--no-tiny-polygon-reduction --drop-smallest-as-needed) ;;
  tippecanoe-default) gen=(--drop-densest-as-needed) ;;
  *) echo "unknown VARIANT=$VARIANT" >&2; exit 1 ;;
esac
parts=()
log "tippecanoe ground"
tippecanoe "${common[@]}" -Z0 -l ground --no-feature-limit --no-tile-size-limit --no-tiny-polygon-reduction \
  -o "$T/ground.mbtiles" "$L/ground.geojsonseq"
parts+=("$T/ground.mbtiles")
for layer in water settlements; do
  zs=$("$PY" -I "$ROOT/scripts/lib/bucket.py" "$L/$layer.geojsonseq" "$T/buckets" "$layer")
  log "tippecanoe $layer, minzoom buckets: $zs"
  for z in $zs; do
    tippecanoe "${common[@]}" -Z"$z" -l "$layer" --detect-shared-borders "${gen[@]}" \
      -o "$T/$layer.z$z.mbtiles" "$T/buckets/$layer.z$z.geojsonseq"
    parts+=("$T/$layer.z$z.mbtiles")
  done
done
log "tile-join (${#parts[@]} parts)"
tile-join --force --quiet --no-tile-size-limit -n "the_map" \
  -N "Ukraine: ground, water, settlements (schema v0.2, $VARIANT, px2=$MINZOOM_PX2, outline=$CLIP_SOURCE)" \
  -A '© OpenStreetMap contributors' -o "$T/the_map.mbtiles" "${parts[@]}"
rm -f "$TILES"; pmtiles convert --quiet "$T/the_map.mbtiles" "$TILES" 2>/dev/null || pmtiles convert "$T/the_map.mbtiles" "$TILES" >/dev/null 2>&1
log "wrote $TILES ($(du -h "$TILES" | cut -f1))"
