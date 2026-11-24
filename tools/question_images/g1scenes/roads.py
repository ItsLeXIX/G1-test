"""Road geometry built along a centreline path.

Convention: the road starts at the camera (y=0) and runs toward +Y.
Traffic drives on the right. Offsets are measured from the centreline,
positive = to the right of the direction of travel.
"""
import math

from . import common as C


class Path:
    """Centreline sampled every `step` metres: list of (x, y, z, heading).

    heading 0 = +Y. Curves are given as segments
    {"start": m, "angle": deg (+ = left), "radius": m}; hills as
    {"start": m, "length": m, "grade": % (+ = up)}.
    """

    def __init__(self, length=3900.0, step=1.0, curves=(), hills=(), start=-30.0):
        self.min_radius = min([c["radius"] for c in curves] or [1e9])     # strips wider than this fold on a bend
        self.pts = []
        x, y, z, h = 0.0, start, 0.0, 0.0
        s = start
        while s <= length:
            self.pts.append((x, y, z, h))
            dh = 0.0
            for c in curves:
                arc = math.radians(abs(c["angle"])) * c["radius"]
                if c["start"] <= s < c["start"] + arc:
                    dh += math.copysign(step / c["radius"], c["angle"])
            dz = 0.0
            for hl in hills:
                if hl["start"] <= s < hl["start"] + hl["length"]:
                    # smooth-step the grade in and out over 15 m
                    t = min(1.0, (s - hl["start"]) / 15, (hl["start"] + hl["length"] - s) / 15)
                    dz += step * hl["grade"] / 100 * max(0.0, t)
            h += dh
            x += -math.sin(h) * step
            y += math.cos(h) * step
            z += dz
            s += step

    def at(self, i):
        return self.pts[max(0, min(i, len(self.pts) - 1))]

    def offset(self, i, off, dz=0.0):
        x, y, z, h = self.at(i)
        # right-hand normal of heading h
        return (x + math.cos(h) * off, y + math.sin(h) * off, z + dz)

    def index_at(self, dist):
        """Index of the sample `dist` metres from the path start (y=start)."""
        return int(round(dist - self.pts[0][1]))


def ribbon(path, name, off0, off1, z_top, mat, i0=0, i1=None, wall_to=None, coll=None):
    """Flat strip between two offsets. If wall_to is set, also builds the
    vertical faces at both edges down to that height (curbs, islands)."""
    i1 = len(path.pts) if i1 is None else min(i1, len(path.pts))
    verts, faces = [], []
    for i in range(i0, i1):
        verts.append(path.offset(i, off0, z_top))
        verts.append(path.offset(i, off1, z_top))
    n = i1 - i0
    for k in range(n - 1):
        a = 2 * k
        faces.append((a, a + 2, a + 3, a + 1) if off1 > off0 else (a, a + 1, a + 3, a + 2))
    if wall_to is not None:
        base = len(verts)
        for i in range(i0, i1):
            verts.append(path.offset(i, off0, wall_to))
            verts.append(path.offset(i, off1, wall_to))
        for k in range(n - 1):
            a, b = 2 * k, base + 2 * k
            faces.append((a, b, b + 2, a + 2))           # off0 edge
            faces.append((a + 1, a + 3, b + 3, b + 1))   # off1 edge
        # end caps, so a strip that stops (e.g. at a side road) never shows
        # the dark gap underneath it
        last = 2 * (n - 1)
        faces.append((0, 1, base + 1, base))
        faces.append((last, base + last, base + last + 1, last + 1))
    return C.mesh_object(name, verts, faces, [mat], coll)


