import math

# ============================================================================
# The desk scene.
#
# ONE VIEWPOINT, SHARED BY EVERYTHING. The scene is laid out in desk
# coordinates first - x to the right, y up from the tabletop, z away from the
# viewer, one unit being one pixel at the front plane - and drawn through one
# projection (`View`): the viewer stands in front of the desk and slightly
# above it, so depth is foreshortened to HALF and recedes UP the picture, with
# a modest turn of one pixel to the LEFT for every six units of depth. Front
# faces stay true rectangles on the grid, tops are visible parallelograms, and
# left sides are thin slivers. Physical positions are decided before anything
# is drawn: every object below has a footprint on the tabletop, a height, and
# a depth, and its contact shadow sits under its front edge on that plane.
#
# Volume comes from deliberate planes, never from shading a single tone: a LIT
# TOP (case_top), a FRONT turned toward us (case_front), a LEFT SIDE turned
# away (case_side), a bright edge where two planes meet toward the light
# (case_edge), and a dark recess or underside (case_deep). The light is up and
# to the left, and it stays there.
#
# Real proportions, at 0.435 px/mm: a 455mm keyboard is 198 wide; a 14-inch
# CRT is 132 wide, 118 tall and 138 deep, stepped from a bezel block to a
# narrower tube housing; a small tower is 66 x 140 x 138; a mouse 27 x 50 and
# 16 high; the desk 1200 x 575 with a 28mm top. The narrow framing keeps the
# same projection at a smaller equipment scale, so the tube stays readable.
# ============================================================================


class View:
    """The scene's one projection. Returns integer canvas coordinates."""

    def __init__(self, x0, y0):
        self.x0, self.y0 = x0, y0          # canvas position of desk-space (0, 0, 0)

    def __call__(self, x, y, z):
        return (round(self.x0 + x - z / 6), round(self.y0 - y - z / 2))

    def col(self, x, z):
        return round(self.x0 + x - z / 6)

    def row(self, y, z):
        return round(self.y0 - y - z / 2)


def frange(a, b, step=0.5):
    n = int(round((b - a) / step))
    return [a + i * step for i in range(n + 1)]


# ----------------------------------------------------------------- helpers


def face_rect(c, p, x0, x1, y0, y1, z, key):
    """The front face of a box: inclusive extents, a true rectangle."""
    ax, ay = p(x0, y1, z)
    bx, by = p(x1, y0, z)
    if key:
        c.rect(ax, ay, bx - ax + 1, by - ay + 1, key)
    return ax, ay, bx, by


def draw_box(c, p, x0, x1, y0, y1, z0, z1, top="case_top", front="case_front",
             side="case_side", edge=True, outline=True):
    """A box with inclusive x/y extents and depth z0..z1: left side, top, front."""
    o = "outline"
    S = [p(x0, y0, z0), p(x0, y1, z0), p(x0, y1, z1), p(x0, y0, z1)]
    T = [p(x0, y1, z0), p(x1, y1, z0), p(x1, y1, z1), p(x0, y1, z1)]
    if side:
        c.poly(S, side)
    if top:
        c.poly(T, top)
    F = face_rect(c, p, x0, x1, y0, y1, z0, front)
    ax, ay, bx, by = F
    if front and edge:
        c.hline(ax + 1, bx - 1, ay + 1, "case_edge")
        c.vline(ax + 1, ay + 1, by - 1, "case_edge")
    if outline:
        if side:
            c.outline_poly(S, o)
        if top:
            c.outline_poly(T, o)
        if front:
            c.frame(ax, ay, bx - ax + 1, by - ay + 1, o)
    return S, T, F


def contact(c, p, x0, x1, z):
    """The tight occlusion shadow under an object's front edge, on the tabletop."""
    r = p(x0, 0, z)[1] + 1
    c.hline(p(x0, 0, z)[0], p(x1, 0, z)[0], r, "desk_side")
    c.hline(p(x0, 0, z)[0] + 2, p(x1, 0, z)[0] - 2, r + 1, "desk_side")


