"""Large green guide sign (distance / destination) on two posts beside a
two-lane provincial highway.

Guide signs carry place names, so there is no single official file; the
artwork (PNG in signs/) must follow the MTO guide-sign layout: green
background, white border, white Highway Gothic / Clearview lettering, real
Ontario destinations. It is passed in spec["sign"] like any other sign.

spec keys:
  sign_dist   default 45
  width       sign width in metres (default from spec["sign"])
"""
from .. import env as E
from .. import props as P
from .. import roads as R
from .base import S, finish, setup, sign_items


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    R.ground(look["snow"])
    road = {"lanes_right": 1, "lanes_left": 1, "centre": "broken_yellow", "edge": "shoulder",
            "shoulder": 2.5, "wet": look["wet"], "snow": look["snow"]}
    road.update(spec.get("road", {}))
    path = R.Path(curves=spec.get("curves", ()))
    R.standard_road(path, road)
    dist = spec.get("sign_dist", 45.0)
    for side in (1, -1):
        e = road["_right_edge"] if side > 0 else road["_left_edge"]
        for k, off in enumerate((16, 26)):
            P.tree_row(path, e + side * off, 0, 400, 8, ("conifer", "deciduous")[k], 50 + k + side,
                       skip=[(dist - 8, dist + 8)] if side > 0 else (), jitter=7, snow=look["snow"])
    i = path.index_at(dist)
    x, y, z = path.offset(i, road["_right_edge"] + 4.0)
    objs, centre = S.ground_mount(sign_items(spec), x, y, bottom=spec.get("sign_bottom", 1.5), z0=z,
                                  posts=2, night=look["night"])
    cam = E.camera(tuple(spec.get("camera", (1.75, 0.0, E.EYE_HEIGHT))), spec.get("lens", 50.0))
    spec.setdefault("screen", (0.62, 0.58))
    finish(cam, centre, spec, look)
