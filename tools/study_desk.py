"""A proportion study of the three desk forms the pixel artwork gets wrong.

Run headless:
    "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup \
        --python tools/study_desk.py -- --out docs/study

This is a REFERENCE GENERATOR, not an asset pipeline. Nothing it produces ships:
the site's artwork is drawn pixel by pixel by tools/pixel_art.py, and that stays
true. What this gives is a correct set of masses and proportions to draw FROM,
because the three forms that were wrong were wrong in the same way - they were
drawn as flat slabs, with no underlying idea of what the object actually is:

  the CRT support   read as a rectangular block, with no tilt/swivel joint, no
                    neck, and a base with no visible top surface
  the keyboard      read as horizontal strips, with no separated keycaps and no
                    consistent row perspective
  the mouse         read as a thin stepped tray, with no arched back, no taper,
                    and no volume in its silhouette

So the order here is the one that matters: get the SILHOUETTE and the MASS right
first, in three dimensions where they cannot cheat, and only then translate them
back to the integer grid. Detail added before the silhouette is right just makes
a wrong shape more elaborate.

Three orthographic views come out: front, left side, and an approximation of the
site's own camera. The site uses an OBLIQUE projection - depth runs back and to
the left on an exact 2:1 screen step - which no perspective camera reproduces.
The third view is therefore an axonometric at the same 26.57 degree screen
angle (atan 1/2): close enough to check masses against, and it is labelled as an
approximation rather than pretended to be the real thing.

Units are metres, at the real size of a 17-inch CRT on a desk.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

# --------------------------------------------------------------------------- args
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default):
    return argv[argv.index(name) + 1] if name in argv else default


OUT_DIR = os.path.abspath(arg("--out", "docs/study"))
RES = int(arg("--res", "1400"))

# ----------------------------------------------------------------- measurements
# A 17-inch CRT, its pedestal, a full-size keyboard and a two-button mouse.
# These are the numbers the pixel artwork has to end up agreeing with.

CASE_W, CASE_D, CASE_H = 0.400, 0.420, 0.375   # the monitor casing
CHIN_H = 0.055                                  # controls strip below the tube

SWIVEL_R, SWIVEL_H = 0.078, 0.032   # the tilt/swivel joint under the casing
NECK_R, NECK_H = 0.090, 0.022       # a SHORT, sturdy support - never a thin post
BASE_W, BASE_D, BASE_H = 0.300, 0.280, 0.034   # a broad, low pedestal

KB_W, KB_D = 0.455, 0.165           # the keyboard's footprint
KB_FRONT_H, KB_BACK_H = 0.016, 0.040  # a shallow wedge, front to back

MOUSE_L, MOUSE_W, MOUSE_H = 0.115, 0.062, 0.038


# ------------------------------------------------------------------- utilities
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def box(name, size, loc):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    # size=1 already makes a one-metre cube. Dividing again halved every box
    # while cylinders retained full size, disconnecting the screen and keys.
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return ob


def cyl(name, r, h, loc, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc)
    ob = bpy.context.object
    ob.name = name
    return ob


def bevel(ob, width, segments=3):
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(35)
    return ob


# ------------------------------------------------------------------ the monitor
def build_monitor(z0):
    """Casing, and the support assembly the artwork has to learn from.

    A real CRT pedestal is three things stacked with no gap: a tilt/swivel joint
    fixed to the flat UNDERSIDE of the casing, a short neck, and a broad base
    whose TOP SURFACE is visible from above. The failure mode at both ends is
    the same mistake - a thin floating post says the monitor would topple, an
    undifferentiated brick says nothing about how it moves.
    """
    parts = []
    base = box("base", (BASE_W, BASE_D, BASE_H), (0, 0, z0 + BASE_H / 2))
    bevel(base, 0.008, 3)
    parts.append(base)

    neck = cyl("neck", NECK_R, NECK_H, (0, 0.012, z0 + BASE_H + NECK_H / 2))
    bevel(neck, 0.004, 2)
    parts.append(neck)

    swivel = cyl("swivel", SWIVEL_R, SWIVEL_H,
                 (0, 0.012, z0 + BASE_H + NECK_H + SWIVEL_H / 2))
    bevel(swivel, 0.010, 3)
    parts.append(swivel)

    case_z0 = z0 + BASE_H + NECK_H + SWIVEL_H
    case = box("case", (CASE_W, CASE_D, CASE_H), (0, 0, case_z0 + CASE_H / 2))
    bevel(case, 0.018, 3)
    parts.append(case)

    # The tube's face, recessed into the front so the moulding reads as a frame.
    tube = box("tube", (CASE_W * 0.80, 0.02, (CASE_H - CHIN_H) * 0.80),
               (0, -CASE_D / 2 + 0.004,
                case_z0 + CHIN_H + (CASE_H - CHIN_H) * 0.80 / 2 + 0.012))
    parts.append(tube)
    return parts, case_z0


# ----------------------------------------------------------------- the keyboard
def build_keyboard(z0, y):
    """A shallow WEDGE with separated keycaps, not a flat deck with stripes.

    Two things make it read. The housing is thicker at the back than the front,
    so the top plane is tilted toward the viewer and every row sits on that one
    plane. And the caps are separate solids with a gap between them, so the eye
    gets a top face and a front face per key instead of one banded rectangle.
    """
    parts = []
    # The wedge: a box whose front edge is lowered, so the top is a single plane.
    housing = box("kb", (KB_W, KB_D, KB_BACK_H), (0, y, z0 + KB_BACK_H / 2))
    me = housing.data
    bm = bmesh.new()
    bm.from_mesh(me)
    drop = KB_BACK_H - KB_FRONT_H
    for v in bm.verts:
        if v.co.z > 0 and v.co.y < 0:      # the top front edge
            v.co.z -= drop
    bm.to_mesh(me)
    bm.free()
    bevel(housing, 0.004, 2)
    parts.append(housing)

    # Five staggered rows on that tilted plane. Widths are in key units.
    rows = [
        [1.15] + [1.0] * 12,                       # function row, furthest back
        [1.0] * 13,
        [1.4] + [1.0] * 11 + [1.4],
        [1.6] + [1.0] * 10 + [2.0],
        [1.4, 1.1, 1.1, 6.0, 1.1, 1.1, 1.4],       # the space bar, nearest
    ]
    inner_w = KB_W - 0.030
    depth = KB_D - 0.026
    n = len(rows)
    for r, weights in enumerate(rows):
        t = (r + 0.5) / n                     # 0 at the back, 1 at the front
        ry = y + depth / 2 - t * depth
        rz = z0 + KB_BACK_H - drop * t + 0.004
        unit = inner_w / max(sum(w) for w in rows)
        x = -inner_w / 2
        for w in weights:
            kw = w * unit
            cap = box(f"key{r}_{x:.3f}", (kw - 0.0035, depth / n - 0.0035, 0.009),
                      (x + kw / 2, ry, rz))
            bevel(cap, 0.0012, 2)
            parts.append(cap)
            x += kw
    return parts


# -------------------------------------------------------------------- the mouse
def build_mouse(z0, x, y):
    """An elongated body with an ARCHED back and a tapered front.

    Built from a sphere rather than a box on purpose: the previous drawing was a
    stepped tray because it was conceived as stacked rectangles. The volume has
    to come from the silhouette - high and round at the palm, falling away to a
    low tapered nose - and a sphere flattened underneath gives exactly that.
    """
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=24, radius=0.5,
                                         location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = "mouse"
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for v in bm.verts:
        v.co.x *= MOUSE_W
        v.co.y *= MOUSE_L
        v.co.z *= MOUSE_H * 2.0
        if v.co.z < 0:
            v.co.z = 0.0                       # flat underside, sitting on the desk
        if v.co.y < 0:                         # the nose: taper it down and in
            t = min(1.0, -v.co.y / (MOUSE_L * 0.5))
            v.co.x *= 1.0 - 0.28 * t
            v.co.z *= 1.0 - 0.52 * t
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(me)
    bm.free()
    ob.location = (x, y, z0)
    bpy.ops.object.shade_smooth()

    # The split between the two buttons, and the wheel sitting in it.
    split = box("split", (0.0025, MOUSE_L * 0.52, 0.02),
                (x, y - MOUSE_L * 0.20, z0 + MOUSE_H * 0.86))
    wheel = cyl("wheel", 0.008, 0.005,
                (x, y - MOUSE_L * 0.24, z0 + MOUSE_H * 0.92), verts=24)
    wheel.rotation_euler = (0, math.radians(90), 0)
    cable = cyl("cable", 0.0035, 0.10, (x, y - MOUSE_L * 0.62, z0 + 0.010), verts=16)
    cable.rotation_euler = (math.radians(90), 0, 0)
    return [ob, split, wheel, cable]


# ------------------------------------------------------------------------ views
def look_at(cam, target):
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def render(view, target, loc, scale, tag):
    scene = bpy.context.scene
    cam = scene.camera
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = scale
    cam.location = loc
    look_at(cam, target)
    scene.render.filepath = os.path.join(OUT_DIR, f"desk-study-{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath)


def main():
    clear_scene()
    scene = bpy.context.scene

    desk_z = 0.0
    mon_parts, case_z0 = build_monitor(desk_z)
    build_keyboard(desk_z, -0.33)
    build_mouse(desk_z, 0.34, -0.30)

    # A desk plane, so every object is seen to be standing ON something.
    box("desk", (1.6, 1.0, 0.02), (0, -0.1, desk_z - 0.01))

    bpy.ops.object.camera_add(location=(0, -2, 0.5))
    scene.camera = bpy.context.object

    # Workbench with cavity shading: this is a form study, so unlit matte solids
    # that show silhouette and curvature beat a lit render that hides them.
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.curvature_ridge_factor = 1.0
    shading.curvature_valley_factor = 1.0
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.render.film_transparent = False

    os.makedirs(OUT_DIR, exist_ok=True)
    target = (0, -0.12, 0.22)
    render("front", target, (0, -2.5, 0.22), 0.95, "front")
    render("side", target, (-2.5, -0.12, 0.22), 0.95, "side")

    # The site's own angle, approximated. Its oblique step is 2 across to 1 up,
    # so the screen angle is atan(1/2) = 26.57 degrees; the azimuth puts the
    # camera off to the LEFT, which is the side of the casing the artwork shows.
    el = math.atan(0.5)
    az = math.radians(38)
    r = 2.5
    loc = (-r * math.sin(az) * math.cos(el),
           -r * math.cos(az) * math.cos(el),
           0.22 + r * math.sin(el))
    render("site", target, loc, 1.15, "site-angle")


main()
