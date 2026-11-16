"""Split a normalised GeoJSONSeq by per-feature tippecanoe.minzoom into one file per minzoom, key stripped.
usage: bucket.py IN.geojsonseq OUTDIR PREFIX   -> OUTDIR/PREFIX.z<N>.geojsonseq ; prints the minzooms used.
Why: tippecanoe 2.49 (Ubuntu noble) mishandles feature minzoom (a feature with minzoom 5 first appears at z14;
see docs/DECISIONS.md 2026-11-16). Each bucket is tiled with -Z<N> and tile-join merges the buckets into one layer."""
import json, os, sys
src, outdir, prefix = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
files = {}
for line in open(src):
    f = json.loads(line)
    z = f.pop("tippecanoe", {}).get("minzoom", 0)
    if z not in files:
        files[z] = open(os.path.join(outdir, f"{prefix}.z{z}.geojsonseq"), "w")
    files[z].write(json.dumps(f, separators=(",", ":")) + "\n")
for fh in files.values():
    fh.close()
print(" ".join(str(z) for z in sorted(files)))
