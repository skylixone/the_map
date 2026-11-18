# Country map config (docs/SCHEMA-country.md). Sources the phase-1 config; every value overridable from the environment.
source "$(dirname "${BASH_SOURCE[0]}")/../config.sh"
CWORK="$WORK/country"; mkdir -p "$CWORK"
CZ_BANDS="${CZ_BANDS:-4 5 6 7 8}"      # one generalised geometry set per zoom; the first band also serves z0..(first-1)
GAP_PX="${GAP_PX:-1}"                  # closing: parts closer than this many px merge
AREA_PX2="${AREA_PX2:-4}"              # drop parts smaller than this many px^2
SIMPLIFY_PX="${SIMPLIFY_PX:-0.5}"      # simplification tolerance in px
RIVER_MIN_KM="${RIVER_MIN_KM:-200}"    # rivers by length inside the outline
RIVER_CLIP_M="${RIVER_CLIP_M:-200}"    # river lines clipped to outline buffered by this (border rivers)
CTAG="${CTAG:-gap${GAP_PX}-area${AREA_PX2}-simp${SIMPLIFY_PX}}"
CTILES="${CTILES:-$OUT/the_map-country.pmtiles}"
