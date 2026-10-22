#!/usr/bin/env python3
"""Composite a REAL road-network geo overlay over an original photo.

This replaces the retired contour version. It draws no invented
geometry: roads come from Overpass JSON files (see SKILL.md Step 3),
labels and coordinates come from the config file, which must contain
only verified values.

Usage:
  python3 make_editorial_geo.py --src photo.jpg \
      --osm-major osm_major.json --osm-minor osm_minor.json \
      --config config.json --out finished.jpg

Config keys:
  lon_min, lon_max, lat_min, lat_max: map bbox, centred on the
      shooting point, sized so its geographic aspect matches the
      map rectangle below.
  map_rect: {left, right, top, bottom} as fractions of width/height.
      Default: 0.04, 0.97, 0.03, 0.33 (top third of the frame).
  title: serif capitals, e.g. "B I J I E".
  coords: e.g. "27.28° N    105.30° E" (two decimals, EXIF-derived).
  subline: optional, e.g. "1766 m  ·  62° NE" (only if EXIF verified).
  viewpoint: {lon, lat, label}  red dot, required.
  nearby: [{lon, lat, label}]  optional, projected, never hand-placed.
  scale_km: default 4. Scale bar ticks at 0, 1, 2 and scale_km.
  compass: {x, y} fractions for the compass centre. Default 0.114, 0.196.
  scale_pos: {x, y} fractions for the scale bar. Default 0.052, 0.276.

Output: only the finished picture. This script deliberately writes
NO transparent layer file. The layer is a working intermediate, not
a deliverable; see SKILL.md "Deliver only the main image".
"""
import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont


