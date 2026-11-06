"""Sign panels made from official artwork, plus their supports.

The sign face is the official PNG (rasterised from the Commons/OTM SVG)
mapped 1:1 onto a flat panel cut to the artwork's alpha. Nothing about the
artwork is redrawn, so shape, colour, symbol and text stay exact.
"""
import math
import os

import bpy
from mathutils import Vector

from . import common as C

SIGN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "signs")


def artwork(name):
    p = name if os.path.isabs(name) else os.path.join(SIGN_DIR, name)
    if not os.path.exists(p):
        raise FileNotFoundError(f"sign artwork missing: {p} (run prepare_signs.py)")
    img = bpy.data.images.load(p, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    return img


def panel(name, art, width, night=False, coll=None):
    """Panel with front face = artwork, back = bare aluminium.

    Origin is at the bottom-centre of the panel; the face points -Y
    (toward a camera that looks up the road)."""
    img = artwork(art)
    w_px, h_px = img.size
    width = float(width)
    height = width * h_px / w_px

    face = bpy.data.materials.new(name + "_face")
    face.use_nodes = True
    nt = face.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    for n in list(nt.nodes):
        if n.name != out.name:
            nt.nodes.remove(n)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    tex.extension = "CLIP"
    # True colour in every weather and light: camera rays see the artwork as
    # emission at strength 1, which under the Standard view transform (no
    # exposure/look) reproduces the artwork's sRGB values exactly. Other rays
    # (reflections in wet asphalt, bounce light) see a normal diffuse panel,
    # so the sign doesn't glow onto the scene.
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    dif = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(tex.outputs["Color"], dif.inputs["Base Color"])
    C.set_input(dif, "Roughness", 0.45)
    lp = nt.nodes.new("ShaderNodeLightPath")
    pick = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], pick.inputs["Fac"])
    nt.links.new(dif.outputs[0], pick.inputs[1])
    nt.links.new(em.outputs[0], pick.inputs[2])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    cut = nt.nodes.new("ShaderNodeMixShader")      # artwork alpha cuts the panel shape
    nt.links.new(tex.outputs["Alpha"], cut.inputs["Fac"])
    nt.links.new(tr.outputs[0], cut.inputs[1])
    nt.links.new(pick.outputs[0], cut.inputs[2])
    nt.links.new(cut.outputs[0], out.inputs["Surface"])
    face["g1_sign_face"] = True

    back = bpy.data.materials.new(name + "_back")
    back.use_nodes = True
    bn = back.node_tree
    bb = next(n for n in bn.nodes if n.type == "BSDF_PRINCIPLED")
    bt = bn.nodes.new("ShaderNodeTexImage")
    bt.image = img
    bt.extension = "CLIP"
    bn.links.new(bt.outputs["Alpha"], bb.inputs["Alpha"])
    C.set_input(bb, "Base Color", (0.62, 0.63, 0.65, 1))
    C.set_input(bb, "Metallic", 1.0)
    C.set_input(bb, "Roughness", 0.45)

    hw, t = width / 2, 0.003
    verts = [(-hw, 0, 0), (hw, 0, 0), (hw, 0, height), (-hw, 0, height),
             (-hw, t, 0), (hw, t, 0), (hw, t, height), (-hw, t, height)]
    faces = [(0, 1, 2, 3), (5, 4, 7, 6)]
    ob = C.mesh_object(name, verts, faces, [face, back], coll, face_mats=[0, 1])
    uv = ob.data.uv_layers.new(name="UV")
    coords = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (0, 1), 4: (0, 0), 5: (1, 0), 6: (1, 1), 7: (0, 1)}
    for loop in ob.data.loops:
        uv.data[loop.index].uv = coords[loop.vertex_index]
    ob["height"] = height
    return ob, height