def line(path, name, off, width, mat, dash=None, gap=None, i0=0, i1=None, coll=None, z=0.004):
    """Painted line. dash/gap in metres (Ontario broken line: 3 m / 6 m)."""
    i1 = len(path.pts) if i1 is None else min(i1, len(path.pts))
    verts, faces = [], []
    period = (dash + gap) if dash else None
    k = i0
    while k < i1 - 1:
        if period:
            seg_end = min(k + int(dash), i1 - 1)
        else:
            seg_end = i1 - 1
        start = len(verts)
        for i in range(k, seg_end + 1):
            verts.append(path.offset(i, off - width / 2, z))
            verts.append(path.offset(i, off + width / 2, z))
        for j in range(seg_end - k):
            a = start + 2 * j
            faces.append((a, a + 2, a + 3, a + 1))
        k = (k + int(period)) if period else i1
    return C.mesh_object(name, verts, faces, [mat], coll)


def standard_road(path, cfg, coll=None):
    """Build a complete cross-section from a config dict.

    cfg keys (all optional):
      lanes_right, lanes_left   lanes per direction (default 1/1)
      lane_w                    3.5
      centre                    'broken_yellow' | 'solid_yellow' | 'double_yellow'
                                | 'none' | 'barrier' | 'median:<width>'
      edge                      'curb' (urban) | 'shoulder' (rural)
      boulevard, sidewalk       widths (urban)
      shoulder                  width (rural)
      lane_lines                'broken_white'
      wet, snow                 0..1
      surface_change            {"at": m, "to": "gravel"}  pavement ends
    """
    lane_w = cfg.get("lane_w", 3.5)
    nr, nl = cfg.get("lanes_right", 1), cfg.get("lanes_left", 1)
    wet, snow = cfg.get("wet", 0.0), cfg.get("snow", 0.0)
    a_mat = C.asphalt(wet, snow)
    med = 0.0
    centre = cfg.get("centre", "broken_yellow")
    flush = centre.startswith("flush:")   # painted median, island added by caller
    if centre.startswith(("median:", "flush:")):
        med = float(centre.split(":")[1])
    right_edge = med / 2 + nr * lane_w
    left_edge = -(med / 2 + nl * lane_w)
    objs = {}

    change = cfg.get("surface_change")
    i_change = path.index_at(change["at"]) if change else None

    cgaps = cfg.get("carriage_gaps", [])      # stretches with no through carriageway (a roundabout sits there)

    def paved(name, o0, o1):
        for a, b in _spans(path, cgaps):
            objs[name] = ribbon(path, name, o0, o1, 0.0, a_mat, i0=a, i1=b if i_change is None else min(b, i_change),
                                wall_to=-0.25, coll=coll)
        if change:
            ribbon(path, name + "_gravel", o0 - 0.4, o1 + 0.4, -0.02, C.gravel(), i0=i_change, coll=coll)

    if flush:
        paved("Road", left_edge, right_edge)
    elif med:
        paved("RoadR", med / 2, right_edge)
        paved("RoadL", left_edge, -med / 2)
        ribbon(path, "Median", -med / 2, med / 2, 0.15, C.grass(snow), wall_to=-0.25, coll=coll)
    else:
        paved("Road", left_edge, right_edge)

    w, y = C.paint("white"), C.paint("yellow")
    i1 = i_change
    def L(name, off, width, mat, dash=None, gap=None):
        for a, b in _spans(path, cgaps):
            line(path, name, off, width, mat, dash, gap, i0=a, i1=b if i1 is None else min(b, i1), coll=coll)

    if centre == "broken_yellow":
        L("Centre", 0, 0.1, y, 3, 6)
    elif centre == "solid_yellow":
        L("Centre", 0, 0.1, y)
    elif centre == "double_yellow":
        L("CentreA", -0.1, 0.1, y)
        L("CentreB", 0.1, 0.1, y)
    elif centre == "barrier":
        ribbon(path, "Barrier", -0.3, 0.3, 0.81, C.concrete("Barrier", 6.0, (0.6, 0.59, 0.56)), wall_to=0.0, coll=coll)
    elif med:
        L("MedEdgeR", med / 2 + 0.15, 0.1, y)
        L("MedEdgeL", -med / 2 - 0.15, 0.1, y)
    for k in range(1, nr):
        L(f"LaneR{k}", med / 2 + k * lane_w, 0.1, w, 3, 6)
    for k in range(1, nl):
        L(f"LaneL{k}", -med / 2 - k * lane_w, 0.1, w, 3, 6)

    edge = cfg.get("edge", "curb")
    side_objs = []
    # gaps: [(d0, d1), ...] stretches where curbs/verges stop (side roads)
    gaps = {1: cfg.get("gaps_right", []), -1: cfg.get("gaps_left", [])}

    def side(sgn, name, o0, o1, z, m, wall_to=None):
        for a, b in _spans(path, gaps[sgn]):
            side_objs.append(ribbon(path, name, o0, o1, z, m, i0=a, i1=b, wall_to=wall_to, coll=coll))

    if edge == "curb":
        cm = C.concrete("Curb", 3.0, (0.56, 0.55, 0.52), wet)
        blvd, walk = cfg.get("boulevard", 2.4), cfg.get("sidewalk", 1.5)
        for sgn, e in ((1, right_edge), (-1, left_edge)):
            o = lambda d: e + sgn * d  # noqa: E731
            # every strip gets walls + end caps down below the ground plane:
            # open edges showed as black strips where strips meet or stop
            side(sgn, "Curb", o(0), o(0.15), 0.15, cm, wall_to=-0.35)
            side(sgn, "Blvd", o(0.15), o(0.15 + blvd), 0.13, C.grass(snow), wall_to=-0.35)
            side(sgn, "Walk", o(0.15 + blvd), o(0.15 + blvd + walk), 0.15,
                 C.concrete("Sidewalk", 1.5, wet=wet), wall_to=-0.35)
            beyond = (C.concrete("Sidewalk", 1.5, wet=wet), 0.15) if cfg.get("beyond") == "walk"                 else (C.grass(snow), 0.14)
            side(sgn, "Lawn", o(0.15 + blvd + walk), o(70), beyond[1], beyond[0], wall_to=-0.35)
        cfg["_roadside_right"] = right_edge + 0.15 + blvd / 2
        cfg["_walk_right"] = right_edge + 0.15 + blvd + walk / 2
    else:
        sh = cfg.get("shoulder", 1.8)
        for sgn, e in ((1, right_edge), (-1, left_edge)):
            o = lambda d: e + sgn * d  # noqa: E731
            gl = (cfg.get("edge_gaps_right", []) if sgn > 0 else []) + cgaps      # e.g. an acceleration lane replaces the edge line
            for a, b in _spans(path, gl):
                line(path, "EdgeLine", o(-0.15), 0.12, w, i0=a, i1=i1 if i1 is not None and i1 < b else b, coll=coll)
            side(sgn, "Shoulder", o(0), o(sh), -0.03, C.gravel())
            side(sgn, "Verge", o(sh), o(sh + 2.5), -0.03, C.grass(snow))
            # on a tight bend a wide strip folds over itself on the inside: stop it short of the
            # centre of curvature (the flush ground plane carries on from there)
            reach = min(90.0, max(sh + 4.0, 0.8 * path.min_radius - abs(e)))
            side(sgn, "Field", o(sh + 2.5), o(reach), -0.05, C.grass(snow))
        cfg["_roadside_right"] = right_edge + sh + 0.8
    if snow > 0:
        # plough banks just beyond the pavement edge
        bank = C.mat("SnowBank", (0.8, 0.82, 0.86), 0.55)
        start = 0.4 if edge == "curb" else cfg.get("shoulder", 1.8) * 0.6
        for sgn, e in ((1, right_edge), (-1, left_edge)):
            o0, o1 = e + sgn * start, e + sgn * (start + 1.2)
            side(sgn, "SnowBank", min(o0, o1), max(o0, o1), 0.45, bank, wall_to=0.0)
    cfg["_right_edge"], cfg["_left_edge"] = right_edge, left_edge
    return objs


