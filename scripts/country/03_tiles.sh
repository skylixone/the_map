#!/usr/bin/env bash
# One tippecanoe run per zoom band, each tiled into its own zoom only (-Z z -z z; the first band also fills z0..),
# then tile-join. Same reason as phase 1: no per-feature minzoom (broken in 2.49), and here each zoom has its own geometry.
# Flags:
#   --no-feature-limit --no-tile-size-limit  never drop to fit; selection already happened in G(z)
#   --no-tiny-polygon-reduction              G(z) already removed parts < AREA_PX2; don't let tippecanoe fake them
#   -r1                                       no point thinning: every place in the band input reaches its zoom
#   default simplification (1 tile unit ≈ 1/8 px at 512 px) is left on; G(z) simplified to SIMPLIFY_PX already
source "$(dirname "$0")/config.sh"
B="$CWORK/$CTAG"; T="$B/tiles"; rm -rf "$T"; mkdir -p "$T"
read -ra bands <<< "$CZ_BANDS"; parts=()
for z in "${bands[@]}"; do
  zmin=$z; [[ $z == "${bands[0]}" ]] && zmin=0
  log "tippecanoe band z$z -> z$zmin..$z"
  tippecanoe -Z"$zmin" -z"$z" -P --force --quiet --no-feature-limit --no-tile-size-limit --no-tiny-polygon-reduction -r1 \
    -L ground:"$B/z$z/ground.geojsonseq" -L water:"$B/z$z/water.geojsonseq" \
    -L builtup:"$B/z$z/builtup.geojsonseq" -L places:"$B/z$z/places.geojsonseq" -o "$T/z$z.mbtiles"
  parts+=("$T/z$z.mbtiles")
done
tile-join --force --quiet --no-tile-size-limit -n "the_map-country" \
  -N "Ukraine country map: ground, water, builtup, places (schema-country v0.1, $CTAG, rivers>=${RIVER_MIN_KM}km)" \
  -A '© OpenStreetMap contributors' -o "$T/country.mbtiles" "${parts[@]}"
rm -f "$CTILES"; pmtiles convert "$T/country.mbtiles" "$CTILES" >/dev/null 2>&1
log "wrote $CTILES ($(stat -c %s "$CTILES") bytes)"
