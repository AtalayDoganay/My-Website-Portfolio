"""Draw the site's pixel art.

    python tools/pixel_art.py --out src/assets/pixel

Everything is placed on an explicit integer grid with a fixed palette. There is no
downsampling of a render and no pixelation filter anywhere in here: shapes are built
from pixel clusters, diagonals are stepped by hand, shading is a small number of
deliberate tones, and the only texture is ordered dithering.

The dark and light variants run the *same geometry code* with different palettes, so
the two images line up pixel for pixel and the screen sits at identical coordinates
in both. That is what lets the page swap themes without moving anything.

No third-party module is used - the PNG writer below is about thirty lines.
"""

import argparse
import binascii
import json
import os
import struct
import zlib

# ---------------------------------------------------------------- PNG output


def write_png(path, width, height, rgba_rows):
    """Write 8-bit RGBA PNG. rgba_rows is a list of rows of (r,g,b,a) tuples."""
    raw = bytearray()
    for row in rgba_rows:
        raw.append(0)  # filter type 0
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return os.path.getsize(path)


def hex_rgba(value):
    value = value.lstrip("#")
    if len(value) == 6:
        value += "ff"
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4, 6))


# ------------------------------------------------------------------- canvas


class Canvas:
    """An indexed pixel grid. Colours are palette keys, so a second palette
    redraws the same picture in another theme without touching the geometry."""

    def __init__(self, w, h, palette):
        self.w, self.h = w, h
        self.palette = palette
        self.px = [[None] * w for _ in range(h)]

    def set(self, x, y, key):
        if key is None:
            return
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = key

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def rect(self, x, y, w, h, key):
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.set(xx, yy, key)

    def frame(self, x, y, w, h, key):
        """A one-pixel outline, the thickness used everywhere."""
        x, y, w, h = int(x), int(y), int(w), int(h)
        for xx in range(x, x + w):
            self.set(xx, y, key)
            self.set(xx, y + h - 1, key)
        for yy in range(y, y + h):
            self.set(x, yy, key)
            self.set(x + w - 1, yy, key)

    def hline(self, x0, x1, y, key):
        for x in range(int(min(x0, x1)), int(max(x0, x1)) + 1):
            self.set(x, y, key)

    def vline(self, x, y0, y1, key):
        for y in range(int(min(y0, y1)), int(max(y0, y1)) + 1):
            self.set(x, y, key)

    def line(self, x0, y0, x1, y1, key):
        """Bresenham, so diagonals step cleanly instead of being anti-aliased."""
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, key)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def poly(self, points, key):
        """Filled convex polygon by scanline, with the edges drawn after so the
        silhouette stays exactly one pixel wide."""
        ys = [p[1] for p in points]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                (x0, y0), (x1, y1) = points[i], points[(i + 1) % n]
                if y0 == y1:
                    continue
                if min(y0, y1) <= y < max(y0, y1):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            if len(xs) >= 2:
                self.hline(round(min(xs)), round(max(xs)), y, key)

    def outline_poly(self, points, key):
        for i in range(len(points)):
            a, b = points[i], points[(i + 1) % len(points)]
            self.line(a[0], a[1], b[0], b[1], key)

    def dither(self, x, y, w, h, key, density=2):
        """Ordered 4x4 dither, used sparingly to shade a large flat area."""
        matrix = [
            [0, 8, 2, 10],
            [12, 4, 14, 6],
            [3, 11, 1, 9],
            [15, 7, 13, 5],
        ]
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                if matrix[yy % 4][xx % 4] < density:
                    self.set(xx, yy, key)

    def to_rows(self, background=None):
        clear = (0, 0, 0, 0)
        rows = []
        for y in range(self.h):
            row = []
            for x in range(self.w):
                key = self.px[y][x]
                if key is None:
                    row.append(hex_rgba(self.palette[background]) if background else clear)
                else:
                    row.append(hex_rgba(self.palette[key]))
            rows.append(row)
        return rows


# ------------------------------------------------------------------ palettes
# Identical keys in both themes. The outline key is the hard requirement: pure
# white on dark, pure black on light, one pixel thick everywhere.

