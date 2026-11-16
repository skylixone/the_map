#!/usr/bin/env bash
# A/B sample build for generalisation (OPEN.md §4): Kyiv + rural Kyiv/Zhytomyr oblast, both variants.
# Output: data/out/sample-explicit.pmtiles, data/out/sample-tippecanoe-default.pmtiles
set -euo pipefail
d="$(dirname "$0")"
export BBOX="${BBOX:-29.2,49.6,31.8,51.3}"
"$d/02_outline.sh"; "$d/03_extract.sh"; "$d/04_export.sh"
for v in ${VARIANTS:-clustered explicit tippecanoe-default}; do
  VARIANT=$v TILES="$(cd "$d/.." && pwd)/data/out/sample-$v.pmtiles" bash -c "'$d/05_normalize.sh' && '$d/06_tiles.sh' && '$d/07_verify.sh'"
done
