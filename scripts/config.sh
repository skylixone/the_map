# Shared config. Source this; every value can be overridden from the environment.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="$ROOT/data"
SRC="$DATA/src"          # downloads, untouched
WORK="$DATA/work"        # intermediates, safe to delete
OUT="$DATA/out"          # final tiles
mkdir -p "$SRC" "$WORK" "$OUT"

# Geofabrik resets every connection from the cloud environment (docs/OPEN.md §0); OSM France mirror verified to cover
# the full COD-AB outline incl. Crimea. Geofabrik: https://download.geofabrik.de/europe/ukraine-latest.osm.pbf
PBF_URL="${PBF_URL:-https://download.openstreetmap.fr/extracts/europe/ukraine.osm.pbf}"
LAND_URL="${LAND_URL:-https://osmdata.openstreetmap.de/download/land-polygons-split-4326.zip}"
GB_URL="${GB_URL:-https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/9469f09/releaseData/gbOpen/UKR/ADM0/geoBoundaries-UKR-ADM0.geojson}"
CODAB_URL="${CODAB_URL:-https://data.humdata.org/dataset/d23f529f-31e4-4021-a65b-13987e5cfb42/resource/681beb86-391b-4a08-8140-ca52e80fcdce/download/ukr_admin_boundaries.geojson.zip}"

# Clip outline source: osm (relation 60199 from the extract) | geoboundaries. See docs/OPEN.md §1.
CLIP_SOURCE="${CLIP_SOURCE:-osm}"   # approved 2026-11-16 (OPEN.md §1)
OSM_UKRAINE_RELATION="${OSM_UKRAINE_RELATION:-60199}"

# Settlement source module: scripts/sources/settlements_<name>.sh. See docs/OPEN.md §2.
SETTLEMENT_SOURCE="${SETTLEMENT_SOURCE:-osm}"

# Optional bbox (minlon,minlat,maxlon,maxlat) for sample builds. Empty = whole country.
BBOX="${BBOX:-}"
MINZOOM_PX2="${MINZOOM_PX2:-4}"
MAXZOOM="${MAXZOOM:-14}"
VARIANT="${VARIANT:-clustered}"   # clustered | explicit | tippecanoe-default. See scripts/06_tiles.sh.
TILES="${TILES:-$OUT/the_map.pmtiles}"

PY="$ROOT/.venv/bin/python"
log() { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*" >&2; }
# Variant tippecanoe-default lets tippecanoe decide visibility, so no prescribed per-feature minzoom.
if [[ "$VARIANT" == "tippecanoe-default" ]]; then MINZOOM_PX2=0; fi
# Settlement clustering gap for minzoom (m); only VARIANT=clustered uses it. ~street width.
CLUSTER_M="${CLUSTER_M:-30}"
if [[ "$VARIANT" != "clustered" ]]; then CLUSTER_M=0; fi
