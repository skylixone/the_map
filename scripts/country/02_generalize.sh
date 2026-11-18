#!/usr/bin/env bash
# Per-zoom generalisation into $CWORK/$CTAG/z<band>/*.geojsonseq (+ stats.json). See lib/country.py.
source "$(dirname "$0")/config.sh"
"$PY" -I "$ROOT/scripts/country/lib/country.py" --work "$WORK" --out "$CWORK/$CTAG" --bands "$CZ_BANDS" \
  --gap-px "$GAP_PX" --water-gap-px "$WATER_GAP_PX" --area-px2 "$AREA_PX2" --simplify-px "$SIMPLIFY_PX" \
  --river-min-km "$RIVER_MIN_KM" --river-clip-m "$RIVER_CLIP_M"
