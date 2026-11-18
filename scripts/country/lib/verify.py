"""Country tiles vs docs/SCHEMA-country.md. usage: verify.py BANDDIR "4 5 6 7 8"
BANDDIR holds metadata.json, z<band>/*.geojsonseq (inputs) and tiles/z<band>.mbtiles (per-band tiles)."""
import json, math, os, subprocess, sys
import numpy as np, shapely
from shapely.geometry import shape

d, bands = sys.argv[1], [int(b) for b in sys.argv[2].split()]
ok = True
md = json.load(open(os.path.join(d, "metadata.json")))
vl = {l["id"]: l for l in md["vector_layers"]}
allowed = {"ground": set(), "water": set(), "builtup": set(), "places": {"place", "pop"}}
good = set(vl) == set(allowed)
print("layers:", sorted(vl), "OK" if good else "MISMATCH")
ok &= good
for lid, l in vl.items():
    extra = set(l.get("fields", {})) - allowed.get(lid, set())
    ok &= not extra
    print(f"  {lid:8s} z{l.get('minzoom')}-{l.get('maxzoom')} fields={l.get('fields')}" + (f"  UNEXPECTED {extra}" if extra else ""))


def tile_bounds(z, x, y):
    n = 2 ** z
    lon0, lon1 = x / n * 360 - 180, (x + 1) / n * 360 - 180
    lat = lambda t: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * t / n))))
    return lon0, lat(y + 1), lon1, lat(y)


def read_seq(p):
    return [json.loads(l) for l in open(p) if l.strip()]


for z in bands:
    out = subprocess.run(["tippecanoe-decode", "-z", str(z), "-Z", str(z), os.path.join(d, "tiles", f"z{z}.mbtiles")],
                         capture_output=True, text=True, check=True).stdout
    fc = json.loads(out)
    pts_in_own = 0
    polys = {"ground": [], "water": [], "builtup": []}
    for tile in fc["features"]:
        tp = tile["properties"]
        b = tile_bounds(tp["zoom"], tp["x"], tp["y"])
        for layer in tile["features"]:
            name = layer["properties"]["layer"]
            for f in layer["features"]:
                g = f["geometry"]
                if name == "places":
                    x, y = g["coordinates"]
                    pts_in_own += b[0] <= x < b[2] and b[1] < y <= b[3]
                elif g["type"] in ("Polygon", "MultiPolygon"):
                    polys[name].append(shape(g))
    n_in = len(read_seq(os.path.join(d, f"z{z}", "places.geojsonseq")))
    line = f"z{z}: places decoded {pts_in_own} / input {n_in}"
    ok &= pts_in_own == n_in
    for name, ps in polys.items():
        inp = [shape(f["geometry"]) for f in read_seq(os.path.join(d, f"z{z}", f"{name}.geojsonseq"))
               if f["geometry"]["type"] in ("Polygon", "MultiPolygon")]
        if not inp:
            line += f" | {name}: no input"
            continue
        rng = np.random.default_rng(z)
        sample = [inp[i] for i in rng.choice(len(inp), min(2000, len(inp)), replace=False)]
        cover = shapely.STRtree(ps)
        pts = shapely.point_on_surface(sample)
        hit = np.zeros(len(pts), bool)
        hit[cover.query(pts, predicate="intersects")[0]] = True
        present = np.zeros(len(sample), bool)
        present[cover.query(sample, predicate="intersects")[0]] = True
        # presence (must be 100 %): the part still exists in the tiles. Interior-point cover is informational:
        # thin winding parts (rivers, ~1 px wide) move their interior point out under tile simplification.
        line += f" | {name}: present {present.sum()}/{len(sample)}, interior pt {hit.sum()}"
        ok &= bool(present.all())
    print(line)
print("RESULT", "OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
