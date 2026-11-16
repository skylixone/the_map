"""Map raw OSM-tagged GeoJSONSeq to the tile schema (docs/SCHEMA.md), clip to the outline, set minzoom.

usage: normalize.py LAYER IN.geojsonseq OUT.geojsonseq --outline F [--bbox a,b,c,d] [--px2 N] [--maxzoom Z] [--source NAME]
LAYER: ground | water | settlements

The mapping tables below ARE the schema in executable form. Change them only together with docs/SCHEMA.md.
"""
import argparse, collections, json, math, sys
import shapely
from shapely.geometry import shape, box
from shapely.ops import unary_union

# ---- schema tables ---------------------------------------------------------------------------
WATER_POLY_BY_WATER = {  # water=* value -> kind; any other water=* value -> "other"
    "river": "river", "stream": "river", "canal": "canal",
    "lake": "lake", "oxbow": "lake", "lagoon": "lake",
    "reservoir": "reservoir", "pond": "pond", "fishpond": "pond",
}
WATER_LINE_KINDS = {"river", "canal", "stream"}
LINE_MINZOOM = {"river": 6, "canal": 8, "stream": 11}


def water_poly_kind(t):
    if "water" in t:
        return WATER_POLY_BY_WATER.get(t["water"], "other")
    if t.get("landuse") == "reservoir":
        return "reservoir"
    if t.get("waterway") == "riverbank":
        return "river"
    if t.get("natural") == "water":
        return "water"
    return None  # e.g. polygon assembled from a closed waterway=river way: not an area


def water_line_kind(t):
    k = t.get("waterway")
    if k not in WATER_LINE_KINDS or t.get("tunnel", "no") != "no":
        return None
    return k


def intermittent(t):
    return t.get("intermittent") == "yes" or t.get("seasonal") == "yes"


# Settlement sources: name -> (tags -> kind | None). A non-OSM source (e.g. polygonised GHSL raster)
# writes properties already shaped as {"kind": ...}; its entry then just passes kind through.
SETTLEMENT_SOURCES = {
    "osm": lambda t: "residential" if t.get("landuse") == "residential" else None,
}

# ---- geometry helpers ------------------------------------------------------------------------
EARTH_C = 40075016.686  # m, equatorial circumference
M_PER_DEG = 111319.49


def area_m2(g):
    return g.area * M_PER_DEG * M_PER_DEG * math.cos(math.radians(g.centroid.y))


def poly_minzoom(g, px2, maxz, area=None):
    """First zoom (512 px tiles) at which an area (default: g's own) covers >= px2 screen px^2. Latitude-corrected."""
    if px2 <= 0:
        return None
    k = math.cos(math.radians(g.centroid.y))
    area_m2 = area if area is not None else g.area * M_PER_DEG * M_PER_DEG * k
    if area_m2 <= 0:
        return maxz
    z = 0.5 * math.log2(px2 * (EARTH_C * k) ** 2 / (512 ** 2 * area_m2))
    return max(0, min(maxz, math.ceil(z)))


def keep_dim(g, dim):
    """Keep only parts of dimension dim (2 polygon, 1 line) after clipping/make_valid."""
    if g is None or g.is_empty:
        return None
    if shapely.get_dimensions(g) == dim and g.geom_type != "GeometryCollection":
        return g
    parts = [p for p in getattr(g, "geoms", [g]) if shapely.get_dimensions(p) == dim]
    if not parts:
        return None
    return unary_union(parts) if dim == 2 else shapely.line_merge(shapely.multilinestrings(
        [q for p in parts for q in getattr(p, "geoms", [p])]))


class Clipper:
    def __init__(self, outline_path, bbox):
        g = shape(json.load(open(outline_path))["features"][0]["geometry"])
        if bbox:
            g = g.intersection(box(*bbox))
        self.g = g
        shapely.prepare(self.g)

    def __call__(self, geom, dim):
        if not geom.is_valid:
            geom = shapely.make_valid(geom)
        if self.g.contains(geom):
            return keep_dim(geom, dim)
        if not self.g.intersects(geom):
            return None
        return keep_dim(shapely.intersection(geom, self.g), dim)


