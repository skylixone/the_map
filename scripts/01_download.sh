#!/usr/bin/env bash
# Downloads (~2 GB total). Resumable via .part files; completed files are skipped (delete to refetch).
source "$(dirname "$0")/config.sh"
fetch() { # url dest
  local url=$1 dest=$2
  if [[ -s "$dest" ]]; then log "have $(basename "$dest")"; return; fi
  log "fetch $url"
  curl -fSL --retry 4 --retry-delay 5 -C - -o "$dest.part" "$url"
  mv "$dest.part" "$dest"
}
fetch "$PBF_URL" "$SRC/ukraine-latest.osm.pbf"
curl -fsSL "$PBF_URL.md5" | awk '{print $1"  ukraine-latest.osm.pbf"}' > "$SRC/ukraine-latest.osm.pbf.md5"
(cd "$SRC" && md5sum -c ukraine-latest.osm.pbf.md5)
fetch "$LAND_URL" "$SRC/land-polygons-split-4326.zip"
mkdir -p "$SRC/boundary" "$SRC/codab"
fetch "$GB_URL"   "$SRC/boundary/geoBoundaries-UKR-ADM0.geojson"
fetch "$CODAB_URL" "$SRC/codab/ukr_admin_boundaries.geojson.zip"
[[ -s "$SRC/codab/ukr_admin0.geojson" ]] || unzip -o -q "$SRC/codab/ukr_admin_boundaries.geojson.zip" ukr_admin0.geojson ukr_adminlines.geojson -d "$SRC/codab"
osmium fileinfo -g header.option.osmosis_replication_timestamp "$SRC/ukraine-latest.osm.pbf" > "$SRC/pbf_timestamp.txt" || true
log "done: $(du -sh "$SRC" | cut -f1), pbf timestamp $(cat "$SRC/pbf_timestamp.txt")"
