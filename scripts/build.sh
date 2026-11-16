#!/usr/bin/env bash
# Full rebuild from downloaded sources. Steps are idempotent; run any single step directly.
# Sample build:  BBOX=29.2,49.6,31.8,51.3 TILES=data/out/sample-explicit.pmtiles scripts/build.sh
set -euo pipefail
d="$(dirname "$0")"
for s in 02_outline 03_extract 04_export 05_normalize 06_tiles 07_verify; do "$d/$s.sh"; done