DARK = {
    "outline": "#FFFFFF",
    "case_top": "#7C88B8",     # the lit top face
    "case_front": "#59648F",   # the face turned toward us
    "case_side": "#3D4670",    # the left side, turned away
    "case_deep": "#2B3054",    # under-shadow and recesses
    "case_edge": "#96A2CE",    # bevel catch-light
    "glass": "#10173A",
    "glass_lit": "#1C2A5E",
    "cyan": "#7FE3F5",
    "violet": "#B49BF0",
    "led": "#7FF5C4",
    "shadow": "#151936",
    "key_top": "#69749E",
    "key_side": "#454E79",
}

LIGHT = {
    "outline": "#000000",
    "case_top": "#F2F6FC",
    "case_front": "#D3DEF0",
    "case_side": "#B3C2DE",
    "case_deep": "#93A3C4",
    "case_edge": "#FFFFFF",
    "glass": "#C9D8EC",
    "glass_lit": "#E6EFFA",
    "cyan": "#5FB6C8",
    "violet": "#9E86D4",
    "led": "#3FA98A",
    "shadow": "#A9B6CE",
    "key_top": "#E4EBF6",
    "key_side": "#BFCCE2",
}

# ------------------------------------------------------- the machine geometry
# One oblique projection, depth running back and to the LEFT. That is what turns
# the monitor to face slightly right: we see its left side casing, while the front
# face - and so the screen - stays a true rectangle on the grid. Keeping the screen
# axis-aligned is what lets the live text sit on the pixel grid without resampling.

W, H = 216, 150

FRONT_X, FRONT_Y = 74, 22          # monitor front face
FRONT_W, FRONT_H = 84, 74
DEPTH_X, DEPTH_Y = 22, 11          # the 2:1 oblique step

SCREEN_X, SCREEN_Y = 82, 29        # the glass, 4:3 on the grid
SCREEN_W, SCREEN_H = 68, 51


