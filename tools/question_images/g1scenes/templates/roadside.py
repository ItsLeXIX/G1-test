"""Sign on a post beside the road — the most common question picture.

spec keys (all optional except "sign"):
  setting       suburban | rural | construction
  sign_dist     metres ahead of the camera to the sign (default 14)
  sign_side     right | left | island
  curves, hills Path segments (see roads.Path); the road ahead shows the
                curve/hill the sign warns about
  road          dict merged into the road config (lanes_right, centre, ...)
  features      list of dicts, each with "type":
      side_road  {at, side: right|left|both, hidden: bool}
      signals    {at}                        traffic lights ahead
      rail       {at}                        tracks crossing the road
      gravel     {at}                        pavement ends
      bridge     {at, length, width, lift}   narrow / lift bridge
      overpass   {at, clearance}
      rock_cut   {from, to, side}
      island     {from, to, width}           raised median island / divided road
      lane_drop  {at, side}                  lane ends (taper)
      crosswalk  {at}
      cones      {from, to, offset}
"""
import bpy

from .. import common as C
from .. import env as E
from .. import props as P
from .. import roads as R
from .base import S, finish, setup, sign_items


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    setting = spec.get("setting", "suburban")
    feats = {f["type"]: f for f in spec.get("features", [])}
    dist = spec.get("sign_dist", 14.0)

    road = {"edge": "curb" if setting == "suburban" else "shoulder",
            "centre": "broken_yellow", "wet": look["wet"], "snow": look["snow"]}
    if setting == "construction":
        road["edge"] = "shoulder"
    if "gravel" in feats:
        road["surface_change"] = {"at": feats["gravel"]["at"]}
    if "island" in feats:
        road["centre"] = f"flush:{feats['island'].get('width', 3.0) + 0.6}"
    for key in ("side_road", "signals"):
        if key not in feats:
            continue
        sr = feats[key]
        gap = [(sr["at"] - 5, sr["at"] + 5)]
        if sr.get("side", "both") in ("both", "right"):
            road["gaps_right"] = gap
        if sr.get("side", "both") in ("both", "left"):
            road["gaps_left"] = gap
    if "bridge" in feats:
        b = feats["bridge"]
        gap = (b["at"] + 1.5, b["at"] + b.get("length", 40) - 1.5)
        road["gaps_right"] = road.get("gaps_right", []) + [gap]
        road["gaps_left"] = road.get("gaps_left", []) + [gap]
    if "roundabout" in feats:
        rb_ = feats["roundabout"]
        rr_ = rb_.get("radius", 18.0)
        lip = rr_ - (rr_ ** 2 - (3.5 + 0.0) ** 2) ** 0.5          # where the road's edge meets the circle
        road["carriage_gaps"] = [(rb_["at"] + lip, rb_["at"] + 2 * rr_ - lip)]
    if "on_ramp" in feats:
        r_ = feats["on_ramp"]
        r_tap, r_par = r_.get("taper", 50.0), r_.get("parallel", 55.0)
        road["edge_gaps_right"] = [(r_["at"] - r_tap - r_par, r_["at"] - r_tap)]
    road.update(spec.get("road", {}))
    path = R.Path(curves=spec.get("curves", ()), hills=spec.get("hills", ()))
    if spec.get("hills"):
        R.terrain(path, look["snow"], drop=0.07)      # ground follows the hill
    else:
        R.ground(look["snow"], z=-1.7 if "bridge" in feats else -0.06)     # a river under a bridge needs the lower plane
    R.standard_road(path, road)

    # ------------------------------------------------------------ features
    skip_trees = [(dist - 9, dist + 6)]
    skip_left = []
    if "side_road" in feats:
        sr = feats["side_road"]
        R.cross_road(path, sr["at"], sr.get("side", "both"), snow=look["snow"], wet=look["wet"])
        if sr.get("hidden"):
            # a hedge of conifers hides the side road until you are close
            P.tree_row(path, road["_right_edge"] + 4, sr["at"] - 30, sr["at"] - 6, 3.0, "conifer", 9, snow=look["snow"])
        skip_trees.append((sr["at"] - 8, sr["at"] + 8))
        skip_left.append((sr["at"] - 8, sr["at"] + 8))
    if "signals" in feats:
        at = feats["signals"]["at"]
        x, y, z = path.offset(path.index_at(at), 0)
        R.cross_road(path, at, "both", snow=look["snow"], wet=look["wet"])
        # one head over each approach lane
        lanes = road.get("lanes_right", 1)
        P.signal_mast(x + road["_right_edge"] + 1.0, y - 3, [x + 1.75 + 3.5 * k for k in range(lanes)])
        skip_trees.append((at - 8, at + 8))
        skip_left.append((at - 8, at + 8))
    if "rail" in feats:
        rf = feats["rail"]
        sh_ = road.get("shoulder", 1.8)
        R.rail_crossing(path, rf["at"], angle=rf.get("angle", 0), span=(road["_left_edge"] - sh_, road["_right_edge"] + sh_))
        if not rf.get("no_signal"):
            x, y, z = path.offset(path.index_at(rf["at"] - 6), road["_right_edge"] + 2.5)
            P.crossing_signal(x, y, flashing=False, art="RA-006.png")
        skip_trees.append((rf["at"] - 14, rf["at"] + 14))
        skip_left.append((rf["at"] - 14, rf["at"] + 14))
    if "roundabout" in feats:
        rb = feats["roundabout"]
        rr = rb.get("radius", 18.0)
        cx, cy = R.roundabout(rb["at"], rr, half_road=road["_right_edge"], wet=look["wet"], snow=look["snow"])
        for k, (dx, dy, sc_) in enumerate(((0.0, 0.5, 0.55), (-3.2, -2.2, 0.45), (3.0, -2.6, 0.4))):
            P.tree(cx + dx, cy + dy, 0.9, "deciduous" if k else "conifer", sc_, 40 + k, look["snow"])
        skip_trees.append((rb["at"] - 10, rb["at"] + 2 * rr + 10))
        skip_left.append((rb["at"] - 10, rb["at"] + 2 * rr + 10))
    if "bridge" in feats:
        b = feats["bridge"]
        P.bridge(path, b["at"], b.get("length", 40), b.get("width", 6.2), lift_towers=b.get("lift", False))
        skip_trees.append((b["at"] - 5, b["at"] + b.get("length", 40) + 5))
    if "overpass" in feats:
        o = feats["overpass"]
        P.overpass(o["at"], clearance=o.get("clearance", 3.8), abut=o.get("abut", 9.0))
        skip_trees.append((o["at"] - 20, o["at"] + 20))
    if "rock_cut" in feats:
        rc = feats["rock_cut"]
        side = 1 if rc.get("side", "right") == "right" else -1
        edge = road["_right_edge"] if side > 0 else road["_left_edge"]
        P.rock_cut(path, rc["from"], rc["to"], edge + side * rc.get("offset", 1.6), height=rc.get("height", 7.0), side=side)
        skip_trees.append((rc["from"], rc["to"]))
    if "island" in feats:
        isl = feats["island"]
        w = isl.get("width", 3.0)
        i0, i1 = path.index_at(isl["from"]), path.index_at(isl["to"])
        top = C.concrete("IslandTop", 2.0, (0.62, 0.61, 0.58)) if isl.get("surface") == "concrete" else C.grass(look["snow"])
        R.ribbon(path, "Island", -w / 2, w / 2, 0.15, top, i0=i0, i1=i1, wall_to=-0.1)
        R.ribbon(path, "IslandCurb", -w / 2 - 0.15, -w / 2, 0.15, C.concrete("Curb", 3.0), i0=i0, i1=i1, wall_to=-0.1)
        R.ribbon(path, "IslandCurb", w / 2, w / 2 + 0.15, 0.15, C.concrete("Curb", 3.0), i0=i0, i1=i1, wall_to=-0.1)
        if isl.get("nose"):
            # rounded concrete nose with its curb, where approaching traffic meets the island
            nx, ny, nz = path.offset(i0, 0)
            C.cylinder("IslandNoseCurb", w / 2 + 0.15, -0.1, 0.149, nx, ny, C.concrete("Curb", 3.0), seg=40)
            C.cylinder("IslandNose", w / 2, -0.1, 0.151, nx, ny, top, seg=40)
    if "hump" in feats:
        # speed hump / road bump across the carriageway: smooth 3.6 m long, 0.11 m high rise, white chevron markings
        import math as _m
        at_ = feats["hump"]["at"]
        le_, re_ = road["_left_edge"], road["_right_edge"]
        v_, f_ = [], []
        n_ = 24
        for k in range(n_ + 1):
            y_ = at_ - 1.8 + 3.6 * k / n_
            h_ = 0.11 * _m.sin(_m.pi * k / n_) ** 2
            v_ += [(le_, y_, h_), (re_, y_, h_)]
            if k:
                a_ = 2 * (k - 1)
                f_.append((a_, a_ + 1, a_ + 3, a_ + 2))
        C.mesh_object("RoadHump", v_, f_, [C.asphalt(look["wet"], look["snow"])])
        wp_ = C.paint("white")
        x_ = le_ + 0.3
        while x_ + 0.9 < re_:
            for dy_ in (-1.2, 0.6):                         # row of white triangles on each slope
                vv_, ff_ = [], []
                for q_, (px_, py_) in enumerate(((x_, at_ + dy_), (x_ + 0.9, at_ + dy_), (x_ + 0.45, at_ + dy_ + 0.6))):
                    k_ = int(round((py_ - (at_ - 1.8)) / 3.6 * n_))
                    hz_ = 0.11 * _m.sin(_m.pi * max(0, min(n_, k_)) / n_) ** 2 + 0.006
                    vv_.append((px_, py_, hz_))
                C.mesh_object("HumpMark", vv_, [(0, 1, 2)], [wp_])
            x_ += 1.4
    if "lane_drop" in feats:
        ld = feats["lane_drop"]
        # dashed lane line that ends where the right lane tapers away
        R.line(path, "LaneDrop", road["_right_edge"] - 3.5, 0.1, C.paint("white"), 3, 6,
               i1=path.index_at(ld["at"]))
    if "on_ramp" in feats:
        _on_ramp(road, feats["on_ramp"], look)
        skip_trees.append((feats["on_ramp"]["at"] - 110, feats["on_ramp"]["at"] + 8))
    if "crosswalk" in feats:
        at = feats["crosswalk"]["at"]
        x, y, z = path.offset(path.index_at(at), 0)
        w = C.paint("white")
        le, re = road["_left_edge"], road["_right_edge"]
        for k in range(int((re - le) / 1.0)):
            xx = le + 0.25 + k * 1.0
            C.box("Zebra", xx, xx + 0.5, y, y + 3.0, 0, 0.004, w)
    if "cones" in feats:
        cf = feats["cones"]
        d = cf["from"]
        while d < cf["to"]:
            x, y, z = path.offset(path.index_at(d), cf.get("offset", road["_right_edge"] - 0.5))
            P.cone(x, y)
            d += cf.get("spacing", 6)

    # ------------------------------------------------------------- scenery
    snow = look["snow"]
    if setting == "suburban":
        P.tree_row(path, road["_right_edge"] + 1.4, 0, 220, 14, seed=2, skip=skip_trees, snow=snow)
        P.tree_row(path, road["_left_edge"] - 1.4, 0, 220, 14, seed=3, skip=skip_left, snow=snow)
        hs_r, hs_l = [(dist - 12, dist + 6)], []
        for key in ("side_road", "signals"):
            if key in feats:
                hs_r.append((feats[key]["at"] - 8, feats[key]["at"] + 8))
                hs_l.append((feats[key]["at"] - 8, feats[key]["at"] + 8))
        P.house_rows(road, snow=snow, skip_right=hs_r, skip_left=hs_l)
        if look["night"]:
            for d in (30, 75, 120):
                x, y, z = path.offset(path.index_at(d), road["_left_edge"] - 1.0)
                P.streetlight(x, y, side=-1, on=True)
    else:
        kind = spec.get("trees", "mixed")
        for side, seed in ((1, 4), (-1, 5)):
            edge = road["_right_edge"] if side > 0 else road["_left_edge"]
            for k, off in enumerate((14, 22, 30)):
                P.tree_row(path, edge + side * off, 10, 300, 9,
                           "conifer" if (kind == "conifer" or (kind == "mixed" and k % 2)) else "deciduous",
                           seed + k * 10, skip=skip_trees if side > 0 else skip_left, snow=snow, jitter=6)

    # ---------------------------------------------------------------- sign
    side = spec.get("sign_side", "right")
    i = path.index_at(dist)
    if side == "island":
        isl = feats["island"]
        i = path.index_at(isl["from"] + spec.get("island_sign_setback", 1.0))
        x, y, z = path.offset(i, 0)
        bottom = spec.get("sign_bottom", 0.9)
    elif side == "left":
        x, y, z = path.offset(i, road["_left_edge"] - (spec["sign_offset"] if spec.get("sign_offset") is not None else 1.2))
        bottom = spec.get("sign_bottom", 2.1)
    else:
        off = spec.get("sign_offset")   # metres from the road edge (pole on curb/grass)
        x, y, z = path.offset(i, road["_right_edge"] + off if off is not None
                              else road.get("_roadside_right", road["_right_edge"] + 1.2))
        bottom = spec.get("sign_bottom", 2.1 if setting == "suburban" else 1.6)
    objs, centre = S.ground_mount(sign_items(spec), x, y, bottom=bottom, z0=z + (0.13 if setting == "suburban" else 0),
                                  yaw=spec.get("sign_yaw", 0), night=look["night"], posts=spec.get("posts", 1))
    if spec.get("beacons"):
        _beacons(objs, sign_items(spec), spec["beacons"])

    cam = E.camera(tuple(spec.get("camera", (1.75 if side != "island" else 3.2, 0.0, E.EYE_HEIGHT))),
                   spec.get("lens", 50.0))
    finish(cam, centre, spec, look)


