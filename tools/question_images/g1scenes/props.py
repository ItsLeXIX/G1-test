"""Scenery and vehicles, all procedural and low-poly.

These are deliberately simple so previews stay light. For final renders on
a stronger PC, drop real models into ../assets/ (see README) and they are
used instead of the procedural stand-ins.
"""
import math
import os

import bpy
from mathutils import Vector

from . import common as C
from . import realism

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _asset(name):
    for ext in (".glb", ".gltf", ".blend"):
        p = os.path.join(ASSET_DIR, name + ext)
        if os.path.exists(p):
            return p
    return None


def import_asset(name, coll=None):
    """Import assets/<name>.glb|.blend if present; returns a root empty or None."""
    p = _asset(name)
    if not p:
        return None
    before = set(bpy.data.objects)
    if p.endswith(".blend"):
        with bpy.data.libraries.load(p, link=False) as (src, dst):
            dst.objects = src.objects
        for o in dst.objects:
            C.link(o, coll)
    else:
        bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name + "_root", None)
    C.link(root, coll)
    for o in new:
        if o.parent is None:
            o.parent = root
    return root


# ------------------------------------------------------------------ trees

def _leaf_mat(name, color):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*[c * 0.7 for c in color], 1)
    ramp.color_ramp.elements[1].color = (*color, 1)
    # leaf-scale speckle: colour variation + bump so the canopy isn't smooth
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 9.0
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    nt.links.new(oi.outputs["Random"], mix.inputs["A"])
    nt.links.new(vor.outputs["Distance"], mix.inputs["B"])
    mix.inputs["Factor"].default_value = 0.6
    nt.links.new(mix.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.08
    nt.links.new(vor.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    C.set_input(b, "Roughness", 0.8)
    C.set_input(b, "Subsurface Weight", 0.15)
    return m


_TREE_PROTOS = {}


def _tree_proto(kind, snow=0.0):
    """One shared mesh per tree kind; every tree is a linked duplicate."""
    key = (kind, snow > 0)
    if key in _TREE_PROTOS:
        return _TREE_PROTOS[key]
    bark = C.mat("Bark", (0.16, 0.12, 0.09), 0.9)
    if kind == "conifer":
        leaf = _leaf_mat("Needles" + ("_snow" if snow else ""), (0.04, 0.09, 0.04) if not snow else (0.55, 0.6, 0.6))
        parts = [C.cylinder("t", 0.18, 0, 3, mat=bark, seg=8)]
        for i, (r, z0, z1) in enumerate(((2.4, 1.5, 6), (1.9, 4, 8.5), (1.3, 6.5, 10.5), (0.7, 9, 12.5))):
            parts.append(C.cylinder("c", r, z0, z1, mat=leaf, seg=10, r_top=0.05))
    else:
        leaf = _leaf_mat("Leaves", (0.06, 0.14, 0.03))
        if snow:  # bare deciduous tree in winter
            leaf = C.mat("BareTwigs", (0.14, 0.11, 0.09), 0.9)
        parts = [C.cylinder("t", 0.25, 0, 4.2, mat=bark, seg=10, r_top=0.16)]
        r = C.rng(11)
        tx = bpy.data.textures.new("lump", "CLOUDS")
        tx.noise_scale = 0.35
        tx.noise_depth = 3
        # many small clumps on a rough dome read as foliage, not as balls
        for i in range(22):
            a = r.uniform(0, 6.28)
            rad = r.uniform(0.3, 2.6)
            z = r.uniform(4.2, 8.0) - 0.25 * rad
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r.uniform(0.9, 1.5),
                                                  location=(rad * math.cos(a), rad * math.sin(a), z))
            s = bpy.context.object
            s.data.materials.append(leaf)
            s.scale = (1, 1, r.uniform(0.7, 0.9))
            d = s.modifiers.new("lumps", "DISPLACE")
            d.texture = tx
            d.strength = 0.9
            d.mid_level = 0.5
            bpy.ops.object.modifier_apply(modifier=d.name)
            for p in s.data.polygons:
                p.use_smooth = True
            parts.append(s)
    for p in parts:
        for c in p.users_collection:
            c.objects.unlink(p)
        bpy.context.scene.collection.objects.link(p)
    proto = C.to_bmesh_join(parts, f"TreeProto_{kind}")
    proto.hide_render = True
    proto.hide_viewport = True
    _TREE_PROTOS[key] = proto
    return proto


def tree(x, y, z=0.0, kind="deciduous", scale=1.0, seed=0, snow=0.0, coll=None):
    if kind == "deciduous" and not snow and realism.has("tree_deciduous"):
        r = C.rng(seed)
        # the model is an ~10 m street tree (linden)
        return realism.instance("tree_deciduous", (x, y, z), r.uniform(0, 360), scale * r.uniform(0.8, 1.05), coll)
    proto = _tree_proto(kind, snow)
    ob = bpy.data.objects.new("Tree", proto.data)
    C.link(ob, coll)
    r = C.rng(seed)
    s = scale * r.uniform(0.85, 1.15)
    ob.scale = (s, s, s * r.uniform(0.9, 1.1))
    ob.location = (x, y, z)
    ob.rotation_euler[2] = r.uniform(0, 6.28)
    return ob


def tree_row(path, offset, d0, d1, spacing, kind="deciduous", seed=1, skip=(), snow=0.0, coll=None, jitter=1.0):
    """Trees along the road. skip: [(d0, d1)] to keep sightlines to signs."""
    r = C.rng(seed)
    d = d0 + r.uniform(0, spacing)
    while d < d1:
        if not any(a <= d <= b for a, b in skip):
            i = path.index_at(d)
            x, y, z = path.offset(i, offset + r.uniform(-jitter, jitter) * 0.3)
            tree(x, y, z + 0.12, kind, r.uniform(0.9, 1.2), r.randint(0, 999), snow, coll)
        d += spacing * r.uniform(0.8, 1.25)


# ----------------------------------------------------------------- houses

def house(x, y, side, seed, coll=None, snow=0.0, curb_x=None):
    """Two-storey Ontario suburban house, gable roof, facing the road."""
    r = C.rng(seed)
    walls = [(0.42, 0.4, 0.36), (0.3, 0.22, 0.17), (0.33, 0.35, 0.37), (0.36, 0.17, 0.12), (0.5, 0.46, 0.38)]
    if realism.enabled():
        # horizontal-groove cladding reads as Ontario siding; tinted per house
        wall = realism.wall("siding", tuple(min(1.0, c * 2.0) for c in walls[seed % 5]))
    else:
        wall = C.mat(f"HouseWall{seed % 5}", walls[seed % 5], 0.85)
    roof = C.mat("RoofSnow" if snow else f"Roof{seed % 2}", (0.8, 0.82, 0.86) if snow else ((0.07, 0.07, 0.08), (0.17, 0.13, 0.11))[seed % 2], 0.8)
    glass = C.mat("Glass", (0.03, 0.04, 0.05), 0.08)
    w, d, h, rh = r.uniform(9, 12), r.uniform(9, 11), r.uniform(5.6, 6.4), r.uniform(2.3, 3.0)
    xs, ys = (x - w / 2, x + w / 2), (y - d / 2, y + d / 2)
    v = [(xx, yy, zz) for zz in (0, h) for yy in ys for xx in xs]
    v += [(x, ys[0], h + rh), (x, ys[1], h + rh)]
    f = [(0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5), (4, 5, 8), (7, 6, 9), (4, 8, 9, 6), (5, 7, 9, 8)]
    ob = C.mesh_object("House", v, f, [wall, roof], coll, face_mats=[0, 0, 0, 0, 0, 0, 1, 1])
    face_x = xs[0] - 0.03 if side > 0 else xs[1] + 0.03
    for wy in (y - d / 4, y + d / 4):
        for wz in (1.0, 3.7):
            C.box("Window", face_x - 0.04, face_x + 0.04, wy - 0.65, wy + 0.65, wz, wz + 1.25, glass, coll)
    C.box("Door", face_x - 0.04, face_x + 0.04, y - 0.45, y + 0.45, 0, 2.1, C.mat("Door", (0.25, 0.1, 0.06), 0.6), coll)
    # driveway from the house to the curb (stops at the road edge)
    if curb_x is not None:
        drive_x0, drive_x1 = sorted((face_x, curb_x))
        C.box("Driveway", drive_x0, drive_x1, y + d / 2 - 3.2, y + d / 2 - 0.2, 0.0, 0.155, C.asphalt(0, snow), coll)
    return ob


def house_rows(cfg, d0=8, d1=260, seed=5, coll=None, snow=0.0, skip_right=(), skip_left=()):
    """Detailed houses (see houses.py)."""
    from . import houses
    return houses.house_rows(cfg, d0, d1, seed, coll, snow, skip_right, skip_left)


def city_block(x_face, y0, y1, side, seed, coll=None, height=(10, 24)):
    """Row of mid-rise buildings with their facade on x = x_face."""
    r = C.rng(seed)
    walls = [(0.42, 0.3, 0.24), (0.55, 0.52, 0.46), (0.32, 0.3, 0.29), (0.6, 0.58, 0.55), (0.38, 0.2, 0.15)]
    y = y0
    i = 0
    while y < y1:
        w = r.uniform(12, 24)
        h = r.uniform(*height)
        wall = walls[r.randint(0, 4)]
        m = C.facade(f"Facade{seed}_{i}", wall)
        x0, x1 = (x_face, x_face + 18) if side > 0 else (x_face - 18, x_face)
        C.box("Building", x0, x1, y, y + w - 0.4, 0, h, m, coll)
        # ground-floor storefront band + cornice
        gx = x_face - side * 0.05
        if realism.enabled():
            # glazed storefront: concrete base, reflective glass, dark mullions
            # (the old flat near-black slab read as a black strip)
            y0s, y1s = y + 0.5, y + w - 0.9
            out = lambda d: (min(gx, gx - side * d), max(gx, gx - side * d))  # noqa: E731
            C.box("ShopBase", *out(0.14), y0s, y1s, 0.0, 0.55, realism.concrete(0.0, "PH_ShopBase"), coll)
            C.box("ShopGlass", *out(0.08), y0s, y1s, 0.55, 3.0, realism.glass(), coll)
            frame = C.mat("ShopFrame", (0.06, 0.065, 0.07), 0.35, 1.0)
            C.box("ShopHead", *out(0.16), y0s, y1s, 3.0, 3.25, frame, coll)
            k = y0s
            while k <= y1s + 1e-6:
                C.box("Mullion", *out(0.12), k - 0.04, k + 0.04, 0.55, 3.0, frame, coll)
                k += 2.4
        else:
            C.box("Storefront", min(gx, gx - side * 0.1), max(gx, gx - side * 0.1), y + 0.5, y + w - 0.9, 0.15, 3.2,
                  C.mat("Storefront", (0.05, 0.06, 0.07), 0.25), coll)
        C.box("Cornice", min(gx, gx - side * 0.4), max(gx, gx - side * 0.4), y, y + w - 0.4, h - 0.5, h,
              C.mat(f"Cornice{i % 3}", tuple(c * 0.8 for c in wall), 0.8), coll)
        y += w
        i += 1


# --------------------------------------------------------------- vehicles

CAR_COLOURS = {
    "white": (0.75, 0.76, 0.77), "silver": (0.45, 0.46, 0.48), "red": (0.45, 0.03, 0.03),
    "blue": (0.03, 0.08, 0.3), "vivid_blue": (0.01, 0.09, 0.62), "vivid_red": (0.62, 0.015, 0.012), "black": (0.02, 0.02, 0.02), "grey": (0.15, 0.16, 0.17),
}


def car(x, y, heading=0.0, colour="silver", kind="sedan", coll=None, brake=False, recolour=False):
    """Generic, unbranded car (no logos). Origin at ground centre; front
    toward +Y at heading 0. kind: sedan | suv. recolour=True paints the real
    model in `colour` (otherwise the model keeps its own paint)."""
    if realism.has(f"car_{kind}"):
        rgb = CAR_COLOURS.get(colour, colour if isinstance(colour, tuple) else None) if recolour else None
        return realism.instance(f"car_{kind}", (x, y, 0), heading, 1.0, coll, paint=rgb)
    root = import_asset(f"car_{kind}", coll)
    if root:
        root.location, root.rotation_euler[2] = (x, y, 0), math.radians(heading)
        return root
    body = C.car_paint(f"Car_{colour}", CAR_COLOURS.get(colour, colour if isinstance(colour, tuple) else (0.5, 0.5, 0.5)))
    glass = C.mat("CarGlass", (0.02, 0.025, 0.03), 0.05, Specular_IOR_Level=0.8)
    tyre = C.mat("Tyre", (0.02, 0.02, 0.02), 0.8)
    rim = C.mat("Rim", (0.5, 0.5, 0.52), 0.3, 1.0)
    trim = C.mat("Trim", (0.03, 0.03, 0.03), 0.5)
    tail = C.emissive("TailLight" + ("On" if brake else ""), (0.6, 0.02, 0.01), 6.0 if brake else 0.3)
    plate = C.mat("Plate", (0.85, 0.86, 0.88), 0.4)
    L, W = (4.7, 1.86) if kind == "sedan" else (4.6, 1.9)
    sill, belt, roof = (0.32, 0.95, 1.45) if kind == "sedan" else (0.42, 1.1, 1.7)
    parts = [C.box("Body", -W / 2, W / 2, -L / 2, L / 2, sill, belt, body)]
    bevel(parts[-1], 0.12, 3)
    cab_front, cab_back = (L * 0.18, -L * 0.3) if kind == "sedan" else (L * 0.22, -L * 0.42)
    cab = C.mesh_object("Cabin", [
        (-W / 2 + 0.06, cab_back, belt), (W / 2 - 0.06, cab_back, belt), (W / 2 - 0.06, cab_front, belt), (-W / 2 + 0.06, cab_front, belt),
        (-W / 2 + 0.18, cab_back + 0.35, roof), (W / 2 - 0.18, cab_back + 0.35, roof), (W / 2 - 0.18, cab_front - 0.55, roof), (-W / 2 + 0.18, cab_front - 0.55, roof),
    ], [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)], [glass, body], face_mats=[0, 0, 0, 0, 1])
    bevel(cab, 0.05, 2)
    parts.append(cab)
    for sx in (-1, 1):
        for sy, wy in ((1, L * 0.32), (-1, -L * 0.3)):
            t = C.cylinder("Tyre", 0.34, -0.12, 0.12, mat=tyre, seg=24)
            t.rotation_euler = (0, math.radians(90), 0)
            t.location = (sx * (W / 2 - 0.12), wy, 0.34)
            parts.append(t)
            rr = C.cylinder("Rim", 0.22, -0.125, 0.125, mat=rim, seg=16)
            rr.rotation_euler = (0, math.radians(90), 0)
            rr.location = t.location
            parts.append(rr)
    for sx in (-1, 1):
        parts.append(C.box("Tail", sx * W / 2 - (0.38 if sx > 0 else -0.06), sx * W / 2 + (-0.06 if sx > 0 else 0.38),
                           -L / 2 - 0.02, -L / 2 + 0.05, belt - 0.22, belt - 0.05, tail))
    parts.append(C.box("Plate", -0.26, 0.26, -L / 2 - 0.03, -L / 2, sill + 0.12, sill + 0.27, plate))
    parts.append(C.box("Bumper", -W / 2 + 0.05, W / 2 - 0.05, -L / 2 - 0.06, -L / 2 + 0.2, sill - 0.05, sill + 0.08, trim))
    root = bpy.data.objects.new("Car", None)
    C.link(root, coll)
    for p in parts:
        for c in p.users_collection:
            c.objects.unlink(p)
        C.link(p, coll)
        p.parent = root
    root.location = (x, y, 0)
    root.rotation_euler[2] = math.radians(heading)
    return root


