#!/usr/bin/env bash
# Downloads (~1.8 GB total). Resumable; skips files whose remote size matches.
source "$(dirname "$0")/config.sh"
fetch() { # url dest
  local url=$1 dest=$2
  log "fetch $url"
  curl -fSL --retry 4 --retry-delay 5 -C - -o "$dest" "$url"
}
fetch "$PBF_URL"  "$SRC/ukraine-latest.osm.pbf"
curl -fsSL "$PBF_URL.md5" -o "$SRC/ukraine-latest.osm.pbf.md5" && (cd "$SRC" && md5sum -c ukraine-latest.osm.pbf.md5)
fetch "$LAND_URL" "$SRC/land-polygons-split-4326.zip"
mkdir -p "$SRC/boundary"
fetch "$GB_URL"   "$SRC/boundary/geoBoundaries-UKR-ADM0.geojson"
osmium fileinfo -e -g header.option.osmosis_replication_timestamp "$SRC/ukraine-latest.osm.pbf" > "$SRC/pbf_timestamp.txt" || true
log "done: $(du -sh "$SRC" | cut -f1)"