def _beacons(objs, items, cfg):
    """Two amber flashing beacons either side of a sign assembly (school zone
    'WHEN FLASHING'): a horizontal arm from the post on each side, a short
    drop, and a round amber beacon head with a visor, facing traffic.
    cfg: {"arm_at": fraction of the top panel's height for the arms,
          "head_at": fraction for the beacon centres}."""
    import math
    rig = next(o for o in bpy.data.objects if o.name.startswith("SignRig") and objs[0].parent == o)
    top = next(o for o in objs if o.name.startswith("Sign_") and o.name.split(".")[0] == f"Sign_{len(items) - 1}")
    art, w = items[0]
    h = S._h(art, w)
    zb = top.location.z
    za, zh = zb + h * cfg.get("arm_at", 0.68), zb + h * cfg.get("head_at", 0.57)
    galv = C.mat("Galvanised", (0.56, 0.57, 0.58), 0.45, 1.0)
    black = C.mat("BeaconHousing", (0.03, 0.03, 0.03), 0.5)
    lit = C.emissive("BeaconAmber", (1.0, 0.55, 0.02), 25.0)
    made = []
    for sx in (-1, 1):
        xo = sx * (w / 2 + 0.30)
        arm = C.cylinder("BeaconArm", 0.025, 0, abs(xo), mat=galv, seg=12)
        arm.rotation_euler = (0, math.radians(90 * sx), 0)
        arm.location = (0, 0.04, za)
        drop = C.cylinder("BeaconArm", 0.025, zh + 0.12, za + 0.025, xo, 0.04, galv, None, 12)
        head = C.cylinder("BeaconHead", 0.15, 0, 0.16, mat=black, seg=28)
        head.rotation_euler = (math.radians(90), 0, 0)
        head.location = (xo, 0.12, zh)
        lens = C.cylinder("BeaconLens", 0.11, 0, 0.012, mat=lit, seg=28)
        lens.rotation_euler = (math.radians(90), 0, 0)
        lens.location = (xo, -0.04, zh)
        visor = C.cylinder("BeaconVisor", 0.155, 0, 0.18, mat=black, seg=28)
        visor.rotation_euler = (math.radians(90), 0, 0)
        visor.location = (xo, -0.04, zh)
        visor.scale = (1.0, 1.0, 1.0)
        # cut the visor to its upper half so it reads as a hood
        import bmesh
        bm = bmesh.new(); bm.from_mesh(visor.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.02], context="VERTS")
        bm.to_mesh(visor.data); bm.free()
        made += [arm, drop, head, lens, visor]
    for o in made:
        o["g1_sign"] = 1
        o.parent = rig