def bevel(ob, w, s):
    C.bevel(ob, w, s)


def hay_wagon(x, y, coll=None):
    """Farm wagon with round bales, seen from behind (slow-moving vehicle).
    Returns (root, world point for the SMV emblem)."""
    root = import_asset("farm_wagon", coll)
    if root:
        root.location = (x, y, 0)
        return root, Vector((x, y - 2.6, 1.0))
    wood = C.mat("WagonWood", (0.32, 0.22, 0.14), 0.85)
    steel = C.mat("WagonSteel", (0.12, 0.25, 0.1), 0.5, 0.5)
    tyre = C.mat("Tyre", (0.02, 0.02, 0.02), 0.8)
    hay = C.mat("Hay", (0.55, 0.45, 0.22), 0.95)
    parts = [C.box("Deck", -1.25, 1.25, -2.5, 2.5, 0.85, 1.0, wood),
             C.box("Frame", -1.1, 1.1, -2.45, 2.45, 0.65, 0.85, steel)]
    for sx in (-1, 1):
        for wy in (-1.6, 1.6):
            t = C.cylinder("Tyre", 0.42, -0.15, 0.15, mat=tyre, seg=24)
            t.rotation_euler = (0, math.radians(90), 0)
            t.location = (sx * 1.0, wy, 0.42)
            parts.append(t)
    for bx in (-0.62, 0.62):
        for by in (-1.5, 0.0, 1.5):
            b = C.cylinder("Bale", 0.65, -0.6, 0.6, mat=hay, seg=24)
            b.rotation_euler = (0, math.radians(90), 0)
            b.location = (bx, by, 1.65)
            parts.append(b)
    root = bpy.data.objects.new("Wagon", None)
    C.link(root, coll)
    for p in parts:
        p.parent = root
    root.location = (x, y, 0)
    return root, Vector((x, y - 2.51, 1.0))


