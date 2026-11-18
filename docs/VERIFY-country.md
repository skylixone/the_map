# Country map — verification record (C5, 2026-11-18)

Build: `scripts/country/build.sh` with defaults = sample C (schema-country v0.2): builtup closing 0.5 px, water union-only,
min area 4 px², simplify 0.5 px, rivers ≥ 200 km inside the outline, river lines clipped to outline + 200 m.
Inputs: phase-1 work dir (OSM 2026-11-15T01:19:34Z). Runtime ≈ 11 min generalisation (4 min of it river grouping) + 5 s tiles.

## Output
`data/out/the_map-country.pmtiles` — 2,695,470 bytes, md5 `f08cf51da3852256e527c17a9f10c7c2`, z0–8, 139 tiles.
Phone page (private artifact, whole file as base64): https://claude.ai/artifact/2DC9v3pJXDNrrgNZFep2AP

## Per band (z0–3 reuse z4)
| z | builtup parts | builtup area ÷ residential (29,620 km²) | place dots | dots suppressed (inside own builtup) | water polygons | water km² |
|---|---|---|---|---|---|---|
| 4 | 110 | 0.52 | 24,570 | 1,893 | 29 | 7,803 |
| 5 | 469 | 0.46 | 24,482 | 1,981 | 65 | 8,132 |
| 6 | 2,940 | 0.71 | 21,718 | 4,745 | 247 | 8,777 |
| 7 | 10,136 | 0.94 | 16,060 | 10,403 | 1,220 | 9,796 |
| 8 | 20,064 | 0.99 | 12,269 | 14,194 | 5,391 | 11,066 |

Ratio < 1 at low zoom = area dropped as sub-4-px² parts; those settlements are carried by dots instead.

## Checks (`scripts/country/04_verify.sh`) — RESULT OK
- Metadata: layers exactly `builtup`, `ground`, `places`, `water`; fields only `place` (String), `pop` (Number); z0–8.
- Places: points decoded inside their own tile == band input, every band (24,570 … 12,269).
- Polygons: every sampled input part (≤ 2,000 per layer per band) is present in the decoded tiles. Interior-point cover is
  reported only: thin winding water parts lose it under tile simplification (z6 water 231/247) while still present.

## Rivers ≥ 200 km (37), length inside the outline
Дніпро 1114; Дністер 935; Південний Буг 847; Сіверський Донець 748; Горинь 652; Десна 600; Псел 570; Інгулець 556; Стир 513;
Случ 481; Сула 451; Оріль 397; Ворскла 389; Рось 376; Тетерів 376; Інгул 371; Удай 360; Самара 353; Вовча 341; Хорол 304;
Західний Буг 301; Прип'ять 291; Прут 277; Уж 276; Сейм 256; Збруч 256; Стохід 249; Серет 248; Стрий 245; Кінська 226;
Айдар 223; Лугань 222; Тиса 220; Висунь 210; Турія 206; Кальміус 205; Снов 204.
Near misses 150–200 km (not drawn): Тясмин 196; Салгир 190; Кринка 189; Ірпінь 186; Уборть 179; Смотрич 177; Гірський Тікич 177;
Чичиклія 176; Оскіл 171; Базавлук 169; Велика Вись 167; Гнилий Тікич 165; Кодима 165; Уди 164; Остер 164; Тилігул 159; Іква 158;
Мокрі Яли 156; Деркул 155; Латориця 153.

Caveat: lengths sum every same-named channel of a river (braids, anabranches not tagged `side_stream`), so they run high —
Дніпро 1,114 km vs the ~981 km commonly cited for its Ukrainian course. Near the 200 km line (Снов 204, Кальміус 205,
Тясмин 196) the selection is within that error. Danube: not in either list (its Ukrainian stretch is short and on the border);
it shows as water polygons.

## Visual (docs/img/country/abc-2026-11-18.png, samples A/B/C)
- Phone z3.9: busy in all samples — ~24k dots on ~400 × 250 px. Data is complete; thinning belongs to style
  (e.g. `pop` ≥ 3 below z5 = 418 dots). Open for the styling phase.
- Desktop z5: western Ukraine reads as dense village texture, river valleys as strings of settlements; reservoirs clear.
- Crimea isthmus z6.5: grid of thin water = North Crimean canal + irrigation canals mapped as water areas (real).
- Kyiv z7.6 (print preview): footprints legible, Dnipro/Desna clean.