def ground_mount(items, x, y, bottom=2.1, yaw=0.0, z0=0.0, posts=1, night=False, coll=None, gap=0.03):
    """Stack sign panels bottom-up (e.g. [tab, main] -> main on top) on
    galvanised round posts. items: list of (artwork, width_m), listed
    TOP to BOTTOM. Returns (objects, centre of the top sign)."""
    galv = C.mat("Galvanised", (0.56, 0.57, 0.58), 0.45, 1.0)
    objs = []
    z = z0 + bottom
    centres = []
    for art, width in reversed(items):
        p, h = panel(f"Sign_{len(objs)}", art, width, night, coll)
        p.location = (0, 0, z)
        objs.append(p)
        centres.append(z + h / 2)
        z += h + gap
    top = z - gap
    widest = max(w for _, w in items)
    xs = [0.0] if posts == 1 else [-widest * 0.3, widest * 0.3]
    for i, px in enumerate(xs):
        objs.append(C.cylinder(f"Post_{i}", 0.032, z0 - 0.4, top - 0.05, px, 0.04, galv, coll))
    rig = bpy.data.objects.new("SignRig", None)
    C.link(rig, coll)
    for o in objs + [rig]:
        o["g1_sign"] = 1          # removed when a cached scene swaps its sign
    for o in objs:
        o.parent = rig
    rig.location = (x, y, 0)
    rig.rotation_euler[2] = math.radians(yaw)
    # yaw turns the rig about its own post, so the centre's x/y don't move
    # (matrix_world isn't updated until the depsgraph runs, so compute it here)
    centre = Vector((x, y, centres[-1]))
    return objs, centre


ARM_R_BASE, ARM_R_TIP = 0.11, 0.06      # tapered mast arm radius at the pole / at the tip


def arm_radius(x, x_pole, x_tip):
    t = min(1.0, max(0.0, (x_pole - x) / max(1e-6, x_pole - x_tip)))
    return ARM_R_BASE + (ARM_R_TIP - ARM_R_BASE) * t


def clamp_band(x, y_arm, z_arm, r, coll=None, width=0.07):
    """Steel band wrapped around a round arm at x (arm runs along X)."""
    steel = C.mat("ClampSteel", (0.5, 0.51, 0.52), 0.4, 1.0)
    band = C.cylinder("ClampBand", r + 0.014, -width / 2, width / 2, 0, 0, steel, coll, 20)
    band.rotation_euler = (0, math.radians(90), 0)
    band.location = (x, y_arm, z_arm)
    return band


def chord_clamp(x, y0, y1, z0, z1, coll=None, width=0.07):
    """U-bolt bracket around a rectangular truss chord."""
    steel = C.mat("ClampSteel", (0.5, 0.51, 0.52), 0.4, 1.0)
    return C.box("ChordClamp", x - width / 2, x + width / 2, y0 - 0.015, y1 + 0.015, z0 - 0.015, z1 + 0.015, steel, coll)


def sign_straps(x_centre, width, y_back, z_panel_top, z_to, y_to, coll=None):
    """Two vertical mounting brackets on the back of a sign panel, from 0.2 m
    below its top edge up to z_to, deep enough (back to y_to(x)) to meet the
    clamp on the arm/chord. y_to: function x -> y of the clamp's front face."""
    steel = C.mat("ClampSteel", (0.5, 0.51, 0.52), 0.4, 1.0)
    xs = [x_centre - width * 0.3, x_centre + width * 0.3]
    for sx in xs:
        C.box("SignStrap", sx - 0.025, sx + 0.025, y_back, max(y_back + 0.012, y_to(sx) + 0.004),
              z_panel_top - 0.2, z_to, steel, coll)
    return xs


def overhead_span(x_left, x_right, y, items, sign_x=None, clearance=5.3, coll=None, night=False, mast=False,
                  top=None):
    """Signs hung from a horizontal mast arm or truss spanning the road.
    Ontario signalised intersections usually use a mast arm (mast=True)
    from a pole on the right; highway signs use a two-post truss.

    Mounting (same for every overhead scene): each panel hangs just in front
    of the arm/truss on two vertical straps that run from behind its top edge
    up to clamps wrapped around the arm (bands) or the truss chord (U-bolts).
    Returns (panels, centre of the last panel). The structure is described by
    a `span` dict (stored on the panels and returned by build_span) so a cached
    scene can hang different signs later with hang_signs()."""
    span = build_span(x_left, x_right, y, top if top is not None else clearance + max(_h(a, w) for a, w in items) + 0.25,
                      sign_x, mast, coll)
    return hang_signs(items, span, coll, night)