def _skin_object(name, chains, mat, smooth_levels=2):
    """Organic limb from skeleton polylines with the Skin modifier + subdivision.
    chains: [[(point Vector, (rx, ry)), ...], ...] each chain a connected limb."""
    verts, edges, radii, roots = [], [], [], []
    for ch in chains:
        base = len(verts)
        roots.append(base)
        for k, (p, r) in enumerate(ch):
            verts.append(tuple(p))
            radii.append(r)
            if k:
                edges.append((base + k - 1, base + k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, edges, [])
    me.update()
    ob = bpy.data.objects.new(name, me)
    C.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.mesh.customdata_skin_add()
    for i, r in enumerate(radii):
        sv = me.skin_vertices[0].data[i]
        sv.radius = r
        sv.use_root = i in roots
    sk = ob.modifiers.new("Skin", "SKIN")
    sk.use_smooth_shade = True
    sk.branch_smoothing = 0.6
    ss = ob.modifiers.new("Subsurf", "SUBSURF")
    ss.levels, ss.render_levels = smooth_levels, smooth_levels + 1
    me.materials.append(mat)
    ob.select_set(False)
    return ob


def skin_material():
    """Human skin: sRGB ~ (196, 140, 108), subsurface scattering, soft sheen."""
    m = bpy.data.materials.get("Skin")
    if m:
        return m
    m = C.mat("Skin", (0.55, 0.27, 0.17), 0.5, Subsurface_Weight=0.35, Specular_IOR_Level=0.35)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    C.set_input(b, "Subsurface Radius", (1.0, 0.35, 0.2))
    C.set_input(b, "Subsurface Scale", 0.025)
    C.set_input(b, "Coat Weight", 0.0)
    return m


def driver_arm(car_root, pose="left", coll=None):
    """Driver's LEFT arm out of the fully lowered driver's window (Canada: driver
    sits on the left, -X in car space; front +Y). MTO hand signals: left = arm
    straight out; right = forearm up; slow/stop = forearm down.

    Built from a skeleton with the Skin modifier (smooth organic limbs, not
    cylinders): short sleeve over the upper arm and shoulder, bare forearm,
    wrist, a flattened palm and four fingers + thumb with three joints each.
    The driver's torso, neck and head sit in the seat behind the arm."""
    skin = skin_material()
    cloth = C.mat("ShirtSleeve", (0.07, 0.14, 0.30), 0.85)
    V = Vector
    S = V((-0.58, 0.18, 1.06))                      # left shoulder joint, at the window frame
    out = V((-1.0, 0.0, 0.0))
    up_len, fore_len = 0.30, 0.26
    elbow = S + out * up_len + V((0, 0, -0.02))
    if pose == "left":                              # arm straight out, palm down
        fdir, pn = out.copy(), V((0, 0, -1))
    elif pose == "right":                           # forearm up, palm forward
        fdir, pn = V((-0.12, 0, 1.0)).normalized(), V((0, 1, 0))
    else:                                           # forearm down along the door, palm back toward traffic behind
        fdir, pn = V((-0.12, 0, -1.0)).normalized(), V((0, -1, 0))
    wrist = elbow + fdir * fore_len
    parts = []
    # arm: shoulder -> elbow -> wrist, tapering like a real arm
    mid_u = S + (elbow - S) * 0.5
    mid_f = elbow + (wrist - elbow) * 0.5
    arm = [(S, (0.046, 0.046)), (S + (elbow - S) * 0.25, (0.046, 0.046)), (mid_u, (0.044, 0.044)),
           (elbow, (0.039, 0.039)), (elbow + (wrist - elbow) * 0.22, (0.040, 0.040)), (mid_f, (0.034, 0.034)),
           (wrist - fdir * 0.05, (0.028, 0.028)), (wrist, (0.025, 0.021))]
    parts.append(_skin_object("DriverArm", [arm], skin))
    # short sleeve over the shoulder and the upper arm (shirt cloth)
    sl = [(S - out * 0.03, (0.066, 0.066)), (S + out * 0.06, (0.062, 0.062)), (S + out * 0.17, (0.058, 0.058)),
          (S + out * 0.215, (0.060, 0.060))]
    parts.append(_skin_object("DriverSleeve", [sl], cloth))
    # hand: flattened palm + fingers (index on the thumb side) + thumb
    t = -(fdir.cross(pn)).normalized()              # thumb side of a LEFT hand
    pn = t.cross(fdir).normalized() * -1 if False else pn
    palm_c = wrist + fdir * 0.050
    palm = bpy.data.objects.new("DriverPalm", bpy.data.meshes.new("DriverPalm"))
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
    bm.to_mesh(palm.data)
    bm.free()
    for p_ in palm.data.polygons:
        p_.use_smooth = True
    from mathutils import Matrix
    basis = Matrix((t, fdir, pn)).transposed()      # local x=across the palm, y=fingers, z=palm normal
    palm.matrix_world = Matrix.Translation(palm_c) @ basis.to_4x4() @ Matrix.Diagonal((0.0425, 0.052, 0.0135, 1.0))
    palm.data.materials.append(skin)
    C.link(palm)
    parts.append(palm)
    knuckle = wrist + fdir * 0.092
    curl = pn * -1.0                                # fingers curl a little toward the palm side
    chains = []
    spec = (("index", 0.032, 0.078, 0.0105), ("middle", 0.011, 0.086, 0.0108), ("ring", -0.011, 0.080, 0.0102),
            ("little", -0.032, 0.063, 0.0092))
    for nm, off, ln, r in spec:
        p0 = knuckle + t * off
        d = (fdir + t * (off * 1.4)).normalized()   # slight natural spread
        pts = [(p0 - fdir * 0.008, (r, r))]
        cur = p0
        for seg, frac, rr in ((0, 0.50, r), (1, 0.30, r * 0.92), (2, 0.20, r * 0.78)):
            bend = (seg * 0.16)
            dd = (d + curl * bend).normalized()
            cur = cur + dd * ln * frac
            pts.append((cur, (rr, rr)))
        chains.append(pts)
    # thumb: leaves the side of the palm, splayed away from the fingers
    p0 = wrist + fdir * 0.026 + t * 0.034
    d = (fdir * 0.55 + t * 0.85).normalized()
    th = [(p0, (0.0125, 0.0125))]
    cur = p0
    for frac, rr in ((0.032, 0.0122), (0.028, 0.0108), (0.024, 0.0092)):
        cur = cur + (d + curl * 0.08).normalized() * frac
        th.append((cur, (rr, rr)))
    chains.append(th)
    parts.append(_skin_object("DriverFingers", chains, skin))
    # the driver: torso in the seat, neck and head (seen through the tinted rear glass)
    shirt = C.mat("DriverShirt", (0.07, 0.14, 0.30), 0.85)
    torso = [(V((-0.38, 0.12, 0.55)), (0.17, 0.11)), (V((-0.38, 0.14, 0.78)), (0.20, 0.11)), (V((-0.38, 0.16, 0.97)), (0.21, 0.10))]
    parts.append(_skin_object("DriverTorso", [torso], shirt, 2))
    # head and neck: a skin ellipsoid with a dark hair cap over the top and back (seen from behind)
    parts.append(_skin_object("DriverNeck", [[(V((-0.54, 0.34, 0.98)), (0.045, 0.045)), (V((-0.54, 0.34, 1.06)), (0.042, 0.042))]], skin))
    hair = C.mat("DriverHair", (0.03, 0.022, 0.016), 0.7)
    parts.append(_ellipsoid("DriverHead", (-0.56, 0.36, 1.17), (0.088, 0.105, 0.118), skin))
    parts.append(_ellipsoid("DriverHair", (-0.56, 0.345, 1.185), (0.094, 0.108, 0.118), hair))
    # the arm and hand must not be mirrored in the tinted rear side glass (that read as a second hand)
    for p_ in parts:
        if p_.name.startswith(("DriverArm", "DriverSleeve", "DriverPalm", "DriverFingers")):
            p_.visible_glossy = False
    for p_ in parts:
        p_.parent = car_root
    return parts


def _ellipsoid(name, centre, radii, mat):
    import bmesh
    from mathutils import Matrix
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=16, radius=1.0)
    bm.to_mesh(ob.data)
    bm.free()
    for p_ in ob.data.polygons:
        p_.use_smooth = True
    ob.matrix_world = Matrix.Translation(Vector(centre)) @ Matrix.Diagonal((*radii, 1.0))
    ob.data.materials.append(mat)
    C.link(ob)
    return ob