def _spans(path, gaps):
    """Index ranges of the path that are not inside any (d0, d1) gap."""
    cuts = sorted((path.index_at(a), path.index_at(b)) for a, b in gaps)
    spans, start = [], 0
    for a, b in cuts:
        if a > start:
            spans.append((start, a + 1))
        start = max(start, b)
    spans.append((start, len(path.pts)))
    return spans


def ground(snow=0.0, z=-0.06, coll=None):
    """Huge plane under everything so the horizon never shows a void. It runs
    past the end of the road path (3.9 km), so a road never stops in the frame.
    Its top is flush with the field strips (-0.05), so there is no step where they end."""
    return C.box("Ground", -4000, 4000, -400, 4400, z - 0.1, z, C.grass(snow), coll)


def terrain(path, snow=0.0, drop=0.3, coll=None):
    """Ground that follows the road's height (hills): one wide strip along the
    path, `drop` under the road surface. Replaces the flat ground plane so a
    road that climbs or falls never leaves the terrain behind."""
    zs = [p[2] for p in path.pts]
    ground(snow, z=min(zs) - 5.0, coll=coll)       # safety floor far below
    return ribbon(path, "Terrain", -3000, 3000, -drop, C.grass(snow), coll=coll)


def _extrude_x(name, x0, x1, profile, mat, coll=None):
    """Prism along X from a closed (y, z) profile."""
    n = len(profile)
    verts = [(x0, y, z) for y, z in profile] + [(x1, y, z) for y, z in profile]
    faces = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    faces.append(tuple(range(n))[::-1])
    faces.append(tuple(range(n, 2 * n)))
    return C.mesh_object(name, verts, faces, [mat], coll)


