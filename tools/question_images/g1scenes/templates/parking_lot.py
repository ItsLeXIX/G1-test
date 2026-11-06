"""Parking lot in front of a low commercial building; sign on a post
facing the lot.

spec keys:
  accessible   true: the stalls by the sign get the blue wheelchair symbol
               (assets: signs/accessible_symbol.png) and a wider aisle
  cars         number of parked cars (default 4)
  sign_dist    default 11
"""
from .. import common as C
from .. import env as E
from .. import props as P
from .. import roads as R
from .base import S, finish, setup, sign_items


def build(spec, quality="preview"):
    weather, look = setup(spec, quality)
    R.ground(look["snow"])
    dist = spec.get("sign_dist", 11.0)
    lot = C.asphalt(look["wet"], look["snow"] * 0.5)
    C.box("Lot", -40, 40, -40, dist + 22, -0.25, 0.0, lot)
    w = C.paint("white")
    stall = 2.75
    # row of stalls facing the building; the sign stands at the head of a stall
    y0 = dist - 0.4
    k = -8
    while k <= 8:
        x = k * stall
        C.box("StallLine", x - 0.05, x + 0.05, y0 - 5.5, y0, 0, 0.004, w)
        k += 1
    if spec.get("accessible"):
        try:
            S.decal("AccessibleSymbol", "accessible_symbol.png", 1.2, (2.4 + stall / 2, y0 - 3.0, 0.005))
        except FileNotFoundError:
            pass
        # hatched access aisle
        C.box("AisleEdge", 2.4 + stall, 2.4 + stall + 0.08, y0 - 5.5, y0, 0, 0.004, w)
    # curb + sidewalk in front of the building
    C.box("Curb", -40, 40, y0, y0 + 0.15, -0.2, 0.15, C.concrete("Curb", 3.0))
    C.box("Walk", -40, 40, y0 + 0.15, y0 + 4.0, -0.2, 0.15, C.concrete("Sidewalk", 1.5, wet=look["wet"]))
    # one-storey brick plaza building
    brick = C.facade("PlazaFacade", (0.36, 0.2, 0.15), glass=(0.05, 0.07, 0.09), bay=7.0, storey=5.2,
                     win_w=4.6, win_h=2.4, along="X")
    C.box("Plaza", -40, 40, y0 + 4.0, y0 + 24, 0, 5.2, brick)
    C.box("Canopy", -40, 40, y0 + 2.6, y0 + 4.0, 3.4, 3.7, C.mat("Canopy", (0.12, 0.12, 0.13), 0.6))
    cols = ["silver", "black", "white", "red", "blue", "grey"]
    placed = 0
    for k in (-6, -5, -3, -1, 3, 4, 6):
        if placed >= spec.get("cars", 4):
            break
        P.car(k * stall + stall / 2, y0 - 2.9, 180, cols[placed % 6])
        placed += 1
    for x in (-34, 30):
        P.streetlight(x, dist - 12, side=1, on=look["night"])

    x = spec.get("sign_x", 2.4)
    objs, centre = S.ground_mount(sign_items(spec), x, y0 + 0.5, bottom=spec.get("sign_bottom", 1.9), z0=0.15,
                                  night=look["night"])
    # standing back in the driving aisle so the stalls and cars read as a lot
    cam = E.camera(tuple(spec.get("camera", (-2.5, -9.0, 1.6))), spec.get("lens", 55.0))
    spec.setdefault("screen", (0.62, 0.55))
    finish(cam, centre, spec, look)
