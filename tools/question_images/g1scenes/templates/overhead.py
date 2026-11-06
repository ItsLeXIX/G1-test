"""Sign hung over the lanes.

spec keys:
  setting     city (mast arm at a signalised intersection, buildings)
              | highway (two-post truss over a freeway)
  sign_dist   metres to the structure (default 24 city / 60 highway)
  sign_x      lateral position of the sign centre (default: over lane 1 right)
  signals     true: add signal heads on the mast arm (city)
  twltl       true: two-way left-turn lane markings in the centre lane
  camera      override camera location, e.g. [1.75, 0, 7] for a high view
"""
from .. import common as C
from .. import env as E
from .. import props as P
from .. import roads as R
from .base import S, finish, setup, sign_items


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    setting = spec.get("setting", "city")
    city = setting == "city"
    R.ground(look["snow"])
    path = R.Path()
    road = {"lanes_right": 2, "lanes_left": 2, "centre": "double_yellow",
            "edge": "curb", "boulevard": 1.0, "sidewalk": 2.5, "wet": look["wet"], "snow": look["snow"]}
    if not city:
        road = {"lanes_right": 3, "lanes_left": 3, "lane_w": 3.75, "centre": "barrier",
                "edge": "shoulder", "shoulder": 3.0, "wet": look["wet"], "snow": look["snow"]}
    if spec.get("twltl"):
        road.update(lanes_right=1, lanes_left=1, centre="flush:3.6")
    road.update(spec.get("road", {}))
    dist = spec.get("sign_dist", 17.0 if city else 45.0)
    if city:
        road["gaps_right"] = road["gaps_left"] = [(dist - 6, dist + 14)]
    R.standard_road(path, road)

    if spec.get("twltl"):
        y_ = C.paint("yellow")
        for sx in (-1, 1):
            # solid outer + broken inner yellow on each side of the centre lane
            R.line(path, "TwltlSolid", sx * 1.9, 0.1, y_)
            R.line(path, "TwltlBroken", sx * 1.65, 0.1, y_, 3, 6)
        # opposing left-turn arrows painted in the centre lane
        w = C.paint("white")
        for d, flip in ((14, 1), (30, -1), (46, 1)):
            C.box("ArrowStem", -0.08, 0.08, d, d + 2.4, 0, 0.004, w)
            C.box("ArrowHead", -0.08 - flip * 0.6, 0.08, d + 2.4 if flip > 0 else d - 0.2, d + 2.6 if flip > 0 else d, 0, 0.004, w)

    if city:
        R.cross_road(path, dist + 4, "both", width=14, snow=look["snow"], wet=look["wet"])
        re, le = road["_right_edge"], road["_left_edge"]
        P.city_block(re + 3.8, -10, dist - 6, 1, seed=21)
        P.city_block(re + 3.8, dist + 14, 220, 1, seed=22)
        P.city_block(le - 3.8, -10, dist - 6, -1, seed=23)
        P.city_block(le - 3.8, dist + 14, 220, -1, seed=24)
        # zebra crosswalk on the near side of the intersection
        wpaint = C.paint("white")
        C.box("StopBar", 0.2, re, dist - 4.2, dist - 3.8, 0, 0.004, wpaint)
        for k in range(int((re - le) / 1.0)):
            xx = le + 0.3 + k * 1.0
            C.box("Zebra", xx, xx + 0.5, dist - 3.4, dist - 0.4, 0, 0.004, wpaint)
        for d in (15, 70, 120):
            P.streetlight(re + 1.5, d, side=1, on=look["night"])
        P.car(5.25, dist + 24, 0, "white")
        P.car(-1.75, dist + 40, 180, "grey")
    else:
        for side in (1, -1):
            e = road["_right_edge"] if side > 0 else road["_left_edge"]
            P.tree_row(path, e + side * 18, 0, 400, 7, "conifer" if side > 0 else "deciduous", 7 + side, jitter=8)

    x_left = road["_left_edge"] - (0.5 if city else 3.5)
    x_right = road["_right_edge"] + (0.6 if city else 3.5)
    items = sign_items(spec)
    if city and spec.get("signals", True):
        objs, centre = S.overhead_span(0.4 if not spec.get("twltl") else -1.0, x_right, dist, items,
                                       sign_x=spec.get("sign_x", 1.9), mast=True, night=look["night"],
                                       top=spec.get("span_top"))
        top, y_arm = objs[0]["arm_z"], objs[0]["arm_y"]     # the real arm height (was estimated from the sign centre)
        for sx in (4.6, 8.0):
            if sx < x_right - 0.5:
                P.traffic_signal(sx, y_arm - 0.05, top - 1.25, spec.get("signal_state", "green"),
                                 hang=(y_arm, top, S.arm_radius(sx, x_right, 0.4 if not spec.get("twltl") else -1.0)))
    else:
        objs, centre = S.overhead_span(x_left, x_right, dist, items,
                                       sign_x=spec.get("sign_x", road["_right_edge"] - 1.9 if not city else 1.9),
                                       mast=city, night=look["night"], top=spec.get("span_top"))

    cam = E.camera(tuple(spec.get("camera", (1.75, 0.0, E.EYE_HEIGHT))), spec.get("lens", 50.0))
    spec.setdefault("screen", (0.6, 0.62))
    finish(cam, centre, spec, look)