# -------------------------------------------------------- road furniture

SIGNAL_LIT = {"red": (1.0, 0.004, 0.0), "amber": (1.0, 0.3, 0.0), "green": (0.0, 1.0, 0.22)}


def lens_material(colr, on):
    """Signal lens: saturated emissive when lit (black base, no specular, so sky
    reflections can't wash it toward white), dim tinted glass when off."""
    if on:
        m = C.mat(f"Lens_{colr}_on", (0, 0, 0), 0.4, Specular_IOR_Level=0.0,
                  Emission_Color=(*SIGNAL_LIT[colr], 1), Emission_Strength=1.6)
        # C.mat reuses a material by name (e.g. one saved in a cached .blend):
        # always re-apply the current colour
        C.set_input(C._bsdf(m), "Emission Color", (*SIGNAL_LIT[colr], 1))
        return m
    # unlit lens: near-black glass with a faint tint, no emission, no specular
    # (reads as a dark, switched-off lens even in a night scene)
    dark = tuple(c * 0.006 + 0.003 for c in SIGNAL_LIT[colr])
    m = C.mat(f"LensOff_{colr}", dark, 0.55, Specular_IOR_Level=0.0)
    C.set_input(C._bsdf(m), "Base Color", (*dark, 1))
    C.set_input(C._bsdf(m), "Emission Strength", 0.0)
    return m


