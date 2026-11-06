"""Following a vehicle.

spec keys:
  vehicle     smv_wagon (farm wagon with the SMV emblem as spec["sign"])
              | car (a car ahead; spec["sign"] is a roadside sign)
  colour      car colour (default "blue")
  setting     rural | suburban
  vehicle_dist  metres ahead (default 9 for the wagon, 12 for a car)
  sign_dist   for car scenes: roadside sign position (default 16)
  side_road   {at, side}: intersection ahead (stop / one-way scenes)
  brake       true: car's brake lights on
"""
from mathutils import Vector

from .. import common as C
from .. import env as E
from .. import props as P
from .. import roads as R
from .base import S, finish, setup, sign_items


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    setting = spec.get("setting", "rural")
    R.ground(look["snow"])
    road = {"edge": "curb" if setting == "suburban" else "shoulder", "centre": spec.get("centre", "broken_yellow"),
            "wet": look["wet"], "snow": look["snow"]}
    sr = spec.get("side_road")
    if sr:
        gap = [(sr["at"] - 6, sr["at"] + 6)]
        road["gaps_right"] = road["gaps_left"] = gap
    road.update(spec.get("road", {}))
    path = R.Path()
    R.standard_road(path, road)
    if sr:
        R.cross_road(path, sr["at"], sr.get("side", "both"), snow=look["snow"], wet=look["wet"])
        w = C.paint("white")
        C.box("StopBar", 0.15, road["_right_edge"], sr["at"] - 7.5, sr["at"] - 7.0, 0, 0.004, w)

    vehicle = spec.get("vehicle", "car")
    if setting == "suburban":
        P.tree_row(path, road["_right_edge"] + 1.4, 0, 220, 14, seed=2, skip=[(0, 30)], snow=look["snow"])
        P.tree_row(path, road["_left_edge"] - 1.4, 0, 220, 14, seed=3, snow=look["snow"])
        P.house_rows(road, snow=look["snow"], skip_right=[(0, 30)])
    else:
        for side, seed in ((1, 4), (-1, 5)):
            e = road["_right_edge"] if side > 0 else road["_left_edge"]
            P.tree_row(path, e + side * 24, 20, 300, 9, "deciduous", seed, jitter=8, snow=look["snow"])
        # farm fence along the field
        post = C.mat("FencePost", (0.3, 0.24, 0.18), 0.9)
        for d in range(0, 200, 4):
            x, y, z = path.offset(path.index_at(d), road["_right_edge"] + 6)
            C.box("FencePost", x - 0.05, x + 0.05, y - 0.05, y + 0.05, z - 0.05, z + 1.2, post)

    if vehicle == "smv_wagon":
        d = spec.get("vehicle_dist", 9.0)
        root, emblem = P.hay_wagon(1.75, d + 2.5)
        items = sign_items(spec)
        art, width = items[0]
        p, h = S.panel("SMV", art, width)
        p.location = (emblem.x + 0.55, emblem.y - 0.01, emblem.z - h / 2)
        target = emblem + Vector((0.55, 0, 0))   # panel is centred on the emblem point
        cam_x = 1.75
    else:
        d = spec.get("vehicle_dist", 12.0)
        P.car(1.75, d + 2.3, 0, spec.get("colour", "blue"), spec.get("kind", "suv"), brake=spec.get("brake", False))
        i = path.index_at(spec.get("sign_dist", 16.0))
        x, y, z = path.offset(i, road.get("_roadside_right", road["_right_edge"] + 1.2))
        objs, target = S.ground_mount(sign_items(spec), x, y, bottom=2.1 if setting == "suburban" else 1.6,
                                      z0=z + (0.13 if setting == "suburban" else 0), night=look["night"])
        cam_x = 1.3
    cam = E.camera(tuple(spec.get("camera", (cam_x, 0.0, E.EYE_HEIGHT))), spec.get("lens", 50.0))
    if vehicle == "smv_wagon":
        spec.setdefault("screen", (0.55, 0.45))
    finish(cam, target, spec, look)