def rail_crossing(path, dist, width=2500.0, coll=None, angle=0.0, span=(-6.0, 6.0), z_off=0.0):
    """Single railway track across the road `dist` metres ahead, built from real
    parts: gravel ballast bed, timber ties (sleepers), two steel rails and a
    flush rubber crossing surface in the road with short asphalt ramps. The
    track runs `width` metres along its axis, past any frame edge.
    span = (x0, x1): road width incl. shoulders, so the crossing surface covers
    exactly the pavement. The crossing is the origin of the track's own frame
    (X along the rails, Y along the road) and is rotated by `angle` degrees."""
    x, y, z, h = path.at(path.index_at(dist))
    z += z_off
    steel = C.mat("RailSteel", (0.22, 0.2, 0.19), 0.45, 0.85)
    tie_m = C.mat("Tie", (0.16, 0.12, 0.09), 0.9)
    rubber = C.mat("CrossingSurface", (0.07, 0.07, 0.075), 0.85)
    ballast = C.gravel()
    half = width / 2
    parts = []
    # ballast bed: trapezoid, ~4 m wide at the top
    parts.append(_extrude_x("Ballast", -half, half,
                            [(-3.2, -0.5), (3.2, -0.5), (2.0, 0.06), (-2.0, 0.06)], ballast, coll))
    # ties every 0.6 m for 300 m either side (beyond that they are sub-pixel), one mesh
    verts, faces = [], []
    tx = -300.0
    while tx < 300.0:
        b = len(verts)
        for xx in (tx, tx + 0.26):
            for yy in (-1.3, 1.3):
                for zz in (-0.03, 0.10):
                    verts.append((xx, yy, zz))
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            faces.append(tuple(b + i for i in q))
        tx += 0.6
    parts.append(C.mesh_object("Tie", verts, faces, [tie_m], coll))
    # rails: foot, web and head (gauge 1.435 m)
    prof = [(-0.075, 0.12), (0.075, 0.12), (0.075, 0.14), (0.02, 0.155), (0.02, 0.25), (0.04, 0.265), (0.04, 0.29),
            (-0.04, 0.29), (-0.04, 0.265), (-0.02, 0.25), (-0.02, 0.155), (-0.075, 0.14)]
    for ry in (-0.7175, 0.7175):
        parts.append(_extrude_x("Rail", -half, half, [(yy + ry, zz) for yy, zz in prof], steel, coll))
    x0, x1 = span
    # flush crossing surface between and outside the rails, across the pavement
    cs = C.box("CrossingPanel", x0, x1, -1.45, 1.45, 0.0, 0.28, rubber, coll)
    parts.append(cs)
    # asphalt ramps up to the crossing surface so the road rises smoothly
    asph = C.asphalt()
    for sgn in (-1, 1):
        ya, yb = 1.45 * sgn, 3.4 * sgn
        v = [(x0, ya, 0.28), (x1, ya, 0.28), (x1, yb, 0.0), (x0, yb, 0.0)]
        parts.append(C.mesh_object("CrossingRamp", v, [(0, 1, 2, 3) if sgn > 0 else (3, 2, 1, 0)], [asph], coll))
    rail = C.to_bmesh_join(parts, "Railway")
    rail.location = (x, y, z)
    rail.rotation_euler[2] = math.radians(angle)
    return rail


