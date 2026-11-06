"""Ontario suburban houses with real 3D detail.

Every house is built in a local frame and mapped to world space:
  u = distance in front of the front wall, toward the road (+), back wall at u = -depth
  v = along the road (world y)
  z = up
so the same code serves both sides of the street.

Detail: foundation band; siding or brick walls; shingled gable roof with
overhangs, fascia and rake boards; chimneys on some; framed windows with
sills, recessed glass and muntins, shutters on some; framed front door with
steps or a porch; attached garages on some; driveways; fences or hedges.
Size, storeys, roof pitch and colours vary per seed so streets don't repeat.
"""
import math

from . import common as C
from . import realism

SIDING = [(0.92, 0.9, 0.84), (0.86, 0.8, 0.66), (0.93, 0.88, 0.7), (0.78, 0.8, 0.8), (0.72, 0.77, 0.66),
          (0.7, 0.77, 0.84), (0.95, 0.95, 0.93), (0.66, 0.6, 0.52)]
BRICK = [(1.0, 1.0, 1.0), (0.85, 0.78, 0.72), (1.05, 0.92, 0.8)]
SHINGLE = [(0.42, 0.42, 0.45), (0.5, 0.42, 0.36), (0.62, 0.62, 0.62), (0.32, 0.3, 0.3), (0.55, 0.5, 0.44)]
DOOR = [(0.45, 0.04, 0.04), (0.04, 0.07, 0.2), (0.03, 0.03, 0.03), (0.05, 0.16, 0.08), (0.3, 0.16, 0.07),
        (0.85, 0.85, 0.82)]
SHUTTER = [(0.02, 0.02, 0.02), (0.04, 0.12, 0.06), (0.03, 0.06, 0.16), (0.25, 0.04, 0.05)]


def params(seed):
    """All random choices for one lot, so house_rows can space lots by real width."""
    r = C.rng(seed)
    storeys = 1 if r.random() < 0.35 else 2
    p = dict(
        storeys=storeys,
        frontage=r.uniform(9.0, 13.5) if storeys == 2 else r.uniform(11.0, 15.0),
        depth=r.uniform(8.0, 10.5),
        storey_h=r.uniform(2.7, 3.0),
        pitch=r.uniform(24, 40) if storeys == 2 else r.uniform(20, 32),
        brick=r.random() < 0.3,
        siding=r.choice(SIDING), brick_tint=r.choice(BRICK), shingle=r.choice(SHINGLE),
        door=r.choice(DOOR), shutter=r.choice(SHUTTER) if r.random() < 0.45 else None,
        porch=r.random() < 0.4, chimney=r.random() < 0.45,
        garage=r.choice((None, None, "left", "right")) if r.random() < 0.8 else None,
        boundary=r.choice(("fence", "hedge", None)),
        door_offset=r.uniform(-0.2, 0.2),
        win_w=r.uniform(1.0, 1.35), win_h=r.uniform(1.25, 1.5),
        setback=r.uniform(12.5, 16.5),
    )
    p["lot"] = p["frontage"] + (3.9 if p["garage"] else 3.6)
    return p


def _mats(p, snow):
    ph = realism.enabled()
    m = {}
    m["trim"] = C.mat("HouseTrim", (0.86, 0.86, 0.84), 0.5)
    if ph:
        m["wall"] = realism.wall("brick", p["brick_tint"]) if p["brick"] else realism.wall("siding", p["siding"])
        m["roof"] = realism.pbr("PH_Shingle_" + "_".join(f"{c:.2f}" for c in p["shingle"]), "roof_slates_02", 2.0,
                                tint=p["shingle"], normal=1.2)
        m["found"] = realism.pbr("PH_Foundation", "plastered_wall_02", 2.2, tint=(0.62, 0.62, 0.6))
        m["chimney"] = realism.wall("brick", (0.85, 0.75, 0.7))
        m["glass"] = realism.glass()
        m["step"] = realism.concrete(0.0, "PH_Step")
        m["hedge"] = realism.pbr("PH_Hedge", "leafy_grass", 0.8, tint=(0.35, 0.7, 0.25), darken=0.7, normal=1.5)
    else:
        m["wall"] = C.mat(f"HouseWall_{p['siding']}", tuple(c * 0.5 for c in p["siding"]), 0.85)
        m["roof"] = C.mat(f"Roof_{p['shingle']}", tuple(c * 0.2 for c in p["shingle"]), 0.8)
        m["found"] = C.mat("Foundation", (0.3, 0.3, 0.29), 0.9)
        m["chimney"] = C.mat("ChimneyBrick", (0.3, 0.12, 0.08), 0.85)
        m["glass"] = C.mat("Glass", (0.03, 0.04, 0.05), 0.08)
        m["step"] = C.mat("Step", (0.4, 0.4, 0.39), 0.85)
        m["hedge"] = C.mat("Hedge", (0.04, 0.1, 0.03), 0.9)
    if snow:
        m["roof"] = C.mat("RoofSnow", (0.8, 0.82, 0.86), 0.8)
    m["door"] = C.mat(f"Door_{p['door']}", p["door"], 0.35)
    if p["shutter"]:
        m["shutter"] = C.mat(f"Shutter_{p['shutter']}", p["shutter"], 0.5)
    m["garage"] = C.mat("GarageDoor", (0.82, 0.82, 0.8), 0.45)
    m["groove"] = C.mat("GarageGroove", (0.45, 0.45, 0.44), 0.6)
    m["fence"] = C.mat("FenceWood", (0.32, 0.22, 0.13), 0.85)
    return m


