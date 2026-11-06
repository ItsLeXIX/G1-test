"""Photographic layer: Poly Haven HDRI sky, PBR textures and real models.

Everything here is optional: if assets/polyhaven/ is missing the procedural
stand-ins in common.py / props.py are used instead. Assets and their
sources are listed in assets/polyhaven/SOURCES.json and assets/CREDITS.md.
"""
import math
import os

import bpy
from mathutils import Vector

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
PH = os.path.join(ASSETS, "polyhaven")

HDRI = {
    # weather -> (file, strength). Strengths are tuned for the Standard view
    # transform (needed so sign faces keep their exact artwork colours).
    "clear": ("kloofendal_38d_partly_cloudy_puresky_4k.hdr", 0.85),
    "overcast": ("overcast_soil_puresky_4k.hdr", 1.1),
    "rain": ("overcast_soil_puresky_4k.hdr", 0.75),
    "snow": ("overcast_soil_puresky_4k.hdr", 0.62),   # snow is bright: lower sky so it does not clip
    "dusk": ("kloofendal_38d_partly_cloudy_puresky_4k.hdr", 0.12),
}

_collections = {}


def enabled():
    return os.path.isdir(PH)


def reset_cache():
    _collections.clear()


# ---------------------------------------------------------------- sky

def _sun_azimuth_of_image(img):
    """Equirect pixel with the most energy -> Blender world azimuth phi
    (phi = atan2(y, -x), the environment texture's convention)."""
    import numpy as np
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    lum = px.reshape(h, w, 4)[:, :, :3].sum(axis=2)
    lum[: h // 2] = 0            # rows are bottom-up: ignore the lower hemisphere
    row, col = np.unravel_index(int(lum.argmax()), lum.shape)
    u, v = (col + 0.5) / w, (row + 0.5) / h
    return (u - 0.5) * 2 * math.pi, (v - 0.5) * math.pi


def hdri_world(weather, sun_azimuth=150.0):
    """World = Poly Haven sky, rotated so its sun sits at `sun_azimuth`
    degrees (from +Y, positive to the left: 150 = behind the camera's left
    shoulder, so sign faces are front-lit). Returns the sun elevation."""
    fname, strength = HDRI.get(weather, HDRI["overcast"])
    img = bpy.data.images.load(os.path.join(PH, fname), check_existing=True)
    phi_img, elev = _sun_azimuth_of_image(img)
    az = math.radians(sun_azimuth)
    want = Vector((-math.sin(az), math.cos(az), 0.0))
    phi_want = math.atan2(want.y, -want.x)
    wd = bpy.data.worlds.new("World")
    bpy.context.scene.world = wd
    wd.use_nodes = True
    nt = wd.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = img
    # rotating the lookup vector by r shifts the image's phi by -r
    mp.inputs["Rotation"].default_value = (0, 0, phi_img - phi_want)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    return math.degrees(elev)


# ----------------------------------------------------------- materials

def _img(folder, kind, colour=True):
    d = os.path.join(PH, folder)
    f = next(x for x in os.listdir(d) if x.startswith(kind + "_"))
    im = bpy.data.images.load(os.path.join(d, f), check_existing=True)
    im.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    return im


def pbr(name, folder, size_m, tint=None, darken=1.0, rough_scale=1.0, wet=0.0, puddles=False,
        normal=1.0, along=None):
    """PBR material from a Poly Haven texture set, box-projected in object
    space at its real-world size (objects here are built in world space)."""
    key = f"{name}_w{wet:.2f}"
    m = bpy.data.materials.get(key)
    if m:
        return m
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / size_m,) * 3
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    vec = mp.outputs["Vector"]

    def tex(kind, colour=True):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _img(folder, kind, colour)
        t.projection = "BOX"
        t.projection_blend = 0.25
        nt.links.new(vec, t.inputs["Vector"])
        return t.outputs["Color"]

    col = tex("diff")
    if tint is not None or darken != 1.0:
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        t = tint or (1, 1, 1)
        mul.inputs["B"].default_value = (t[0] * darken, t[1] * darken, t[2] * darken, 1)
        nt.links.new(col, mul.inputs["A"])
        col = mul.outputs["Result"]
    rough = tex("rough", False)
    rs = nt.nodes.new("ShaderNodeMath")
    rs.operation = "MULTIPLY"
    rs.inputs[1].default_value = rough_scale * (1 - 0.8 * wet)
    nt.links.new(rough, rs.inputs[0])
    rough = rs.outputs[0]
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = normal
    nt.links.new(tex("nor_gl", False), nm.inputs["Color"])
    nrm = nm.outputs["Normal"]

    if wet > 0:
        # wet: darker albedo, low roughness; puddles: near-black mirror patches
        dk = nt.nodes.new("ShaderNodeMix")
        dk.data_type = "RGBA"
        dk.blend_type = "MULTIPLY"
        dk.inputs["Factor"].default_value = 1.0
        dk.inputs["B"].default_value = (0.42, 0.42, 0.42, 1)
        nt.links.new(col, dk.inputs["A"])
        col = dk.outputs["Result"]
        if puddles:
            gtc = nt.nodes.new("ShaderNodeTexCoord")
            noise = nt.nodes.new("ShaderNodeTexNoise")
            noise.inputs["Scale"].default_value = 0.12
            noise.inputs["Detail"].default_value = 3.0
            noise.inputs["Roughness"].default_value = 0.55
            nt.links.new(gtc.outputs["Object"], noise.inputs["Vector"])
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].position = 0.5
            ramp.color_ramp.elements[1].position = 0.56
            nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
            mask = ramp.outputs["Color"]
            pc = nt.nodes.new("ShaderNodeMix")
            pc.data_type = "RGBA"
            nt.links.new(mask, pc.inputs["Factor"])
            nt.links.new(col, pc.inputs["A"])
            pc.inputs["B"].default_value = (0.012, 0.012, 0.013, 1)
            col = pc.outputs["Result"]
            pr = nt.nodes.new("ShaderNodeMix")
            pr.data_type = "FLOAT"
            nt.links.new(mask, pr.inputs["Factor"])
            nt.links.new(rough, pr.inputs["A"])
            pr.inputs["B"].default_value = 0.015
            rough = pr.outputs["Result"]
            pn = nt.nodes.new("ShaderNodeMix")
            pn.data_type = "VECTOR"
            nt.links.new(mask, pn.inputs["Factor"])
            nt.links.new(nrm, pn.inputs["A"])
            nt.links.new(gtc.outputs["Normal"], pn.inputs["B"])
            nrm = pn.outputs["Result"]
    nt.links.new(col, b.inputs["Base Color"])
    nt.links.new(rough, b.inputs["Roughness"])
    nt.links.new(nrm, b.inputs["Normal"])
    return m


