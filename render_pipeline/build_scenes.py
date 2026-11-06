"""Build the cached base scenes (one .blend per scene type).

  blender -b --factory-startup -P render_pipeline/build_scenes.py
  blender -b --factory-startup -P render_pipeline/build_scenes.py -- --only roadside,overhead

Each base scene is built once from the templates in tools/question_images/g1scenes
with clear weather and a placeholder sign, and saved to render_pipeline/scenes/<kind>.blend.
Re-run this whenever a template changes. render_cached.py opens these files, applies
the weather, swaps in the official sign artwork and renders; it never rebuilds a scene.

The scene's custom property "g1_base" (JSON) says how the sign is mounted, so
render_cached.py can put any sign in the same place:
  ground   {"x", "y", "z0", "bottom"}      post-mounted beside the road / lot
  span     scene["g1_span"]                hung from a mast arm or truss
  surface  {"x", "y", "z"}                 stuck on a vehicle (SMV emblem)
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "question_images"))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from g1scenes import templates  # noqa: E402

SCENES = os.path.join(HERE, "scenes")
PLACEHOLDER = os.path.join(HERE, "sign_assets", "Ra-002.png")

# One spec per base scene. Signs are swapped later, so the placeholder only fixes
# where the sign stands. sign_dist / side road match the approved #10 framing.
BASES = {
    "roadside": {"template": "roadside", "setting": "suburban", "sign_dist": 14.0, "sign_offset": 2.0,
                 "features": [{"type": "side_road", "at": 27.0, "side": "both"}]},
    "overhead": {"template": "overhead", "setting": "city", "sign_x": 3.25,
                 # fixed arm height: 5.3 m clearance under a sign up to 1.45 m tall
                 "span_top": 5.3 + 1.45 + 0.25},
    "parking_lot": {"template": "parking_lot"},
    "city_street": {"template": "city_street"},
    "vehicle_rear": {"template": "vehicle_rear", "setting": "suburban", "vehicle": "car", "kind": "sedan",
                     "colour": "blue", "vehicle_dist": 12.0},
}


def ground_mount_info():
    panels = [o for o in bpy.data.objects if o.name.startswith("Sign_")]
    posts = [o for o in bpy.data.objects if o.name.startswith("Post_")]
    rig = bpy.data.objects["SignRig"]
    bpy.context.view_layer.update()
    z_panel = min((p.matrix_world.translation.z for p in panels))
    z_post0 = min((p.matrix_world @ v.co).z for p in posts for v in p.data.vertices)
    z0 = z_post0 + 0.4
    return {"type": "ground", "x": rig.location.x, "y": rig.location.y, "z0": z0, "bottom": z_panel - z0}


def vehicle_anchor():
    """Centre of the car's rear face at emblem height, found by ray casting."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    car = next(o for o in bpy.data.objects if o.get("g1_kind", "").startswith("car_"))
    x = car.location.x
    zc = 0.75             # centre of a ~0.31 m tall emblem, on the flat lower rear face
    ys = []
    for z in (zc - 0.17, zc - 0.08, zc, zc + 0.08, zc + 0.17):
        for dx in (-0.2, 0.0, 0.2):
            hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, Vector((x + dx, car.location.y - 8, z)), Vector((0, 1, 0)))
            if hit and loc.y < car.location.y and ob.name != "Ground":
                ys.append(loc.y)
    if ys:
        # in front of the nearest point under the whole emblem, so no part sinks into the body
        return {"type": "surface", "x": x, "y": min(ys) - 0.012, "z": zc, "found_by": "ray"}
    # ray casts don't always see collection instances: fall back to the model's
    # known length (4.8 m, origin at its centre), slightly proud of the bumper
    return {"type": "surface", "x": x, "y": car.location.y - 2.45, "z": 0.85, "found_by": "model length"}


def build(kind):
    spec = dict(BASES[kind])
    spec["weather"] = "clear"
    spec["sign"] = [[PLACEHOLDER, 0.75]]
    spec["lens"] = 50.0
    t0 = time.time()
    templates.get(spec["template"]).build(spec, "final")
    if kind == "overhead":
        info = {"type": "span"}
    elif kind == "vehicle_rear":
        # the template also puts a roadside sign up; the SMV emblem goes on the car instead
        for o in [o for o in bpy.data.objects if o.get("g1_sign")]:
            bpy.data.objects.remove(o)
        info = vehicle_anchor()
    else:
        info = ground_mount_info()
    info["kind"] = kind
    info["template"] = spec["template"]
    info["spec"] = {k: v for k, v in spec.items() if k != "sign"}
    sc = bpy.context.scene
    sc["g1_base"] = json.dumps(info)
    sc.render.resolution_x, sc.render.resolution_y = 2400, 1000
    sc.render.resolution_percentage = 100
    os.makedirs(SCENES, exist_ok=True)
    out = os.path.join(SCENES, kind + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print(f"BUILT {kind} in {time.time() - t0:.1f}s -> {out} ({os.path.getsize(out) / 1e6:.1f} MB)")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else list(BASES)
    from g1scenes import props, realism
    for kind in only:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        realism.reset_cache()
        props._TREE_PROTOS.clear()
        build(kind)


main()