def cast(c, p, x1, z0, z1, width=8):
    """The longer shadow an object throws to the RIGHT along its depth.

    The light is up and to the left, so everything on this desk throws the
    same way; the band follows the object's footprint on the tabletop plane.
    """
    c.poly([p(x1 + 1, 0, z0), p(x1 + width, 0, z0), p(x1 + width, 0, z1), p(x1 + 1, 0, z1)],
           "desk_cast")


def fill_holes(layer):
    """Close single pixels the sampled surfaces skipped inside a solid shape.

    The outline pass rings anything transparent, so a one-pixel hole inside a
    shell would come out as a white diamond on it. A pixel is a hole when solid
    material lies in all four directions of it.
    """
    solid = [(x, y) for y, row in enumerate(layer.px) for x, k in enumerate(row) if k]
    if not solid:
        return
    x0, x1 = min(x for x, _ in solid), max(x for x, _ in solid)
    y0, y1 = min(y for _, y in solid), max(y for _, y in solid)
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            if layer.get(xx, yy):
                continue
            around = []
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                x, y = xx + dx, yy + dy
                while x0 <= x <= x1 and y0 <= y <= y1 and not layer.get(x, y):
                    x, y = x + dx, y + dy
                around.append(layer.get(x, y))
            if all(around):
                layer.set(xx, yy, around[2])


