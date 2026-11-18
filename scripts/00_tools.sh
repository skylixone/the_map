#!/usr/bin/env bash
# Install the toolchain. Ubuntu 24.04 packages + go-pmtiles + a project venv with shapely.
source "$(dirname "$0")/config.sh"
need_apt=()
command -v osmium     >/dev/null || need_apt+=(osmium-tool)   # 1.16 on noble
command -v ogr2ogr    >/dev/null || need_apt+=(gdal-bin)      # 3.8 on noble
command -v tippecanoe >/dev/null || need_apt+=(tippecanoe)    # 2.49 on noble; writes .pmtiles directly
if ((${#need_apt[@]})); then log "apt: ${need_apt[*]}"; apt-get install -y --no-install-recommends "${need_apt[@]}"; fi
if ! command -v pmtiles >/dev/null; then
  log "go-pmtiles v1.31.2"; GOBIN=/usr/local/bin go install github.com/protomaps/go-pmtiles@v1.31.2
  ln -sf /usr/local/bin/go-pmtiles /usr/local/bin/pmtiles
fi
[[ -x "$PY" ]] || { python3 -m venv "$ROOT/.venv"; "$PY" -m pip install -q 'shapely>=2.0,<3' 'pyproj>=3.6,<4'; }
"$PY" -c 'import pyproj' 2>/dev/null || "$PY" -m pip install -q 'pyproj>=3.6,<4'   # country map (scripts/country)
for t in osmium ogr2ogr tippecanoe; do printf "%-11s %s\n" "$t" "$($t --version 2>&1 | head -1)"; done; printf "%-11s %s\n" pmtiles "$(pmtiles version 2>&1 | head -1)"
"$PY" -c 'import shapely; print("shapely    ", shapely.__version__)'