def draw_machine(c):
    o = "outline"
    fx, fy, fw, fh = FRONT_X, FRONT_Y, FRONT_W, FRONT_H
    dx, dy = DEPTH_X, DEPTH_Y

    # ---- cast shadow on the desk, a flat stepped ellipse ------------------
    for half, yy in ((30, 113), (34, 114), (31, 115)):
        c.hline(116 - half, 116 + half, yy, "shadow")
    for half, yy in ((62, 142), (66, 143), (63, 144)):
        c.hline(116 - half, 116 + half, yy, "shadow")

    # ---- monitor: left side face -----------------------------------------
    side = [(fx, fy), (fx - dx, fy - dy), (fx - dx, fy + fh - dy), (fx, fy + fh)]
    c.poly(side, "case_side")
    # vent slots, stepped along the oblique so they sit on the side plane
    for i in range(6):
        sy = fy + 16 + i * 7
        c.line(fx - 4, sy, fx - dx + 3, sy - (dy - 6), "case_deep")

    # ---- monitor: top face ------------------------------------------------
    top = [(fx, fy), (fx + fw, fy), (fx + fw - dx, fy - dy), (fx - dx, fy - dy)]
    c.poly(top, "case_top")

    # ---- monitor: front face ---------------------------------------------
    c.rect(fx, fy, fw, fh, "case_front")
    # bevel catch-light along the top and left of the front moulding
    c.hline(fx + 1, fx + fw - 2, fy + 1, "case_edge")
    c.vline(fx + 1, fy + 1, fy + fh - 2, "case_edge")
    # moulded seam where the front shell meets the back
    c.vline(fx + 3, fy + 3, fy + fh - 3, "case_deep")

    # ---- the tube ---------------------------------------------------------
    sx, sy, sw, sh = SCREEN_X, SCREEN_Y, SCREEN_W, SCREEN_H
    c.rect(sx - 2, sy - 2, sw + 4, sh + 4, "case_deep")     # recess
    c.rect(sx, sy, sw, sh, "glass")
    # the tube is brighter toward the middle; two steps, no gradient
    c.rect(sx + 6, sy + 5, sw - 12, sh - 10, "glass_lit")
    # only where the two tones meet, so the tube does not read as a dotted field
    c.dither(sx + 3, sy + 3, sw - 6, 3, "glass_lit", density=6)
    c.dither(sx + 3, sy + sh - 6, sw - 6, 3, "glass_lit", density=6)
    c.frame(sx - 1, sy - 1, sw + 2, sh + 2, o)

    # ---- chin: controls ---------------------------------------------------
    chin_y = sy + sh + 7
    c.frame(fx + 6, chin_y, 7, 7, o)                 # power switch
    c.rect(fx + 7, chin_y + 1, 5, 5, "case_top")
    c.set(fx + 9, chin_y + 2, o)
    c.set(fx + 9, chin_y + 3, o)
    c.rect(fx + 17, chin_y + 2, 3, 3, "led")         # power indicator
    for i in range(4):                                # adjustment buttons
        c.rect(fx + 46 + i * 8, chin_y + 2, 5, 3, "case_deep")
    c.hline(fx + 6, fx + 30, chin_y - 5, "case_deep")  # moulded strip

    # ---- monitor silhouette ----------------------------------------------
    c.outline_poly(top, o)
    c.outline_poly(side, o)
    c.frame(fx, fy, fw, fh, o)

    # ---- stand ------------------------------------------------------------
    neck = [(104, fy + fh), (128, fy + fh), (128, fy + fh + 9), (104, fy + fh + 9)]
    c.poly(neck, "case_front")
    c.vline(105, fy + fh, fy + fh + 8, "case_edge")
    c.outline_poly(neck, o)

    base_front = [(92, 105), (140, 105), (140, 112), (92, 112)]
    base_top = [(92, 105), (140, 105), (140 - 10, 100), (92 - 10, 100)]
    c.poly(base_top, "case_top")
    c.poly(base_front, "case_front")
    c.outline_poly(base_top, o)
    c.outline_poly(base_front, o)

    # ---- keyboard ---------------------------------------------------------
    kb_fl, kb_fr, kb_y = 52, 180, 138
    kdx, kdy = 34, 17
    deck = [(kb_fl, kb_y), (kb_fr, kb_y), (kb_fr - kdx, kb_y - kdy), (kb_fl - kdx, kb_y - kdy)]
    lip = [(kb_fl, kb_y), (kb_fr, kb_y), (kb_fr, kb_y + 6), (kb_fl, kb_y + 6)]
    c.poly(lip, "case_side")
    c.poly(deck, "case_front")

    # Keycaps: five rows following the deck's own slope, so every row lands on it.
    # step_y is the deck depth divided by the rows, step_x the matching oblique run.
    n_rows = 5
    step_y = kdy / (n_rows + 0.6)
    step_x = kdx / (n_rows + 0.6)
    rows = [(7, 1.6), (13, 1.0), (14, 1.0), (15, 1.0), (16, 1.0)]   # front to back
    for r, (count, kw_mul) in enumerate(rows):
        ry = int(kb_y - 3 - r * step_y)
        rx = int(kb_fl + 6 - r * step_x)
        right = int(kb_fr - 6 - r * step_x)
        span = right - rx
        pitch = span / count
        kw = max(3, int(pitch / kw_mul) - 1)
        for k in range(count):
            kx = rx + int(k * pitch)
            if kx + kw > right:
                continue
            c.rect(kx, ry - 2, kw, 2, "case_top")
            c.hline(kx, kx + kw - 1, ry, "case_deep")

    c.outline_poly(deck, o)
    c.outline_poly(lip, o)
    return {
        "screen": {"x": sx, "y": sy, "w": sw, "h": sh},
        "canvas": {"w": W, "h": H},
    }


# ------------------------------------------------ the compact composition
# A 216-wide picture on a 390-wide phone can only be shown at 1x before it runs
# off the screen, which leaves the tube far too small to read. So narrow screens
# get their own framing rather than a shrunken copy of this one: the monitor
# alone, drawn larger on a smaller canvas, at the same scale on the same grid.

CW, CH = 120, 126
C_FX, C_FY, C_FW, C_FH = 20, 10, 88, 78
C_DX, C_DY = 16, 8
C_SX, C_SY, C_SW, C_SH = 28, 17, 72, 54