def serif(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    return ImageFont.truetype(path, max(8, int(size)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--osm-major", required=True)
    parser.add_argument("--osm-minor", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--no-grain", action="store_true")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    base = Image.open(args.src).convert("RGBA")
    width, height = base.size
    scale = width / 1320.0

    rect = cfg.get("map_rect", {})
    left = int(width * rect.get("left", 0.04))
    right = int(width * rect.get("right", 0.97))
    top = int(height * rect.get("top", 0.03))
    bottom = int(height * rect.get("bottom", 0.33))
    mw, mh = right - left, bottom - top

    lon_min, lon_max = cfg["lon_min"], cfg["lon_max"]
    lat_min, lat_max = cfg["lat_min"], cfg["lat_max"]

    def proj(lon, lat):
        x = left + (lon - lon_min) / (lon_max - lon_min) * mw
        y = top + (lat_max - lat) / (lat_max - lat_min) * mh
        return x, y

    ink = (238, 238, 232)
    roads = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    rd = ImageDraw.Draw(roads)

    for path, is_major in [(args.osm_minor, False), (args.osm_major, True)]:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for el in data.get("elements", []):
            if el.get("type") != "way":
                continue
            geom = el.get("geometry", [])
            if len(geom) < 2:
                continue
            pts = [proj(g["lon"], g["lat"]) for g in geom]
            hw = el.get("tags", {}).get("highway", "")
            if not is_major:
                rd.line(pts, fill=ink + (110,), width=1, joint="curve")
            elif hw in ("motorway", "trunk", "primary"):
                rd.line(pts, fill=ink + (215,), width=2, joint="curve")
            elif hw == "secondary":
                rd.line(pts, fill=ink + (185,), width=2, joint="curve")
            else:
                rd.line(pts, fill=ink + (165,), width=1, joint="curve")

    # Edge fade: roads dissolve over ~70 px inside the map rectangle.
    try:
        import numpy as np
        arr = np.array(roads).astype("float32")
        ys, xs = np.mgrid[0:height, 0:width]
        dx = np.minimum(xs - left, right - xs)
        dy = np.minimum(ys - top, bottom - ys)
        d = np.minimum(dx, dy)
        fade = np.clip(d / 70.0, 0, 1)
        fade = fade * fade * (3 - 2 * fade)
        arr[..., 3] *= fade
        roads = Image.fromarray(arr.astype("uint8"), "RGBA")
    except Exception as exc:
        print(f"edge fade skipped: {exc}", file=sys.stderr)

    layer = roads.copy()
    ld = ImageDraw.Draw(layer)
    dark = (30, 40, 50, 150)

    # Title, coordinates, subline: top left, serif, like the Xi'an reference.
    tx = int(width * 0.05)
    ld.text((tx, int(height * 0.039)), cfg.get("title", ""), font=serif(54 * scale, True),
            fill=(242, 242, 238, 255), stroke_width=1, stroke_fill=(30, 40, 50, 120))
    ld.text((tx + 2, int(height * 0.080)), cfg.get("coords", ""), font=serif(22 * scale),
            fill=(242, 242, 238, 240))
    if cfg.get("subline"):
        ld.text((tx + 2, int(height * 0.097)), cfg["subline"], font=serif(18 * scale),
                fill=(242, 242, 238, 200))

    # Compass rose, left side over the map.
    comp = cfg.get("compass", {"x": 0.114, "y": 0.196})
    cx, cy, r = int(width * comp["x"]), int(height * comp["y"]), int(42 * scale)
    ld.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(242, 242, 238, 200), width=1)
    ld.polygon([(cx, cy - r - 8), (cx - 7, cy), (cx, cy + r + 8), (cx + 7, cy)],
               outline=(242, 242, 238, 220), width=1)
    ld.polygon([(cx - r - 8, cy), (cx, cy - 7), (cx + r + 8, cy), (cx, cy + 7)],
               outline=(242, 242, 238, 220), width=1)
    ld.text((cx - 7, cy - r - 32), "N", font=serif(20 * scale, True), fill=(242, 242, 238, 240))
    ld.text((cx + r + 12, cy - 12), "E", font=serif(20 * scale, True), fill=(242, 242, 238, 240))
    ld.text((cx - 7, cy + r + 10), "S", font=serif(20 * scale, True), fill=(242, 242, 238, 240))
    ld.text((cx - r - 26, cy - 12), "W", font=serif(20 * scale, True), fill=(242, 242, 238, 240))

    # Scale bar, computed from the real map width, never copied.
    mean_lat = math.radians((lat_min + lat_max) / 2)
    map_width_km = (lon_max - lon_min) * 111.32 * math.cos(mean_lat)
    scale_km = cfg.get("scale_km", 4)
    px_per_km = mw / map_width_km if map_width_km else 0
    spos = cfg.get("scale_pos", {"x": 0.052, "y": 0.276})
    sx, sy = int(width * spos["x"]), int(height * spos["y"])
    x_end = sx + int(scale_km * px_per_km)
    ld.line([(sx, sy), (x_end, sy)], fill=(242, 242, 238, 230), width=2)
    for km in (0, 1, 2, scale_km):
        x = sx + int(km * px_per_km)
        ld.line([(x, sy - 6), (x, sy + 6)], fill=(242, 242, 238, 230), width=2)
        label = f"{km} km" if km == scale_km else str(km)
        ld.text((x - 6, sy - 28), label, font=serif(16 * scale), fill=(242, 242, 238, 220))

    # Shooting point: red dot at the projected EXIF point.
    vp = cfg["viewpoint"]
    vx, vy = proj(vp["lon"], vp["lat"])
    red = (193, 39, 45)
    ld.ellipse([vx - 18, vy - 18, vx + 18, vy + 18], outline=(193, 39, 45, 70), width=1)
    ld.ellipse([vx - 11, vy - 11, vx + 11, vy + 11], outline=(255, 255, 255, 230), width=2)
    ld.ellipse([vx - 7, vy - 7, vx + 7, vy + 7], fill=red + (255,))
    ld.text((vx + 18, vy - 14), vp.get("label", ""), font=serif(22 * scale),
            fill=(242, 242, 238, 245), stroke_width=1, stroke_fill=dark)

    # Verified nearby places, at their own projected coordinates.
    for nb in cfg.get("nearby", []):
        nx, ny = proj(nb["lon"], nb["lat"])
        ld.line([(vx + 9, vy + 8), (nx - 8, ny - 6)], fill=(242, 242, 238, 150), width=1)
        ld.ellipse([nx - 6, ny - 6, nx + 6, ny + 6], fill=(242, 242, 238, 255),
                   outline=(255, 255, 255, 200), width=1)
        ld.text((nx + 12, ny - 12), nb.get("label", ""), font=serif(18 * scale),
                fill=(242, 242, 238, 235), stroke_width=1, stroke_fill=dark)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    out = Image.alpha_composite(base, layer)
    if not args.no_grain:
        try:
            import numpy as np
            arr = np.array(out).astype("int16")
            noise = np.random.default_rng(7).normal(0, 4, arr.shape[:2])[..., None]
            out = Image.fromarray(np.clip(arr + noise, 0, 255).astype("uint8"), "RGBA")
        except Exception as exc:
            print(f"grain skipped: {exc}", file=sys.stderr)
    out.convert("RGB").save(args.out, quality=95)
    print(f"saved {args.out} {width}x{height} map_width_km={map_width_km:.2f}")


if __name__ == "__main__":
    main()
