"""400-series freeway: three lanes each way, paved shoulders, concrete
median barrier; sign on the right shoulder.

spec keys:
  lanes        lanes per direction (default 3)
  sign_dist    default 30
  sign_side    right | median
  traffic      true: a few cars ahead
"""
from .. import env as E
from .. import props as P
from .. import roads as R
from .base import S, finish, setup, sign_items


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    R.ground(look["snow"])
    n = spec.get("lanes", 3)
    road = {"lanes_right": n, "lanes_left": n, "lane_w": 3.75, "centre": spec.get("centre", "barrier"),
            "edge": "shoulder", "shoulder": 3.0, "wet": look["wet"], "snow": look["snow"]}
    road.update(spec.get("road", {}))
    path = R.Path(curves=spec.get("curves", ()))
    R.standard_road(path, road)
    dist = spec.get("sign_dist", 22.0)
    for side in (1, -1):
        e = road["_right_edge"] if side > 0 else road["_left_edge"]
        P.tree_row(path, e + side * 20, 0, 500, 7, "conifer", 30 + side, jitter=10, snow=look["snow"])
        P.tree_row(path, e + side * 32, 0, 500, 8, "deciduous", 40 + side, jitter=10, snow=look["snow"])
    if spec.get("traffic", True):
        P.car(road["_right_edge"] - 3.75 * 1.5, dist + 45, 0, "white")
        P.car(road["_right_edge"] - 3.75 * 2.5, dist + 90, 0, "grey", kind="suv")

    i = path.index_at(dist)
    if spec.get("sign_side") == "median":
        x, y, z = path.offset(i, -0.9)
    else:
        x, y, z = path.offset(i, road["_right_edge"] + 3.4)
    objs, centre = S.ground_mount(sign_items(spec), x, y, bottom=spec.get("sign_bottom", 1.8), z0=z,
                                  night=look["night"], posts=spec.get("posts", 1))
    lane_x = road["_right_edge"] - 3.75 * 0.5
    cam = E.camera(tuple(spec.get("camera", (lane_x, 0.0, E.EYE_HEIGHT))), spec.get("lens", 50.0))
    finish(cam, centre, spec, look)