def asphalt(wet=0.0):
    return pbr("PH_Asphalt", "asphalt_02", 3.0, darken=0.85, wet=wet, puddles=wet > 0)


def grass():
    """Mown lawn: Poly Haven leafy_grass detail (its luminance, normal and
    roughness) recoloured to lawn greens; the raw texture is mostly brown leaves."""
    m = bpy.data.materials.get("PH_Lawn_w0.00")
    if m:
        return m
    m = pbr("PH_Lawn", "leafy_grass", 1.6, normal=0.6)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    src = b.inputs["Base Color"].links[0].from_socket
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(src, bw.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.05
    ramp.color_ramp.elements[0].color = (0.025, 0.06, 0.012, 1)
    ramp.color_ramp.elements[1].position = 0.45
    ramp.color_ramp.elements[1].color = (0.16, 0.27, 0.06, 1)
    nt.links.new(bw.outputs[0], ramp.inputs["Fac"])
    # large-scale patchiness so the lawn isn't a flat repeat
    gtc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.08
    nt.links.new(gtc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MULTIPLY"
    nt.links.new(ramp.outputs["Color"], mx.inputs["A"])
    pr = nt.nodes.new("ShaderNodeValToRGB")
    pr.color_ramp.elements[0].color = (0.75, 0.78, 0.7, 1)
    pr.color_ramp.elements[1].color = (1.1, 1.05, 1.0, 1)
    nt.links.new(nz.outputs["Fac"], pr.inputs["Fac"])
    nt.links.new(pr.outputs["Color"], mx.inputs["B"])
    mx.inputs["Factor"].default_value = 1.0
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    return m


def concrete(wet=0.0, name="PH_Sidewalk"):
    # the paver photo is brown; Ontario sidewalks/curbs are light-grey poured
    # concrete: keep the texture's detail, map its luminance onto concrete greys
    key = f"{name}_w{wet * 0.6:.2f}"
    if bpy.data.materials.get(key):
        return bpy.data.materials[key]
    m = pbr(name, "concrete_pavement_03", 2.1, wet=wet * 0.6)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    link = b.inputs["Base Color"].links[0]
    src = link.from_socket
    # with wet > 0 the chain ends in the darkening multiply; recolour before it
    if link.from_node.type == "MIX" and link.from_node.inputs["A"].links:
        tgt = link.from_node.inputs["A"]
        src = tgt.links[0].from_socket
    else:
        tgt = b.inputs["Base Color"]
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(src, bw.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.22, 0.22, 0.215, 1)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (0.6, 0.6, 0.585, 1)
    nt.links.new(bw.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], tgt)
    return m


def wall(kind, tint):
    folder, size = {"brick": ("red_brick", 1.4), "siding": ("exterior_wall_cladding_03", 1.96),
                    "plaster": ("plastered_wall_02", 2.23)}[kind]
    key = f"PH_{kind}_{'_'.join(f'{c:.2f}' for c in tint)}"
    return pbr(key, folder, size, tint=tint)


def facade(name, kind, tint, glass=(0.02, 0.025, 0.03), win_w=1.4, win_h=1.6, bay=3.2, storey=3.4, along="Y"):
    """Textured wall with a window grid (brick-node mask: mortar = wall)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    base = wall(kind, tint).copy()
    base.name = name
    nt = base.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    wall_col = b.inputs["Base Color"].links[0].from_socket
    wall_rough = b.inputs["Roughness"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    com = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs[along], com.inputs["X"])
    nt.links.new(sep.outputs["Z"], com.inputs["Y"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = bay
    br.inputs["Row Height"].default_value = storey
    br.inputs["Mortar Size"].default_value = min(bay - win_w, storey - win_h) / 2
    br.inputs["Mortar Smooth"].default_value = 0.0
    nt.links.new(com.outputs[0], br.inputs["Vector"])
    mask = br.outputs["Fac"]             # 1 on the wall, 0 in the windows
    mc = nt.nodes.new("ShaderNodeMix")
    mc.data_type = "RGBA"
    nt.links.new(mask, mc.inputs["Factor"])
    mc.inputs["A"].default_value = (*glass, 1)
    nt.links.new(wall_col, mc.inputs["B"])
    nt.links.new(mc.outputs["Result"], b.inputs["Base Color"])
    mr = nt.nodes.new("ShaderNodeMix")
    mr.data_type = "FLOAT"
    nt.links.new(mask, mr.inputs["Factor"])
    mr.inputs["A"].default_value = 0.04
    nt.links.new(wall_rough, mr.inputs["B"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    return base


def glass():
    m = bpy.data.materials.get("PH_ShopGlass")
    if m:
        return m
    m = bpy.data.materials.new("PH_ShopGlass")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.03, 0.035, 0.04, 1)
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["Specular IOR Level"].default_value = 0.9
    return m


# --------------------------------------------------------------- models

def _collection(name):
    """Load assets/<name>.blend's collection once; returns it (not linked to the scene)."""
    if name in _collections:
        try:
            if _collections[name].name in bpy.data.collections:
                return _collections[name]
        except ReferenceError:          # removed by a scene reset
            pass
        del _collections[name]
    p = os.path.join(ASSETS, name + ".blend")
    if not os.path.exists(p):
        return None
    with bpy.data.libraries.load(p, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c.endswith("_root")] or src.collections[:1]
    c = dst.collections[0]
    _collections[name] = c
    return c


def has(name):
    return os.path.exists(os.path.join(ASSETS, name + ".blend"))


def instance(name, loc, yaw_deg=0.0, scale=1.0, coll=None):
    c = _collection(name)
    if c is None:
        return None
    ob = bpy.data.objects.new(name, None)
    ob.instance_type = "COLLECTION"
    ob.instance_collection = c
    ob.location = loc
    ob.rotation_euler[2] = math.radians(yaw_deg)
    ob.scale = (scale,) * 3
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob["g1_kind"] = name
    return ob


# ---------------------------------------------------------------- rain

def rain_streaks(cam, keep_clear, count=1100, seed=7):
    """Faint rain streaks in front of the camera. keep_clear: (x0, y0, x1, y1)
    in normalised camera-view coords; no streak is drawn over that area
    (the sign)."""
    import random
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    r = random.Random(seed)
    m = bpy.data.materials.new("RainStreak")
    m.use_nodes = True
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    for n in list(nt.nodes):
        if n.name != out.name:
            nt.nodes.remove(n)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.85, 0.88, 0.92, 1)
    em.inputs["Strength"].default_value = 0.4
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.13          # light streaks only
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])

    mw = cam.matrix_world
    fwd = -(mw.to_3x3() @ Vector((0, 0, 1)))
    right = mw.to_3x3() @ Vector((1, 0, 0))
    up = mw.to_3x3() @ Vector((0, 1, 0))
    tan_w = cam.data.sensor_width / 2 / cam.data.lens
    tan_h = tan_w * sc.render.resolution_y / sc.render.resolution_x
    x0, y0, x1, y1 = keep_clear
    verts, faces = [], []
    tilt = Vector((0.04, 0.0, -1.0)).normalized()
    side = Vector((1, 0, 0))
    placed = tries = 0
    while placed < count and tries < count * 5:
        tries += 1
        d = 4.0 + (r.random() ** 1.4) * 26
        sx, sy = r.uniform(-1, 1), r.uniform(-1, 1)
        p = Vector(mw.translation) + fwd * d + right * (sx * tan_w * d) + up * (sy * tan_h * d)
        v = world_to_camera_view(sc, cam, p)
        if x0 <= v.x <= x1 and y0 <= v.y <= y1:
            continue
        L = r.uniform(0.12, 0.3) * (0.7 + d / 25)
        wdt = 0.0009 * (1 + d / 12)
        a, b = p - tilt * (L / 2), p + tilt * (L / 2)
        # the streak's far end must not reach into the sign area either
        va, vb = world_to_camera_view(sc, cam, a), world_to_camera_view(sc, cam, b)
        if any(x0 <= q.x <= x1 and y0 <= q.y <= y1 for q in (va, vb)):
            continue
        k = len(verts)
        verts += [a - side * wdt, a + side * wdt, b + side * wdt, b - side * wdt]
        faces.append((k, k + 1, k + 2, k + 3))
        placed += 1
    me = bpy.data.meshes.new("Rain")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.materials.append(m)
    ob = bpy.data.objects.new("Rain", me)
    sc.collection.objects.link(ob)
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_glossy = False
    ob.visible_transmission = False
    return ob