def draw_machine_compact(c):
    o = "outline"
    fx, fy, fw, fh = C_FX, C_FY, C_FW, C_FH
    dx, dy = C_DX, C_DY

    for half, yy in ((26, 106), (29, 107), (27, 108)):
        c.hline(64 - half, 64 + half, yy, "shadow")

    side = [(fx, fy), (fx - dx, fy - dy), (fx - dx, fy + fh - dy), (fx, fy + fh)]
    c.poly(side, "case_side")
    for i in range(5):
        sy = fy + 16 + i * 9
        c.line(fx - 3, sy, fx - dx + 2, sy - (dy - 5), "case_deep")

    top = [(fx, fy), (fx + fw, fy), (fx + fw - dx, fy - dy), (fx - dx, fy - dy)]
    c.poly(top, "case_top")

    c.rect(fx, fy, fw, fh, "case_front")
    c.hline(fx + 1, fx + fw - 2, fy + 1, "case_edge")
    c.vline(fx + 1, fy + 1, fy + fh - 2, "case_edge")
    c.vline(fx + 3, fy + 3, fy + fh - 3, "case_deep")

    sx, sy, sw, sh = C_SX, C_SY, C_SW, C_SH
    c.rect(sx - 2, sy - 2, sw + 4, sh + 4, "case_deep")
    c.rect(sx, sy, sw, sh, "glass")
    c.rect(sx + 6, sy + 5, sw - 12, sh - 10, "glass_lit")
    c.dither(sx + 3, sy + 3, sw - 6, 3, "glass_lit", density=6)
    c.dither(sx + 3, sy + sh - 6, sw - 6, 3, "glass_lit", density=6)
    c.frame(sx - 1, sy - 1, sw + 2, sh + 2, o)

    chin_y = sy + sh + 6
    c.frame(fx + 6, chin_y, 7, 7, o)
    c.rect(fx + 7, chin_y + 1, 5, 5, "case_top")
    c.set(fx + 9, chin_y + 2, o)
    c.set(fx + 9, chin_y + 3, o)
    c.rect(fx + 17, chin_y + 2, 3, 3, "led")
    for i in range(4):
        c.rect(fx + 48 + i * 8, chin_y + 2, 5, 3, "case_deep")

    c.outline_poly(top, o)
    c.outline_poly(side, o)
    c.frame(fx, fy, fw, fh, o)

    neck = [(52, fy + fh), (76, fy + fh), (76, fy + fh + 8), (52, fy + fh + 8)]
    c.poly(neck, "case_front")
    c.vline(53, fy + fh, fy + fh + 7, "case_edge")
    c.outline_poly(neck, o)

    base_front = [(44, 96), (84, 96), (84, 103), (44, 103)]
    base_top = [(44, 96), (84, 96), (84 - 8, 92), (44 - 8, 92)]
    c.poly(base_top, "case_top")
    c.poly(base_front, "case_front")
    c.outline_poly(base_top, o)
    c.outline_poly(base_front, o)

    return {"screen": {"x": sx, "y": sy, "w": sw, "h": sh}, "canvas": {"w": CW, "h": CH}}


# ------------------------------------------------------------- the wallpaper
# A pixel landscape for the desktop: a dithered sky, a low ridge, and the lit
# doorway that appears everywhere else on the site.

WALL_W, WALL_H = 240, 150


