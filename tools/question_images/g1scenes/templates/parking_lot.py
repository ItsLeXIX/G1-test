"""Parking lot in front of a low commercial building; the sign stands on a
small curbed island at the aisle end of a stall (the post is never on the
asphalt or the sidewalk) and faces the aisle.

Layout (+Y runs away from the camera):  aisle -> stalls (5.5 m deep, painted
lines, parked cars) -> curb -> sidewalk -> brick building.

spec keys:
  accessible   true: the stall beside the sign gets the painted wheelchair
               symbol and a hatched access aisle
  cars         number of parked cars (default 3)
  sign_dist    y of the stall mouth (default 11)
  cam_height   camera height (m), raised so the lot ground shows (default 3.4)
"""
import math

from .. import common as C
from .. import env as E
from .. import props as P
from .. import realism
from .. import roads as R
from .base import S, finish, setup, sign_items

STALL_W = 2.75
STALL_D = 5.5


def _stripe(name, x0, y0, x1, y1, w, mat, z=0.004):
    """Painted line from (x0,y0) to (x1,y1), w metres wide (flat quad)."""
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln * w / 2, dx / ln * w / 2
    v = [(x0 - nx, y0 - ny, z), (x0 + nx, y0 + ny, z), (x1 + nx, y1 + ny, z), (x1 - nx, y1 - ny, z)]
    return C.mesh_object(name, v, [(0, 1, 2, 3)], [mat])


def _brick_wall():
    """One consistent brick material for the whole building (no window-grid patches)."""
    if realism.enabled():
        return realism.wall("brick", (1.0, 1.0, 1.0))
    return C.mat("PlazaBrick", (0.36, 0.2, 0.15), 0.85)


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    R.ground(look["snow"])
    y0 = spec.get("sign_dist", 11.0)                # stall mouth (aisle side)
    y1 = y0 + STALL_D                                # stall head (curb side)
    lot = C.asphalt(look["wet"], look["snow"] * 0.5)
    C.box("Lot", -45, 45, -40, y1, -0.25, 0.0, lot)
    white = C.paint("white")
    blue_ = None

    x_s = spec.get("sign_x", 0.0)                    # the sign island sits on the stall boundary here
    acc = bool(spec.get("accessible"))

    # ---- stall lines (every 2.75 m across the row), aisle edge line, end curb
    k = -9
    while k <= 9:
        x = x_s + k * STALL_W
        C.box("StallLine", x - 0.05, x + 0.05, y0, y1 - 0.2, 0, 0.004, white)
        k += 1
    if acc:
        xa = x_s - STALL_W / 2                       # accessible stall: left of the sign island
        # painted wheelchair symbol (official artwork, flat on the stall)
        S.decal("AccessibleSymbol", "MTO-accessible.png", 1.1, (xa, y0 + 2.3, 0.006))
        # access aisle on the left of that stall: hatched with diagonal lines, edge lines
        ax0, ax1 = xa - STALL_W / 2 - 1.5, xa - STALL_W / 2
        for q in range(7):
            yy = y0 + 0.2 + q * 0.75
            _stripe("AisleHatch", ax0, yy, ax1, yy + 1.0, 0.1, white)
        C.box("AisleEdge", ax0 - 0.05, ax0 + 0.05, y0, y1 - 0.2, 0, 0.004, white)

    # ---- curb, sidewalk, plain brick building
    C.box("Curb", -45, 45, y1 - 0.2, y1, -0.25, 0.14, C.concrete("Curb", 3.0))
    C.box("Walk", -45, 45, y1, y1 + 3.8, -0.25, 0.14, C.concrete("Sidewalk", 1.5, wet=look["wet"]))
    brick = _brick_wall()
    C.box("Plaza", -45, 45, y1 + 3.8, y1 + 24, 0, 5.4, brick)
    C.box("Canopy", -45, 45, y1 + 2.4, y1 + 3.8, 3.6, 3.9, C.mat("Canopy", (0.12, 0.12, 0.13), 0.6))
    C.box("Parapet", -45, 45, y1 + 3.8, y1 + 24, 5.4, 5.8, C.concrete("Parapet", 2.0))
    # shopfront glass band so the wall reads as a building (one material, not a patch)
    C.box("ShopGlass", -45, 45, y1 + 3.78, y1 + 3.8, 0.6, 2.9, C.mat("ShopGlass", (0.03, 0.035, 0.04), 0.05, 0.0))

    # ---- parked cars nose-in, one in the stall right of the sign, others along the row
    placed = 0
    cols = ["silver", "black", "white", "red", "blue", "grey"]
    for kk in (1, -3, 2, -2, 3):
        if placed >= spec.get("cars", 3):
            break
        cx = x_s + kk * STALL_W + (STALL_W / 2 if kk > 0 else -STALL_W / 2)
        P.car(cx - (STALL_W * 0 if kk > 0 else 0), y0 + 3.2, 0, cols[placed % 6])
        placed += 1
    for x in (-34, 30):
        P.streetlight(x, y1 + 2.0, side=-1, on=look["night"])

    # ---- the sign: on a small curbed concrete island in the aisle mouth, at the stall boundary
    C.box("Island", x_s - 0.7, x_s + 0.7, y0 - 1.4, y0 - 0.1, -0.25, 0.14, C.concrete("SignIsland", 1.5, wet=look["wet"]))
    objs, centre = S.ground_mount(sign_items(spec), x_s, y0 - 0.75, bottom=spec.get("sign_bottom", 1.9), z0=0.14,
                                  night=look["night"])
    spec.setdefault("lat", 0.6)
    spec.setdefault("cam_height", 3.4)
    cam = E.camera((x_s - spec["lat"], y0 - 6.0, spec["cam_height"]), spec.get("lens", 50.0))
    spec.setdefault("screen", (0.62, 0.5))
    finish(cam, centre, spec, look)