def set_signal_state(state):
    """Re-light every signal head in the scene (used on cached scenes)."""
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.name.startswith("Lens") or not o.material_slots:
            continue
        name = o.material_slots[0].material.name if o.material_slots[0].material else ""
        colr = next((c for c in SIGNAL_LIT if c in name), None)
        if colr:
            o.material_slots[0].material = lens_material(colr, colr == state)


def traffic_signal(x, y, z_bottom=5.2, state="green", coll=None, yaw=0.0, hang=None):
    """Vertical 3-section signal head (red/amber/green), facing -Y.
    hang=(y_arm, z_arm, r_arm): hang the head from a mast arm with a vertical
    pipe hanger and a clamp band around the arm (Ontario rigid mount)."""
    housing = C.mat("SignalHousing", (0.02, 0.02, 0.02), 0.6)
    backplate = C.mat("SignalBackplate", (0.02, 0.02, 0.02), 0.7)
    yb = C.mat("BackplateBorder", (0.85, 0.65, 0.05), 0.5)  # Ontario retroreflective yellow border
    # strength 2 under the Standard view: the dominant channel clips, the hue stays
    # (strength 25 clipped every channel and a red lamp rendered yellow-white)
    lit = {"red": (1.0, 0.004, 0.0), "amber": (1.0, 0.3, 0.0), "green": (0.0, 1.0, 0.55)}
    parts = [C.box("BackplateEdge", -0.42, 0.42, 0.06, 0.07, z_bottom - 0.12, z_bottom + 1.12, yb, coll),
             C.box("Backplate", -0.38, 0.38, 0.055, 0.065, z_bottom - 0.08, z_bottom + 1.08, backplate, coll),
             C.box("Housing", -0.18, 0.18, -0.2, 0.06, z_bottom, z_bottom + 1.0, housing, coll)]
    for k, colr in enumerate(("green", "amber", "red")):
        on = colr == state
        lens = lens_material(colr, on)
        ln = C.cylinder("Lens", 0.13, 0.2, 0.23, 0, 0, lens, coll, 20)
        ln.rotation_euler = (math.radians(90), 0, 0)
        ln.location = (0, -0.0, z_bottom + 0.17 + k * 0.33)
        parts.append(ln)
    root = bpy.data.objects.new("Signal", None)
    C.link(root, coll)
    for p in parts:
        p.parent = root
    root.location = (x, y, 0)
    root.rotation_euler[2] = math.radians(yaw)
    if hang:
        from . import signs as S
        y_arm, z_arm, r_arm = hang
        steel = C.mat("ClampSteel", (0.5, 0.51, 0.52), 0.4, 1.0)
        # top cap plate on the housing, pipe hanger up to the arm, band around it
        C.box("HangerPlate", x - 0.14, x + 0.14, y_arm - 0.12, y_arm + 0.06, z_bottom + 1.0, z_bottom + 1.04, steel, coll)
        C.cylinder("SignalHanger", 0.035, z_bottom + 1.0, z_arm, x, y_arm, steel, coll, 12)
        S.clamp_band(x, y_arm, z_arm, r_arm, coll, width=0.09)
    return root