def composite(c, layer):
    """Outline the union of a layer: joined parts get material seams, not gaps."""
    fill_holes(layer)
    for yy, row in enumerate(layer.px):
        for xx, key in enumerate(row):
            if key is None:
                continue
            edge = any(layer.get(xx + dx, yy + dy) is None
                       for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            c.set(xx, yy, "outline" if edge else key)


# -------------------------------------------------------------------- desk


def desk_plan(canvas_h, fy, dy, lip):
    """The narrow tabletop's horizontal structure, row by row, for the page.

    Only the narrow framing uses this. Its tabletop runs off both sides of the
    canvas, and unless the page continues these rows out to the viewport edges
    the desk ends in mid-air with wall showing past either end. The wide
    framing draws a finite desk and reports None, and the page paints no band.
    """
    by = fy - dy
    rows = [
        [1, "outline"],                 # the back edge
        [fy - by - 1, "desk_top"],      # the tabletop itself
        [1, "outline"],                 # the front edge
        [1, "desk_edge"],               # catch-light along it
        [lip - 3, "desk_front"],        # the front thickness
        [1, "outline"],                 # the underside
    ]
    assert sum(n for n, _ in rows) == fy + lip - by
    return {"fromBottom": canvas_h - (fy + lip), "rows": rows}


def draw_desk(c, p, x0, x1, d, t, leg, legs):
    """A plain rectangular table: top, front thickness, left end, square legs.

    The back legs go down first and the top over them, so they hang from the
    underside; from this viewpoint they show below the thin end face on the
    left and just inside the front legs on the right, which is the overlap a
    real table has. All four run off the bottom of the frame, where the page
    bottom-aligns the artwork.
    """
    o = "outline"

    def post(x, z):
        draw_box(c, p, x, x + leg - 1, -t - 400, -t, z, z + leg, top=None,
                 front="desk_front", side="desk_side", edge=False)
        ax, ay = p(x, -t, z)
        c.vline(ax + 1, ay + 1, c.h, "desk_edge")

    # Every leg goes down first. Each stands a little behind the edge it hangs
    # from, so its top projects a few rows above that edge's underside; the
    # top, the end face and the front thickness are drawn over them and hide
    # exactly those rows, which is what attaches the legs to the underside.
    for x, z, back in legs:
        post(x, z)
    top = [p(x0, 0, 0), p(x1, 0, 0), p(x1, 0, d), p(x0, 0, d)]
    end = [p(x0, 0, 0), p(x0, 0, d), p(x0, -t + 1, d), p(x0, -t + 1, 0)]
    c.poly(top, "desk_top")
    c.poly(end, "desk_side")
    ax, ay, bx, by = face_rect(c, p, x0, x1, -t + 1, 0, 0, "desk_front")
    c.hline(ax + 1, bx - 1, ay + 1, "desk_edge")
    c.outline_poly(top, o)
    c.outline_poly(end, o)
    c.frame(ax, ay, bx - ax + 1, by - ay + 1, o)


def desk_legs(x0, x1, d, leg, inset):
    return [(x0 + inset, d - inset - leg, True), (x1 - inset - leg + 1, d - inset - leg, True),
            (x0 + inset, inset, False), (x1 - inset - leg + 1, inset, False)]


# ------------------------------------------------------------------ monitor


def draw_stand(c, p, plate, housing, chin_row):
    """The tilt/swivel support, built in the order the monitor is assembled.

    Under the casing there is a mounting area (its underside, in shadow); a
    short tilt/swivel HOUSING - a truncated cone - is seated into it; and the
    housing stands in a shaded socket on a broad, low PLATE with rounded
    corners that rests on the desk. The housing sits behind the casing's front
    face, under its depth, so from this viewpoint the chin hides its top rows
    and the joint is the dark band that emerges beneath the bezel. One layer,
    one outline: no silhouette is separated from another by air.
    """
    layer = c.__class__(c.w, c.h, c.palette)
    x, w, z0, d, h, r = (plate[k] for k in ("x", "w", "z", "d", "h", "r"))

    def inset(dist):
        return r - math.sqrt(r * r - (r - dist) ** 2) if dist < r else 0

    for z in frange(z0, z0 + d):
        ins = inset(min(z - z0, z0 + d - z))
        a, b = p(x + ins, h, z), p(x + w - ins, h, z)
        layer.hline(a[0], b[0], a[1], "case_top")
    for xx in frange(x, x + w):
        zf = z0 + inset(min(xx - x, x + w - xx))
        for y in frange(0, h):
            layer.set(*p(xx, y, zf), "case_front")
    a, b = p(x + r, h, z0), p(x + w - r, h, z0)
    layer.hline(a[0] + 1, b[0] - 1, a[1], "case_edge")

    cx, cz, r0, r1, y0, y1 = (housing[k] for k in ("cx", "cz", "r0", "r1", "y0", "y1"))
    # The socket shows only as the shadow crescent in front of the foot. A ring
    # that continued round the sides read as a bowl sunk into the plate.
    for z in frange(cz - r0 - 1.5, cz - 4):
        half = math.sqrt(max(0.0, (r0 + 1.5) ** 2 - (z - cz) ** 2))
        a, b = p(cx - half, h, z), p(cx + half, h, z)
        layer.hline(a[0], b[0], a[1], "case_deep")
    for y in frange(y0, y1):
        t = (y - y0) / (y1 - y0)
        rad = r0 + (r1 - r0) * t
        for deg in range(-90, 91, 2):
            th = math.radians(deg)
            key = "case_front"
            if deg < -62 or deg > 68:
                key = "case_side"
            px, py = p(cx + rad * math.sin(th), y, cz - rad * math.cos(th))
            if py <= chin_row + 2:
                key = "case_deep"           # the joint: the rows in the chin's shadow
            layer.set(px, py, key)
    composite(c, layer)


def draw_monitor(c, p, m, stand):
    """Support, then the tube housing, then the bezel block with the glass."""
    x, w, y, h, z, bd = (m[k] for k in ("x", "w", "y", "h", "z", "bezel_d"))
    r = m["rear"]
    draw_stand(c, p, chin_row=p(x, y, z)[1], **stand)
    x1, y1 = x + w - 1, y + h - 1

    # The tube housing: narrower and lower than the bezel block, and it
    # TAPERS toward the back, as a CRT's does around the tube's neck. Its
    # front section is inset from the bezel block; its back section is inset
    # further, so the top and the side are trapezoids rather than a box.
    o = "outline"
    tp = r.get("taper", {})
    rx0, rx1 = x + r["inset"], x1 - r["inset"]
    ry0, ry1 = y + r["bottom"], y1 - r["top"]
    rz0, rz1 = z + bd, z + bd + r["d"]
    bx0, bx1 = rx0 + tp.get("x", 0), rx1 - tp.get("x", 0)
    by0, by1 = ry0 + tp.get("bottom", 0), ry1 - tp.get("top", 0)
    side = [p(rx0, ry0, rz0), p(rx0, ry1, rz0), p(bx0, by1, rz1), p(bx0, by0, rz1)]
    top = [p(rx0, ry1, rz0), p(rx1, ry1, rz0), p(bx1, by1, rz1), p(bx0, by1, rz1)]
    c.poly(side, "case_side")
    c.poly(top, "case_top")
    c.outline_poly(side, o)
    c.outline_poly(top, o)
    for k in range(4):                       # vents across the housing's top
        zz = rz1 - 12 - k * 8
        t = (zz - rz0) / (rz1 - rz0)
        xa, xb = rx0 + 16 + (bx0 - rx0) * t, rx1 - 16 - (rx1 - bx1) * t
        yy = ry1 + (by1 - ry1) * t
        a, b = p(xa, yy, zz), p(xb, yy, zz)
        c.hline(a[0], b[0], a[1], "case_deep")

    # The bezel block, whose front face is the true rectangle the glass sits in.
    S, T, F = draw_box(c, p, x, x1, y, y1, z, z + bd)
    ax, ay, bx, by = F
    c.vline(ax + 3, ay + 3, by - 3, "case_deep")
    for k in range(4):                       # side vents, along the depth
        yy = y + 30 + k * 9
        a, b = p(x, yy, z + 5), p(x, yy, z + bd - 5)
        c.line(a[0], a[1], b[0], b[1], "case_deep")

    s = m["screen"]
    sx, sy = p(x + s["x"], y + s["y"] + s["h"] - 1, z)
    sw, sh = s["w"], s["h"]
    c.rect(sx - 2, sy - 2, sw + 4, sh + 4, "case_deep")
    c.rect(sx, sy, sw, sh, "glass")
    c.rect(sx + 6, sy + 5, sw - 12, sh - 10, "glass_lit")
    c.dither(sx + 3, sy + 3, sw - 6, 3, "glass_lit", density=6)
    c.dither(sx + 3, sy + sh - 6, sw - 6, 3, "glass_lit", density=6)
    c.frame(sx - 1, sy - 1, sw + 2, sh + 2, "outline")

    chin = sy + sh + 6                       # controls under the glass
    c.frame(ax + 7, chin, 8, 8, "outline")
    c.rect(ax + 8, chin + 1, 6, 6, "case_top")
    c.rect(ax + 10, chin + 2, 2, 4, "case_deep")
    c.rect(ax + 20, chin + 3, 3, 3, "led")
    for k in range(4):
        c.rect(ax + 48 + k * 9, chin + 3, 6, 3, "case_deep")
    # The mounting area: the casing's underside is in shadow where the
    # support is received, right above the joint that emerges beneath it.
    c.hline(ax + 2, bx - 2, by - 1, "case_deep")
    return {"x": sx, "y": sy, "w": sw, "h": sh}


# -------------------------------------------------------------------- tower


def draw_tower(c, p, t):
    """An upright case: optical bay, floppy slot, vents, power button, LED."""
    o = "outline"
    x, w, h, z, d = (t[k] for k in ("x", "w", "h", "z", "d"))
    S, T, F = draw_box(c, p, x, x + w - 1, 0, h - 1, z, z + d)
    fx, fy, bx, by = F
    fw, fh = bx - fx + 1, by - fy + 1
    for k in range(4):                       # side vents, along the depth
        yy = 30 + k * 9
        a, b = p(x, yy, z + 6), p(x, yy, z + d - 8)
        c.line(a[0], a[1], b[0], b[1], "case_deep")

    c.rect(fx + 5, fy + 7, fw - 10, 7, "case_deep")       # optical drive
    c.rect(fx + 6, fy + 9, fw - 18, 2, "case_top")
    c.rect(fx + fw - 10, fy + 10, 3, 2, "case_edge")
    c.rect(fx + 5, fy + 17, fw - 10, 5, "case_deep")      # floppy slot
    c.rect(fx + 6, fy + 19, fw - 19, 2, "case_top")
    for k in range(4):                                     # vents
        c.rect(fx + 6, fy + 26 + k * 5, fw - 12, 2, "case_deep")
    c.frame(fx + 6, fy + fh - 16, 9, 9, o)                 # power button
    c.rect(fx + 7, fy + fh - 15, 7, 7, "case_top")
    c.rect(fx + 9, fy + fh - 13, 3, 3, "case_deep")
    c.rect(fx + fw - 6, fy + fh - 12, 3, 3, "led")         # indicator
    c.hline(fx + 2, bx - 2, by - 1, "case_deep")           # feet, in shadow


# ----------------------------------------------------------------- keyboard
# A full-size ANSI layout in key units, nearest row first. Each key is
# (u, width, kind): 'k' a plain cap, 'm' a modifier or cluster key, 't' a
# tall numpad key that spans this row and the one behind it. Row 5 is the
# function row, set half a unit further back. The main block is 15u; the
# navigation cluster starts at 15.5u; the numeric keypad at 19u; 23u in all.

ANSI_ROWS = [
    # bottom: Ctrl Win Alt Space Alt Win Menu Ctrl | Left Down Right | 0 . Enter
    [(0, 1.25, "m"), (1.25, 1.25, "m"), (2.5, 1.25, "m"), (3.75, 6.25, "m"),
     (10, 1.25, "m"), (11.25, 1.25, "m"), (12.5, 1.25, "m"), (13.75, 1.25, "m"),
     (15.5, 1, "m"), (16.5, 1, "m"), (17.5, 1, "m"),
     (19, 2, "m"), (21, 1, "k"), (22, 1, "t")],
    # Shift row | Up | 1 2 3
    [(0, 2.25, "m")] + [(2.25 + i, 1, "k") for i in range(10)] + [(12.25, 2.75, "m"),
     (16.5, 1, "m"),
     (19, 1, "k"), (20, 1, "k"), (21, 1, "k")],
    # Caps row, Enter | 4 5 6 +
    [(0, 1.75, "m")] + [(1.75 + i, 1, "k") for i in range(11)] + [(12.75, 2.25, "m"),
     (19, 1, "k"), (20, 1, "k"), (21, 1, "k"), (22, 1, "t")],
    # Tab row, backslash | Del End PgDn | 7 8 9
    [(0, 1.5, "m")] + [(1.5 + i, 1, "k") for i in range(12)] + [(13.5, 1.5, "m"),
     (15.5, 1, "m"), (16.5, 1, "m"), (17.5, 1, "m"),
     (19, 1, "k"), (20, 1, "k"), (21, 1, "k")],
    # number row, Backspace | Ins Home PgUp | NumLk / * -
    [(i, 1, "k") for i in range(13)] + [(13, 2, "m"),
     (15.5, 1, "m"), (16.5, 1, "m"), (17.5, 1, "m"),
     (19, 1, "m"), (20, 1, "m"), (21, 1, "m"), (22, 1, "m")],
    # function row: Esc, F1-F4, F5-F8, F9-F12 | PrtSc ScrLk Pause
    [(0, 1, "m"), (2, 1, "m"), (3, 1, "m"), (4, 1, "m"), (5, 1, "m"),
     (6.5, 1, "m"), (7.5, 1, "m"), (8.5, 1, "m"), (9.5, 1, "m"),
     (11, 1, "m"), (12, 1, "m"), (13, 1, "m"), (14, 1, "m"),
     (15.5, 1, "m"), (16.5, 1, "m"), (17.5, 1, "m")],
]
F_ROW_GAP = 4          # half a key unit, in depth units


def draw_keyboard(c, p, kb):
    """The housing as a shallow wedge, then the layout projected onto its deck.

    The layout lives in key units (ANSI_ROWS) and is placed on the deck with
    one x unit and one z unit; the projection does the rest, so every row gets
    the same slope and spacing. Each cap is a lit top three rows deep, stepped
    on the projection's own line, over a one-row front, in a dark well with a
    one-unit gap around it. Nothing is lettered: at this size the shapes and
    the grouping are what read.
    """
    o = "outline"
    x, w, z0, d, hf, hb, ux, uz, full = (kb[k] for k in ("x", "w", "z", "d", "hf", "hb", "ux", "uz", "full"))
    x1, z1 = x + w - 1, z0 + d

    def deck_y(z):
        return hf + (z - z0) * (hb - hf) / d

    side = [p(x, 0, z0), p(x, hf, z0), p(x, hb, z1), p(x, 0, z1)]
    deck = [p(x, hf, z0), p(x1, hf, z0), p(x1, hb, z1), p(x, hb, z1)]
    c.poly(side, "case_side")
    c.poly(deck, "case_top")
    ax, ay, bx, by = face_rect(c, p, x, x1, 0, hf, z0, "case_front")
    c.hline(ax + 1, bx - 1, ay + 1, "case_edge")

    rows = ANSI_ROWS if full else ANSI_ROWS[:5]
    kx0, kz0 = x + (w - 23 * ux) // 2 if full else x + (w - 15 * ux) // 2, z0 + 6
    clusters = ((0, 15), (15.5, 18.5), (19, 23)) if full else ((0, 15),)

    def row_z(r):
        return kz0 + r * uz + (F_ROW_GAP if r == 5 else 0)

    z_far = row_z(len(rows) - 1) + uz - 1
    for u0, u1 in clusters:
        c.poly([p(kx0 + u0 * ux - 1, deck_y(kz0 - 2), kz0 - 2),
                p(kx0 + u1 * ux, deck_y(kz0 - 2), kz0 - 2),
                p(kx0 + u1 * ux, deck_y(z_far), z_far),
                p(kx0 + u0 * ux - 1, deck_y(z_far), z_far)], "case_deep")

    def key(u, width, r, kind):
        z = row_z(r)
        depth = (2 * uz if kind == "t" else uz) - 2
        top_rows = 3 + (5 if kind == "t" else 0)
        kx = kx0 + u * ux
        kw = round(width * ux) - 1
        near = round(p.y0 - (deck_y(z) + 1.5) - z / 2)
        tone = "case_front" if kind == "m" else "key_top"
        for k in range(top_rows):
            zk = z + depth * k / max(1, top_rows - 1)
            a = round(p.x0 + kx - zk / 6)
            c.hline(a, a + kw - 1, near - k, tone)
        a = round(p.x0 + kx - z / 6)
        c.hline(a, a + kw - 1, near + 1, "key_side")

    for r in reversed(range(len(rows))):
        for u, width, kind in rows[r]:
            if full or u + width <= 15:
                key(u, width, r, kind)
    c.outline_poly(deck, o)
    c.outline_poly(side, o)
    c.frame(ax, ay, bx - ax + 1, by - ay + 1, o)


# -------------------------------------------------------------------- mouse
# A wired mouse used the way a person facing the monitor uses it: buttons and
# cable at the FAR end, the rounded palm nearest us. Its shell is a height
# field over a pebble-shaped footprint: a longitudinal profile that rises
# quickly from the rear to the palm and falls to a low nose, times a rounded
# cross-section, with near-vertical walls up to about half the height.

#
# The buttons slope only gently toward the nose. From this elevation a steep
# front would be seen almost edge-on and the seam, division and wheel would
# collapse into two rows; a front that stays high, as on a traditional
# two-button mouse, keeps the two button surfaces readable.
MOUSE_PROFILE = [(0.0, 0.35), (0.05, 0.65), (0.15, 0.92), (0.26, 1.0), (0.4, 0.97),
                 (0.54, 0.91), (0.7, 0.86), (0.84, 0.8), (0.94, 0.74), (1.0, 0.6)]
MOUSE_SEAM = 0.52      # where the palm ends and the two buttons begin
MOUSE_WHEEL = (0.76, 0.92)


def curve(pts, u):
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        if u0 <= u <= u1:
            t = (u - u0) / (u1 - u0)
            t = t * t * (3 - 2 * t)
            return v0 + (v1 - v0) * t
    return pts[-1][1]


def mouse_shape(m):
    x, w, z0, length, hmax = (m[k] for k in ("x", "w", "z", "length", "hmax"))
    cx = x + (w - 1) / 2

    def half(t):                       # footprint half-width: rounded both ends
        return (w - 1) / 2 * (0.62 + 0.38 * math.sin(math.pi * t) ** 0.6)

    def height(t, u):                  # u across the width, -1..1
        base = hmax * curve(MOUSE_PROFILE, t)
        return base * (0.5 + 0.5 * math.sqrt(max(0.0, 1 - u * u)))

    return cx, half, height


def mouse_contact(c, p, m):
    cx, half, _ = mouse_shape(m)
    z0 = m["z"]
    contact(c, p, cx - half(0), cx + half(0), z0)
    cast(c, p, cx + half(0.5), z0 + 4, z0 + m["length"] - 6, width=6)


def draw_mouse(c, p, m):
    """Rear to nose, far to near, one continuous shell.

    Each cross-section is drawn from far to near so nearer material covers
    farther: the left wall, then the top across the width. The rear wall
    facing us closes the shell. Then the details on the top: the seam
    between palm and buttons, the division between the buttons running to
    the nose, and the wheel set into that division near the nose.
    """
    layer = c.__class__(c.w, c.h, c.palette)
    cx, half, height = mouse_shape(m)
    z0, length, w = m["z"], m["length"], m["w"]
    for z in frange(z0 + length, z0, -0.5):
        t = (z - z0) / length
        hw = half(t)
        wall = height(t, 0) * 0.5
        for y in frange(0, wall):
            layer.set(*p(cx - hw, y, z), "case_side")
        for x in frange(cx - hw, cx + hw):
            u = (x - cx) / hw if hw else 0
            key = "case_top"
            if u < -0.78:
                key = "case_side"
            elif u > 0.84:
                key = "case_front"
            layer.set(*p(x, height(t, u), z), key)
    hw = half(0)
    for x in frange(cx - hw, cx + hw):
        u = (x - cx) / hw
        for y in frange(0, height(0, u)):
            layer.set(*p(x, y, z0), "case_front")
    # the seam between palm and buttons, across the shell
    zs = z0 + MOUSE_SEAM * length
    hw = half(MOUSE_SEAM)
    for x in frange(cx - hw + 1, cx + hw - 1):
        u = (x - cx) / hw
        layer.set(*p(x, height(MOUSE_SEAM, u) + 0.3, zs), "case_deep")
    # the division between the two buttons, to the nose
    for z in frange(zs, z0 + length - 1.5):
        t = (z - z0) / length
        layer.set(*p(cx, height(t, 0) + 0.3, z), "case_deep")
    # the wheel, set into the division
    ww = max(3, round(w * 0.16))
    for z in frange(z0 + MOUSE_WHEEL[0] * length, z0 + MOUSE_WHEEL[1] * length):
        t = (z - z0) / length
        for x in frange(cx - ww / 2, cx + ww / 2):
            layer.set(*p(x, height(t, (x - cx) / half(t)) + 0.3, z), "case_deep")
    wz = z0 + MOUSE_WHEEL[0] * length
    layer.set(*p(cx - ww / 2 + 0.5, height(MOUSE_WHEEL[0], 0) + 0.3, wz), "case_edge")
    composite(c, layer)


# ------------------------------------------------------------------- cables


def draw_cable(c, p, pts, steps=240):
    """A quadratic curve through three desk-space points, sampled onto the grid.

    One outline pixel with a dark one under it. Cables are drawn before the
    equipment, so each starts hidden under its own object and ends inside the
    tower: nothing terminates in open tabletop.
    """
    (ax, ay), (bx, by), (cx, cy) = (p(*q) for q in pts)
    prev = None
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * ax + 2 * (1 - t) * t * bx + t * t * cx
        y = (1 - t) ** 2 * ay + 2 * (1 - t) * t * by + t * t * cy
        pt = (round(x), round(y))
        if pt != prev:
            c.set(pt[0], pt[1], "outline")
            c.set(pt[0], pt[1] + 1, "desk_side")
        prev = pt


# --------------------------------------------------------------- the scenes


def draw_layout(c, L):
    p = View(*L["origin"])
    D, M, T, K, MO = L["desk"], L["monitor"], L["tower"], L["keyboard"], L["mouse"]
    legs = D.get("legs") or desk_legs(D["x0"], D["x1"], D["d"], D["leg"], D["inset"])
    draw_desk(c, p, D["x0"], D["x1"], D["d"], D["t"], D["leg"], legs)

    plate = L["stand"]["plate"]
    cast(c, p, plate["x"] + plate["w"], plate["z"], plate["z"] + plate["d"] - 20)
    cast(c, p, T["x"] + T["w"] - 1, T["z"], T["z"] + T["d"] - 30)
    cast(c, p, K["x"] + K["w"] - 1, K["z"], K["z"] + K["d"] - 8, width=6)
    contact(c, p, plate["x"] + plate["r"], plate["x"] + plate["w"] - plate["r"], plate["z"])
    contact(c, p, T["x"], T["x"] + T["w"] - 1, T["z"])
    contact(c, p, K["x"], K["x"] + K["w"] - 1, K["z"])
    mouse_contact(c, p, MO)

    for pts in L["cables"].values():
        draw_cable(c, p, pts)

    draw_tower(c, p, T)
    screen = draw_monitor(c, p, M, L["stand"])
    draw_keyboard(c, p, K)
    draw_mouse(c, p, MO)
    return p, screen


# --- wide framing -----------------------------------------------------------
# 576 x 330. At 2x it displays as 1152 x 660, which still fits a 1280 x 720
# window; at 3x it fits 1920 x 1080. Desk space: the tabletop's front-left
# corner is at canvas (48, 292).

W, H = 576, 330

WIDE = dict(
    origin=(48, 292),
    desk=dict(x0=0, x1=521, d=250, t=12, leg=14, inset=12),
    # The tube housing is 84 deep (it was 108) and tapers 12 a side and 6 on
    # top toward the back; the tower is 114 deep (it was 138). Both were read
    # as elongated from this elevation, which shows their tops in full.
    monitor=dict(x=142, w=132, y=28, h=118, z=102, bezel_d=30,
                 rear=dict(inset=10, top=10, bottom=10, d=84, taper=dict(x=12, top=6, bottom=2)),
                 screen=dict(x=12, y=26, w=108, h=81)),
    stand=dict(plate=dict(x=164, w=88, z=108, d=96, h=5, r=10),
               housing=dict(cx=208, cz=132, r0=16, r1=12, y0=5, y1=28)),
    tower=dict(x=324, w=66, h=140, z=108, d=114),
    keyboard=dict(x=194, w=198, z=6, d=64, hf=6, hb=14, ux=8, uz=8, full=True),
    mouse=dict(x=424, w=27, z=14, length=50, hmax=16),
    cables=dict(monitor=[(274, 0, 200), (304, 0, 190), (324, 0, 170)],
                keyboard=[(364, 0, 74), (354, 0, 96), (342, 4, 108)],
                mouse=[(437, 2, 58), (448, 0, 100), (354, 4, 108)]),
)


def draw_scene(c):
    """Wide framing: a freestanding desk, monitor left, tower right, keyboard and wired mouse."""
    p, screen = draw_layout(c, WIDE)
    return {"screen": screen, "canvas": {"w": W, "h": H}, "desk": None}


# --- narrow framing ---------------------------------------------------------
# 180 x 252, the same projection at a smaller equipment scale. It displays at
# 360 x 504 (2x) on 360–430px phones. The desk runs off both sides here - a
# phone cannot hold a desk with ends and a readable monitor at once - and the
# page continues its rows to the viewport edges from desk_plan().

CW, CH = 180, 252

COMPACT = dict(
    origin=(8, 223),
    desk=dict(x0=-60, x1=240, d=176, t=9, leg=12, legs=[(6, 10, False), (148, 10, False)]),
    monitor=dict(x=12, w=120, y=21, h=109, z=84, bezel_d=24,
                 rear=dict(inset=8, top=8, bottom=8, d=48, taper=dict(x=8, top=4, bottom=1)),
                 screen=dict(x=12, y=23, w=96, h=72)),
    stand=dict(plate=dict(x=32, w=80, z=90, d=60, h=4, r=8),
               housing=dict(cx=72, cz=108, r0=13, r1=10, y0=4, y1=21)),
    tower=dict(x=140, w=34, h=80, z=90, d=70),
    keyboard=dict(x=22, w=96, z=6, d=50, hf=5, hb=11, ux=6, uz=8, full=False),
    mouse=dict(x=134, w=18, z=12, length=34, hmax=11),
    cables=dict(monitor=[(124, 0, 140), (137, 0, 130), (142, 0, 120)],
                keyboard=[(90, 0, 60), (110, 0, 76), (150, 4, 90)],
                mouse=[(143, 2, 40), (152, 0, 70), (152, 4, 90)]),
)


def draw_scene_compact(c):
    p, screen = draw_layout(c, COMPACT)
    D = COMPACT["desk"]
    return {"screen": screen, "canvas": {"w": CW, "h": CH},
            "desk": desk_plan(CH, p.y0, D["d"] // 2, D["t"])}
