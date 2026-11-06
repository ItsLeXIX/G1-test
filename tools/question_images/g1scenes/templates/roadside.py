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
    road.update(spec.get("road", {}))
    path = R.Path(curves=spec.get("curves", ()), hills=spec.get("hills", ()))
    R.ground(look["snow"])
    R.standard_road(path, road)

    # ------------------------------------------------------------ features
    skip_trees = [(dist - 9, dist + 6)]
    if "side_road" in feats:
        sr = feats["side_road"]
        R.cross_road(path, sr["at"], sr.get("side", "both"), snow=look["snow"], wet=look["wet"])
        if sr.get("hidden"):
            # a hedge of conifers hides the side road until you are close
            P.tree_row(path, road["_right_edge"] + 4, sr["at"] - 30, sr["at"] - 6, 3.0, "conifer", 9, snow=look["snow"])
        skip_trees.append((sr["at"] - 8, sr["at"] + 8))
    if "signals" in feats:
        at = feats["signals"]["at"]
        x, y, z = path.offset(path.index_at(at), 0)
        R.cross_road(path, at, "both", snow=look["snow"], wet=look["wet"])
        # one head over each approach lane
        lanes = road.get("lanes_right", 1)
        P.signal_mast(x + road["_right_edge"] + 1.0, y - 3, [x + 1.75 + 3.5 * k for k in range(lanes)])
    if "rail" in feats:
        R.rail_crossing(path, feats["rail"]["at"], angle=feats["rail"].get("angle", 0))
        x, y, z = path.offset(path.index_at(feats["rail"]["at"] - 6), road["_right_edge"] + 2.5)
        P.crossing_signal(x, y, flashing=False)
    if "bridge" in feats:
        b = feats["bridge"]
        P.bridge(path, b["at"], b.get("length", 40), b.get("width", 6.2), lift_towers=b.get("lift", False))
        skip_trees.append((b["at"] - 5, b["at"] + b.get("length", 40) + 5))
    if "overpass" in feats:
        o = feats["overpass"]
        P.overpass(o["at"], clearance=o.get("clearance", 3.8))
        skip_trees.append((o["at"] - 20, o["at"] + 20))
    if "rock_cut" in feats:
        rc = feats["rock_cut"]
        side = 1 if rc.get("side", "right") == "right" else -1
        edge = road["_right_edge"] if side > 0 else road["_left_edge"]
        P.rock_cut(path, rc["from"], rc["to"], edge + side * 2.5)
        skip_trees.append((rc["from"], rc["to"]))
    if "island" in feats:
        isl = feats["island"]
        w = isl.get("width", 3.0)
        i0, i1 = path.index_at(isl["from"]), path.index_at(isl["to"])
        R.ribbon(path, "Island", -w / 2, w / 2, 0.15, C.grass(look["snow"]), i0=i0, i1=i1, wall_to=-0.1)
        R.ribbon(path, "IslandCurb", -w / 2 - 0.15, -w / 2, 0.15, C.concrete("Curb", 3.0), i0=i0, i1=i1, wall_to=-0.1)
        R.ribbon(path, "IslandCurb", w / 2, w / 2 + 0.15, 0.15, C.concrete("Curb", 3.0), i0=i0, i1=i1, wall_to=-0.1)
    if "lane_drop" in feats:
        ld = feats["lane_drop"]
        # dashed lane line that ends where the right lane tapers away
        R.line(path, "LaneDrop", road["_right_edge"] - 3.5, 0.1, C.paint("white"), 3, 6,
               i1=path.index_at(ld["at"]))
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
        P.tree_row(path, road["_left_edge"] - 1.4, 0, 220, 14, seed=3, snow=snow)
        P.house_rows(road, snow=snow, skip_right=[(dist - 12, dist + 6)])
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
                           seed + k * 10, skip=skip_trees if side > 0 else (), snow=snow, jitter=6)

    # ---------------------------------------------------------------- sign
    side = spec.get("sign_side", "right")
    i = path.index_at(dist)
    if side == "island":
        isl = feats["island"]
        i = path.index_at(isl["from"] + 1.0)
        x, y, z = path.offset(i, 0)
        bottom = spec.get("sign_bottom", 0.9)
    elif side == "left":
        x, y, z = path.offset(i, road["_left_edge"] - 1.2)
        bottom = spec.get("sign_bottom", 2.1)
    else:
        off = spec.get("sign_offset")   # metres from the road edge (pole on curb/grass)
        x, y, z = path.offset(i, road["_right_edge"] + off if off is not None
                              else road.get("_roadside_right", road["_right_edge"] + 1.2))
        bottom = spec.get("sign_bottom", 2.1 if setting == "suburban" else 1.6)
    objs, centre = S.ground_mount(sign_items(spec), x, y, bottom=bottom, z0=z + (0.13 if setting == "suburban" else 0),
                                  yaw=spec.get("sign_yaw", 0), night=look["night"], posts=spec.get("posts", 1))

    cam = E.camera(tuple(spec.get("camera", (1.75 if side != "island" else 3.2, 0.0, E.EYE_HEIGHT))),
                   spec.get("lens", 50.0))
    finish(cam, centre, spec, look)
