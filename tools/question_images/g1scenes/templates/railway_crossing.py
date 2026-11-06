"""Level railway crossing seen from the approach: tracks across the road,
crossing signal with crossbuck (spec["sign"][0] = crossbuck artwork) and
flashing red lights.

spec keys:
  crossing_dist  metres to the tracks (default 22)
  flashing       true: the left light of each pair is lit
"""
from mathutils import Vector

from .. import env as E
from .. import props as P
from .. import roads as R
from .base import finish, setup, sign_items


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    R.ground(look["snow"])
    road = {"edge": "shoulder", "centre": "solid_yellow", "wet": look["wet"], "snow": look["snow"]}
    path = R.Path()
    R.standard_road(path, road)
    at = spec.get("crossing_dist", 22.0)
    R.rail_crossing(path, at, width=300)
    art = sign_items(spec)[0][0] if spec.get("sign") else "crossbuck.png"
    flashing = spec.get("flashing", True)
    x = road["_right_edge"] + 2.6
    P.crossing_signal(x, at - 4.5, flashing=flashing, art=art)
    P.crossing_signal(road["_left_edge"] - 2.6, at + 4.5, flashing=flashing, yaw=180, art=art)
    for side in (1, -1):
        e = road["_right_edge"] if side > 0 else road["_left_edge"]
        P.tree_row(path, e + side * 22, 40, 300, 9, "deciduous", 60 + side, jitter=8, snow=look["snow"])
    target = Vector((x, at - 4.5, 3.3))
    cam = E.camera(tuple(spec.get("camera", (1.75, 0.0, E.EYE_HEIGHT))), spec.get("lens", 45.0))
    spec.setdefault("screen", (0.66, 0.6))
    finish(cam, target, spec, look)