def draw_wallpaper(c):
    o = "outline"
    # sky: three flat bands, dithered where they meet instead of blended
    c.rect(0, 0, WALL_W, 54, "case_deep")
    c.dither(0, 46, WALL_W, 14, "case_side", density=6)
    c.rect(0, 60, WALL_W, 26, "case_side")
    c.dither(0, 78, WALL_W, 12, "case_front", density=6)
    c.rect(0, 90, WALL_W, 18, "case_front")

    # stars, on a fixed scatter so both themes match
    for sx, sy in ((18, 10), (46, 22), (73, 8), (101, 17), (137, 11), (166, 25),
                   (191, 9), (215, 19), (29, 33), (122, 31), (203, 38)):
        c.set(sx, sy, "case_edge")

    # a disc: the moon in dark, the sun in light. Same circle either way.
    cx, cy, r = 186, 30, 13
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            if x * x + y * y <= r * r:
                c.set(cx + x, cy + y, "case_edge")
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            if x * x + y * y <= r * r and (x * x + y * y) > (r - 1) * (r - 1):
                c.set(cx + x, cy + y, o)

    # far ridge, stepped
    ridge = [(0, 100)]
    for x, y in ((28, 92), (52, 98), (84, 86), (112, 96), (148, 88), (180, 97), (212, 90), (240, 96)):
        ridge.append((x, y))
    ridge += [(WALL_W, WALL_H), (0, WALL_H)]
    c.poly(ridge, "case_side")
    c.outline_poly(ridge, o)

    # near ground
    near = [(0, 116), (40, 111), (92, 118), (150, 110), (198, 117), (WALL_W, 112),
            (WALL_W, WALL_H), (0, WALL_H)]
    c.poly(near, "case_deep")
    c.outline_poly(near, o)
    c.dither(0, 124, WALL_W, WALL_H - 124, "shadow", density=3)

    # the doorway, standing in the field
    dx0, dy0 = 62, 104
    c.rect(dx0, dy0, 9, 16, "led")
    c.frame(dx0 - 1, dy0 - 1, 11, 18, o)
    c.set(dx0 - 2, dy0 + 17, "case_edge")
    c.set(dx0 + 10, dy0 + 17, "case_edge")
    return {"canvas": {"w": WALL_W, "h": WALL_H}}


# ------------------------------------------------------------------- runner


def emit(name, width, height, draw, out_dir, background=None):
    meta = {}
    sizes = {}
    for theme, palette in (("dark", DARK), ("light", LIGHT)):
        c = Canvas(width, height, palette)
        meta = draw(c) or {}
        path = os.path.join(out_dir, f"{name}-{theme}.png")
        sizes[theme] = write_png(path, width, height, c.to_rows(background))
    return meta, sizes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="src/assets/pixel")
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    machine_meta, machine_sizes = emit("machine", W, H, draw_machine, out)
    compact_meta, compact_sizes = emit("machine-compact", CW, CH, draw_machine_compact, out)
    wall_meta, wall_sizes = emit("wallpaper", WALL_W, WALL_H, draw_wallpaper, out, background="case_deep")

    s = machine_meta["screen"]
    meta = {
        "generatedBy": "tools/pixel_art.py",
        "note": "Drawn on an integer grid from a fixed palette. Not a downscaled render.",
        "machine": {
            "canvas": [W, H],
            "screen": s,
            # as fractions of the image, which is what the CSS overlay needs
            "screenFraction": {
                "left": s["x"] / W, "top": s["y"] / H,
                "width": s["w"] / W, "height": s["h"] / H,
            },
            "bytes": machine_sizes,
        },
        "machineCompact": {
            "canvas": [CW, CH],
            "screen": compact_meta["screen"],
            "screenFraction": {
                "left": compact_meta["screen"]["x"] / CW,
                "top": compact_meta["screen"]["y"] / CH,
                "width": compact_meta["screen"]["w"] / CW,
                "height": compact_meta["screen"]["h"] / CH,
            },
            "bytes": compact_sizes,
        },
        "wallpaper": {"canvas": [WALL_W, WALL_H], "bytes": wall_sizes},
    }
    with open(os.path.join(out, "pixel.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print("machine  %d x %d  screen %d,%d %dx%d  dark %d B  light %d B" % (
        W, H, s["x"], s["y"], s["w"], s["h"], machine_sizes["dark"], machine_sizes["light"]))
    print("wallpaper %d x %d  dark %d B  light %d B" % (
        WALL_W, WALL_H, wall_sizes["dark"], wall_sizes["light"]))
    cs = compact_meta["screen"]
    print("compact   %d x %d  screen %d,%d %dx%d  dark %d B" % (
        CW, CH, cs["x"], cs["y"], cs["w"], cs["h"], compact_sizes["dark"]))
    print("screen aspect wide %.3f compact %.3f (4:3 = 1.333)" % (
        s["w"] / s["h"], cs["w"] / cs["h"]))


if __name__ == "__main__":
    main()
