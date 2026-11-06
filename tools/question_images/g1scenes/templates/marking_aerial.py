"""High view looking down at a pavement marking in the right lane
(e.g. the shared-lane "sharrow"). spec["sign"][0] is the marking artwork,
with its width in metres; it is laid flat on the road reading away from
the camera.

spec keys:
  marking_dist  metres ahead (default 12)
  lane          1 = right lane (default)
"""
from mathutils import Vector

from .. import env as E
from .. import props as P
from .. import roads as R
from .base import S, finish, setup, sign_items


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    R.ground(look["snow"])
    road = {"edge": "curb", "centre": "double_yellow", "lanes_right": 1, "lanes_left": 1,
            "lane_w": 4.2, "wet": look["wet"], "snow": look["snow"]}
    path = R.Path()
    R.standard_road(path, road)
    d = spec.get("marking_dist", 12.0)
    # keep tree shadows off the marking: no trees beside it, sun behind camera
    P.tree_row(path, road["_right_edge"] + 1.4, -10, 120, 13, seed=2, skip=[(d - 14, d + 10)], snow=look["snow"])
    P.tree_row(path, road["_left_edge"] - 1.4, -10, 120, 13, seed=3, skip=[(d - 14, d + 10)], snow=look["snow"])
    lane_x = road["_right_edge"] - 4.2 / 2
    for k, dd in enumerate((d, d + 30)):
        art, width = sign_items(spec)[0]
        S.decal(f"Marking{k}", art, width, (lane_x, dd, 0.006))
    P.car(-2.1, d + 22, 180, "silver")
    cam = E.camera(tuple(spec.get("camera", (lane_x - 1.0, d - 9.0, 9.0))), spec.get("lens", 35.0))
    spec.setdefault("screen", (0.5, 0.45))
    spec.setdefault("fstop", 5.6)
    finish(cam, Vector((lane_x, d + 1.0, 0)), spec, look)
