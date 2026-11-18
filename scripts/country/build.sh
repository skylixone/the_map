#!/usr/bin/env bash
# Country map from the phase-1 work dir (needs data/work/{region.osm.pbf,outline.geojson,layers/}).
set -euo pipefail; D="$(dirname "$0")"
"$D/01_extract.sh"; "$D/02_generalize.sh"; "$D/03_tiles.sh"; "$D/04_verify.sh"