def _on_ramp(road, cfg, look):
    """Entrance ramp joining from the right (straight road along +Y).

    The ramp swings in from the field on a curve, runs beside the through lane
    as an acceleration lane (broken white line between them), then tapers: its
    pavement narrows to nothing at cfg["at"] with its inner edge exactly on the
    road's edge, so both surfaces are at height 0 and meet with no gap and no
    overlap. The road's solid edge line is replaced by the broken line along the
    acceleration lane and resumes (continuous) for the taper; the ramp has its
    own white edge lines on both sides. Nothing stops inside the frame: the
    ramp's start is behind the camera and its end is the zero-width taper."""
    re = road["_right_edge"]
    at = cfg["at"]
    w = cfg.get("width", 3.75)
    taper, parallel = cfg.get("taper", 50.0), cfg.get("parallel", 55.0)
    y_taper0 = at - taper
    y_par0 = y_taper0 - parallel           # ramp lane becomes parallel to the road here
    k = cfg.get("swing_k", 0.0156)         # lateral drift of the ramp before it runs parallel: k * d^2
    y_start = -140.0                       # far behind the camera

    def inner(y):
        return re if y >= y_par0 else re + k * (y_par0 - y) ** 2

    def outer(y):
        if y >= y_taper0:
            return re + w * max(0.0, (at - y) / taper)
        return inner(y) + w
    ys = [y_start + j * (at - y_start) / 220 for j in range(221)]
    ys = sorted(set(ys + [y_par0, y_taper0, at]))
    asph = C.asphalt(look["wet"], look["snow"])
    verts, faces = [], []
    for j, y in enumerate(ys):
        verts += [(inner(y), y, 0.0), (outer(y), y, 0.0)]
        if j:
            a_ = 2 * (j - 1)
            faces.append((a_, a_ + 1, a_ + 3, a_ + 2))
    C.mesh_object("RoadMerge", verts, faces, [asph])
    # gravel shoulder along the ramp's outer edge (full-width lane with its own shoulder, tapering out with the ramp)
    sv, sf = [], []
    for j, y in enumerate(ys):
        sw = 1.8 * max(0.0, min(1.0, (at - y) / taper))
        o_ = outer(y)
        sv += [(o_, y, -0.012), (o_ + sw, y, -0.012)]
        if j:
            a_ = 2 * (j - 1)
            sf.append((a_, a_ + 1, a_ + 3, a_ + 2))
    C.mesh_object("RampShoulder", sv, sf, [C.gravel()])
    white = C.paint("white")

    def stripe(name, fx, y0, y1, width=0.15, dash=None, gap=None):
        v, f = [], []
        ysx = [y0 + j * (y1 - y0) / 120 for j in range(121)]
        for j, y in enumerate(ysx):
            x = fx(y)
            v += [(x - width / 2, y, 0.006), (x + width / 2, y, 0.006)]
            if j:
                a_ = 2 * (j - 1)
                f.append((a_, a_ + 1, a_ + 3, a_ + 2))
        C.mesh_object(name, v, f, [white])
    stripe("RampEdgeOuter", lambda y: outer(y) - 0.2, y_start, at - 0.5)
    stripe("RampGoreLine", lambda y: inner(y) + 0.2, y_start, y_par0)
    # broken line (3 m / 6 m) between the acceleration lane and the through lane
    y = y_par0
    while y < y_taper0:
        C.box("RampDash", re - 0.075, re + 0.075, y, min(y + 3.0, y_taper0), 0.004, 0.007, white)
        y += 9.0
    # the through road's solid edge line stays continuous: it just resumes at the taper
    return y_par0, y_taper0
