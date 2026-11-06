"""Render one question image from a cached base scene (no scene rebuild).

  blender -b render_pipeline/scenes/roadside.blend -P render_pipeline/render_cached.py -- --image 10

Steps: open base .blend (done by Blender) -> apply weather -> per-image extras ->
swap in the official sign artwork -> place the 50 mm camera -> checks -> render
to render_pipeline/out/<n>.png. run_batch.py drives this for many images.
"""
import argparse
import importlib.util
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
spec_ = importlib.util.spec_from_file_location("g1render", os.path.join(HERE, "render.py"))
R = importlib.util.module_from_spec(spec_)
_argv, sys.argv = sys.argv, [sys.argv[0]]
spec_.loader.exec_module(R)          # shared helpers: camera, checks, engine (main() is guarded)
sys.argv = _argv

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from g1scenes import common as C  # noqa: E402
from g1scenes import env as E  # noqa: E402
from g1scenes import props as P  # noqa: E402
from g1scenes import realism  # noqa: E402
from g1scenes import signs as S  # noqa: E402

PLAN = os.path.join(HERE, "test_plan.json")


# ------------------------------------------------------------------ weather

def _replace_material(prefixes, new_mat):
    n = 0
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            if slot.material and slot.material.name.startswith(prefixes):
                slot.material = new_mat
                n += 1
    return n


def snow_material():
    m = bpy.data.materials.get("SnowCover")
    if m:
        return m
    m = bpy.data.materials.new("SnowCover")
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.8, 0.82, 0.86, 1)
    b.inputs["Roughness"].default_value = 0.55
    if "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = 0.08
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.5
    nz.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.35
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def _gaps_y():
    """y-ranges where curbs stop (side roads, driveways) - no snow banks there."""
    gaps = []
    for o in bpy.data.objects:
        if o.name.startswith(("SideRoad", "Driveway")):
            ys = [(o.matrix_world @ Vector(c)).y for c in o.bound_box]
            gaps.append((min(ys) - 0.5, max(ys) + 0.5))
    return gaps


def snow_banks(seed=3):
    """Plough banks on the boulevard just behind both curbs."""
    road = [o for o in bpy.data.objects if o.name in ("Road", "RoadR", "RoadL")]
    if not road:
        return 0
    xs = [v.co.x for o in road for v in o.data.vertices]
    re, le = max(xs), min(xs)
    gaps = _gaps_y()
    mat = snow_material()
    r = random.Random(seed)
    n = 0
    for x0, x1 in ((re + 0.2, re + 1.25), (le - 1.25, le - 0.2)):
        y = -5.0
        while y < 160:
            seg = r.uniform(2.5, 4.0)
            if not any(a < y + seg and y < b for a, b in gaps):
                h = r.uniform(0.3, 0.55)
                ob = C.box("SnowBank", x0, x1, y, y + seg + 0.4, 0.05, 0.13 + h, mat)
                C.bevel(ob, min(0.25, h * 0.6), 3)
                n += 1
            y += seg
    return n


def snowy_trees():
    """Leafy street trees don't belong in a snow scene: swap them for snow-laden conifers."""
    trees = [o for o in bpy.data.objects if o.get("g1_kind") == "tree_deciduous"]
    for k, o in enumerate(trees):
        loc, s = o.location.copy(), o.scale.z
        bpy.data.objects.remove(o)
        P.tree(loc.x, loc.y, loc.z, "conifer", scale=s, seed=100 + k, snow=1.0)
    return len(trees)


def apply_weather(weather):
    if weather in ("night",):
        E.world("night")
    else:
        realism.hdri_world(weather)
    notes = []
    if weather == "rain":
        notes.append(f"wet asphalt x{_replace_material(('PH_Asphalt',), realism.asphalt(1.0))}")
        for name in ("PH_Sidewalk", "PH_Curb", "PH_Step"):
            _replace_material((name,), realism.concrete(1.0, name))
    elif weather == "snow":
        snow = snow_material()
        notes.append(f"snow ground x{_replace_material(('PH_Lawn', 'Grass_'), snow)}")
        notes.append(f"snow roofs x{_replace_material(('PH_Shingle', 'Roof', 'GarageRoof', 'PorchRoof'), snow)}")
        _replace_material(("PH_Hedge",), snow)
        # ploughed road: wet and dark, slush only at the edges (the banks)
        _replace_material(("PH_Asphalt",), realism.asphalt(0.6))
        for name in ("PH_Sidewalk", "PH_Curb"):
            _replace_material((name,), realism.concrete(0.6, name))
        notes.append(f"{snowy_trees()} trees -> snowy conifers")
        notes.append(f"{snow_banks()} bank segments")
    return notes


