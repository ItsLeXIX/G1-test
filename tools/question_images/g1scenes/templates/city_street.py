"""Downtown street with buildings; sign on a post at the curb.

spec keys:
  lanes        lanes per direction (default 1)
  one_way      true: all lanes run away from the camera, white lane lines
  parking      true: parked cars along the right curb
  bike_lane    true: painted bike lane along the right curb
  crossover    true: pedestrian crossover (ladder crosswalk + shark teeth)
  school       true: school building on the right
  sign_dist    default 15
  car_ahead    colour of a car driving ahead (e.g. "blue")
  sign_mount   post | pole (sign strapped to a utility/light pole)
"""
from .. import common as C
from .. import env as E
from .. import props as P
from .. import roads as R
from .base import S, finish, setup, sign_items


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    n = spec.get("lanes", 1)
    road = {"lanes_right": n, "lanes_left": 0 if spec.get("one_way") else n,
            "centre": "none" if spec.get("one_way") else "double_yellow",
            "edge": "curb", "boulevard": 0.8, "sidewalk": 3.2, "wet": look["wet"], "snow": look["snow"]}
    if spec.get("one_way"):
        road["lanes_right"] = n
        road["lanes_left"] = 0
    if spec.get("bike_lane") or spec.get("parking"):
        road["lanes_right"] = n + 1          # outer lane becomes bike lane / parking lane
    dist = spec.get("sign_dist", 15.0)
    if spec.get("cross_street_at"):
        a = spec["cross_street_at"]
        road["gaps_right"] = road["gaps_left"] = [(a - 6, a + 6)]
    road.update(spec.get("road", {}))
    path = R.Path()
    R.ground(look["snow"])
    R.standard_road(path, road)
    re, le = road["_right_edge"], road["_left_edge"]
    if spec.get("cross_street_at"):
        R.cross_road(path, spec["cross_street_at"], "both", width=11, snow=look["snow"], wet=look["wet"])

    if spec.get("bike_lane"):
        w = C.paint("white")
        R.line(path, "BikeLaneLine", re - 1.8, 0.15, w)
        try:
            S.decal("BikeSymbol", "bike_lane_symbol.png", 1.6, (re - 0.9, dist + 12, 0.005))
        except FileNotFoundError:
            pass
    if spec.get("parking"):
        for k, d in enumerate((dist + 9, dist + 16, dist + 23, dist + 30)):
            P.car(re - 1.2, d, 0, ("silver", "black", "white", "red")[k % 4])
    if spec.get("crossover"):
        at = spec.get("crossover_at", dist + 6)
        w = C.paint("white")
        for k in range(int((re - le) / 0.9)):
            xx = le + 0.2 + k * 0.9
            C.box("Ladder", xx, xx + 0.45, at, at + 3.0, 0, 0.004, w)
        C.box("CrossSide", le, re, at - 0.1, at, 0, 0.004, w)
        C.box("CrossSide", le, re, at + 3.0, at + 3.1, 0, 0.004, w)
        # shark teeth (yield line) 6 m before the crosswalk
        k = 0.2
        while k < re - 0.3:
            C.mesh_object("Tooth", [(k, at - 6, 0.004), (k + 0.45, at - 6, 0.004), (k + 0.225, at - 5.4, 0.004)],
                          [(0, 1, 2)], [w])
            k += 0.75
    if spec.get("car_ahead"):
        P.car(1.75 if not spec.get("one_way") else 1.75, dist + 14, 0, spec["car_ahead"])

    bx = 0.15 + 0.8 + 3.2
    if spec.get("school"):
        sch = C.facade("SchoolFacade", (0.45, 0.22, 0.15), storey=4.0, bay=4.0, win_w=2.6, win_h=2.0)
        C.box("School", re + bx + 12, re + bx + 50, dist + 10, dist + 90, 0, 8, sch)
        C.box("Schoolyard", re + bx, re + bx + 12, dist + 10, dist + 90, 0.0, 0.14, C.grass(look["snow"]))
        P.city_block(re + bx, -10, dist + 9, 1, seed=31, height=(8, 14))
    else:
        P.city_block(re + bx, -10, 220, 1, seed=31)
    P.city_block(le - bx, -10, 220, -1, seed=32)
    for d in (dist + 22, dist + 54, dist + 86):
        P.streetlight(re + 0.6, d, side=1, on=look["night"])
    for d, s in ((24, 4), (58, 5)):
        P.tree(re + 0.6, d, 0.13, scale=0.75, seed=s, snow=look["snow"])

    x = re + 0.6
    objs, centre = S.ground_mount(sign_items(spec), x, dist, bottom=spec.get("sign_bottom", 2.1), z0=0.15,
                                  night=look["night"])
    cam = E.camera(tuple(spec.get("camera", (re - 1.75 if not spec.get("parking") else re - 4.5, 0.0, E.EYE_HEIGHT))),
                   spec.get("lens", 50.0))
    finish(cam, centre, spec, look)