def signal_mast(x_pole, y, heads_x, state="green", coll=None, height=6.2):
    """Ontario-style mast arm from a pole on the right with signal heads
    hanging over the lanes (heads_x = x of each head)."""
    steel = C.mat("Galvanised", (0.56, 0.57, 0.58), 0.45, 1.0)
    C.cylinder("SignalPole", 0.17, -0.5, height + 0.8, x_pole, y + 0.3, steel, coll, 20, 0.13)
    reach = x_pole - min(heads_x) + 0.6
    arm = C.cylinder("SignalArm", 0.11, 0, reach, 0, 0, steel, coll, 16, 0.06)
    arm.rotation_euler = (0, math.radians(-90), 0)
    arm.location = (x_pole, y + 0.3, height)
    from . import signs as S
    x_tip = x_pole - reach
    for hx in heads_x:
        traffic_signal(hx, y + 0.25, height - 1.15, state, coll,
                       hang=(y + 0.3, height, S.arm_radius(hx, x_pole, x_tip)))
    traffic_signal(x_pole - 0.05, y, 2.7, state, coll)   # near-side head on the pole


def streetlight(x, y, side=1, coll=None, on=False):
    pole = C.mat("Galvanised", (0.56, 0.57, 0.58), 0.45, 1.0)
    C.cylinder("LightPole", 0.11, 0, 9.0, x, y, pole, coll, 12, 0.07)
    C.box("LightArm", min(x, x - side * 2.2), max(x, x - side * 2.2), y - 0.05, y + 0.05, 8.9, 9.0, pole, coll)
    head = C.box("Luminaire", x - side * 2.2 - 0.35, x - side * 2.2 + 0.35, y - 0.18, y + 0.18, 8.75, 8.92,
                 C.emissive("LED", (1.0, 0.9, 0.75), 30.0) if on else C.mat("LuminaireOff", (0.4, 0.4, 0.42), 0.4), coll)
    if on:
        ld = bpy.data.lights.new("StreetLamp", "SPOT")
        ld.energy = 3500
        ld.spot_size = math.radians(120)
        ld.color = (1.0, 0.88, 0.72)
        lo = C.link(bpy.data.objects.new("StreetLamp", ld), coll)
        lo.location = (x - side * 2.2, y, 8.7)
    return head


def cone(x, y, coll=None):
    o = C.mat("ConeOrange", (0.9, 0.22, 0.02), 0.5)
    w = C.mat("ConeBand", (0.9, 0.9, 0.9), 0.3)
    C.box("ConeBase", x - 0.22, x + 0.22, y - 0.22, y + 0.22, 0, 0.03, C.mat("ConeBaseBlack", (0.02, 0.02, 0.02), 0.8), coll)
    C.cylinder("Cone", 0.15, 0.03, 0.72, x, y, o, coll, 16, 0.03)
    C.cylinder("ConeBand", 0.115, 0.36, 0.5, x, y, w, coll, 16, 0.085)


def _rock_material():
    try:
        return realism.pbr("PH_RockCut", "rock_face_03", 2.7, tint=(0.95, 0.97, 1.0), darken=0.8, normal=1.8, saturation=0.35)
    except Exception:
        return C.mat("Rock", (0.16, 0.15, 0.15), 0.9)


