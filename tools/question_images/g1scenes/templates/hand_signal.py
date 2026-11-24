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
    _roll_down_driver_window(root)
    P.driver_arm(root, spec.get("pose", "left"))
    # behind the car and to its left, at eye height, so the arm comes out of the
    # open driver's window and is seen against the road and the houses
    cam = E.camera(tuple(spec.get("camera", (-0.8, car_y - 4.3, 1.5))), spec.get("lens", 50.0))
    pose = spec.get("pose", "left")
    local = {"left": (-0.95, 0.2, 1.05), "right": (-0.88, 0.2, 1.22), "stop": (-0.86, 0.2, 0.92)}.get(pose, (-0.95, 0.2, 1.05))
    target = Vector((1.75 + local[0], car_y + local[1], local[2]))
    spec.setdefault("screen", (0.38, 0.55))
    spec.setdefault("fstop", 4.0)
    finish(cam, target, spec, look)


def _roll_down_driver_window(root):
    """Fully lower the driver's (left front) window: this car instance gets its
    own copy of the model's collection without the left front window glass."""
    import bpy
    src = root.instance_collection
    drop = set()

    def collect(o):
        drop.add(o)
        for ch in o.children:
            collect(ch)
    for o in src.all_objects:
        if o.name.startswith("door-front-window-glass-l"):
            collect(o)
    new = bpy.data.collections.new(src.name + "_window_down")
    new.instance_offset = src.instance_offset
    copies = {}
    for o in src.all_objects:
        if o in drop:
            continue
        copies[o] = o.copy()
        new.objects.link(copies[o])
    for o, cp in copies.items():
        if o.parent in copies:
            cp.parent = copies[o.parent]
    root.instance_collection = new
