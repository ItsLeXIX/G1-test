"""Render G1 question images from render_pipeline/manifest.json (headless).

  blender -b --factory-startup -P render_pipeline/render.py -- --only 57
  blender -b --factory-startup -P render_pipeline/render.py -- --only 10,53,120 --install
  blender -b --factory-startup -P render_pipeline/render.py -- --only 10 --engine eevee

Scene geometry comes from the templates in tools/question_images/g1scenes
(roadside, highway, city_street, parking_lot, overhead, vehicle_rear,
hand_signal, railway_crossing, intersection_aerial, marking_aerial, ...).
Which template/setting/features each image uses comes from
tools/question_images/manifest.json; the sign artwork comes from
render_pipeline/sign_map.json + render_pipeline/sign_assets/ (official
artwork, never redrawn). Camera lens/height come from this folder's
manifest.json so every image shares them.

Output: render_pipeline/out/<n>.png at 2400x1000. --install writes
<n>.png / <n>@2x.png / <n>@3x.png into the imageset and rewrites its
Contents.json; it refuses to run unless the backup folder exists.
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCENES = os.path.join(REPO, "tools", "question_images")
sys.path.insert(0, SCENES)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from g1scenes import env as E  # noqa: E402
from g1scenes import realism  # noqa: E402
from g1scenes import templates  # noqa: E402

IMAGESETS = os.path.join(REPO, "G1 test", "Assets.xcassets", "QuestionsImages")
BACKUP = os.path.join(HERE, "backup_QuestionsImages_2026-11-05")
ASSETS = os.path.join(HERE, "sign_assets")
OUT = os.path.join(HERE, "out")
SCALES = {"1x": 800, "2x": 1600, "3x": 2400}
NO_SIGN_TEMPLATES = ("intersection_aerial", "hand_signal")

# manifest scene name -> template name in g1scenes
SCENE_TO_TEMPLATE = {"city_street": "city_street", "roadside": "roadside", "highway": "highway",
                     "overhead": "overhead", "parking_lot": "parking_lot", "hand_signal": "hand_signal",
                     "vehicle_rear": "vehicle_rear", "railway_crossing": "railway_crossing",
                     "pavement_marking": "marking_aerial", "aerial_intersection": "intersection_aerial"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_spec(entry, scene_specs, sign_map):
    n = entry["imageName"]
    spec = dict(scene_specs.get(n, {}))
    spec.setdefault("template", SCENE_TO_TEMPLATE[entry["scene"]])
    spec["weather"] = entry.get("weather", spec.get("weather", "clear"))
    if n in sign_map:
        spec["sign"] = [[os.path.join(ASSETS, f), w] for f, w in sign_map[n]]
    # per-image overrides decided in this render round (render_pipeline/spec_overrides.json);
    # applied before the template-specific defaults below so they follow a changed template
    for k, v in SPEC_OVERRIDES.get(n, {}).items():
        if k == "sign":
            spec["sign"] = [[os.path.join(ASSETS, f), w] for f, w in v]
        elif not k.startswith("_"):
            spec[k] = v
    if not spec.get("sign") and spec["template"] not in NO_SIGN_TEMPLATES:
        raise SystemExit(f"image {n}: no artwork in sign_map.json yet")
    cam = entry.get("camera", {})
    spec["lens"] = LENS
    E.EYE_HEIGHT = EYE if cam.get("preset") not in ("topdown", "aerial") else E.EYE_HEIGHT
    spec["fstop"] = spec.get("fstop", 4.0)   # sign sharp, background only slightly soft
    if spec["template"] in ("overhead", "city_street") and spec.get("setting", "city") == "city":
        # pave right up to the building fronts (no lawn strip under storefronts)
        spec.setdefault("road", {})["beyond"] = "walk"
    if spec["template"] == "roadside" and spec.get("sign_side", "right") == "right":
        spec.setdefault("sign_offset", 2.0)    # right shoulder, 2-4 m from the road edge (2 keeps the road in frame)
    if spec["template"] == "overhead":
        if "red" in entry.get("correctAnswer", "").lower() or "red" in " ".join(entry.get("signs", [])).lower():
            spec.setdefault("signal_state", "red")
        if spec.get("setting", "city") == "city":
            # hang the sign beside the first signal head (x 4.6) so both are in the
            # close-up frame the 15 % rule forces
            spec.setdefault("sign_x", 3.25)
    tweak = IMAGE_TWEAKS.get(n)
    if tweak and tweak.get("spec"):
        tweak["spec"](spec)
    return spec


def _load_overrides():
    p = os.path.join(HERE, "spec_overrides.json")
    return {k: v for k, v in load(p).items() if not k.startswith("_")} if os.path.exists(p) else {}


SPEC_OVERRIDES = _load_overrides()


# ------------------------------------------------------------- framing

LENS = 50.0          # one lens for every image
EYE = 1.7            # driver eye height (m), SUV/pickup; overhead scenes use the sign's height. With a 50 mm lens at 2.4:1 the
                     # frame is only 17 deg tall; at 1.2 m a sign close enough to fill
                     # 15 % of the width sits so far above eye level that no road shows.
SIGN_FRACTION = 0.155 # main sign >= 15 % of image width (projected; small margin)
SIGN_CENTRE_X = 0.60  # aim the main sign's centre here (road stays visible on the left)
CENTRE_RANGE = (0.55, 0.65)   # check: main sign centre must land in this band of the width
EDGE_MARGIN = 0.05    # check: whole sign stack keeps >= 5 % from every frame edge
SIGN_TEMPLATES = ("roadside", "city_street", "highway", "parking_lot", "overhead",
                  "railway_crossing", "guide_sign")


def main_sign():
    """The main sign panel: highest of the ground-mounted stack, or the first overhead panel."""
    panels = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(("Sign_", "OverheadSign_"))]
    if not panels:
        xb = _near_crossbuck()
        panels = [xb] if xb else []
    if not panels:
        return None
    bpy.context.view_layer.update()

    def box(o):
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        return Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), \
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))

    over = [o for o in panels if o.name.startswith("OverheadSign_")]
    o = sorted(over, key=lambda o: o.name)[0] if over else max(panels, key=lambda o: box(o)[1].z)
    lo, hi = box(o)
    return o, (lo + hi) / 2, max(hi.x - lo.x, hi.y - lo.y), (lo, hi)


def place_camera(spec):
    """Put the 50 mm camera where the main sign fills SIGN_FRACTION of the width."""
    sc = bpy.context.scene
    cam = sc.camera
    cam.data.lens = LENS
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    found = main_sign() if spec["template"] in SIGN_TEMPLATES else None
    if not found:
        return None
    _, c, w, _ = found
    tan_w = cam.data.sensor_width / 2 / cam.data.lens
    # per-image target only where the 15 % rule and 5 % headroom can't both hold
    # (signs narrower than ~0.4 x their height, e.g. a 0.3 x 0.9 m hazard marker)
    d = w / (spec.get("sign_fraction", SIGN_FRACTION) * 2 * tan_w)   # line-of-sight distance to the sign
    if spec["template"] == "overhead":
        # as if from a pedestrian bridge: camera at the sign's height, level,
        # square to the sign face (no tilt, so no keystone); shifted left so
        # the sign centre lands at SIGN_CENTRE_X instead of dead centre
        cam.location = (c.x - (SIGN_CENTRE_X - 0.5) * 2 * d * tan_w, c.y - d, c.z)
        cam.rotation_euler = (math.pi / 2, 0.0, 0.0)
        cam.data.dof.use_dof = True
        cam.data.dof.focus_distance = d
        cam.data.dof.aperture_fstop = spec.get("fstop", 4.0)
        return found
    if spec.get("view_from") == "sidewalk":
        # standing on the sidewalk looking back across the street, so parked cars
        # and the street are behind the sign (it gets squared to the camera later)
        a = math.radians(spec.get("view_angle", 20.0))
        dz = c.z - EYE
        horiz = math.sqrt(max(d * d - dz * dz, 1.0))
        cam.location = (c.x + horiz * math.cos(a), c.y - horiz * math.sin(a), EYE)
        tan_h = tan_w * sc.render.resolution_y / sc.render.resolution_x
        dy = ((found[3][1].z - c.z) / d) / (2 * tan_h)
        E.frame(cam, c, (SIGN_CENTRE_X, min(0.62, 0.92 - dy)), fstop=spec.get("fstop", 4.0))
        return found
    # roadside: camera in the right driving lane, ~0.5 m in from the lane's right edge
    if "lat" in spec:                      # e.g. parking lots: no road edge to measure from
        cam_x = c.x - spec["lat"]
    else:
        edge = road_right_edge()
        cam_x = (edge - 0.3) if c.x > 0 else -(abs(edge) - 0.3)
    lat = c.x - cam_x
    dz = c.z - EYE
    # the sign faces straight down the road, so seen from the lane it is
    # foreshortened by cos(bearing): move closer until its projected width
    # still meets SIGN_FRACTION
    d0 = d
    for _ in range(4):
        horiz = math.sqrt(max(d * d - dz * dz, 1.0))
        fwd = math.sqrt(max(horiz * horiz - lat * lat, 1.0))
        d = d0 * fwd / horiz
    # headroom beats size: if the whole stack (tabs included) can't fit the
    # frame height with >= 5 % margins at this distance, back off just enough
    # and flag it (the 15 % size check is then reported, not enforced)
    tan_h0 = tan_w * sc.render.resolution_y / sc.render.resolution_x
    zlo0 = min([(o.matrix_world @ Vector(v)).z for o in sign_panels() for v in o.bound_box] or [found[3][0].z])
    d_min = (found[3][1].z - zlo0) / (0.84 * 2 * tan_h0)
    if d < d_min:
        d = d_min
        horiz = math.sqrt(max(d * d - dz * dz, 1.0))
        fwd = math.sqrt(max(horiz * horiz - lat * lat, 1.0))
        spec["_size_limited"] = True
    cam.location = (cam_x, c.y - fwd, EYE)
    # turn toward the sign so its centre sits at SIGN_CENTRE_X (55-65 % band)
    # with the road visible on the left; top of the sign ~8 % under the top
    # edge (>= 5 % headroom) so as much road as possible shows below.
    # A template/manifest "screen" x is deliberately ignored: one rule for all.
    lo, hi = found[3]
    tan_h = tan_w * sc.render.resolution_y / sc.render.resolution_x
    dy = ((hi.z - c.z) / d) / (2 * tan_h)
    # bottom of the whole stack (tabs included) below the main sign centre, as screen fraction
    zlo = min([(o.matrix_world @ Vector(v)).z for o in sign_panels() for v in o.bound_box] or [lo.z])
    db = ((c.z - zlo) / d) / (2 * tan_h)
    sy = 0.92 - dy
    if sy - db < 0.07:                 # tall stack: lift it so the bottom keeps its margin
        sy = 0.07 + db
    if sy + dy > 0.93:                 # still doesn't fit: centre it vertically
        sy = 0.5 + (db - dy) / 2
    screen = (SIGN_CENTRE_X, sy)
    E.frame(cam, c, screen, fstop=spec.get("fstop", 4.0))
    return found


def _near_crossbuck():
    """Railway scenes: the crossbuck on the near (approach) signal, facing the camera."""
    bpy.context.view_layer.update()
    xs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("Crossbuck")]
    return min(xs, key=lambda o: o.matrix_world.translation.y) if xs else None


def sign_panels():
    bpy.context.view_layer.update()
    ps = [o for o in bpy.data.objects
          if o.type == "MESH" and o.name.startswith(("Sign_", "OverheadSign_")) and not o.hide_render]
    if not ps:
        xb = _near_crossbuck()
        ps = [xb] if xb else []
    return ps


def square_to_camera():
    """Turn the ground-mounted sign rig about its post so the panel faces the
    camera exactly (no foreshortening). Panels face -Y at yaw 0."""
    rig = bpy.data.objects.get("SignRig")
    cam = bpy.context.scene.camera
    if not rig:
        raise SystemExit("square_to_camera: no SignRig")
    dx, dy = cam.location.x - rig.location.x, cam.location.y - rig.location.y
    rig.rotation_euler[2] = math.atan2(dx, -dy)
    bpy.context.view_layer.update()
    return round(math.degrees(rig.rotation_euler[2]), 1)


def check_framing(found):
    """Main sign centre in CENTRE_RANGE of the width; the whole sign stack
    (main sign + tabs) at least EDGE_MARGIN from every frame edge."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    main = [world_to_camera_view(sc, sc.camera, found[0].matrix_world @ Vector(c)) for c in found[0].bound_box]
    cx = (min(p.x for p in main) + max(p.x for p in main)) / 2
    pts = [world_to_camera_view(sc, sc.camera, o.matrix_world @ Vector(c)) for o in sign_panels() for c in o.bound_box]
    x0, x1 = min(p.x for p in pts), max(p.x for p in pts)
    y0, y1 = min(p.y for p in pts), max(p.y for p in pts)
    m = {"centre_x": round(cx, 3), "margin_left": round(x0, 3), "margin_right": round(1 - x1, 3),
         "margin_bottom": round(y0, 3), "margin_top": round(1 - y1, 3)}
    errs = []
    if not (CENTRE_RANGE[0] <= cx <= CENTRE_RANGE[1]):
        errs.append(f"sign centre at {cx:.1%} of width (needs {CENTRE_RANGE[0]:.0%}-{CENTRE_RANGE[1]:.0%})")
    for k in ("margin_left", "margin_right", "margin_bottom", "margin_top"):
        if m[k] < EDGE_MARGIN:
            errs.append(f"{k.split('_')[1]} margin {m[k]:.1%} (< {EDGE_MARGIN:.0%})")
    if errs:
        raise SystemExit("framing: " + "; ".join(errs))
    return m