def build_span(x_left, x_right, y, top, sign_x=None, mast=False, coll=None):
    """The arm or truss itself (no signs). Returns the span description."""
    steel = C.mat("Galvanised", (0.56, 0.57, 0.58), 0.45, 1.0)
    y_arm = y + 0.3
    span = {"mast": mast, "x_left": x_left, "x_right": x_right, "y": y, "y_arm": y_arm, "top": top,
            "sign_x": (x_left + x_right) / 2 if sign_x is None else sign_x}
    if mast:
        C.cylinder("MastPole", 0.17, -0.5, top + 0.6, x_right, y_arm, steel, coll, 20, 0.13)
        arm = C.cylinder("MastArm", ARM_R_BASE, 0, x_right - x_left, 0, 0, steel, coll, 16, ARM_R_TIP)
        arm.rotation_euler = (0, math.radians(-90), 0)
        arm.location = (x_right, y_arm, top)
        span["y_panel"] = y_arm - ARM_R_BASE - 0.02 - 0.003   # panel back just clear of the thickest arm + band
    else:
        for px in (x_left, x_right):
            C.cylinder("TrussPost", 0.2, -0.5, top + 0.6, px, y_arm, steel, coll, 20)
        span["chords"] = []
        for dz in (0.0, 0.9):
            z0, z1 = top - 0.35 + dz, top - 0.2 + dz
            C.box("TrussChord", x_left, x_right, y + 0.22, y + 0.38, z0, z1, steel, coll)
            span["chords"].append((z0, z1))
        span["y_panel"] = y + 0.22 - 0.03 - 0.003
    return span


def hang_signs(items, span, coll=None, night=False):
    """Hang sign panels (with straps and clamps) on an existing span."""
    mast, x_left, x_right, y = span["mast"], span["x_left"], span["x_right"], span["y"]
    y_arm, top, y_panel = span["y_arm"], span["top"], span["y_panel"]
    objs, centre = [], None
    total_w = sum(w for _, w in items) + 0.3 * (len(items) - 1)
    cx = span["sign_x"] - total_w / 2
    before = set(bpy.data.objects)
    for i, (art, w) in enumerate(items):
        p, h = panel(f"OverheadSign_{i}", art, w, night, coll)
        xc = cx + w / 2
        z_top = top - 0.25
        p.location = (xc, y_panel, z_top - h)
        y_back = y_panel + 0.003
        if mast:
            xs = sign_straps(xc, w, y_back, z_top, top,
                             lambda sx: y_arm - arm_radius(sx, x_right, x_left) - 0.014, coll)
            for sx in xs:
                clamp_band(sx, y_arm, top, arm_radius(sx, x_right, x_left), coll)
        else:
            z_hi = span["chords"][1][1]
            xs = sign_straps(xc, w, y_back, z_top, z_hi, lambda sx: y + 0.22 - 0.015, coll)
            for sx in xs:
                for z0, z1 in span["chords"]:
                    chord_clamp(sx, y + 0.22, y + 0.38, z0, z1, coll)
        p["mount"] = "mast" if mast else "truss"
        p["arm_z"], p["arm_y"] = top, y_arm
        objs.append(p)
        centre = Vector((xc, y_panel, z_top - h / 2))
        cx += w + 0.3
    for o in set(bpy.data.objects) - before:
        o["g1_sign"] = 1
    import json
    bpy.context.scene["g1_span"] = json.dumps(span)    # lets a cached scene re-hang signs
    return objs, centre


def _h(art, width):
    img = artwork(art)
    return width * img.size[1] / img.size[0]


def on_surface(name, art, width, loc, rot=(0, 0, 0), coll=None):
    """Artwork stuck on a surface (e.g. SMV triangle on a wagon). Faces -Y."""
    p, h = panel(name, art, width, coll=coll)
    p.location = loc
    p.rotation_euler = rot
    return p


def decal(name, art, length, loc, heading=0.0, coll=None):
    """Pavement marking from artwork (e.g. sharrow), lying flat on the road,
    reading toward +Y."""
    p, h = panel(name, art, length, coll=coll)
    p.rotation_euler = (math.radians(-90), 0, math.radians(heading))
    p.location = loc
    return p
