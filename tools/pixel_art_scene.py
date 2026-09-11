# ============================================================================
# The desk scene.
#
# One oblique projection for everything: depth runs back and to the LEFT on a
# 2:1 step. That is what turns the monitor to face slightly right - you see its
# left casing - and it is the same diagonal the desk, tower, keyboard and mouse
# all recede along, so the group reads as one surface rather than a pile of
# separately-drawn objects.
#
# Volume comes from deliberate planes, never from shading a single tone. Every
# object that has depth is built the same way: a LIT TOP (case_top), a FRONT
# turned toward us (case_front), a LEFT SIDE turned away (case_side), a bright
# edge where two planes meet toward the light (case_edge), and a dark recess or
# underside (case_deep). The light is up and to the left, and it stays there.
#
# Objects are placed by their CONTACT POINT: the y where their base meets the
# tabletop. The tabletop runs from the back edge to the front edge, so every
# base y below is a position within that span and nothing floats:
#
#     100  back edge of the tabletop
#     108  tower stands here      (furthest back)
#     114  monitor base stands here
#     118  back edge of the keyboard
#     134  front edge of the keyboard; 138 the mouse
#     142  front edge of the tabletop, then 10px of thickness, then the legs
#
# The desk runs off both sides of the frame. A visible end would have to be a
# parallelogram as wide as the depth step, and at this scale that reads as a
# ramp rather than as furniture; two legs under a surface that continues past
# the frame reads as a desk immediately.
#
# The legs run off the BOTTOM edge too - DESK_FOOT is past the canvas, so their
# outlines are clipped rather than closed. The page bottom-aligns the artwork,
# so they leave the frame the way the tabletop leaves it at the sides, and the
# scene needs no drawn floor and no CSS band pretending to be one.
# ============================================================================

# --- wide framing -----------------------------------------------------------
W, H = 340, 180

DESK_FY, DESK_DX, DESK_DY = 142, 84, 42        # front edge, and the 2:1 step back
DESK_FX0, DESK_FX1 = -60, 420                  # past both edges of the frame
DESK_LIP = 10                                  # front thickness of the tabletop
DESK_FOOT = H + 4                              # past the bottom edge: see below
DESK_LEGS = (40, 282)

MON_X, MON_Y, MON_W, MON_H = 58, 14, 88, 76
MON_DX, MON_DY = 22, 11
SCREEN_X, SCREEN_Y, SCREEN_W, SCREEN_H = 66, 21, 72, 54
MON_BASE_Y = 114

# The tower moved 30px left: the gap between the monitor's front-right edge and
# the tower's rearmost corner went from 57px to 25px. They read as one setup now
# rather than two objects at opposite ends of the desk, and no silhouette
# overlaps another.
TOW_X, TOW_Y, TOW_W, TOW_H = 186, 32, 40, 76
TOW_DX, TOW_DY = 15, 8

KB_X0, KB_X1, KB_Y = 126, 258, 134
KB_DX, KB_DY = 32, 16
MOUSE_X, MOUSE_Y, MOUSE_W, MOUSE_D = 276, 133, 26, 6

# Each cable starts UNDER its own object and ends inside the tower, so it
# emerges from behind the one and vanishes behind the other. Nothing is left
# hanging in open tabletop, and none crosses a base, a deck or the case.
MON_CABLE = [((112, 112), (148, 110), (178, 102))]
KB_CABLE = [((150, 128), (176, 118), (196, 104))]
MOUSE_CABLE = [((280, 131), (256, 122), (224, 106))]


def contact(c, x0, x1, y):
    """The tight occlusion shadow where an object meets the tabletop.

    `y` is the object's OWN contact row - the row immediately after its last
    drawn pixel. The previous version started a row lower, which left a strip of
    bare tabletop between every object and its shadow and made the whole group
    look like it was hovering.
    """
    c.hline(x0, x1, y, "desk_side")
    c.hline(x0 + 2, x1 - 2, y + 1, "desk_side")


def cast(c, x0, x1, y, rows, step=2):
    """The longer shadow an object throws, stepping down and to the RIGHT.

    Distinct from the contact shadow in both value and direction: the light is
    up and to the left, so everything on this desk throws the same way.
    """
    for i in range(rows):
        c.hline(x0 + (i + 1) * step, x1 + (i + 1) * step, y + i, "desk_cast")