def rock_cut(path, d0, d1, offset, height=15.0, coll=None, seed=3, side=1):
    """Blasted rock cut beside the road, like a highway through the Canadian
    Shield: a tall stepped face (three lifts separated by narrow benches, each
    lift leaning back a little, so it never overhangs) rising from below grade
    at its foot, then a wooded plateau behind it. The foot is buried 0.35 m, so
    there is no gap under it, and its ends taper into the terrain over 25 m.
    The face carries the Poly Haven rock_face_03 texture plus two displacement
    layers (large blocks, small fractures). Fallen rocks lie on the shoulder
    and at the foot. offset = where the foot meets the ground; side = +1 right."""
    rock = _rock_material()
    r = C.rng(seed)
    i0, i1 = path.index_at(d0), path.index_at(d1)
    # profile across the cut: (distance from offset, height). Lifts + benches. It varies along the
    # road (irregular top edge, leaning face, benches that widen and narrow) so the cut is not a
    # uniform wall.
    top = height

    def prof_row(i):
        nz = 0.5 * math.sin(i * 0.045 + 1.3) + 0.3 * math.sin(i * 0.11 + 0.7) + 0.2 * math.sin(i * 0.23 + 2.1)
        hv = 1.0 + 0.2 * nz                               # top edge rises and falls +-20 %
        lean = 0.14 + 0.16 * (0.5 + 0.5 * math.sin(i * 0.07 + 0.4) * math.cos(i * 0.021))
        bench = 1.0 + 2.4 * (0.5 + 0.5 * math.sin(i * 0.05 + 2.2))
        tp = top * hv
        lifts = [(0.3, tp * 0.36), (tp * 0.36, tp * 0.70), (tp * 0.70, tp)]
        pr = [(0.0, -0.35)]
        lat = 0.0
        fi = []
        for li, (z0, z1) in enumerate(lifts):
            steps = 7
            for k in range(steps + 1):
                z = z0 + (z1 - z0) * k / steps
                fi.append(len(pr))
                pr.append((lat + lean * (z - z0), z))
            lat += lean * (z1 - z0)
            if li < len(lifts) - 1:
                lat += bench * (0.7 + 0.6 * li)               # ledge between lifts, different width each time
                fi.append(len(pr))
                pr.append((lat, z1))
        lat_top = lat
        pr += [(lat + 0.8, tp + 0.5), (lat + 9.0, tp + 1.2), (lat + 28.0, tp + 1.8), (lat + 28.0, -0.35)]
        return pr, fi, lat_top

    prof0, face_idx, _ = prof_row(i0)
    npf = len(prof0)
    verts, faces = [], []
    idx = list(range(i0, i1 + 1, 2))
    ramp = 25.0                                    # taper into the terrain at both ends
    tops = []
    for a, i in enumerate(idx):
        dd = min(i - i0, i1 - i)
        hf = max(0.04, min(1.0, dd / ramp))
        hf = hf * hf * (3 - 2 * hf)                 # smoothstep: no vertical end wall
        prof, _fi, lat_top = prof_row(i)
        tops.append((i, lat_top, hf))
        for k, (o, z) in enumerate(prof):
            z2 = -0.35 + (z + 0.35) * hf if z > -0.35 else z
            jit = jz = 0.0
            if k in face_idx and k not in (face_idx[0], face_idx[-1]):
                jit = r.uniform(-0.28, 0.28)        # blasted, uneven face
                jz = r.uniform(-0.2, 0.2)
            verts.append(path.offset(i, offset + side * (o * (0.35 + 0.65 * hf) + jit), z2 + jz))
    for a in range(len(idx) - 1):
        for k in range(npf - 1):
            p = a * npf + k
            q = (p, p + npf, p + npf + 1, p + 1)
            faces.append(q if side > 0 else q[::-1])
        p = a * npf + npf - 1                       # back wall down to the foot
        q = (p, p + npf, a * npf + npf, a * npf)
        faces.append(q if side > 0 else q[::-1])
    last = (len(idx) - 1) * npf
    faces.append(tuple(range(npf))[::-1] if side > 0 else tuple(range(npf)))      # end caps
    faces.append(tuple(range(last, last + npf)) if side > 0 else tuple(range(last, last + npf))[::-1])
    ob = C.mesh_object("RockCut", verts, faces, [rock], coll)
    sub = ob.modifiers.new("sub", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = sub.render_levels = 3
    for nm, kind, scale, strength in (("blocks", "VORONOI", 2.2, 0.55), ("fractures", "CLOUDS", 0.6, 0.32)):
        d = ob.modifiers.new(nm, "DISPLACE")
        tx = bpy.data.textures.new("rock_" + nm, kind)
        tx.noise_scale = scale
        if kind == "CLOUDS":
            tx.noise_depth = 4
        d.texture = tx
        d.texture_coords = "OBJECT"
        d.strength = strength
        d.mid_level = 0.5
        d.direction = "NORMAL"
    # fallen rocks: on the shoulder and at the foot of the face (never on the pavement)
    for k in range(14):
        i = r.randint(i0 + 30, min(i1 - 30, i0 + 160))
        rad = r.uniform(0.14, 0.42)
        x, y, z = path.offset(i, offset - side * r.uniform(0.6, 3.6), rad * 0.4)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=rad, location=(x, y, z))
        o = bpy.context.object
        o.name = "FallenRock"
        o.scale = (r.uniform(0.8, 1.4), r.uniform(0.8, 1.4), r.uniform(0.55, 0.85))
        o.rotation_euler = (r.uniform(0, 3), r.uniform(0, 3), r.uniform(0, 3))
        o.data.materials.append(rock)
        for p_ in o.data.polygons:
            p_.use_smooth = True
        d = o.modifiers.new("chip", "DISPLACE")
        tx = bpy.data.textures.new("chip", "VORONOI")
        tx.noise_scale = 0.35
        d.texture, d.strength, d.mid_level = tx, 0.35 * rad, 0.5
        d.texture_coords = "OBJECT"
        if coll:
            C.link(o, coll)
    # scrub and trees on the plateau behind the top edge (feet are snapped to the rock later)
    for k in range(38):
        a = r.randint(2, len(tops) - 3)
        i, lat_top, hf = tops[a]
        if hf < 0.9:
            continue
        lat_ = (lat_top + r.uniform(0.5, 9.0)) * (0.35 + 0.65 * hf)
        x, y, z = path.offset(i, offset + side * lat_)
        tp_ = "conifer" if r.random() < 0.45 else "deciduous"
        tree(x, y, 0.0, tp_, r.uniform(0.35, 0.8) if k % 3 else r.uniform(0.9, 1.3), seed + 100 + k)
    return ob


