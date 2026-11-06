"""Driver giving a hand signal, seen from behind and to the left of the car
(the view of the driver behind). No sign artwork is needed.

spec keys:
  pose      left (arm straight out) | right (forearm up) | stop (forearm down)
  colour    car colour (default "red")
"""
from mathutils import Vector

from .. import env as E
from .. import props as P
from .. import roads as R
from .base import finish, setup


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    R.ground(look["snow"])
    road = {"edge": "curb", "centre": "broken_yellow", "wet": look["wet"], "snow": look["snow"]}
    path = R.Path()
    R.standard_road(path, road)
    P.tree_row(path, road["_right_edge"] + 1.4, 0, 220, 14, seed=2, snow=look["snow"])
    P.tree_row(path, road["_left_edge"] - 1.4, 0, 220, 14, seed=3, snow=look["snow"])
    P.house_rows(road, snow=look["snow"])
    car_y = 8.0
    root = P.car(1.75, car_y, 0, spec.get("colour", "red"), "sedan", brake=spec.get("pose") == "stop")
    P.driver_arm(root, spec.get("pose", "left"))
    # behind the car and to its left, eye a little above the roof line so
    # the arm is seen against the road and trees rather than the car body
    cam = E.camera(tuple(spec.get("camera", (-0.6, 0.0, 1.75))), spec.get("lens", 55.0))
    target = Vector((1.75 - 1.1, car_y + 0.35, 1.25))
    spec.setdefault("screen", (0.42, 0.5))
    spec.setdefault("fstop", 2.8)
    finish(cam, target, spec, look)
