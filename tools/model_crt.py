"""Model and render the CRT computer for the home page.

Run headless:
    "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup \
        --python tools/model_crt.py -- --out src/assets/scene --samples 160

Everything is modelled from scratch in this file - no downloaded meshes, no stock
imagery, nothing with a licence attached. The output is a pre-rendered RGBA image of
the machine on a transparent background, plus a JSON file giving the exact rectangle
the screen occupies in that image so the live text can be laid over it precisely.

Camera note: the camera is level and looks straight down +Y, with the framing done by
lens SHIFT rather than rotation. That keeps the screen plane parallel to the image
plane, so the screen projects as an axis-aligned rectangle and the HTML overlay needs
no perspective transform. Depth still reads because the machine sits off-axis, which
is what reveals its right side and the top of the keyboard.

Units are metres, at the real size of a 17-inch CRT.
"""

import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

# --------------------------------------------------------------------------- args
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default):
    if name in argv:
        return argv[argv.index(name) + 1]
    return default


OUT_DIR = os.path.abspath(arg("--out", "src/assets/scene"))
SAMPLES = int(arg("--samples", "160"))
RES_X = int(arg("--width", "2200"))
RES_Y = int(arg("--height", "1900"))

# --------------------------------------------------------------- machine geometry
# A 17-inch CRT: 400mm across the front, 390mm tall, and 420mm deep, because these
# things were deep. The visible tube is 4:3 with a thin top bezel and a tall chin.
SHELL_W = 0.400
SHELL_H = 0.390
FRONT_D = 0.115           # the front moulding, which carries the bezel
BACK_D = 0.300            # the rear shell over the tube, tapering to the neck
SEAM = 0.004              # the gap where the two mouldings meet

SCREEN_W = 0.320
SCREEN_H = 0.240
BEZEL_TOP = 0.030
RECESS = 0.016            # how far the tube sits back from the bezel face

STAND_H = 0.052
BASE_W = 0.270
BASE_D = 0.250

FRONT_Y = -0.210          # the plane of the bezel face
SCREEN_CZ = 0.0           # filled in below

# Where the screen sits vertically inside the front moulding.
SCREEN_TOP_Z = SHELL_H / 2 - BEZEL_TOP
SCREEN_BOT_Z = SCREEN_TOP_Z - SCREEN_H
SCREEN_CZ = (SCREEN_TOP_Z + SCREEN_BOT_Z) / 2
MONITOR_Z = STAND_H + SHELL_H / 2          # centre of the shell above the desk