def bridge(path, d0, length, width, coll=None, lift_towers=False, water=True):
    """Concrete bridge deck with parapets on BOTH sides (symmetric) over a real
    water channel: sloped earth banks down to the water, abutment wing walls.
    The caller must leave a gap in the roadside ribbons over [d0+1.5, d0+length-1.5]
    (cfg gaps_right/gaps_left) and set the base ground plane to z=-1.7."""
    conc = C.concrete("BridgeConcrete", 4.0, (0.55, 0.54, 0.5))
    steel = C.mat("BridgeSteel", (0.22, 0.3, 0.33), 0.55, 0.3)
    x, y, z, h = path.at(path.index_at(d0))
    objs = []
    for sx in (-1, 1):
        x0 = sx * width / 2
        # concrete parapet wall with a steel handrail on top (both sides identical)
        objs.append(C.box("Parapet", min(x0, x0 + sx * 0.3), max(x0, x0 + sx * 0.3), y, y + length, -0.6, 0.85, conc, coll))
        for xr in (x0 + sx * 0.15,):
            C.box("BridgeRailTop", xr - 0.05, xr + 0.05, y, y + length, 0.85, 0.95, steel, coll)
            for q in range(int(length / 2.0) + 1):
                C.box("BridgeRailPost", xr - 0.04, xr + 0.04, y + q * 2.0 - 0.04, y + q * 2.0 + 0.04, 0.85, 1.2, steel, coll)
            C.box("BridgeRailTop", xr - 0.05, xr + 0.05, y, y + length, 1.17, 1.23, steel, coll)
    C.box("Deck", -width / 2 - 0.3, width / 2 + 0.3, y, y + length, -0.9, -0.01, conc, coll)
    if water:
        from . import roads as _R
        grass = C.grass()
        y0, y1 = y + 1.5, y + length - 1.5           # the channel runs between the abutments
        zw = -0.8                                    # water surface
        # earth banks: level with the road for 400 m, then sloping 1:2 down into the channel
        _R._extrude_x("BankNear", -400, 400, [(y0 - 400, -1.7), (y0 - 400, -0.06), (y0, -0.06), (y0 + 1.6, zw - 0.2), (y0 + 1.6, -1.7)], grass, coll)
        _R._extrude_x("BankFar", -400, 400, [(y1 + 400, -1.7), (y1 + 400, -0.06), (y1, -0.06), (y1 - 1.6, zw - 0.2), (y1 - 1.6, -1.7)], grass, coll)
        C.box("Water", -400, 400, y0 + 0.5, y1 - 0.5, zw - 0.3, zw, C.mat("Water", (0.03, 0.07, 0.08), 0.03), coll)
        # concrete abutment faces under the deck ends
        for yy in (y0 - 0.4, y1):
            C.box("BridgeWall", -width / 2 - 0.3, width / 2 + 0.3, yy, yy + 0.4, -1.6, -0.01, conc, coll)
    if lift_towers:
        for sx in (-1, 1):
            for yy in (y + length * 0.35, y + length * 0.65):
                C.box("LiftTower", sx * (width / 2 + 0.6) - 0.6, sx * (width / 2 + 0.6) + 0.6, yy - 0.6, yy + 0.6, 0, 22, steel, coll)
        C.box("LiftSpan", -width / 2 - 1.2, width / 2 + 1.2, y + length * 0.35 - 0.4, y + length * 0.65 + 0.4, 19, 22, steel, coll)
    return objs


def overpass(y, span=40.0, clearance=3.8, coll=None, abut=9.0):
    """Bridge deck across the road at y; abut = distance of each abutment's
    inner face from the road centreline (just outside the shoulders makes the
    road clearly pass under it)."""
    conc = C.concrete("Overpass", 5.0, (0.58, 0.57, 0.54))
    C.box("OverpassDeck", -span, span, y, y + 12, clearance, clearance + 1.4, conc, coll)
    C.box("OverpassParapet", -span, span, y - 0.3, y, clearance + 1.4, clearance + 2.4, conc, coll)
    for sx in (-1, 1):
        a0, a1 = sorted((sx * abut, sx * (abut + 1.6)))
        C.box("Abutment", a0, a1, y, y + 12, -0.3, clearance, conc, coll)
        e0, e1 = sorted((sx * (abut + 1.6), sx * 400))
        # road embankment carrying the deck: level with the deck on top, 1:3 grass slopes down to grade
        # along the road at both ends (a solid vertical block read as a hedge)
        from . import roads as _R
        _R._extrude_x("Embankment", e0, e1,
                      [(y - 3.0 * clearance, -0.3), (y, clearance), (y + 12, clearance), (y + 12 + 3.0 * clearance, -0.3)],
                      C.grass(), coll)


def crossing_signal(x, y, coll=None, flashing=True, yaw=0.0, art="crossbuck.png"):
    """Railway crossing signal: mast, crossbuck (artwork if available),
    two pairs of red flashers, bell. Faces -Y."""
    from . import signs as S
    pole = C.mat("Galvanised", (0.56, 0.57, 0.58), 0.45, 1.0)
    black = C.mat("FlasherBack", (0.02, 0.02, 0.02), 0.5)
    on = C.emissive("FlasherOn", (1.0, 0.05, 0.02), 40.0)
    off = C.mat("FlasherOff", (0.18, 0.02, 0.02), 0.1)
    parts = [C.cylinder("XingMast", 0.09, 0, 4.6, 0, 0, pole, coll, 16)]
    for sx, st in ((-0.42, on if flashing else off), (0.42, off)):
        # cylinders run along Z; +90 deg about X turns +Z into -Y (toward camera)
        parts.append(C.cylinder("FlasherBack", 0.3, 0.0, 0.03, 0, 0, black, coll, 24))
        parts[-1].rotation_euler = (math.radians(90), 0, 0)
        parts[-1].location = (sx, -0.05, 2.9)
        parts.append(C.cylinder("Flasher", 0.15, 0.03, 0.1, 0, 0, st, coll, 24))
        parts[-1].rotation_euler = (math.radians(90), 0, 0)
        parts[-1].location = (sx, -0.05, 2.9)
    parts.append(C.box("FlasherBar", -0.45, 0.45, -0.02, 0.04, 2.86, 2.94, pole, coll))
    try:
        cb, h = S.panel("Crossbuck", art, 1.22, coll=coll)
        cb.location = (0, -0.08, 3.65)
        parts.append(cb)
    except FileNotFoundError:
        print(f"{art} not found; signal built without crossbuck")
    root = bpy.data.objects.new("XingSignal", None)
    C.link(root, coll)
    for p in parts:
        p.parent = root
    root.location = (x, y, 0)
    root.rotation_euler[2] = math.radians(yaw)
    return root