def check_bare_poles(allow_two=False):
    """Fail if any sign post is not holding up a sign: every Post_ must end
    inside a panel's height, on the panel's vertical centre line (which every
    sign shape covers; an off-centre post shows as a bare pole beside a diamond
    or disc). Two posts per stack only when the plan says the real sign has two."""
    bpy.context.view_layer.update()
    posts = [o for o in bpy.data.objects if o.type == "MESH" and o.name.split(".")[0].startswith("Post_")]
    panels = [o for o in sign_panels() if o.name.startswith("Sign_")]
    bad = []
    for p in posts:
        plo, phi = _bbox(p, 0.0)
        px, py, ptop = (plo.x + phi.x) / 2, (plo.y + phi.y) / 2, phi.z
        held = False
        for s in panels:
            slo, shi = _bbox(s, 0.0)
            sx, sy = (slo.x + shi.x) / 2, (slo.y + shi.y) / 2
            w = max(shi.x - slo.x, shi.y - slo.y)
            off = math.hypot(px - sx, py - sy)
            tol = (0.32 * w) if allow_two else max(0.06, 0.08 * w)
            if off <= tol and slo.z - 0.02 <= ptop <= shi.z + 0.02:
                held = True
                break
        if not held:
            bad.append(f"{p.name} at ({px:.2f}, {py:.2f}) top {ptop:.2f}")
    if len(posts) > (2 if allow_two else 1):
        bad.append(f"{len(posts)} posts for one sign")
    if bad:
        raise SystemExit("bare pole: " + "; ".join(bad))
    return len(posts)


