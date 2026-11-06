"""High view of an uncontrolled 4-way intersection of two residential
streets, with vehicles and painted path arrows showing what each driver
intends to do.

spec keys:
  vehicles  list of {colour, approach: west|east|north|south, move:
            straight|left|right}; default = question 161 (blue from the
            west going straight, red from the east turning left)
"""
import math

from mathutils import Vector

from .. import common as C
from .. import env as E
from .. import props as P
from .base import finish, setup

ROAD_W = 7.0       # two 3.5 m lanes
ARM = 60.0


def _arrow(name, pts, width, colour):
    """Flat arrow along a polyline (x, y) at z=0.03, with a triangular head."""
    m = C.emissive(f"Arrow_{colour}", colour, 1.5)
    verts, faces = [], []
    for i, (x, y) in enumerate(pts[:-1]):
        nx, ny = pts[i + 1]
        d = Vector((nx - x, ny - y, 0)).normalized()
        n = Vector((-d.y, d.x, 0)) * width / 2
        verts += [(x + n.x, y + n.y, 0.03), (x - n.x, y - n.y, 0.03)]
    # last body point stops short of the tip to leave room for the head
    tip = Vector((*pts[-1], 0.03))
    d = (tip - Vector((*pts[-2], 0.03))).normalized()
    base = tip - d * width * 2.5
    n = Vector((-d.y, d.x, 0)) * width / 2
    verts += [tuple(base + n), tuple(base - n)]
    for k in range(len(verts) // 2 - 1):
        a = 2 * k
        faces.append((a, a + 1, a + 3, a + 2))
    hn = n * 2.6
    hb = len(verts)
    verts += [tuple(base + hn), tuple(base - hn), tuple(tip)]
    faces.append((hb, hb + 1, hb + 2))
    return C.mesh_object(name, verts, faces, [m])


def _turn_left_from_east(steps=12):
    """Path of the westbound car (north lane, y=+1.75) turning left to head
    south in the southbound lane (x=-1.75)."""
    pts = [(9.0, 1.75), (3.5, 1.75)]
    cx, cy, r = 3.5, -3.5, 5.25        # arc centre at the SE of the turn
    for k in range(steps + 1):
        a = math.radians(90 + 90 * k / steps)
        pts.append((cx + r * math.cos(a) + 0.0, cy + r * math.sin(a)))
    pts.append((-1.75, -10.0))
    return pts


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    a = C.asphalt(look["wet"], look["snow"])
    C.box("Ground", -300, 300, -300, 300, -0.4, -0.3, C.grass(look["snow"]))
    # the two roads share the square in the middle; offset by 1 mm so the
    # coincident surfaces don't fight (which renders as black patches)
    C.box("RoadNS", -ROAD_W / 2, ROAD_W / 2, -ARM, ARM, -0.2, 0.0, a)
    C.box("RoadEW", -ARM, -ROAD_W / 2, -ROAD_W / 2, ROAD_W / 2, -0.2, 0.0, a)
    C.box("RoadEW", ROAD_W / 2, ARM, -ROAD_W / 2, ROAD_W / 2, -0.2, 0.0, a)
    y_ = C.paint("yellow")
    w = C.paint("white")
    # double yellow centre lines on each leg, stopping before the crosswalks
    for s in (-1, 1):
        lo, hi = sorted((s * 7.5, s * ARM))
        for off in (-0.13, 0.13):
            C.box("CL", off - 0.05, off + 0.05, lo, hi, 0, 0.004, y_)   # north/south legs
            C.box("CL", lo, hi, off - 0.05, off + 0.05, 0, 0.004, y_)   # east/west legs
    # ladder crosswalks on all four legs
    for s in (-1, 1):
        for k in range(7):
            o = -ROAD_W / 2 + 0.3 + k * 1.0
            C.box("Zebra", o, o + 0.5, s * 5.3 - 1.5, s * 5.3 + 1.5, 0, 0.004, w)
            C.box("Zebra", s * 5.3 - 1.5, s * 5.3 + 1.5, o, o + 0.5, 0, 0.004, w)
    curb = C.concrete("Curb", 3.0)
    walk = C.concrete("Sidewalk", 1.5, wet=look["wet"])
    hedge = C.mat("Hedge", (0.05, 0.13, 0.04), 0.9)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, y0 = sx * ROAD_W / 2, sy * ROAD_W / 2
            xs, ys = sorted((x0, sx * ARM)), sorted((y0, sy * ARM))
            C.box("Corner", xs[0], xs[1], ys[0], ys[1], -0.2, 0.13, C.grass(look["snow"]))
            C.box("CurbX", xs[0], xs[1], *sorted((y0, y0 + sy * 0.15)), -0.2, 0.15, curb)
            C.box("CurbY", *sorted((x0, x0 + sx * 0.15)), ys[0], ys[1], -0.2, 0.151, curb)
            C.box("WalkX", xs[0], xs[1], *sorted((y0 + sy * 2.4, y0 + sy * 4.0)), -0.2, 0.15, walk)
            C.box("WalkY", *sorted((x0 + sx * 2.4, x0 + sx * 4.0)), ys[0], ys[1], -0.2, 0.152, walk)
            C.box("Hedge", *sorted((x0 + sx * 6.0, x0 + sx * 40)), *sorted((y0 + sy * 6.0, y0 + sy * 7.0)), 0, 1.1, hedge)
            for k in range(3):
                P.tree(x0 + sx * (9 + 9 * k), y0 + sy * (11 + 4 * (k % 2)), 0.13, seed=k + 7 * sx + 3 * sy, snow=look["snow"])

    # vehicles + intended paths (default: question 161)
    P.car(-11.0, -1.75, -90, "blue")                 # from the west, heading east
    P.car(11.0, 1.75, 90, "red")                     # from the east, heading west
    _arrow("PathBlue", [(-8.0, -1.75), (9.0, -1.75)], 0.35, (0.05, 0.2, 1.0))
    _arrow("PathRed", _turn_left_from_east(), 0.35, (1.0, 0.08, 0.05))

    cam = E.camera(tuple(spec.get("camera", (0.0, -26.0, 19.0))), spec.get("lens", 35.0))
    spec.setdefault("screen", (0.5, 0.5))
    spec.setdefault("fstop", 8.0)
    finish(cam, Vector((0, 0, 0)), spec, look)