def cross_road(path, dist, side="both", width=7.0, length=2500.0, coll=None, snow=0.0, wet=0.0):
    """Side road meeting the main road `dist` metres ahead (T or cross)."""
    x, y, z, h = path.at(path.index_at(dist))
    a = C.asphalt(wet, snow)
    if side in ("both", "right"):
        C.box("SideRoadR", x, x + length, y - width / 2, y + width / 2, z - 0.25, z - 0.002, a, coll)
    if side in ("both", "left"):
        C.box("SideRoadL", x - length, x, y - width / 2, y + width / 2, z - 0.25, z - 0.002, a, coll)
    # stop bar on the near side of the main road is not needed (main road has priority)
    return y


# ------------------------------------------------------------------ roundabout

def _annulus(name, r0, r1, zf, mat, cx, cy, a0=0.0, a1=360.0, wall_to=None, n_per_360=96, coll=None):
    """Ring sector between radii r0..r1 around (cx, cy), height zf (number or f(r)),
    with vertical faces down to wall_to on both edges (and end caps for arcs)."""
    f = zf if callable(zf) else (lambda r: zf)
    full = abs((a1 - a0) - 360.0) < 1e-6
    n = max(2, int(abs(a1 - a0) / 360.0 * n_per_360))
    cols = n if full else n + 1                     # a full ring shares its seam
    angs = [math.radians(a0 + (a1 - a0) * k / n) for k in range(cols)]
    verts, faces = [], []
    for a in angs:
        verts.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a), f(r0)))
        verts.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a), f(r1)))
    nq = n if full else n
    for k in range(nq):
        i, j = 2 * k, 2 * ((k + 1) % cols)
        faces.append((i, i + 1, j + 1, j))
    if wall_to is not None:
        base = len(verts)
        for a in angs:
            verts.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a), wall_to))
            verts.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a), wall_to))
        for k in range(nq):
            i, j = 2 * k, 2 * ((k + 1) % cols)
            faces.append((i, j, base + j, base + i))                 # inner wall
            faces.append((i + 1, base + i + 1, base + j + 1, j + 1))  # outer wall
        if not full:
            last = 2 * (cols - 1)
            faces.append((0, base, base + 1, 1))
            faces.append((last, last + 1, base + last + 1, base + last))
    return C.mesh_object(name, verts, faces, [mat], coll)


def _poly_prism(name, pts, z_top, z_bot, mat, coll=None):
    """Convex polygon (CCW, XY) extruded between z_bot and z_top."""
    n = len(pts)
    verts = [(x, y, z_top) for x, y in pts] + [(x, y, z_bot) for x, y in pts]
    faces = [tuple(range(n))]
    for k in range(n):
        faces.append((k, n + k, n + (k + 1) % n, (k + 1) % n))
    return C.mesh_object(name, verts, faces, [mat], coll)