def sign_width_fraction(found):
    """Projected width of the main sign panel as a fraction of the image width."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    o = found[0]
    xs = [world_to_camera_view(sc, sc.camera, o.matrix_world @ Vector(c)).x for c in o.bound_box]
    return max(xs) - min(xs)


def road_right_edge():
    """Right edge of the main carriageway near the camera (max x of the Road strip)."""
    xs = [v.co.x for o in bpy.data.objects if o.type == "MESH" and o.name in ("Road", "RoadR")
          for v in o.data.vertices if -5 < v.co.y < 40]
    return max(xs) if xs else 3.5


def _bbox(o, pad=0.004):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))) - Vector((pad,) * 3)
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))) + Vector((pad,) * 3)
    return lo, hi


def _touch(a, b):
    (alo, ahi), (blo, bhi) = a, b
    return all(alo[i] <= bhi[i] and blo[i] <= ahi[i] for i in range(3))


def check_overhead_mounts():
    """Every overhead sign and signal head must be physically attached:
    strap touches its panel and a clamp, clamp touches the arm/chord,
    hanger touches a clamp band and the signal housing."""
    bpy.context.view_layer.update()
    obs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    def group(prefix):
        return [_bbox(o) for n, o in obs.items() if n.split(".")[0] == prefix]
    panels = group("OverheadSign_0") + [_bbox(o) for n, o in obs.items() if n.startswith("OverheadSign_")]
    if not panels:
        return 0
    straps, bands, uclamps = group("SignStrap"), group("ClampBand"), group("ChordClamp")
    arms = group("MastArm") + group("SignalArm") + group("TrussChord")
    hangers, housings = group("SignalHanger"), group("Housing")
    errs = []
    for i, st in enumerate(straps):
        if not any(_touch(st, p) for p in panels):
            errs.append(f"strap {i} not on a panel")
        if not any(_touch(st, c) for c in bands + uclamps):
            errs.append(f"strap {i} not at a clamp")
    for i, c in enumerate(bands + uclamps):
        if not any(_touch(c, a) for a in arms):
            errs.append(f"clamp {i} not on the arm/truss")
    for i, h in enumerate(hangers):
        if not any(_touch(h, b) for b in bands):
            errs.append(f"signal hanger {i} not clamped to the arm")
        if not any(_touch(h, hs) for hs in housings):
            errs.append(f"signal hanger {i} not on a signal head")
    over_heads = [hs for hs in housings if hs[0].z > 3.0]
    if len(hangers) < len(over_heads):
        errs.append(f"{len(over_heads)} overhead signal heads but only {len(hangers)} hangers")
    if errs:
        raise SystemExit("overhead mounting: " + "; ".join(errs))
    return len(straps) + len(hangers)


def check_sign_posts():
    """Fail if any sign post stands on asphalt (posts must be on curb or grass)."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    bad = []
    for o in bpy.data.objects:
        if not o.name.startswith("Post_"):
            continue
        p = o.matrix_world.translation
        start = Vector((p.x, p.y, 3.5))
        # skip the post itself and any sign panels above it
        for _ in range(6):
            hit, loc, nrm, idx, ob, _m = sc.ray_cast(dg, start, Vector((0, 0, -1)))
            if not hit:
                break
            if ob.name.startswith(("Post_", "Sign_")):
                start = loc + Vector((0, 0, -0.01))
                continue
            mats = [s.material.name for s in ob.material_slots if s.material]
            if any("Asphalt" in n for n in mats):
                bad.append((o.name, ob.name, round(p.x, 2)))
            break
    if bad:
        raise SystemExit(f"sign post on asphalt: {bad}")


