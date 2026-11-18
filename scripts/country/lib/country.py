"""Country-map generalisation: phase-1 layers + place nodes + rivers -> one GeoJSONSeq set per zoom band.
The rules ARE docs/SCHEMA-country.md in executable form; change them only together with that file.

usage: country.py --work DATA/work --out DIR --bands "4 5 6 7 8" [--gap-px 1 --area-px2 4 --simplify-px 0.5
                  --river-min-km 200 --river-clip-m 200]
Writes OUT/z<band>/{ground,water,builtup,places}.geojsonseq and OUT/stats.json.
All geometry work happens in UTM 36N (EPSG:32636); pixel sizes are latitude-corrected per feature (512 px tiles).
"""
import argparse, collections, json, math, os, re, sys, time
import numpy as np, shapely
from shapely.geometry import shape
from pyproj import Transformer

EARTH_C = 40075016.686
FWD = Transformer.from_crs(4326, 32636, always_xy=True)
INV = Transformer.from_crs(32636, 4326, always_xy=True)


def to_m(g):
    return shapely.transform(g, lambda c: np.column_stack(FWD.transform(c[:, 0], c[:, 1])))


def to_deg(g):
    return shapely.transform(g, lambda c: np.column_stack(INV.transform(c[:, 0], c[:, 1])))


def lat_of(g_m):
    """Latitude of each (metric) geometry's centroid."""
    c = shapely.centroid(g_m)
    _, lat = INV.transform(shapely.get_x(c), shapely.get_y(c))
    return np.asarray(lat)


def px_m(z, lat):
    """Ground metres per screen pixel at zoom z (512 px tiles, Web Mercator) at latitude lat."""
    return EARTH_C * np.cos(np.radians(lat)) / (512 * 2 ** z)


def read_seq(path):
    with open(path) as f:
        for line in f:
            line = line.strip().lstrip("\x1e")
            if line:
                yield json.loads(line)


def write_seq(path, feats):
    n = 0
    with open(path, "w") as f:
        for props, g in feats:
            f.write('{"type":"Feature","properties":' + json.dumps(props, separators=(",", ":"), ensure_ascii=False)
                    + ',"geometry":' + shapely.to_geojson(g) + "}\n")
            n += 1
    return n


def polys(g):
    """Polygon parts of a geometry array (drops lines/points produced by buffers or clipping)."""
    p = shapely.get_parts(shapely.make_valid(np.asarray(g)))
    return p[(shapely.get_type_id(p) == 3) & ~shapely.is_empty(p)]


# ---- areal generalisation G(z) ---------------------------------------------------------------
def generalise(geoms_m, z, a, outline_m, gap_px):
    """Union; closing (< gap_px px; 0 = union only); drop parts < area px^2; simplify; clip. Metric in and out."""
    lat = lat_of(geoms_m)
    px = px_m(z, lat)
    g = shapely.simplify(geoms_m, px * a.simplify_px * 0.5)  # cheap pre-thinning; final tolerance applied below
    if gap_px > 0:
        r = px * gap_px / 2
        merged = polys([shapely.union_all(shapely.buffer(g, r, quad_segs=2))])
        r2 = px_m(z, lat_of(merged)) * gap_px / 2
        g = polys(shapely.buffer(merged, -r2, quad_segs=2))
    elif gap_px == 0:
        g = polys([shapely.union_all(polys(g))])
    else:  # < 0: no union at all (ground: keep coastline parts as drawn)
        g = polys(g)
    pxp = px_m(z, lat_of(g))
    g = g[shapely.area(g) >= a.area_px2 * pxp ** 2]
    pxp = px_m(z, lat_of(g))
    g = polys(shapely.simplify(g, pxp * a.simplify_px, preserve_topology=True))
    inside = shapely.contains(outline_m, g)
    g = np.concatenate([g[inside], polys(shapely.intersection(g[~inside], outline_m))])
    pxp = px_m(z, lat_of(g))
    return g[shapely.area(g) >= a.area_px2 * pxp ** 2]  # clipping can leave slivers


# ---- rivers ----------------------------------------------------------------------------------
OPL_ESC = re.compile(r"%([0-9a-fA-F]+)%")


def opl_unescape(s):
    return OPL_ESC.sub(lambda m: chr(int(m.group(1), 16)), s)


