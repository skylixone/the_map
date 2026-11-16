#!/usr/bin/env bash
# Tags -> schema attributes, clip to outline (∩ BBOX), per-feature minzoom. Output = the schema, layer by layer.
source "$(dirname "$0")/config.sh"
mkdir -p "$WORK/layers"
n() { "$PY" -I "$ROOT/scripts/lib/normalize.py" "$@" --outline "$WORK/outline.geojson" --bbox "$BBOX" --px2 "$MINZOOM_PX2" --maxzoom "$MAXZOOM"; }
n ground      "$WORK/land.raw.geojsonseq"        "$WORK/layers/ground.geojsonseq"
n water       "$WORK/water.raw.geojsonseq"       "$WORK/layers/water.geojsonseq"
n settlements "$WORK/settlements.raw.geojsonseq" "$WORK/layers/settlements.geojsonseq" --source "$SETTLEMENT_SOURCE" --cluster-m "$CLUSTER_M"