def roundabout(at, radius=18.0, half_road=3.5, wet=0.0, snow=0.0, coll=None):
    """Single-lane roundabout straddling a straight road along +Y (x = 0): the
    road enters at y = `at` and leaves at y = at + 2 * radius. Circulating
    lane, truck apron, raised grass central island with curb, curbed outer edge
    with openings at entry and exit, raised splitter islands on both approaches
    and yield lines ('shark teeth') across the entry lanes. Returns the centre
    (cx, cy). The caller removes the through-carriageway between at+ and
    at + 2R- (standard_road carriage_gaps) and keeps trees out of the circle."""
    R = radius
    cx, cy = 0.0, at + R
    r_isl, r_apron, r_in = 0.5 * R, 0.6 * R, 0.6 * R
    asph = C.asphalt(wet, snow)
    conc = C.concrete("RoundaboutConcrete", 2.0, (0.6, 0.59, 0.56))
    curb = C.concrete("Curb", 3.0, (0.62, 0.61, 0.58))
    grass = C.grass(snow)
    white = C.paint("white")
    # circulating lane
    _annulus("RoadRound", r_in, R, 0.0, asph, cx, cy, wall_to=-0.25, coll=coll)
    # truck apron (low, concrete) and the raised, domed grass island with its curb
    _annulus("RoundaboutApron", r_isl + 0.25, r_apron, 0.06, conc, cx, cy, wall_to=0.0, coll=coll)
    _annulus("RoundaboutCurb", r_isl, r_isl + 0.25, 0.16, curb, cx, cy, wall_to=0.0, coll=coll)
    rs = [0.05, 1.5, 3.0, 4.5, 6.0, 7.5, r_isl]
    verts, faces = [], []
    na = 64
    for r in rs:
        for k in range(na):
            a = 2 * math.pi * k / na
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), 0.16 + 0.85 * (1 - (r / r_isl) ** 2)))
    for j in range(len(rs) - 1):
        for k in range(na):
            a, b = j * na + k, j * na + (k + 1) % na
            faces.append((a, a + na, b + na, b))
    C.mesh_object("RoundaboutIsland", verts, faces, [grass], coll, smooth=True)
    # curbed outer edge, open where the road enters and leaves
    gap = math.degrees(math.asin((half_road + 0.7) / R))
    for a0, a1 in ((-90 + gap, 90 - gap), (90 + gap, 270 - gap)):
        _annulus("RoundaboutCurb", R, R + 0.3, 0.14, curb, cx, cy, a0, a1, wall_to=0.0, coll=coll)
    # splitter islands: tapered raised islands that split each approach
    for sgn, y_ring in ((-1, at), (1, at + 2 * R)):
        y_nose = y_ring + sgn * -16.0 if sgn < 0 else y_ring + 16.0
        if sgn < 0:
            pts = [(-0.25, at - 16.0), (0.25, at - 16.0), (1.25, at - 3.0), (1.25, at + 0.25), (-1.25, at + 0.25), (-1.25, at - 3.0)]
        else:
            ye = at + 2 * R
            pts = [(1.25, ye - 0.25), (1.25, ye + 3.0), (0.25, ye + 16.0), (-0.25, ye + 16.0), (-1.25, ye + 3.0), (-1.25, ye - 0.25)]
        _poly_prism("Splitter", pts, 0.16, -0.05, conc, coll)
    # yield line (shark teeth) across the right-hand entry lane
    v, f = [], []
    x = 1.5
    while x + 0.6 <= half_road - 0.1:
        b = len(v)
        v += [(x, at - 0.15, 0.006), (x + 0.6, at - 0.15, 0.006), (x + 0.3, at - 0.95, 0.006)]
        f.append((b, b + 2, b + 1))
        x += 0.8
    C.mesh_object("YieldLine", v, f, [white], coll)
    return cx, cy
