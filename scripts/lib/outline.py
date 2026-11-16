"""Normalise a clip-outline source to one (Multi)Polygon and test what it contains.
usage: outline.py SRC.geojson OUT.geojson LABEL
Fails loudly if Crimea is not inside: the outline must be the internationally recognised border."""
import json, sys
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union
from shapely.validation import make_valid

src, out, label = sys.argv[1:4]
feats = json.load(open(src))["features"]
geom = make_valid(unary_union([shape(f["geometry"]) for f in feats if f["geometry"]["type"] in ("Polygon", "MultiPolygon")]))
must_in = {"Kyiv": (30.523, 50.450), "Simferopol": (34.100, 44.952), "Sevastopol": (33.522, 44.616),
           "Kerch": (36.471, 45.357), "Nova Kakhovka": (33.36, 46.75), "Donetsk": (37.80, 48.00), "Izmail": (28.84, 45.35), "Zmiinyi Is.": (30.204, 45.255), "Tuzla Is.": (36.56, 45.30)}
must_out = {"Taganrog RU": (38.90, 47.22), "Chisinau MD": (28.86, 47.01), "Brest BY": (23.69, 52.10), "Tulcea RO": (28.80, 45.17), "Taman RU": (36.72, 45.21)}
bad = [k for k, p in must_in.items() if not geom.contains(Point(p))] + [k for k, p in must_out.items() if geom.contains(Point(p))]
parts = len(getattr(geom, "geoms", [geom]))
nverts = sum(len(r.coords) for g in getattr(geom, "geoms", [geom]) for r in [g.exterior, *g.interiors])
print(f"outline[{label}]: {geom.geom_type}, {parts} part(s), {nverts} vertices, bounds {[round(b, 3) for b in geom.bounds]}")
if bad:
    sys.exit(f"outline[{label}] FAILED containment test: {bad}")
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"source": label}, "geometry": mapping(geom)}]}, open(out, "w"))
print("containment test passed:", ", ".join(must_in), "inside;", ", ".join(must_out), "outside")
