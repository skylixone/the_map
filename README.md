# OSM extract snapshot used for the_map phase 1

Data-only branch. Code and docs live on the working branch (`docs/ROADMAP.md` §5, retention).

| field | value |
|---|---|
| file | `ukraine-2026-11-15.osm.pbf` (Git LFS) |
| source | https://download.openstreetmap.fr/extracts/europe/ukraine.osm.pbf (OSM France mirror, Ukraine incl. Crimea) |
| OSM timestamp | 2026-11-15T01:19:34Z |
| size | 1,016,918,979 bytes |
| md5 | 6a81a0abe569f39e155d945bb8aa68d2 |
| licence | ODbL 1.0, © OpenStreetMap contributors — https://www.openstreetmap.org/copyright |

Use: `git lfs pull` on this branch, then copy to `data/src/ukraine-latest.osm.pbf` and run `scripts/02_outline.sh` onwards
(skip `01_download.sh`, which would fetch a newer extract).