def house(x_face, y_start, side, seed, coll=None, snow=0.0, curb_x=None, p=None):
    """Build one lot starting at y_start (along the road). x_face: world x of
    the front wall. side: +1 = right of the road (front faces -x), -1 = left.
    Returns the lot's end y."""
    p = p or params(seed)
    r = C.rng(seed + 1)
    m = _mats(p, snow)
    out = -side                       # world x direction toward the road

    def X(u):
        return x_face + out * u

    def box(name, u0, u1, v0, v1, z0, z1, mat):
        a, b = sorted((X(u0), X(u1)))
        return C.box(name, a, b, min(v0, v1), max(v0, v1), z0, z1, mat, coll)

    def mesh(name, pts, faces, mat):
        return C.mesh_object(name, [(X(u), v, z) for u, v, z in pts], faces, [mat], coll)

    F, D = p["frontage"], p["depth"]
    garage_w = 3.9 if p["garage"] else 0.0
    v0 = y_start + (garage_w if p["garage"] == "left" else 0.0) + 1.8
    v1 = v0 + F
    found = 0.45
    H = found + p["storeys"] * p["storey_h"]
    t = math.tan(math.radians(p["pitch"]))
    rise = D / 2 * t

    # body with gable ends (ridge parallel to the road)
    pts = [(0, v0, 0), (-D, v0, 0), (-D, v1, 0), (0, v1, 0), (0, v0, H), (-D, v0, H), (-D, v1, H), (0, v1, H),
           (-D / 2, v0, H + rise), (-D / 2, v1, H + rise)]
    mesh("House", pts, [(0, 3, 7, 4), (1, 5, 6, 2), (0, 4, 8, 5, 1), (3, 2, 6, 9, 7), (0, 1, 2, 3)], m["wall"])
    box("Foundation", 0.04, -D - 0.04, v0 - 0.04, v1 + 0.04, 0.0, found, m["found"])

    # roof: two shingled slabs with eave and gable overhangs, fascia + rake boards
    oh, goh, th = 0.45, 0.35, 0.14
    for s in (1, -1):                  # front (+u) and back slope
        ue = oh if s > 0 else -D - oh
        ze = H - oh * t
        zr = H + rise
        a, b = (ue, -D / 2) if s > 0 else (-D / 2, ue)
        za, zb = (ze, zr) if s > 0 else (zr, ze)
        va, vb = v0 - goh, v1 + goh
        top = [(a, va, za + th), (b, va, zb + th), (b, vb, zb + th), (a, vb, za + th)]
        bot = [(a, va, za), (b, va, zb), (b, vb, zb), (a, vb, za)]
        mesh("Roof", top + bot, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (2, 6, 7, 3), (0, 3, 7, 4), (1, 5, 6, 2)],
             m["roof"])
        uf0, uf1 = (oh - 0.03, oh + 0.03) if s > 0 else (-D - oh - 0.03, -D - oh + 0.03)
        box("Fascia", uf0, uf1, va, vb, ze - 0.22, ze + 0.02, m["trim"])
        box("Soffit", 0.0 if s > 0 else -D, uf0 if s > 0 else uf1, va, vb, ze - 0.22, ze - 0.19, m["trim"])
    for vv in (v0 - goh - 0.03, v1 + goh):   # rake boards along both gable edges
        for s in (1, -1):
            ue = oh if s > 0 else -D - oh
            p0, p1 = (ue, H - oh * t - 0.2), (-D / 2, H + rise - 0.06)
            pts = [(p0[0], vv, p0[1]), (p1[0], vv, p1[1]), (p1[0], vv, p1[1] + 0.26), (p0[0], vv, p0[1] + 0.26)]
            pts += [(q[0], vv + 0.03, q[2]) for q in pts]
            mesh("Rake", pts, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7)], m["trim"])
    if p["chimney"]:
        cv = v1 - 1.2 if r.random() < 0.5 else v0 + 0.4
        box("Chimney", -D * 0.7, -D * 0.7 - 0.75, cv, cv + 0.8, H - 1.0, H + rise + 0.8, m["chimney"])
        box("ChimneyCap", -D * 0.7 + 0.05, -D * 0.7 - 0.8, cv - 0.05, cv + 0.85, H + rise + 0.8, H + rise + 0.9,
            m["found"])

    # front door: off-centre, framed, with steps or a porch
    dv = v0 + F * (0.5 + p["door_offset"])
    dw, dh = 0.95, 2.1
    box("Door", -0.02, 0.02, dv - dw / 2, dv + dw / 2, found, found + dh, m["door"])
    box("DoorGlass", 0.02, 0.025, dv - 0.12, dv + 0.12, found + 1.2, found + 1.8, m["glass"])
    for a, b in ((dv - dw / 2 - 0.14, dv - dw / 2), (dv + dw / 2, dv + dw / 2 + 0.14)):
        box("DoorFrame", 0.0, 0.08, a, b, found, found + dh + 0.14, m["trim"])
    box("DoorHead", 0.0, 0.1, dv - dw / 2 - 0.2, dv + dw / 2 + 0.2, found + dh, found + dh + 0.2, m["trim"])
    if p["porch"]:
        pv0, pv1 = dv - 1.9, dv + 1.9
        box("PorchDeck", 0.0, 2.1, pv0, pv1, 0.0, found - 0.15, m["step"])
        box("PorchStep", 2.1, 2.45, dv - 0.8, dv + 0.8, 0.0, found - 0.3, m["step"])
        for pv in (pv0 + 0.1, pv1 - 0.22):
            box("PorchPost", 1.85, 1.97, pv, pv + 0.12, found - 0.15, found + 2.45, m["trim"])
        box("PorchRoof", -0.05, 2.25, pv0 - 0.1, pv1 + 0.1, found + 2.45, found + 2.6, m["roof"])
        box("PorchFascia", 2.25, 2.3, pv0 - 0.1, pv1 + 0.1, found + 2.38, found + 2.62, m["trim"])
    else:
        box("Landing", 0.0, 1.1, dv - 0.8, dv + 0.8, 0.0, found - 0.15, m["step"])
        box("Step", 1.1, 1.45, dv - 0.8, dv + 0.8, 0.0, found - 0.3, m["step"])

    # windows on the front: frame, sill, recessed glass, muntins, optional shutters
    ww, wh = p["win_w"], p["win_h"]
    slots = []
    n = max(2, int(F // 3.0))
    for k in range(n):
        vc = v0 + F * (k + 0.5) / n
        if abs(vc - dv) < ww / 2 + dw / 2 + 0.6:
            continue
        slots.append(vc)
    for storey in range(p["storeys"]):
        zb = found + storey * p["storey_h"] + 0.9
        row = slots if storey == 0 else [v0 + F * (k + 0.5) / n for k in range(n)]
        for vc in row:
            a, b = vc - ww / 2, vc + ww / 2
            box("WinGlass", -0.02, 0.004, a, b, zb, zb + wh, m["glass"])
            box("WinFrameL", 0.0, 0.07, a - 0.1, a, zb, zb + wh, m["trim"])
            box("WinFrameR", 0.0, 0.07, b, b + 0.1, zb, zb + wh, m["trim"])
            box("WinHead", 0.0, 0.08, a - 0.14, b + 0.14, zb + wh, zb + wh + 0.13, m["trim"])
            box("WinSill", 0.0, 0.12, a - 0.16, b + 0.16, zb - 0.07, zb, m["trim"])
            box("WinBottomRail", 0.0, 0.05, a, b, zb, zb + 0.05, m["trim"])
            box("Muntin", 0.0, 0.03, vc - 0.02, vc + 0.02, zb, zb + wh, m["trim"])
            box("Muntin", 0.0, 0.03, a, b, zb + wh * 0.55 - 0.02, zb + wh * 0.55 + 0.02, m["trim"])
            if p["shutter"]:
                sw = ww * 0.45
                box("Shutter", 0.0, 0.045, a - 0.12 - sw, a - 0.12, zb, zb + wh, m["shutter"])
                box("Shutter", 0.0, 0.045, b + 0.12, b + 0.12 + sw, zb, zb + wh, m["shutter"])

    # attached garage, gable facing the road, sectional door
    drive_v = None
    if p["garage"]:
        gv0, gv1 = (v0 - garage_w, v0) if p["garage"] == "left" else (v1, v1 + garage_w)
        gu0, gu1 = 1.2, -6.2
        gh = 2.95
        grise = garage_w / 2 * math.tan(math.radians(26))
        gm = (gv0 + gv1) / 2
        pts = [(gu0, gv0, 0), (gu1, gv0, 0), (gu1, gv1, 0), (gu0, gv1, 0), (gu0, gv0, gh), (gu1, gv0, gh),
               (gu1, gv1, gh), (gu0, gv1, gh), (gu0, gm, gh + grise), (gu1, gm, gh + grise)]
        mesh("Garage", pts, [(0, 4, 8, 7, 3), (1, 2, 6, 9, 5), (0, 1, 5, 4), (3, 7, 6, 2)], m["wall"])
        box("GarageFound", gu0 + 0.04, gu1 - 0.04, gv0 - 0.04, gv1 + 0.04, 0.0, 0.25, m["found"])
        for s in (1, -1):
            ve = gv0 - 0.3 if s > 0 else gv1 + 0.3
            ze = gh - 0.3 * math.tan(math.radians(26))
            top = [(gu0 + 0.35, ve, ze + 0.12), (gu0 + 0.35, gm, gh + grise + 0.12), (gu1 - 0.1, gm, gh + grise + 0.12),
                   (gu1 - 0.1, ve, ze + 0.12)]
            bot = [(q[0], q[1], q[2] - 0.12) for q in top]
            mesh("GarageRoof", top + bot, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (2, 6, 7, 3), (0, 3, 7, 4),
                                           (1, 5, 6, 2)], m["roof"])
            box("GarageFascia", gu0 + 0.35, gu1 - 0.1, ve - 0.03, ve + 0.03, ze - 0.2, ze + 0.02, m["trim"])
        da, db = gv0 + 0.45, gv1 - 0.45
        box("GarageDoor", gu0 - 0.02, gu0 + 0.02, da, db, 0.0, 2.2, m["garage"])
        for zz in (0.55, 1.1, 1.65):
            box("GarageGroove", gu0 + 0.02, gu0 + 0.03, da, db, zz - 0.015, zz + 0.015, m["groove"])
        box("GarageFrame", gu0, gu0 + 0.08, da - 0.12, db + 0.12, 2.2, 2.34, m["trim"])
        for a, b in ((da - 0.12, da), (db, db + 0.12)):
            box("GarageFrame", gu0, gu0 + 0.08, a, b, 0.0, 2.2, m["trim"])
        drive_v = (da - 0.3, db + 0.3)
        drive_u0 = gu0
    else:
        side_v = (v1 + 0.4, v1 + 3.4) if r.random() < 0.5 else (v0 - 3.4, v0 - 0.4)
        drive_v, drive_u0 = side_v, -4.0
    if curb_x is not None and drive_v:
        u_curb = (x_face - curb_x) * (1 if side > 0 else -1)
        box("Driveway", drive_u0, u_curb, drive_v[0], drive_v[1], 0.0, 0.155, C.asphalt(0, snow))

    # lot boundary on the far side: wood privacy fence (back yard) or hedge (front yard)
    edge = y_start + p["lot"] if p["garage"] != "right" else y_start
    if p["boundary"] == "fence":
        fv = y_start + p["lot"] - 0.1
        box("Fence", -D * 0.4, -D - 6, fv - 0.04, fv + 0.04, 0.05, 1.8, m["fence"])
        u = -D * 0.4
        while u > -D - 6:
            box("FencePost", u + 0.06, u - 0.06, fv - 0.07, fv + 0.07, 0.0, 1.9, m["fence"])
            u -= 2.4
        box("FenceRail", -D * 0.4, -D - 6, fv - 0.06, fv + 0.06, 1.78, 1.86, m["fence"])
    elif p["boundary"] == "hedge":
        hv = y_start + p["lot"] - 0.6
        box("Hedge", 0.0 + p["setback"] * 0.15, p["setback"] * 0.7, hv - 0.45, hv + 0.45, 0.0, 1.05, m["hedge"])
    del edge
    return y_start + p["lot"]


def house_rows(cfg, d0=8, d1=260, seed=5, coll=None, snow=0.0, skip_right=()):
    """Both sides of the street, lots spaced by each house's real width."""
    r = C.rng(seed)
    for side in (1, -1):
        e = cfg["_right_edge"] if side > 0 else cfg["_left_edge"]
        curb = e + side * 0.15
        y = d0 + r.uniform(0, 6)
        while y < d1:
            s = r.randint(0, 99999)
            p = params(s)
            if side > 0 and any(a <= y + p["lot"] and y <= b for a, b in skip_right):
                y += p["lot"]
                continue
            house(e + side * p["setback"], y, side, s, coll, snow, curb_x=curb, p=p)
            y += p["lot"]