def parse_relations(path):
    """OPL relations -> list of (names:set, members:[(way_id, role)], label)."""
    rels = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("r"):
            continue
        tags, mem = {}, []
        for field in line.rstrip("\n").split(" "):
            if field.startswith("T") and len(field) > 1:
                for kv in field[1:].split(","):
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        tags[opl_unescape(k)] = opl_unescape(v)
            elif field.startswith("M") and len(field) > 1:
                for m in field[1:].split(","):
                    ref, _, role = m.partition("@")
                    if ref.startswith("w"):
                        mem.append((int(ref[1:]), opl_unescape(role)))
        names = {tags[k] for k in ("name", "name:uk") if k in tags}
        rels.append((names, mem, tags.get("name:uk") or tags.get("name") or "?"))
    return rels


def rivers(work, outline_m, a):
    """Group river ways into rivers (relation membership, then same name + shared endpoint); keep those whose
    length inside the outline >= river_min_km. Returns (list of (label, km, metric MultiLineString), near-miss list)."""
    ways = {}
    for f in read_seq(os.path.join(work, "rivers.raw.geojsonseq")):
        p, g = f["properties"], f["geometry"]
        if p.get("@type") != "way" or g["type"] != "LineString":
            continue
        ways[p["@id"]] = (p.get("name"), p.get("waterway"), g["coordinates"])
    rels = parse_relations(os.path.join(work, "river-rels.opl"))
    names = collections.defaultdict(set)
    side = set()
    label_of = {}
    for rnames, mem, label in rels:
        for wid, role in mem:
            if wid in ways:
                names[wid] |= rnames
                label_of.setdefault(wid, label)
                if role == "side_stream":
                    side.add(wid)
    for wid, (nm, kind, _) in ways.items():
        if nm and (kind == "river" or wid in names):
            names[wid].add(nm)
    ids = [w for w in ways if names[w]]  # unnamed, relation-less ways cannot be attributed to a river
    idx = {w: i for i, w in enumerate(ids)}
    parent = list(range(len(ids)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
    for _, mem, _ in rels:
        m = [idx[w] for w, _ in mem if w in idx]
        for i in m[1:]:
            union(m[0], i)
    ends = collections.defaultdict(list)
    for w in ids:
        c = ways[w][2]
        for pt in (tuple(c[0]), tuple(c[-1])):
            ends[pt].append(w)
    for pt, ws in ends.items():
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                if names[ws[i]] & names[ws[j]]:
                    union(idx[ws[i]], idx[ws[j]])
    groups = collections.defaultdict(list)
    for w in ids:
        groups[find(idx[w])].append(w)
    clip = shapely.buffer(outline_m, a.river_clip_m)
    shapely.prepare(clip)
    shapely.prepare(outline_m)
    keep, near = [], []
    for ws in groups.values():
        lines = to_m(np.array([shapely.linestrings(ways[w][2]) for w in ws]))
        main = np.array([w not in side for w in ws])
        km = float(shapely.length(shapely.intersection(lines[main], outline_m)).sum()) / 1000
        lab = collections.Counter(label_of.get(w) or ways[w][0] for w in ws).most_common(1)[0][0]
        if km >= a.river_min_km:
            geom = shapely.intersection(shapely.line_merge(shapely.multilinestrings(lines)), clip)
            keep.append((lab, round(km, 1), geom))
        elif km >= 0.75 * a.river_min_km:
            near.append((lab, round(km, 1)))
    keep.sort(key=lambda t: -t[1])
    near.sort(key=lambda t: -t[1])
    return keep, near


def lines_only(g):
    p = shapely.get_parts(np.asarray(g))
    return p[np.isin(shapely.get_type_id(p), (1, 2))]


# ---- places ----------------------------------------------------------------------------------
POP_CLASSES = [(1_000_000, 5), (100_000, 4), (10_000, 3), (1_000, 2), (0, 1)]


def pop_class(s):
    s = re.sub(r"[\s  ,.]", "", s or "")
    m = re.match(r"^(\d+)", s)
    if not m:
        return None
    n = int(m.group(1))
    return next(c for t, c in POP_CLASSES if n >= t)


# ---- main ------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bands", default="4 5 6 7 8")
    ap.add_argument("--gap-px", type=float, default=1)
    ap.add_argument("--water-gap-px", type=float, default=None, help="closing gap for water (default: --gap-px; 0 = union only)")
    ap.add_argument("--area-px2", type=float, default=4)
    ap.add_argument("--simplify-px", type=float, default=0.5)
    ap.add_argument("--river-min-km", type=float, default=200)
    ap.add_argument("--river-clip-m", type=float, default=200)
    a = ap.parse_args()
    bands = [int(b) for b in a.bands.split()]
    if a.water_gap_px is None:
        a.water_gap_px = a.gap_px
    cw = os.path.join(a.work, "country")
    log = lambda *m: print("[country]", *m, file=sys.stderr, flush=True)

    outline_m = to_m(shapely.union_all([shape(f["geometry"]) for f in
                                        json.load(open(os.path.join(a.work, "outline.geojson")))["features"]]))
    shapely.prepare(outline_m)

    def layer_geoms(name, pred):
        return to_m(np.array([shape(f["geometry"]) for f in read_seq(os.path.join(a.work, "layers", name + ".geojsonseq"))
                              if f["geometry"]["type"] in ("Polygon", "MultiPolygon") and pred(f["properties"])]))
    ground = layer_geoms("ground", lambda p: True)
    water = layer_geoms("water", lambda p: not p.get("intermittent"))
    settle = layer_geoms("settlements", lambda p: True)
    log(f"inputs: ground {len(ground)}, water polygons {len(water)} (non-intermittent), settlements {len(settle)}")
    settle_area = float(shapely.area(settle).sum())

    pl_geom, pl_props = [], []
    for f in read_seq(os.path.join(cw, "places.raw.geojsonseq")):
        p = f["properties"]
        if p.get("place") not in ("city", "town", "village"):
            continue
        props = {"place": p["place"]}
        c = pop_class(p.get("population"))
        if c:
            props["pop"] = c
        pl_geom.append(shape(f["geometry"]))
        pl_props.append(props)
    pl_m = to_m(np.array(pl_geom))
    inside = shapely.contains(outline_m, pl_m)
    pl_m, pl_props = pl_m[inside], [p for p, k in zip(pl_props, inside) if k]
    log(f"places inside outline: {len(pl_props)}")

    t = time.time()
    rv, near = rivers(cw, outline_m, a)
    log(f"rivers grouped in {time.time()-t:.0f}s")
    log(f"rivers >= {a.river_min_km} km: {len(rv)}; near misses: {len(near)}")

    stats = {"params": vars(a), "rivers": [(l, k) for l, k, _ in rv], "river_near_misses": near,
             "settlement_area_km2": round(settle_area / 1e6, 1), "bands": {}}
    for z in bands:
        log(f"band z{z}")
        d = os.path.join(a.out, f"z{z}")
        os.makedirs(d, exist_ok=True)
        t = time.time()
        g_ground = generalise(ground, z, a, outline_m, -1); log(f"  ground {len(g_ground)} parts {time.time()-t:.0f}s")
        t = time.time()
        g_water = generalise(water, z, a, outline_m, a.water_gap_px); log(f"  water {len(g_water)} parts {time.time()-t:.0f}s")
        t = time.time()
        g_built = generalise(settle, z, a, outline_m, a.gap_px); log(f"  builtup {len(g_built)} parts {time.time()-t:.0f}s")
        tree = shapely.STRtree(g_built)
        covered = np.zeros(len(pl_m), bool)
        hit = tree.query(pl_m, predicate="within")[0]
        covered[hit] = True
        r_lines = []
        for _, _, geom in rv:
            px = float(px_m(z, lat_of(np.array([geom]))[0]))
            r_lines.extend(lines_only(shapely.simplify(geom, px * a.simplify_px)))
        s = {
            "ground": write_seq(os.path.join(d, "ground.geojsonseq"), [({}, g) for g in to_deg(g_ground)]),
            "water_polygons": len(g_water),
            "water_lines": len(r_lines),
            "builtup": write_seq(os.path.join(d, "builtup.geojsonseq"), [({}, g) for g in to_deg(g_built)]),
            "places": write_seq(os.path.join(d, "places.geojsonseq"),
                                [(p, g) for p, g, c in zip(pl_props, to_deg(pl_m), covered) if not c]),
            "places_suppressed_by_builtup": int(covered.sum()),
            "builtup_area_km2": round(float(shapely.area(g_built).sum()) / 1e6, 1),
            "water_area_km2": round(float(shapely.area(g_water).sum()) / 1e6, 1),
        }
        write_seq(os.path.join(d, "water.geojsonseq"),
                  [({}, g) for g in to_deg(g_water)] + [({}, g) for g in to_deg(np.array(r_lines))])
        s["builtup_area_ratio"] = round(s["builtup_area_km2"] * 1e6 / settle_area, 3)
        stats["bands"][z] = s
        log(json.dumps(s))
    json.dump(stats, open(os.path.join(a.out, "stats.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