# --------------------------------------------------------------- sign swap

def swap_sign(base, items, night=False, posts=1):
    for o in [o for o in bpy.data.objects if o.get("g1_sign")]:
        bpy.data.objects.remove(o)
    t = base["type"]
    if t == "ground":
        # one post per sign; two only when the plan says the real sign has two
        S.ground_mount(items, base["x"], base["y"], bottom=base["bottom"], z0=base["z0"],
                       posts=posts, night=night)
    elif t == "span":
        span = json.loads(bpy.context.scene["g1_span"])
        S.hang_signs(items, span, night=night)
    elif t == "surface":
        art, w = items[0]
        p, h = S.panel("Sign_0", art, w, night)
        p.location = (base["x"], base["y"], base["z"] - h / 2)
        p["g1_sign"] = 1
    else:
        raise SystemExit(f"unknown mount {t}")


def place_camera_vehicle(base):
    """Straight behind the vehicle at eye height, emblem filling SIGN_FRACTION."""
    found = R.main_sign()
    sc = bpy.context.scene
    cam = sc.camera
    cam.data.lens = R.LENS
    _, c, w, _ = found
    tan_w = cam.data.sensor_width / 2 / cam.data.lens
    d = w / (R.SIGN_FRACTION * 2 * tan_w)
    dz = R.EYE - c.z
    cam.location = (c.x, c.y - math.sqrt(max(d * d - dz * dz, 1.0)), R.EYE)
    E.frame(cam, c, (R.SIGN_CENTRE_X, 0.42), fstop=4.0)
    return found


# -------------------------------------------------------------------- main

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--quality", default="final", choices=["preview", "final"])
    args = ap.parse_args(argv)
    t0 = time.time()
    plan = {e["image"]: e for e in R.load(PLAN)["images"]}[args.image]
    base = json.loads(bpy.context.scene["g1_base"])
    weather = plan["weather"]
    notes = apply_weather(weather)
    items = [[os.path.join(R.ASSETS, f), w] for f, w in plan["sign"]]
    swap_sign(base, items, night=weather == "night", posts=plan.get("posts", 1))
    if plan.get("signal_state"):
        P.set_signal_state(plan["signal_state"])
    for extra in plan.get("extras", []):
        if extra["type"] == "car":
            P.car(extra["x"], extra["y"], extra["heading"], extra.get("colour", "silver"))
    spec = {"template": base["template"], "weather": weather, "fstop": 4.0}
    if base["kind"] == "vehicle_rear":
        found = place_camera_vehicle(base)
    else:
        if base["kind"] == "parking_lot":
            spec["lat"] = 1.2
        found = R.place_camera(spec)
    R.check_sign_posts()
    posts = R.check_bare_poles(allow_two=plan.get("posts", 1) == 2)
    R.check_overhead_mounts()
    frac = R.sign_width_fraction(found)
    if frac < (0.0 if spec.get("_size_limited") else 0.15):
        raise SystemExit(f"image {args.image}: sign only {frac:.1%} of width")
    framing = R.check_framing(found)
    dropped = R.drop_clipped_trees()
    if weather == "rain":
        realism.rain_streaks(bpy.context.scene.camera, R.sign_screen_rect(found))
    if weather == "night":
        E.headlights(bpy.context.scene.camera, found[1])
    engine = R.pick_engine("auto")
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 2400, 1000
    sc.render.resolution_percentage = 100 if args.quality == "final" else 40
    sc.cycles.samples = 384 if args.quality == "final" else 24
    os.makedirs(R.OUT, exist_ok=True)
    out = os.path.join(R.OUT, f"{args.image}.png")
    sc.render.filepath = out
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    t2 = time.time()
    print("RESULT " + json.dumps({"image": args.image, "path": "cached", "base": base["kind"], "weather": weather,
                                  "engine": engine, "sign_fraction": round(frac, 4), "framing": framing, "posts": posts,
                                  "size_limited_by_headroom": bool(spec.get("_size_limited")),
                                  "dropped_trees": dropped, "weather_notes": notes,
                                  "prep_s": round(t1 - t0, 1), "render_s": round(t2 - t1, 1),
                                  "gpu_render_s": round(t2 - t1, 1) if engine.startswith("Cycles GPU") else None,
                                  "out": out}))


main()
