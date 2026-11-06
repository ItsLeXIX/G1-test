"""Shared helpers: scene reset, meshes, procedural materials.

Everything is procedural (no texture downloads) so a scene stays light enough
for an 8 GB laptop preview. All texture coordinates are in metres (Object
space with objects at the origin), so patterns have real-world scale.
"""
import math
import random

import bpy

from . import realism


def reset():
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    else:
        # live Blender (e.g. driven over MCP): factory reset would disable the
        # add-ons, so empty the file's data instead
        for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                     bpy.data.cameras, bpy.data.curves, bpy.data.node_groups, bpy.data.worlds,
                     bpy.data.particles):
            for block in list(coll):
                coll.remove(block)
        for img in list(bpy.data.images):
            if img.name != "Render Result":
                bpy.data.images.remove(img)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def collection(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def mesh_object(name, verts, faces, mats=(), coll=None, face_mats=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for m in mats:
        me.materials.append(m)
    if face_mats:
        for p, mi in zip(me.polygons, face_mats):
            p.material_index = mi
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return link(bpy.data.objects.new(name, me), coll)


def box(name, x0, x1, y0, y1, z0, z1, mat=None, coll=None):
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return mesh_object(name, v, f, [mat] if mat else (), coll)


def cylinder(name, r, z0, z1, x=0.0, y=0.0, mat=None, coll=None, seg=16, r_top=None):
    r_top = r if r_top is None else r_top
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((x + r * math.cos(a), y + r * math.sin(a), z0))
        v.append((x + r_top * math.cos(a), y + r_top * math.sin(a), z1))
    for i in range(seg):
        j = (i + 1) % seg
        f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    f.append(tuple(2 * i + 1 for i in range(seg)))
    f.append(tuple(2 * i for i in reversed(range(seg))))
    ob = mesh_object(name, v, f, [mat] if mat else (), coll)
    for p in ob.data.polygons[:seg]:
        p.use_smooth = True
    return ob


def bevel(ob, width=0.02, segments=2):
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    return m


# ---------------------------------------------------------------- materials

def _bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def mat(name, color, rough=0.7, metal=0.0, **extra):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = _bsdf(m)
    set_input(b, "Base Color", (*color, 1))
    set_input(b, "Roughness", rough)
    set_input(b, "Metallic", metal)
    for k, v in extra.items():
        set_input(b, k.replace("_", " "), v)
    return m


def emissive(name, color, strength):
    return mat(name, color, 0.3, Emission_Color=(*color, 1), Emission_Strength=strength)


def _proc(name, build):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    build(nt, _bsdf(m), nt.nodes.new("ShaderNodeTexCoord").outputs["Object"])
    return m


def _ramp(nt, fac, c0, c1):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].color = (*c0, 1)
    r.color_ramp.elements[1].color = (*c1, 1)
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def _noise(nt, vec, scale, detail=6.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    nt.links.new(vec, n.inputs["Vector"])
    return n.outputs["Fac"]


def _bump(nt, b, height, strength, distance=0.01):
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = distance
    nt.links.new(height, bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])


def asphalt(wet=0.0, snow=0.0):
    """Ontario-grey asphalt. wet adds dark glossy patches and puddles;
    snow adds packed slush in the wheel-free areas."""
    if realism.enabled() and not snow:
        return realism.asphalt(wet)
    def build(nt, b, vec):
        grain = _noise(nt, vec, 45.0, 8)
        stain = _noise(nt, vec, 0.35, 3)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = 0.35
        nt.links.new(_ramp(nt, grain, (0.06, 0.06, 0.06), (0.16, 0.16, 0.155)), mix.inputs["A"])
        nt.links.new(_ramp(nt, stain, (0.09, 0.09, 0.09), (0.13, 0.13, 0.125)), mix.inputs["B"])
        col = mix.outputs["Result"]
        _bump(nt, b, grain, 0.25)
        set_input(b, "Specular IOR Level", 0.3)
        rough = 0.93
        if wet > 0:
            puddle = _noise(nt, vec, 0.6, 4)
            pr = nt.nodes.new("ShaderNodeValToRGB")
            # a few glossy puddles (rough 0.05) on a damp, semi-gloss road
            pr.color_ramp.elements[0].position = 0.42 - 0.14 * wet
            pr.color_ramp.elements[1].position = 0.42 - 0.14 * wet + 0.05
            pr.color_ramp.elements[0].color = (0.05, 0.05, 0.05, 1)
            pr.color_ramp.elements[1].color = (0.5, 0.5, 0.5, 1)
            nt.links.new(puddle, pr.inputs["Fac"])
            nt.links.new(pr.outputs["Color"], b.inputs["Roughness"])
            dark = nt.nodes.new("ShaderNodeMix")
            dark.data_type = "RGBA"
            dark.inputs["Factor"].default_value = 0.55 * wet
            nt.links.new(col, dark.inputs["A"])
            dark.inputs["B"].default_value = (0.02, 0.02, 0.02, 1)
            col = dark.outputs["Result"]
        else:
            set_input(b, "Roughness", rough)
        if snow > 0:
            sn = _noise(nt, vec, 1.2, 5)
            sr = nt.nodes.new("ShaderNodeValToRGB")
            # scattered packed-snow patches, mostly bare road
            sr.color_ramp.elements[0].position = 0.66 - 0.08 * snow
            sr.color_ramp.elements[1].position = 0.7 - 0.08 * snow
            nt.links.new(sn, sr.inputs["Fac"])
            sm = nt.nodes.new("ShaderNodeMix")
            sm.data_type = "RGBA"
            nt.links.new(sr.outputs["Color"], sm.inputs["Factor"])
            nt.links.new(col, sm.inputs["A"])
            sm.inputs["B"].default_value = (0.75, 0.77, 0.8, 1)
            col = sm.outputs["Result"]
        nt.links.new(col, b.inputs["Base Color"])
    return _proc(f"Asphalt_w{wet:.1f}_s{snow:.1f}", build)


def concrete(name="Concrete", joint=1.5, color=(0.5, 0.49, 0.46), wet=0.0):
    """Poured concrete with control joints every `joint` metres (sidewalks)."""
    if realism.enabled() and name in ("Sidewalk", "Curb"):
        return realism.concrete(wet, "PH_" + name)
    def build(nt, b, vec):
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.offset = 0.0
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = joint
        br.inputs["Row Height"].default_value = joint
        br.inputs["Mortar Size"].default_value = 0.008
        br.inputs["Color1"].default_value = (*color, 1)
        br.inputs["Color2"].default_value = (*[c * 0.94 for c in color], 1)
        br.inputs["Mortar"].default_value = (*[c * 0.55 for c in color], 1)
        nt.links.new(vec, br.inputs["Vector"])
        grain = _noise(nt, vec, 30.0)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 0.25
        nt.links.new(br.outputs["Color"], mix.inputs["A"])
        nt.links.new(_ramp(nt, grain, (0.8, 0.8, 0.8), (1, 1, 1)), mix.inputs["B"])
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
        set_input(b, "Roughness", 0.9 - 0.6 * wet)
        _bump(nt, b, grain, 0.15)
    return _proc(f"{name}_{wet:.1f}", build)


def grass(snow=0.0):
    if realism.enabled() and not snow:
        return realism.grass()
    def build(nt, b, vec):
        n = _noise(nt, vec, 0.5, 6)
        fine = _noise(nt, vec, 60.0, 4)
        base = _ramp(nt, n, (0.045, 0.1, 0.02), (0.11, 0.19, 0.04))
        if snow > 0:
            m = nt.nodes.new("ShaderNodeMix")
            m.data_type = "RGBA"
            m.inputs["Factor"].default_value = min(1.0, 0.92 * snow + 0.05)
            nt.links.new(base, m.inputs["A"])
            m.inputs["B"].default_value = (0.82, 0.84, 0.88, 1)
            base = m.outputs["Result"]
        nt.links.new(base, b.inputs["Base Color"])
        set_input(b, "Roughness", 0.95 if not snow else 0.6)
        _bump(nt, b, fine, 0.6, 0.02)
    return _proc(f"Grass_s{snow:.1f}", build)


def gravel():
    def build(nt, b, vec):
        v = nt.nodes.new("ShaderNodeTexVoronoi")
        v.inputs["Scale"].default_value = 40.0
        nt.links.new(vec, v.inputs["Vector"])
        nt.links.new(_ramp(nt, v.outputs["Distance"], (0.3, 0.25, 0.18), (0.58, 0.52, 0.42)), b.inputs["Base Color"])
        set_input(b, "Roughness", 0.95)
        _bump(nt, b, v.outputs["Distance"], 0.9, 0.03)
    return _proc("Gravel", build)


def facade(name, wall, glass=(0.05, 0.07, 0.09), win_w=1.4, win_h=1.6, bay=3.2, storey=3.4, along="Y"):
    """Building wall with a cheap procedural window grid (brick node trick:
    bricks = windows, mortar = wall). along: the horizontal axis of the
    wall — "Y" for buildings lining the street, "X" for a wall facing the
    camera."""
    if realism.enabled():
        kind = "brick" if (wall[0] > wall[2] * 1.25) else "plaster"
        tint = tuple(min(1.0, c / 0.45) for c in wall) if kind == "plaster" else (1.0, 1.0, 1.0)
        return realism.facade(name, kind, tint, win_w=win_w, win_h=win_h, bay=bay, storey=storey, along=along)
    def build(nt, b, vec):
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.offset = 0.0
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = bay
        br.inputs["Row Height"].default_value = storey
        br.inputs["Mortar Size"].default_value = min(bay - win_w, storey - win_h) / 2
        br.inputs["Color1"].default_value = (*glass, 1)
        br.inputs["Color2"].default_value = (*glass, 1)
        br.inputs["Mortar"].default_value = (*wall, 1)
        # map (along, z) to brick (u, v)
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        com = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(vec, sep.inputs[0])
        nt.links.new(sep.outputs[along], com.inputs["X"])
        nt.links.new(sep.outputs["Z"], com.inputs["Y"])
        nt.links.new(com.outputs[0], br.inputs["Vector"])
        nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
        r = nt.nodes.new("ShaderNodeMapRange")
        r.inputs["To Min"].default_value = 0.85
        r.inputs["To Max"].default_value = 0.3   # glass: some reflection, not a mirror
        nt.links.new(br.outputs["Fac"], r.inputs["Value"])
        nt.links.new(r.outputs["Result"], b.inputs["Roughness"])
    return _proc(name, build)


def car_paint(name, color):
    return mat(name, color, 0.35, 0.6, Coat_Weight=1.0, Coat_Roughness=0.05)


PAINT_WHITE = ((0.82, 0.82, 0.8), 0.55)
PAINT_YELLOW = ((0.85, 0.6, 0.04), 0.55)


def paint(kind="white"):
    c, r = PAINT_WHITE if kind == "white" else PAINT_YELLOW
    return mat(f"Paint_{kind}", c, r)


def rng(seed):
    return random.Random(seed)


def to_bmesh_join(objs, name):
    """Join objects into one mesh (fewer objects = less memory/overhead)."""
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = name
    return objs[0]