def clear_side_road_driveways():
    """House driveways run to the curb; where a side road cuts the curb they
    stuck out into it as raised blocks. Remove those."""
    bpy.context.view_layer.update()
    roads = []
    for o in bpy.data.objects:
        if o.name.startswith("SideRoad"):
            ys = [(o.matrix_world @ Vector(c)).y for c in o.bound_box]
            roads.append((min(ys) - 2.0, max(ys) + 2.0))
    gone = 0
    for o in list(bpy.data.objects):
        if o.name.startswith("Driveway"):
            ys = [(o.matrix_world @ Vector(c)).y for c in o.bound_box]
            if any(min(ys) < b and max(ys) > a for a, b in roads):
                bpy.data.objects.remove(o)
                gone += 1
    return gone


def drop_clipped_trees():
    """Remove trees whose canopy is cut off by the top of the frame."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = sc.camera
    bpy.context.view_layer.update()
    gone = 0
    for o in list(bpy.data.objects):
        kind = o.get("g1_kind", "")
        if not (kind.startswith("tree") or o.name.startswith("Tree")):
            continue
        s = o.scale.z
        top = world_to_camera_view(sc, cam, o.location + Vector((0, 0, 10.3 * s)))
        base = world_to_camera_view(sc, cam, o.location)
        left = world_to_camera_view(sc, cam, o.location + Vector((-5.5 * s, 0, 6 * s)))
        right = world_to_camera_view(sc, cam, o.location + Vector((5.5 * s, 0, 6 * s)))
        in_front = base.z > 0
        overlaps = min(left.x, right.x, base.x) < 1.0 and max(left.x, right.x, base.x) > 0.0
        if in_front and overlaps and top.y > 1.0:
            bpy.data.objects.remove(o)
            gone += 1
    return gone


def sign_screen_rect(found, pad=0.015):
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    lo, hi = found[3]
    pts = [world_to_camera_view(sc, sc.camera, Vector((x, y, z)))
           for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    return (min(p.x for p in pts) - pad, min(p.y for p in pts) - pad,
            max(p.x for p in pts) + pad, max(p.y for p in pts) + pad)


def _tweak_10_spec(spec):
    # Yield: the sign has to sit at a visible intersection
    # the ground first shows ~17 m ahead of the camera (see EYE), i.e. ~11 m past the sign
    spec["features"] = [{"type": "side_road", "at": spec.get("sign_dist", 14.0) + 13.0, "side": "both"}]


def _tweak_10_scene(spec):
    from g1scenes import props
    at = spec.get("sign_dist", 14.0) + 13.0
    # cross traffic on the through road, coming from the right (in view, clear of the sign)
    props.car(9.0, at + 1.75, 90.0, "silver")


IMAGE_TWEAKS = {"10": {"spec": _tweak_10_spec, "scene": _tweak_10_scene}}


def pick_engine(want):
    """Cycles on the GPU if one is available (HIP for AMD), else EEVEE."""
    sc = bpy.context.scene
    if want in ("auto", "cycles"):
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("HIP", "OPTIX", "CUDA", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = t
            except TypeError:
                continue
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type != "CPU"]
            # skip integrated graphics (e.g. "AMD Radeon(TM) Graphics") when a discrete GPU exists
            discrete = [d for d in gpus if "(TM) Graphics" not in d.name and "Intel" not in d.name]
            gpus = discrete or gpus
            if gpus:
                for d in prefs.devices:
                    d.use = d in gpus
                sc.render.engine = "CYCLES"
                sc.cycles.device = "GPU"
                return f"Cycles GPU ({t}: {', '.join(d.name for d in gpus)})"
        if want == "cycles":
            sc.render.engine = "CYCLES"
            sc.cycles.device = "CPU"
            return "Cycles CPU"
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 128
    return "EEVEE"


def install(name, rendered):
    if not os.path.isdir(BACKUP):
        raise SystemExit(f"backup folder missing ({BACKUP}); back up the imagesets first")
    folder = os.path.join(IMAGESETS, f"{name}.imageset")
    if not os.path.isdir(folder):
        raise SystemExit(f"no imageset {folder}")
    if not os.path.isdir(os.path.join(BACKUP, f"{name}.imageset")):
        raise SystemExit(f"{name}.imageset is not in the backup")
    for f in os.listdir(folder):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            os.remove(os.path.join(folder, f))
    images = []
    for scale, width in SCALES.items():
        fname = f"{name}.png" if scale == "1x" else f"{name}@{scale}.png"
        img = bpy.data.images.load(rendered)
        if img.size[0] != width:
            img.scale(width, round(width / 2.4))
        img.filepath_raw = os.path.join(folder, fname)
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
        images.append({"filename": fname, "idiom": "universal", "scale": scale})
    with open(os.path.join(folder, "Contents.json"), "w") as f:
        json.dump({"images": images, "info": {"author": "xcode", "version": 1}}, f, indent=2)
    print("installed", folder)


def main(argv=None):
    if argv is None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated imageNames, e.g. 10,53,120")
    ap.add_argument("--quality", default="final", choices=["preview", "draft", "final"])
    ap.add_argument("--engine", default="auto", choices=["auto", "cycles", "eevee"])
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--save-blend", action="store_true")
    ap.add_argument("--no-render", action="store_true", help="build, frame and check only")
    args = ap.parse_args(argv)

    manifest = load(os.path.join(HERE, "manifest.json"))
    scene_specs = load(os.path.join(SCENES, "manifest.json"))["images"]
    sign_map = {k: v for k, v in load(os.path.join(HERE, "sign_map.json")).items() if not k.startswith("_")}
    entries = manifest["images"]
    if args.only:
        want = set(args.only.split(","))
        entries = [e for e in entries if e["imageName"] in want]
        missing = want - {e["imageName"] for e in entries}
        if missing:
            raise SystemExit(f"not in manifest: {sorted(missing)}")
    os.makedirs(OUT, exist_ok=True)

    for entry in entries:
        n = entry["imageName"]
        spec = build_spec(entry, scene_specs, sign_map)
        t0 = time.time()
        from g1scenes import props
        props._TREE_PROTOS.clear()      # cached objects die with each scene reset (matters in a live Blender)
        realism.reset_cache()
        templates.get(spec["template"]).build(spec, args.quality)
        tweak = IMAGE_TWEAKS.get(n, {})
        if tweak.get("scene"):
            tweak["scene"](spec)
        for ex in spec.get("extras", []):          # e.g. a car stopped at the stop line (spec_overrides.json)
            if ex["type"] == "car":
                x = road_right_edge() - ex["from_right_edge"] if "from_right_edge" in ex else ex["x"]
                props.car(x, ex["y"], ex.get("heading", 0.0), ex.get("colour", "silver"), brake=ex.get("brake", False))
        clear_side_road_driveways()
        found = place_camera(spec)
        yaw = square_to_camera() if (found and spec.get("square_to_camera")) else None
        check_sign_posts()
        posts = check_bare_poles(allow_two=spec.get("posts", 1) == 2)
        check_overhead_mounts()
        dropped = drop_clipped_trees()
        frac, framing = None, {}
        if not found and spec["template"] in SIGN_TEMPLATES:
            raise SystemExit(f"image {n}: no sign panel in the scene (artwork missing?)")
        if found:
            frac = sign_width_fraction(found)
            if frac < spec.get("min_sign_fraction", 0.0 if spec.get("_size_limited") else 0.15):
                raise SystemExit(f"image {n}: sign is only {frac:.1%} of the image width (< 15 %)")
            framing = check_framing(found)
            print(f"sign {found[0].name}: {found[2]:.2f} m wide = {frac:.1%} of width, framing {framing}, "
                  f"camera {tuple(round(v, 2) for v in bpy.context.scene.camera.location)}, dropped {dropped} clipped trees")
        if spec["weather"] == "rain" and found:
            realism.rain_streaks(bpy.context.scene.camera, sign_screen_rect(found))
        if spec["weather"] == "night" and found:
            # the template aimed headlights from its own camera spot; re-aim from the final camera
            for o in [o for o in bpy.data.objects if o.name.startswith("Headlight")]:
                bpy.data.objects.remove(o)
            E.headlights(bpy.context.scene.camera, found[1])
        if args.no_render:
            continue
        engine = pick_engine(args.engine)
        sc = bpy.context.scene
        sc.render.resolution_x, sc.render.resolution_y = 2400, 1000
        sc.render.resolution_percentage = 100 if args.quality == "final" else 40
        out = os.path.join(OUT, f"{n}.png")
        sc.render.filepath = out
        if args.save_blend:
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{n}.blend"))
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        t2 = time.time()
        print("RESULT " + json.dumps({
            "image": n, "path": "full", "base": spec["template"], "weather": spec["weather"], "engine": engine,
            "sign_fraction": round(frac, 4) if frac else None, "framing": framing, "posts": posts,
            "square_yaw_deg": yaw, "size_limited_by_headroom": bool(spec.get("_size_limited")), "dropped_trees": dropped, "prep_s": round(t1 - t0, 1),
            "render_s": round(t2 - t1, 1),
            "gpu_render_s": round(t2 - t1, 1) if engine.startswith("Cycles GPU") else None, "out": out}))
        if args.install:
            if args.quality != "final":
                raise SystemExit("--install needs --quality final")
            install(n, out)


if __name__ == "__main__":   # blender -b -P render.py -- ...
    main()