def desk_plan(canvas_h, fy, dy, lip):
    """The tabletop's horizontal structure, row by row, for the page to extend.

    The artwork is centred and is narrower than the window, so unless the page
    continues these rows out to both edges the desk ends in mid-air with wall
    showing past either end. Reporting the plan from here is what keeps that
    extension in step with what is drawn: no row count is ever copied by hand.
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


def draw_desk(c, fx0, fx1, fy, dx, dy, lip, foot, legs, leg_w=14):
    """Tabletop, its front thickness, and the legs holding it up."""
    o = "outline"
    bx0, bx1, by = fx0 - dx, fx1 - dx, fy - dy

    top = [(fx0, fy), (fx1, fy), (bx1, by), (bx0, by)]
    c.poly(top, "desk_top")
    c.hline(0, c.w, by, o)

    # legs first: they belong behind the front edge they hang from
    for lx in legs:
        c.rect(lx, fy, leg_w, foot - fy, "desk_side")
        c.vline(lx + 1, fy + lip, foot - 1, "desk_front")
        c.frame(lx, fy + lip - 1, leg_w, foot - fy - lip + 1, o)

    c.rect(fx0, fy, fx1 - fx0, lip, "desk_front")
    c.hline(0, c.w, fy + 1, "desk_edge")        # catch-light along the front edge
    c.hline(0, c.w, fy, o)
    c.hline(0, c.w, fy + lip - 1, o)


def draw_stand(c, cx, top_y, base_y, collar=20, foot=26, collar_h=8, dx=8, dy=4):
    """The monitor's support, drawn as ONE assembly rather than stacked slabs.

    Real CRT pedestals are built this way: a rocker fixed to the flat underside
    of the casing, seated into a recess in a broad pedestal whose top is a flat
    ring (US4575033A). There is no thin post anywhere in it, and often no
    visible neck at all - the casing sits almost straight onto the pedestal.

    Two things were wrong before. Each piece was outlined on all four sides, and
    an outline between two parts that are joined is a SEAM - which is exactly
    what the eye uses to separate them, so it read as thin slabs balanced on
    each other. And there were three stacked widths, which put two steps in the
    left profile and made it jagged. Now the silhouette is one stepped polygon
    with a single step, the outline runs only around the OUTSIDE, and every
    internal junction is an overlap with a shadow under it.
    """
    o = "outline"
    y1 = top_y + collar_h          # the collar sinks into the pedestal's ring

    # 1. the pedestal's top ring, laid down first so the collar seats into it
    ring = [(cx - foot, y1), (cx + foot, y1),
            (cx + foot - dx, y1 - dy), (cx - foot - dx, y1 - dy)]
    c.poly(ring, "case_top")
    c.outline_poly(ring, o)

    # 2. one stepped silhouette for the whole assembly, and one side plane
    front = [
        (cx - collar, top_y), (cx + collar, top_y), (cx + collar, y1),
        (cx + foot, y1), (cx + foot, base_y), (cx - foot, base_y),
        (cx - foot, y1), (cx - collar, y1),
    ]
    edge = [(cx - collar, top_y), (cx - collar, y1),
            (cx - foot, y1), (cx - foot, base_y)]
    side = edge + [(x - dx, y - dy) for x, y in reversed(edge)]
    c.poly(side, "case_side")
    c.poly(front, "case_front")

    # 3. the joins: shadow where one part meets the next, never an outline
    c.hline(cx - collar + 1, cx + collar - 1, top_y, "case_deep")     # under the casing
    c.hline(cx - collar + 2, cx + collar - 2, top_y + 1, "case_deep")
    c.hline(cx - collar - 3, cx + collar + 3, y1 - 1, "case_deep")    # into the ring

    # 4. the light is up and to the left, so the left of every plane catches it
    c.vline(cx - collar + 1, top_y + 2, y1 - 2, "case_edge")
    c.vline(cx - foot + 1, y1 + 2, base_y - 3, "case_edge")
    c.hline(cx - foot + 1, cx + foot - 2, y1 + 1, "case_edge")        # the pedestal rim
    c.vline(cx + collar - 2, top_y + 2, y1 - 2, "case_deep")
    c.vline(cx + foot - 2, y1 + 2, base_y - 3, "case_deep")
    c.hline(cx - foot + 2, cx + foot - 2, base_y - 2, "case_deep")    # the underside

    c.outline_poly(side, o)
    c.outline_poly(front, o)
    return cx - foot - dx, cx + foot


def draw_monitor(c, fx, fy, fw, fh, dx, dy, sx, sy, sw, sh, base_y, stand=None):
    """Front moulding, left side, top, tube, chin controls, stand and base."""
    o = "outline"
    # The stand goes down FIRST: its collar reaches a few rows up behind the
    # casing's bottom edge, and drawing it afterwards left that corner poking
    # through the front face as a detached notch.
    foot = draw_stand(c, fx + fw // 2, fy + fh, base_y, **(stand or {}))

    side = [(fx, fy), (fx - dx, fy - dy), (fx - dx, fy + fh - dy), (fx, fy + fh)]
    c.poly(side, "case_side")
    for i in range(4):
        vy = fy + 22 + i * 8
        c.line(fx - 6, vy, fx - dx + 5, vy - (dy - 6), "case_deep")

    top = [(fx, fy), (fx + fw, fy), (fx + fw - dx, fy - dy), (fx - dx, fy - dy)]
    c.poly(top, "case_top")

    c.rect(fx, fy, fw, fh, "case_front")
    c.hline(fx + 1, fx + fw - 2, fy + 1, "case_edge")
    c.vline(fx + 1, fy + 1, fy + fh - 2, "case_edge")
    c.vline(fx + 3, fy + 3, fy + fh - 3, "case_deep")

    c.rect(sx - 2, sy - 2, sw + 4, sh + 4, "case_deep")
    c.rect(sx, sy, sw, sh, "glass")
    c.rect(sx + 6, sy + 5, sw - 12, sh - 10, "glass_lit")
    c.dither(sx + 3, sy + 3, sw - 6, 3, "glass_lit", density=6)
    c.dither(sx + 3, sy + sh - 6, sw - 6, 3, "glass_lit", density=6)
    c.frame(sx - 1, sy - 1, sw + 2, sh + 2, o)

    chin = sy + sh + 6
    c.frame(fx + 7, chin, 8, 8, o)
    c.rect(fx + 8, chin + 1, 6, 6, "case_top")
    c.rect(fx + 10, chin + 2, 2, 4, "case_deep")
    c.rect(fx + 20, chin + 3, 3, 3, "led")
    for i in range(4):
        c.rect(fx + 48 + i * 9, chin + 3, 6, 3, "case_deep")

    c.outline_poly(top, o)
    c.outline_poly(side, o)
    c.frame(fx, fy, fw, fh, o)
    return foot


def draw_tower(c, fx, fy, fw, fh, dx, dy):
    """An upright case: optical bay, floppy slot, power button, LED, vents, feet."""
    o = "outline"
    side = [(fx, fy), (fx - dx, fy - dy), (fx - dx, fy + fh - dy), (fx, fy + fh)]
    c.poly(side, "case_side")
    for i in range(4):
        vy = fy + 30 + i * 7
        c.line(fx - 4, vy, fx - dx + 4, vy - (dy - 5), "case_deep")

    top = [(fx, fy), (fx + fw, fy), (fx + fw - dx, fy - dy), (fx - dx, fy - dy)]
    c.poly(top, "case_top")

    c.rect(fx, fy, fw, fh, "case_front")
    c.hline(fx + 1, fx + fw - 2, fy + 1, "case_edge")
    c.vline(fx + 1, fy + 1, fy + fh - 2, "case_edge")

    # optical drive with a tray line and an eject button, floppy slot beneath
    c.rect(fx + 5, fy + 7, fw - 10, 7, "case_deep")
    c.rect(fx + 6, fy + 9, fw - 18, 2, "case_top")
    c.rect(fx + fw - 10, fy + 10, 3, 2, "case_edge")
    c.rect(fx + 5, fy + 17, fw - 10, 5, "case_deep")
    c.rect(fx + 6, fy + 19, fw - 19, 2, "case_top")

    vent_top, vent_end = fy + 24, fy + fh - 20      # between the floppy and the
    for i in range(max(0, min(4, (vent_end - vent_top) // 5))):   # power button
        c.rect(fx + 6, vent_top + i * 5, fw - 12, 2, "case_deep")

    c.frame(fx + 6, fy + fh - 16, 9, 9, o)              # power button
    c.rect(fx + 7, fy + fh - 15, 7, 7, "case_top")
    c.rect(fx + 9, fy + fh - 13, 3, 3, "case_deep")
    c.rect(fx + fw - 6, fy + fh - 12, 3, 3, "led")      # indicator

    c.outline_poly(top, o)
    c.outline_poly(side, o)
    c.frame(fx, fy, fw, fh, o)

    c.rect(fx, fy + fh, fw, 3, "case_deep")             # feet, and the dark
    c.rect(fx + 8, fy + fh, fw - 16, 2, "desk_side")    # gap between them


def draw_keyboard(c, x0, x1, y, dx, dy):
    """A cased keyboard: a deck, a left end, a front lip, and raised keycaps.

    Each key is a solid, not a tile: a lit top face, a front face turned toward
    us, and the shadow it drops on the deck behind the key in front of it. Rows
    are drawn BACK TO FRONT so a nearer row occludes the one behind it, which is
    what stops the caps reading as a flat printed grid.
    """
    o = "outline"
    lip_h = 7
    deck = [(x0, y), (x1, y), (x1 - dx, y - dy), (x0 - dx, y - dy)]
    left = [(x0, y), (x0 - dx, y - dy), (x0 - dx, y - dy + lip_h), (x0, y + lip_h)]
    lip = [(x0, y), (x1, y), (x1, y + lip_h), (x0, y + lip_h)]
    c.poly(left, "case_deep")                   # the end turned furthest away
    c.poly(lip, "case_side")
    c.poly(deck, "case_front")
    c.hline(x0 + 1, x1 - 1, y + 1, "case_edge")   # catch-light on the front edge
    c.hline(x0 + 1, x1 - 1, y + lip_h - 1, "case_deep")   # the underside, in shadow

    rows = [
        [1.4, 1.1, 1.1, 6.0, 1.1, 1.1, 1.4],        # the space bar, nearest
        [1.6] + [1] * 10 + [2.0],
        [1.4] + [1] * 11 + [1.4],
        [1] * 13,
        [1.2] + [0.8] * 12,                         # function row, furthest back
    ]
    n = len(rows)
    step_y, step_x = dy / (n + 0.8), dx / (n + 0.8)
    for r in reversed(range(n)):                    # back row first
        weights = rows[r]
        ry = int(y - 5 - r * step_y)
        rx = int(x0 + 7 - r * step_x)
        right = int(x1 - 7 - r * step_x)
        unit = (right - rx) / sum(weights)
        kx = rx
        for weight in weights:
            kw = max(3, int(weight * unit) - 1)
            if kx + kw > right:
                break
            c.rect(kx, ry - 2, kw, 2, "key_top")            # the cap's lit top
            c.hline(kx, kx + kw - 1, ry, "key_side")        # the face toward us
            c.hline(kx, kx + kw - 1, ry + 1, "case_deep")   # the shadow it drops
            kx += int(weight * unit)

    c.outline_poly(deck, o)
    c.outline_poly(left, o)
    c.outline_poly(lip, o)


def draw_mouse(c, x, y, w, d):
    """An old wired mouse: two buttons and a wheel at the far end, palm nearest.

    (x, y) is the near edge of the shell; the body hangs five rows below it, so
    the contact point is y + 6.

    The silhouette is stepped rather than cut on a straight bevel - two pixels
    in, then one, at each corner - which is what gives it a rounded read at this
    size. Inside it, value separation does the rest: a mid-tone shell, two lit
    button pads, a dark split that runs all the way to the far edge, one bright
    pixel for the wheel, and a dark underside so it sits ON the desk.
    """
    o = "outline"
    fx = x - d * 2                              # far edge: d back, so 2d left
    s = d // 2                                  # the buttons take the far half
    sx, sy = x - s * 2, y - s

    shell = [
        (x + 4, y), (x + w - 4, y),             # the near edge
        (x + w - 2, y - 1), (x + w - 1, y - 3),  # stepped corner
        (fx + w - 2, y - d + 2), (fx + w - 4, y - d),
        (fx + 4, y - d), (fx + 2, y - d + 2),
        (x + 1, y - 3), (x + 2, y - 1),          # stepped corner
    ]
    c.poly(shell, "case_front")
    c.line(x + 3, y - 1, fx + 5, y - d + 1, "case_edge")    # the lit left flank

    pads = [(fx + 4, y - d + 1), (fx + w - 4, y - d + 1), (sx + w - 4, sy), (sx + 4, sy)]
    c.poly(pads, "case_top")
    c.hline(sx + 5, sx + w - 5, sy + 1, "case_deep")        # seam behind the buttons
    c.line(sx + w // 2, sy, fx + w // 2, y - d, "case_deep")  # the split between them

    wx, wy = sx + w // 2 - 4, sy - 4                        # the wheel, in the split
    c.rect(wx, wy, 3, 4, "case_deep")
    c.rect(wx + 1, wy + 1, 1, 2, "case_edge")

    c.rect(x + 3, y + 1, w - 6, 4, "case_side")             # the body
    c.vline(x + 4, y + 1, y + 3, "case_front")              # lit on the left
    c.hline(x + 4, x + w - 4, y + 4, "case_deep")           # dark underside
    c.outline_poly(shell, o)
    c.hline(x + 4, x + w - 4, y + 5, o)
    c.vline(x + 3, y, y + 5, o)
    c.vline(x + w - 3, y, y + 5, o)


def draw_cable(c, p0, p1, p2, steps=200):
    """A quadratic curve sampled onto the grid: stepped pixels, never smoothed.

    One outline pixel with a dark one under it. Three was thick enough that the
    flatter stretches stacked into a slab and competed with the objects.
    """
    prev = None
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        pt = (round(x), round(y))
        if pt != prev:
            c.set(pt[0], pt[1], "outline")
            c.set(pt[0], pt[1] + 1, "desk_side")
        prev = pt


# ---------------------------------------------------------------------------


def draw_scene(c):
    """Wide framing: desk, monitor left, tower right, keyboard and wired mouse."""
    draw_desk(c, DESK_FX0, DESK_FX1, DESK_FY, DESK_DX, DESK_DY, DESK_LIP,
              DESK_FOOT, DESK_LEGS)

    cx = MON_X + MON_W // 2
    cast(c, cx - 37, cx + 27, MON_BASE_Y, 5)
    cast(c, TOW_X - TOW_DX, TOW_X + TOW_W, TOW_Y + TOW_H + 3, 5)
    contact(c, cx - 37, cx + 27, MON_BASE_Y)
    contact(c, TOW_X - TOW_DX - 1, TOW_X + TOW_W + 1, TOW_Y + TOW_H + 3)
    contact(c, KB_X0 - 1, KB_X1 + 1, KB_Y + 7)
    contact(c, MOUSE_X - 2, MOUSE_X + MOUSE_W + 1, MOUSE_Y + 6)

    # Cables are drawn before the objects, so they pass behind them.
    for arc in MON_CABLE + KB_CABLE + MOUSE_CABLE:
        draw_cable(c, *arc)

    draw_tower(c, TOW_X, TOW_Y, TOW_W, TOW_H, TOW_DX, TOW_DY)
    draw_monitor(c, MON_X, MON_Y, MON_W, MON_H, MON_DX, MON_DY,
                 SCREEN_X, SCREEN_Y, SCREEN_W, SCREEN_H, MON_BASE_Y)
    draw_keyboard(c, KB_X0, KB_X1, KB_Y, KB_DX, KB_DY)
    draw_mouse(c, MOUSE_X, MOUSE_Y, MOUSE_W, MOUSE_D)

    return {"screen": {"x": SCREEN_X, "y": SCREEN_Y, "w": SCREEN_W, "h": SCREEN_H},
            "canvas": {"w": W, "h": H},
            "desk": desk_plan(H, DESK_FY, DESK_DY, DESK_LIP)}


# --- narrow framing ---------------------------------------------------------
# Not a shrunken copy, and not the same canvas at a smaller scale either.
#
# Raster pixel art is only ever shown at a whole-number multiple, so the canvas
# WIDTH decides the scale a phone can reach: 120 divides 360 exactly and fits
# three times into 390, 412 and 430, so every common phone lands on 3x. A wider
# canvas would drop to 2x on the same screens and the tube would come out
# SMALLER in real pixels despite the picture being bigger on the grid.
#
# Inside that 120 the monitor takes what it needs to stay readable, the tower
# stands behind and to the right of it and shows the part of itself that is not
# hidden by the monitor, and the keyboard and mouse sit in front. Contact
# points, front to back: 98 tower, 104 monitor base, 109 keyboard back, 124
# mouse, 128 the desk's front edge.

CW, CH = 120, 168
C_DESK_FY, C_DESK_DX, C_DESK_DY = 128, 76, 38
C_DESK_FX0, C_DESK_FX1 = -40, 200
C_DESK_LIP = 7
C_DESK_FOOT = CH + 4
C_DESK_LEGS = (20, 84)

C_MON_X, C_MON_Y, C_MON_W, C_MON_H = 12, 8, 80, 70
C_MON_DX, C_MON_DY = 10, 5
C_SCREEN_X, C_SCREEN_Y, C_SCREEN_W, C_SCREEN_H = 20, 15, 64, 48
C_MON_BASE_Y = 104

C_TOW_X, C_TOW_Y, C_TOW_W, C_TOW_H = 96, 48, 20, 50
C_TOW_DX, C_TOW_DY = 8, 4

C_KB_X0, C_KB_X1, C_KB_Y = 18, 94, 120
C_KB_DX, C_KB_DY = 24, 12
C_MOUSE_X, C_MOUSE_Y, C_MOUSE_W, C_MOUSE_D = 96, 119, 20, 4

C_MON_CABLE = [((60, 102), (78, 100), (94, 94))]
C_KB_CABLE = [((56, 115), (76, 110), (98, 94))]
# The compact tower stands almost directly above the mouse, so a single arc
# between them would be a straight vertical line and read as a pole. Two chained
# arcs give the cable the slack a real one has: out to the left across the
# tabletop, then back up and behind the case.
C_MOUSE_CABLE = [((102, 121), (94, 115), (86, 110)),
                 ((86, 110), (88, 102), (98, 95))]


def draw_scene_compact(c):
    draw_desk(c, C_DESK_FX0, C_DESK_FX1, C_DESK_FY, C_DESK_DX, C_DESK_DY,
              C_DESK_LIP, C_DESK_FOOT, C_DESK_LEGS, leg_w=10)

    cx = C_MON_X + C_MON_W // 2
    cast(c, cx - 26, cx + 18, C_MON_BASE_Y, 4)
    cast(c, C_TOW_X - C_TOW_DX, C_TOW_X + C_TOW_W, C_TOW_Y + C_TOW_H + 3, 4)
    contact(c, cx - 26, cx + 18, C_MON_BASE_Y)
    contact(c, C_TOW_X - C_TOW_DX - 1, C_TOW_X + C_TOW_W + 1, C_TOW_Y + C_TOW_H + 3)
    contact(c, C_KB_X0 - 1, C_KB_X1 + 1, C_KB_Y + 7)
    contact(c, C_MOUSE_X - 2, C_MOUSE_X + C_MOUSE_W + 1, C_MOUSE_Y + 6)

    for arc in C_MON_CABLE + C_KB_CABLE + C_MOUSE_CABLE:
        draw_cable(c, *arc)

    draw_tower(c, C_TOW_X, C_TOW_Y, C_TOW_W, C_TOW_H, C_TOW_DX, C_TOW_DY)
    draw_monitor(c, C_MON_X, C_MON_Y, C_MON_W, C_MON_H, C_MON_DX, C_MON_DY,
                 C_SCREEN_X, C_SCREEN_Y, C_SCREEN_W, C_SCREEN_H, C_MON_BASE_Y,
                 stand=dict(collar=14, foot=19, collar_h=6, dx=6, dy=3))
    draw_keyboard(c, C_KB_X0, C_KB_X1, C_KB_Y, C_KB_DX, C_KB_DY)
    draw_mouse(c, C_MOUSE_X, C_MOUSE_Y, C_MOUSE_W, C_MOUSE_D)

    return {"screen": {"x": C_SCREEN_X, "y": C_SCREEN_Y, "w": C_SCREEN_W, "h": C_SCREEN_H},
            "canvas": {"w": CW, "h": CH},
            "desk": desk_plan(CH, C_DESK_FY, C_DESK_DY, C_DESK_LIP)}
