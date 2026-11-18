#!/usr/bin/env bash
# Mechanical checks: PMTiles metadata vs docs/SCHEMA.md, feature counts, file size.
source "$(dirname "$0")/config.sh"
pmtiles show "$TILES" | grep -vE '^\s*$' | sed -n '1,30p'
pmtiles show --metadata "$TILES" > "$WORK/metadata.json"
"$PY" -I - "$WORK/metadata.json" "$WORK/layers" <<'PYEOF'
import json, sys, glob, os
md = json.load(open(sys.argv[1]))
vl = {l["id"]: l for l in md["vector_layers"]}
allowed = {"ground": set(), "water": {"kind", "intermittent"}, "settlements": {"kind", "source"}}
ok = set(vl) == set(allowed)
print("layers:", sorted(vl), "OK" if ok else "MISMATCH vs SCHEMA.md")
for lid, l in vl.items():
    extra = set(l.get("fields", {})) - allowed.get(lid, set())
    ok &= not extra
    print(f"  {lid:12s} z{l.get('minzoom')}-{l.get('maxzoom')} fields={l.get('fields')}" + (f"  UNEXPECTED {extra}" if extra else ""))
for ls in md.get("tilestats", {}).get("layers", []):
    vals = {a["attribute"]: a.get("values") for a in ls.get("attributes", [])}
    print(f"  tilestats {ls['layer']:12s} count={ls.get('count')} values={vals}")
for f in sorted(glob.glob(os.path.join(sys.argv[2], "*.stats.json"))):
    s = json.load(open(f)); print("  input", s["layer"], s["counts"])
sys.exit(0 if ok else 1)
PYEOF
ls -l "$TILES"