def cluster_areas(geoms, gap_m):
    """Union-find over polygons closer than gap_m; returns, per geometry, the summed area (m^2) of its cluster.
    Why: OSM maps cities as many block-sized polygons and villages as one, so per-feature area measures mapping
    granularity, not settlement size. Clustering across streets (gap < street width) restores the settlement as unit."""
    import numpy as np
    n = len(geoms)
    parent = np.arange(n)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    gap_deg = gap_m / M_PER_DEG / math.cos(math.radians(52.4))  # conservative in lon across Ukraine's latitudes
    tree = shapely.STRtree(geoms)
    a, b = tree.query(geoms, predicate="dwithin", distance=gap_deg)
    for i, j in zip(a, b):
        if i < j:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj
    roots = np.array([find(i) for i in range(n)])
    areas = np.array([area_m2(g) for g in geoms])
    tot = collections.defaultdict(float)
    for r, ar in zip(roots, areas):
        tot[r] += ar
    return [tot[r] for r in roots], len(set(roots.tolist()))


def read_seq(path):
    with open(path) as f:
        for line in f:
            line = line.strip().lstrip("\x1e")
            if line:
                yield json.loads(line)


def feature(props, geom, minzoom):
    s = '{"type":"Feature","properties":' + json.dumps(props, separators=(",", ":"))
    if minzoom:
        s += ',"tippecanoe":{"minzoom":%d}' % minzoom
    return s + ',"geometry":' + shapely.to_geojson(geom) + "}\n"


# ---- layers ----------------------------------------------------------------------------------
def run(a):
    clip = Clipper(a.outline, a.bbox)
    stats = collections.Counter()
    mz = collections.Counter()
    out = open(a.out, "w")

    if a.layer == "ground":
        pieces = [shape(f["geometry"]) for f in read_seq(a.inp)]
        land = keep_dim(shapely.intersection(unary_union(pieces), clip.g), 2)
        for p in getattr(land, "geoms", [land]):
            out.write(feature({}, p, None))
            stats["ground"] += 1
            mz[0] += 1

    elif a.layer == "water":
        for f in read_seq(a.inp):
            t, gt = f["properties"], f["geometry"]["type"]
            if gt in ("Polygon", "MultiPolygon"):
                kind, dim = water_poly_kind(t), 2
            elif gt in ("LineString", "MultiLineString"):
                kind, dim = water_line_kind(t), 1
            else:
                kind = None
            if not kind:
                stats["skipped:" + gt] += 1
                continue
            g = clip(shape(f["geometry"]), dim)
            if g is None:
                stats["outside"] += 1
                continue
            props = {"kind": kind}
            if intermittent(t):
                props["intermittent"] = True
            z = poly_minzoom(g, a.px2, a.maxzoom) if dim == 2 else LINE_MINZOOM[kind]
            out.write(feature(props, g, z))
            stats[("poly:" if dim == 2 else "line:") + kind] += 1
            stats["intermittent"] += "intermittent" in props
            mz[z or 0] += 1

    elif a.layer == "settlements":
        to_kind = SETTLEMENT_SOURCES[a.source]
        kept = []
        for f in read_seq(a.inp):
            if f["geometry"]["type"] not in ("Polygon", "MultiPolygon"):
                continue
            kind = to_kind(f["properties"])
            if not kind:
                stats["skipped"] += 1
                continue
            g = clip(shape(f["geometry"]), 2)
            if g is None:
                stats["outside"] += 1
                continue
            kept.append((kind, g))
        areas = [None] * len(kept)
        if a.cluster_m > 0 and kept:
            areas, nclusters = cluster_areas([g for _, g in kept], a.cluster_m)
            stats["clusters"] = nclusters
        for (kind, g), ar in zip(kept, areas):
            z = poly_minzoom(g, a.px2, a.maxzoom, ar)
            out.write(feature({"kind": kind, "source": a.source}, g, z))
            stats[kind] += 1
            mz[z or 0] += 1

    out.close()
    report = {"layer": a.layer, "counts": dict(sorted(stats.items())), "minzoom_histogram": dict(sorted(mz.items())),
              "px2": a.px2, "cluster_m": a.cluster_m, "bbox": a.bbox}
    json.dump(report, open(a.out + ".stats.json", "w"), indent=1)
    print(json.dumps(report), file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("layer", choices=["ground", "water", "settlements"])
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--outline", required=True)
    ap.add_argument("--bbox", type=lambda s: [float(x) for x in s.split(",")] if s else None, default=None)
    ap.add_argument("--px2", type=float, default=4)
    ap.add_argument("--maxzoom", type=int, default=14)
    ap.add_argument("--source", default="osm")
    ap.add_argument("--cluster-m", type=float, default=0, help="settlements: cluster polygons closer than this (m) for minzoom")
    run(ap.parse_args())
