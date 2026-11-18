#!/usr/bin/env bash
# Checks vs docs/SCHEMA-country.md: metadata (layers, fields, zooms) and per-band no-loss by decoding tiles:
#   places: points decoded inside their own tile (buffer excluded) == band input count;
#   polygons: a sample of input parts' interior points must be covered by decoded polygons at the band zoom.
source "$(dirname "$0")/config.sh"
pmtiles show "$CTILES" | grep -vE '^\s*$' | sed -n '1,20p'
pmtiles show --metadata "$CTILES" > "$CWORK/$CTAG/metadata.json"
"$PY" -I "$ROOT/scripts/country/lib/verify.py" "$CWORK/$CTAG" "$CZ_BANDS"
ls -l "$CTILES"