# --------------------------------------------------------------------- utilities
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_mesh(name):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def box(name, size, location=(0, 0, 0)):
    """An axis-aligned box of the given full size."""
    obj = new_mesh(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(obj.data)
    bm.free()
    obj.location = location
    return obj


def taper_back(obj, sx, sz, axis_y):
    """Squeeze the vertices behind `axis_y` toward the object's centre line."""
    for v in obj.data.vertices:
        if v.co.y > axis_y:
            v.co.x *= sx
            v.co.z = (v.co.z - 0) * sz


def add_bevel(obj, width=0.0022, segments=2, angle=35.0):
    m = obj.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    return m


def add_boolean(obj, cutter, operation="DIFFERENCE"):
    m = obj.modifiers.new("bool", "BOOLEAN")
    m.object = cutter
    m.operation = operation
    m.solver = "EXACT"
    cutter.hide_render = True
    cutter.hide_viewport = True
    return m


def shade_smooth(obj, angle=32.0):
    obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    obj.data.update()
    m = obj.modifiers.new("smooth_by_angle", "SMOOTH_BY_ANGLE") if hasattr(
        bpy.types, "SmoothByAngleModifier"
    ) else None
    if m is None:
        # Fall back to a weighted normal modifier, which keeps hard edges crisp.
        wn = obj.modifiers.new("weighted", "WEIGHTED_NORMAL")
        wn.keep_sharp = True


# --------------------------------------------------------------------- materials
def principled(name, **kw):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    for key, value in kw.items():
        socket = bsdf.inputs.get(key)
        if socket is not None:
            socket.default_value = value
    return mat, bsdf


def aged_plastic(name, base, rough_lo=0.34, rough_hi=0.54, bump=0.02, tint_scale=14.0):
    """Beige moulding: fine surface texture, and slow tonal drift across the panel.

    The drift is what stops a large flat panel reading as a single flat fill; the
    fine noise is the moulding grain. Both are deliberately weak - the machine is
    meant to look used, not derelict.
    """
    mat, bsdf = principled(name, **{"Base Color": (*base, 1.0), "Metallic": 0.0})
    nodes, links = mat.node_tree.nodes, mat.node_tree.links

    coords = nodes.new("ShaderNodeTexCoord")

    # Roughness variation
    n_rough = nodes.new("ShaderNodeTexNoise")
    n_rough.inputs["Scale"].default_value = 220.0
    n_rough.inputs["Detail"].default_value = 3.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (rough_lo, rough_lo, rough_lo, 1)
    ramp.color_ramp.elements[1].position = 0.68
    ramp.color_ramp.elements[1].color = (rough_hi, rough_hi, rough_hi, 1)
    links.new(coords.outputs["Object"], n_rough.inputs["Vector"])
    links.new(n_rough.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])

    # Slow tonal drift, so the beige is not one flat value across a big panel
    n_tint = nodes.new("ShaderNodeTexNoise")
    n_tint.inputs["Scale"].default_value = tint_scale
    n_tint.inputs["Detail"].default_value = 2.0
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["Factor"].default_value = 0.10
    mix.inputs[6].default_value = (*base, 1.0)
    mix.inputs[7].default_value = (base[0] * 0.86, base[1] * 0.87, base[2] * 0.90, 1.0)
    links.new(coords.outputs["Object"], n_tint.inputs["Vector"])
    links.new(n_tint.outputs["Fac"], mix.inputs["Factor"])
    links.new(mix.outputs[2], bsdf.inputs["Base Color"])

    # Moulding grain
    n_bump = nodes.new("ShaderNodeTexNoise")
    n_bump.inputs["Scale"].default_value = 900.0
    n_bump.inputs["Detail"].default_value = 2.0
    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs["Strength"].default_value = bump
    links.new(coords.outputs["Object"], n_bump.inputs["Vector"])
    links.new(n_bump.outputs["Fac"], bump_node.inputs["Height"])
    links.new(bump_node.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ------------------------------------------------------------------- the monitor
def build_monitor(mat_front, mat_back, mat_dark, mat_glass, mat_screen, mat_led):
    parts = []

    # --- front moulding, with the tube opening cut out of it -------------------
    front = box(
        "front_shell",
        (SHELL_W, FRONT_D, SHELL_H),
        (0, FRONT_Y + FRONT_D / 2, MONITOR_Z),
    )
    cutter = box(
        "screen_cut",
        (SCREEN_W, RECESS * 2 + 0.02, SCREEN_H),
        (0, FRONT_Y + RECESS, MONITOR_Z + SCREEN_CZ),
    )
    add_boolean(front, cutter)
    add_bevel(front, width=0.0026, segments=3, angle=32)
    assign(front, mat_front)
    parts.append(front)

    # The tube face: one slightly domed surface that is both the glass and the
    # blank display. Kept as a single object so there are no normals to flip and no
    # coincident surfaces to fight over the depth buffer.
    glass = new_mesh("tube_face")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=32, y_segments=32, size=0.5)
    bmesh.ops.scale(bm, vec=Vector((SCREEN_W, SCREEN_H, 1)), verts=bm.verts)
    for v in bm.verts:
        nx = v.co.x / (SCREEN_W / 2)
        ny = v.co.y / (SCREEN_H / 2)
        # A flat-square tube is very nearly flat. The cosine reaches zero at the
        # edges with a continuous slope, so there is no curvature discontinuity to
        # catch the light and read as a ring.
        v.co.z = 0.0013 * math.cos(nx * math.pi / 2) * math.cos(ny * math.pi / 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(glass.data)
    bm.free()
    # rotate so +Z faces the camera (-Y), then confirm by flipping if needed
    glass.rotation_euler = (math.radians(-90), 0, 0)
    glass.location = (0, FRONT_Y + RECESS, MONITOR_Z + SCREEN_CZ)
    assign(glass, mat_screen)
    shade_smooth(glass)
    parts.append(glass)

    # A dark surround inside the recess, so the tube is not floating in a lit box.
    surround = box(
        "tube_surround",
        (SCREEN_W + 0.010, 0.004, SCREEN_H + 0.010),
        (0, FRONT_Y + RECESS + 0.004, MONITOR_Z + SCREEN_CZ),
    )
    assign(surround, mat_dark)
    parts.append(surround)

    # --- rear shell over the tube, tapering back toward the neck --------------
    # The slots are cut before the bevel runs: the exact solver copes far better with
    # a plain box than with an already-rounded shell, and bevelling afterwards gives
    # every slot edge the same soft highlight as the rest of the moulding.
    back_y0 = FRONT_Y + FRONT_D + SEAM
    back = box(
        "back_shell",
        (SHELL_W - 0.0015, BACK_D, SHELL_H - 0.0015),
        (0, back_y0 + BACK_D / 2, MONITOR_Z),
    )
    taper_back(back, 0.70, 0.74, axis_y=0.055)

    # Grouped up front: join_objects frees the objects it merges, so the lists have
    # to be partitioned before any of them is joined.
    side_x = (SHELL_W - 0.0015) / 2        # the planar part of the side face
    top_z = MONITOR_Z + (SHELL_H - 0.0015) / 2
    right_cutters, left_cutters, top_cutters = [], [], []
    for i in range(10):
        y = back_y0 + 0.026 + i * 0.0152
        h = 0.115 - abs(i - 4.5) * 0.004
        right_cutters.append(box("ventR_%d" % i, (0.026, 0.0085, h),
                                 (side_x, y, MONITOR_Z + 0.012)))
        left_cutters.append(box("ventL_%d" % i, (0.026, 0.0085, h),
                                (-side_x, y, MONITOR_Z + 0.012)))
    for i in range(9):
        y = back_y0 + 0.030 + i * 0.0165
        top_cutters.append(box("ventT_%d" % i, (0.215, 0.0085, 0.026), (0, y, top_z)))

    # One modifier per group keeps each boolean operand a simple, well separated set.
    for group, name in ((right_cutters, "vent_right"), (left_cutters, "vent_left"),
                        (top_cutters, "vent_top")):
        add_boolean(back, join_objects(group, name))

    add_bevel(back, width=0.0035, segments=3, angle=32)
    assign(back, mat_back)
    parts.append(back)

    # --- the chin: buttons and the power light --------------------------------
    chin_z = MONITOR_Z + SCREEN_BOT_Z - 0.056
    face_y = FRONT_Y - 0.0015

    power = cylinder("btn_power", r=0.0125, depth=0.006, loc=(-0.118, face_y, chin_z))
    assign(power, mat_front)
    parts.append(power)
    ring = cylinder("btn_power_ring", r=0.0155, depth=0.003, loc=(-0.118, FRONT_Y + 0.0006, chin_z))
    assign(ring, mat_dark)
    parts.append(ring)

    for i, x in enumerate((0.052, 0.081, 0.110, 0.139)):
        b = box("btn_%d" % i, (0.020, 0.006, 0.008), (x, face_y, chin_z))
        add_bevel(b, width=0.0012, segments=2)
        assign(b, mat_front)
        parts.append(b)

    led = cylinder("led", r=0.0035, depth=0.004, loc=(-0.082, face_y, chin_z))
    assign(led, mat_led)
    parts.append(led)

    # A moulded strip under the screen, the way these fronts were styled.
    strip = box("chin_strip", (0.130, 0.004, 0.0035), (0.06, face_y, chin_z + 0.026))
    assign(strip, mat_dark)
    parts.append(strip)

    # A shallow recessed panel on the chin where a maker plate would sit. Left blank:
    # this machine is nobody's product.
    plate = box("chin_plate", (0.052, 0.005, 0.011), (-0.150, FRONT_Y + 0.0012, chin_z + 0.030))
    add_bevel(plate, width=0.0008, segments=2)
    assign(plate, mat_back)
    parts.append(plate)

    # --- stand: a tilt-swivel neck on a rounded base --------------------------
    neck = box("neck", (0.150, 0.150, STAND_H + 0.02), (0, FRONT_Y + 0.19, STAND_H / 2))
    taper_back(neck, 1.0, 1.0, axis_y=99)
    add_bevel(neck, width=0.010, segments=4, angle=40)
    assign(neck, mat_back)
    parts.append(neck)

    base = box("base", (BASE_W, BASE_D, 0.020), (0, FRONT_Y + 0.19, 0.010))
    add_bevel(base, width=0.008, segments=4, angle=40)
    assign(base, mat_back)
    parts.append(base)

    return parts


def cylinder(name, r, depth, loc, axis="Y"):
    obj = new_mesh(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=48, radius1=r, radius2=r, depth=depth
    )
    bm.to_mesh(obj.data)
    bm.free()
    if axis == "Y":
        obj.rotation_euler = (math.radians(90), 0, 0)
    obj.location = loc
    shade_smooth(obj)
    return obj


def join_objects(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    return joined


# ------------------------------------------------------------------ the keyboard
# Row widths in key units. 1u is 19mm, the real pitch.
LAYOUT = [
    # (z-row, [widths...]) with a gap marker as a negative number
    [1, 1, -0.5, 1, 1, 1, 1, -0.25, 1, 1, 1, 1, -0.25, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [1.5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1.5],
    [1.75, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2.25],
    [2.25, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2.75],
    [1.25, 1.25, 1.25, 6.25, 1.25, 1.25, 1.25, 1.25],
]

U = 0.0190
KEY = 0.0172
KEY_H = 0.0090
KB_W = 0.445
KB_D = 0.165
KB_BACK_H = 0.026
KB_FRONT_H = 0.015
KB_X = 0.030
KB_Y = -0.415


def keycap(name, w_units, loc, mat):
    """A keycap with a dished top, which is where the readable highlight comes from."""
    w = KEY + (w_units - 1) * U
    obj = new_mesh(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((w, KEY, KEY_H)), verts=bm.verts)
    # taper the top slightly and dish it
    top = [v for v in bm.verts if v.co.z > 0]
    for v in top:
        v.co.x *= 0.88
        v.co.y *= 0.86
        v.co.z -= 0.0012
    bm.to_mesh(obj.data)
    bm.free()
    obj.location = loc
    m = obj.modifiers.new("bevel", "BEVEL")
    m.width = 0.0009
    m.segments = 2
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(30)
    assign(obj, mat)
    return obj


def build_keyboard(mat_case, mat_key):
    caps = []
    row_gap = 0.0016
    z_top = KB_BACK_H

    for r, row in enumerate(LAYOUT):
        y = KB_Y + KB_D / 2 - 0.016 - r * (KEY + row_gap) - (0.006 if r == 1 else 0)
        # the deck slopes, so keys further back sit higher
        t = r / (len(LAYOUT) - 1)
        z = z_top - t * (KB_BACK_H - KB_FRONT_H) + KEY_H / 2 + 0.0015
        x = KB_X - KB_W / 2 + 0.010
        for i, w in enumerate(row):
            if w < 0:
                x += -w * U
                continue
            width = KEY + (w - 1) * U
            caps.append(keycap("key_%d_%d" % (r, i), w, (x + width / 2, y, z), mat_key))
            x += w * U + (U - KEY)

    case = box(
        "kb_case",
        (KB_W, KB_D, KB_BACK_H),
        (KB_X, KB_Y, KB_BACK_H / 2),
    )
    # slope the front down
    for v in case.data.vertices:
        if v.co.y < 0 and v.co.z > 0:
            v.co.z -= (KB_BACK_H - KB_FRONT_H)
    add_bevel(case, width=0.0018, segments=3, angle=30)
    assign(case, mat_case)

    keys = join_objects(caps, "keycaps")
    return [case, keys]


# ------------------------------------------------------------------------ render
def build_scene():
    clear_scene()
    scene = bpy.context.scene

    beige = (0.660, 0.601, 0.454)   # sRGB ~ #D8CDB2, warm putty
    mat_front = aged_plastic("plastic_front", beige, 0.34, 0.52, 0.020, 12.0)
    mat_back = aged_plastic("plastic_back", (beige[0] * 0.92, beige[1] * 0.92, beige[2] * 0.93),
                            0.40, 0.60, 0.028, 9.0)
    mat_key = aged_plastic("plastic_key", (0.700, 0.648, 0.508), 0.30, 0.44, 0.014, 26.0)
    mat_case = aged_plastic("plastic_case", (0.640, 0.583, 0.440), 0.36, 0.54, 0.022, 16.0)

    mat_dark, _ = principled("trim_dark", **{
        "Base Color": (0.030, 0.030, 0.034, 1), "Roughness": 0.55})

    # Glass: clear, glossy, and just reflective enough to catch the room.
    mat_glass, glass_bsdf = principled("glass", **{
        "Base Color": (0.02, 0.02, 0.025, 1),
        "Roughness": 0.045,
        "IOR": 1.52,
        "Transmission Weight": 0.0,
        "Metallic": 0.0,
    })
    if "Coat Weight" in glass_bsdf.inputs:
        glass_bsdf.inputs["Coat Weight"].default_value = 1.0
        glass_bsdf.inputs["Coat Roughness"].default_value = 0.02

    # The blank display. Dim, cool, and emissive so it lights the bezel the way a
    # real screen does. The words are drawn by the browser on top of this.
    mat_screen, screen_bsdf = principled("screen_blank", **{
        "Base Color": (0.006, 0.009, 0.015, 1),
        "Roughness": 0.085,
        "IOR": 1.52,
        "Metallic": 0.0,
    })
    if "Coat Weight" in screen_bsdf.inputs:
        screen_bsdf.inputs["Coat Weight"].default_value = 0.85
        screen_bsdf.inputs["Coat Roughness"].default_value = 0.035
    if "Emission Color" in screen_bsdf.inputs:
        screen_bsdf.inputs["Emission Color"].default_value = (0.045, 0.105, 0.150, 1)
        screen_bsdf.inputs["Emission Strength"].default_value = 0.30

    mat_led, led_bsdf = principled("led", **{"Base Color": (0.10, 0.80, 0.55, 1)})
    if "Emission Color" in led_bsdf.inputs:
        led_bsdf.inputs["Emission Color"].default_value = (0.25, 1.0, 0.70, 1)
        led_bsdf.inputs["Emission Strength"].default_value = 14.0

    build_monitor(mat_front, mat_back, mat_dark, mat_glass, mat_screen, mat_led)
    build_keyboard(mat_case, mat_key)

    # --- desk, as a shadow catcher only ---------------------------------------
    desk = box("desk", (7.0, 5.0, 0.002), (0.02, -0.60, -0.001))
    desk.is_shadow_catcher = True
    mat_desk, _ = principled("desk", **{"Base Color": (0.05, 0.05, 0.07, 1), "Roughness": 0.6})
    assign(desk, mat_desk)

    # --- lighting -------------------------------------------------------------
    # A warm near-neutral key, because under a cyan key the beige moulding turns
    # grey-green and stops reading as period plastic. The cyan and violet are rims:
    # they describe the edges of the casing without colouring its faces.
    key = bpy.data.lights.new("key", type="AREA")
    key.energy = 78.0
    key.size = 0.85
    key.color = (1.0, 0.94, 0.86)
    key_obj = bpy.data.objects.new("key", key)
    key_obj.location = (-1.25, -1.55, 1.55)
    key_obj.rotation_euler = (math.radians(50), 0, math.radians(-40))
    bpy.context.collection.objects.link(key_obj)

    # Cyan from the right, the colour of the room the machine stands in.
    cyan = bpy.data.lights.new("cyan", type="AREA")
    cyan.energy = 52.0
    cyan.size = 1.0
    cyan.color = (0.42, 0.86, 1.0)
    cyan_obj = bpy.data.objects.new("cyan", cyan)
    cyan_obj.location = (1.95, -1.05, 0.66)
    cyan_obj.rotation_euler = (math.radians(84), 0, math.radians(64))
    bpy.context.collection.objects.link(cyan_obj)

    # Violet from behind and above, to lift the top edge off the dark background.
    rim = bpy.data.lights.new("rim", type="AREA")
    rim.energy = 46.0
    rim.size = 0.9
    rim.color = (0.86, 0.52, 1.0)
    rim_obj = bpy.data.objects.new("rim", rim)
    rim_obj.location = (0.95, 1.35, 1.35)
    rim_obj.rotation_euler = (math.radians(128), 0, math.radians(158))
    bpy.context.collection.objects.link(rim_obj)

    # Very dim fill so the shadow side keeps its shape rather than going black.
    fill = bpy.data.lights.new("fill", type="AREA")
    fill.energy = 6.0
    fill.size = 3.0
    fill.color = (0.62, 0.70, 0.95)
    fill_obj = bpy.data.objects.new("fill", fill)
    fill_obj.location = (-0.9, -1.9, 0.15)
    fill_obj.rotation_euler = (math.radians(96), 0, math.radians(-24))
    bpy.context.collection.objects.link(fill_obj)

    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.045, 0.052, 0.090, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    scene.world = world

    # --- camera: level, framed by shift, so the screen stays a rectangle -------
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 60.0
    cam_data.sensor_width = 36.0
    cam = bpy.data.objects.new("cam", cam_data)
    # Standing to the right of the desk and a little above the monitor. The offset
    # is what reveals the right side and the top; the camera itself never tilts, so
    # the screen plane stays parallel to the image plane.
    cam.location = (0.62, -1.95, 0.575)
    cam.rotation_euler = (math.radians(90), 0, 0)   # dead level, no tilt at all
    # Standing well to the right of the desk is what shows the depth of the casing:
    # a level camera reveals a side face only through off-axis position. The frame is
    # then shifted back over the machine, which moves the frame without tilting it,
    # so the screen plane stays parallel to the sensor and projects as a rectangle.
    cam_data.shift_x = -0.500
    cam_data.shift_y = -0.292    # drop the frame to take in the desk and keyboard
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

    # --- render settings ------------------------------------------------------
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.transmission_bounces = 4
    scene.render.film_transparent = True
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.compression = 20
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    prefs = bpy.context.preferences.addons.get("cycles")
    if prefs:
        cp = prefs.preferences
        for t in ("OPTIX", "CUDA"):
            try:
                cp.compute_device_type = t
                cp.get_devices()
                if any(d.type == t for d in cp.devices):
                    for d in cp.devices:
                        d.use = d.type in (t, "CPU")
                    print("RENDER-DEVICE", t)
                    break
            except Exception:
                continue
    return scene, cam


def _project_rect(scene, cam, y, half_w, half_h, cz):
    """Project an axis-aligned rectangle lying in a plane of constant Y."""
    from bpy_extras.object_utils import world_to_camera_view

    # world_to_camera_view reads cam.matrix_world, which is still identity until the
    # depsgraph catches up with the location and rotation set during build. Without
    # this the projection is computed for a camera at the origin.
    bpy.context.view_layer.update()

    corners = [
        Vector((-half_w, y, cz + half_h)),   # top-left
        Vector((half_w, y, cz + half_h)),    # top-right
        Vector((half_w, y, cz - half_h)),    # bottom-right
        Vector((-half_w, y, cz - half_h)),   # bottom-left
    ]
    pts = [world_to_camera_view(scene, cam, c) for c in corners]
    xs = [p.x for p in pts]
    ys = [1.0 - p.y for p in pts]  # flip: Blender's frame origin is bottom-left
    return {
        "left": min(xs) * 100.0,
        "top": min(ys) * 100.0,
        "right": max(xs) * 100.0,
        "bottom": max(ys) * 100.0,
        "width": (max(xs) - min(xs)) * 100.0,
        "height": (max(ys) - min(ys)) * 100.0,
        # With a level camera and a plane parallel to the image plane these are ~0.
        # If they are not, the overlay would need a perspective transform.
        "skew_x": (abs(xs[0] - xs[3]) + abs(xs[1] - xs[2])) * 100.0,
        "skew_y": (abs(ys[0] - ys[1]) + abs(ys[2] - ys[3])) * 100.0,
    }


def screen_rect(scene, cam):
    """Where the live text goes, and how much of it the bezel hides.

    Two rectangles matter. The GLASS is the plane the content lives on, set back
    inside the moulding. The APERTURE is the opening in the front of the bezel,
    nearer the camera. Because the machine sits off the optical axis, the aperture
    does not project exactly over the glass: the recess wall on one side eats into
    it. The visible glass is the intersection, and the browser clips to that so the
    text is occluded by the moulding instead of painted over it.
    """
    cz = MONITOR_Z + SCREEN_CZ
    glass = _project_rect(scene, cam, FRONT_Y + RECESS, SCREEN_W / 2, SCREEN_H / 2, cz)
    aperture = _project_rect(scene, cam, FRONT_Y, SCREEN_W / 2, SCREEN_H / 2, cz)

    vis = {
        "left": max(glass["left"], aperture["left"]),
        "top": max(glass["top"], aperture["top"]),
        "right": min(glass["right"], aperture["right"]),
        "bottom": min(glass["bottom"], aperture["bottom"]),
    }
    # Expressed as a clip inset in percentages of the glass rectangle itself, which
    # is exactly what CSS clip-path: inset() wants.
    clip = {
        "top": (vis["top"] - glass["top"]) / glass["height"] * 100.0,
        "right": (glass["right"] - vis["right"]) / glass["width"] * 100.0,
        "bottom": (glass["bottom"] - vis["bottom"]) / glass["height"] * 100.0,
        "left": (vis["left"] - glass["left"]) / glass["width"] * 100.0,
    }
    return {"glass": glass, "aperture": aperture, "clip": clip}


def crop_to_content(path, margin_frac=0.010, threshold=0.035):
    """Trim the transparent border, and report the crop as fractions of the render.

    The framing is chosen for the composition, not for the file size, so the render
    carries a lot of empty pixels. Cropping to what is actually drawn - including the
    soft contact shadow, which lives only in the alpha - keeps the asset small. The
    screen rectangle is then re-expressed against the cropped frame.
    """
    import numpy as np

    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    alpha = px[:, :, 3]
    rows = np.where(alpha.max(axis=1) > threshold)[0]
    cols = np.where(alpha.max(axis=0) > threshold)[0]
    if len(rows) == 0 or len(cols) == 0:
        bpy.data.images.remove(img)
        return None

    mx = int(w * margin_frac)
    my = int(h * margin_frac)
    x0 = max(0, int(cols[0]) - mx)
    x1 = min(w, int(cols[-1]) + 1 + mx)
    # Blender's pixel rows run bottom-up; convert to a top-down box.
    y0_bl = max(0, int(rows[0]) - my)
    y1_bl = min(h, int(rows[-1]) + 1 + my)

    cropped = px[y0_bl:y1_bl, x0:x1, :]
    ch, cw = cropped.shape[0], cropped.shape[1]

    out = bpy.data.images.new("crt_cropped", width=cw, height=ch, alpha=True)
    out.pixels.foreach_set(cropped.reshape(-1))
    out.file_format = "PNG"
    out.filepath_raw = path
    out.save()

    box = {
        "x": x0 / w,
        "y": (h - y1_bl) / h,       # top edge, top-down
        "w": cw / w,
        "h": ch / h,
        "pixels": [cw, ch],
    }
    bpy.data.images.remove(img)
    bpy.data.images.remove(out)
    return box


def rebase(rect, box):
    """Re-express a rectangle given in render percentages against the cropped frame."""
    out = {}
    for key in ("glass", "aperture"):
        r = rect[key]
        out[key] = {
            "left": (r["left"] / 100 - box["x"]) / box["w"] * 100,
            "top": (r["top"] / 100 - box["y"]) / box["h"] * 100,
            "width": r["width"] / 100 / box["w"] * 100,
            "height": r["height"] / 100 / box["h"] * 100,
            "skew_x": r["skew_x"],
            "skew_y": r["skew_y"],
        }
    out["clip"] = rect["clip"]
    return out


def main():
    scene, cam = build_scene()
    os.makedirs(OUT_DIR, exist_ok=True)

    rect = screen_rect(scene, cam)
    png = os.path.join(OUT_DIR, "crt.png")
    scene.render.filepath = png
    bpy.ops.render.render(write_still=True)

    box = crop_to_content(png)
    if box:
        rect = rebase(rect, box)
        print("CROPPED-TO", box["pixels"])

    meta = {
        "generatedBy": "tools/model_crt.py",
        "note": "Modelled and rendered from scratch. No third-party mesh, texture or image.",
        "renderer": "Blender %s / Cycles, OptiX" % bpy.app.version_string.split()[0],
        "renderResolution": [RES_X, RES_Y],
        "assetPixels": box["pixels"] if box else [RES_X, RES_Y],
        "samples": SAMPLES,
        "screen": rect,
    }
    with open(os.path.join(OUT_DIR, "crt.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    # Ship WebP: the page never needs the lossless master, and an RGBA PNG of a
    # render this size is several megabytes. Two widths, so a phone does not pull
    # the desktop asset.
    scene.render.image_settings.file_format = "WEBP"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.quality = 90
    src = bpy.data.images.load(png)
    full_w, full_h = src.size
    for label, factor in (("", 1.0), ("@half", 0.5)):
        img = src.copy()
        if factor != 1.0:
            img.scale(int(full_w * factor), int(full_h * factor))
        target = os.path.join(OUT_DIR, "crt%s.webp" % label)
        img.save_render(target, scene=scene)
        print("EXPORT %-14s %5d x %-5d %7.1f KB" % (
            os.path.basename(target), img.size[0], img.size[1],
            os.path.getsize(target) / 1024.0))
        bpy.data.images.remove(img)
    bpy.data.images.remove(src)

    print("SCREEN-RECT", json.dumps(rect["glass"]))
    print("WROTE", png)


if __name__ == "__main__":
    main()
