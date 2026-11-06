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

    def __init__(self, length=320.0, step=1.0, curves=(), hills=(), start=-30.0):
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

    def paved(name, o0, o1):
        objs[name] = ribbon(path, name, o0, o1, 0.0, a_mat, i1=i_change, wall_to=-0.25, coll=coll)
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
    if centre == "broken_yellow":
        line(path, "Centre", 0, 0.1, y, 3, 6, i1=i1, coll=coll)
    elif centre == "solid_yellow":
        line(path, "Centre", 0, 0.1, y, i1=i1, coll=coll)
    elif centre == "double_yellow":
        line(path, "CentreA", -0.1, 0.1, y, i1=i1, coll=coll)
        line(path, "CentreB", 0.1, 0.1, y, i1=i1, coll=coll)
    elif centre == "barrier":
        ribbon(path, "Barrier", -0.3, 0.3, 0.81, C.concrete("Barrier", 6.0, (0.6, 0.59, 0.56)), wall_to=0.0, coll=coll)
    elif med:
        line(path, "MedEdgeR", med / 2 + 0.15, 0.1, y, i1=i1, coll=coll)
        line(path, "MedEdgeL", -med / 2 - 0.15, 0.1, y, i1=i1, coll=coll)
    for k in range(1, nr):
        line(path, f"LaneR{k}", med / 2 + k * lane_w, 0.1, w, 3, 6, i1=i1, coll=coll)
    for k in range(1, nl):
        line(path, f"LaneL{k}", -med / 2 - k * lane_w, 0.1, w, 3, 6, i1=i1, coll=coll)

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
            line(path, "EdgeLine", o(-0.15), 0.12, w, i1=i1, coll=coll)
            side(sgn, "Shoulder", o(0), o(sh), -0.03, C.gravel())
            side(sgn, "Verge", o(sh), o(sh + 2.5), -0.03, C.grass(snow))
            side(sgn, "Field", o(sh + 2.5), o(90), -0.05, C.grass(snow))
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


def ground(snow=0.0, z=-0.3, coll=None):
    """Huge plane under everything so the horizon never shows a void."""
    return C.box("Ground", -2000, 2000, -200, 4000, z - 0.1, z, C.grass(snow), coll)


def rail_crossing(path, dist, width=40.0, coll=None, angle=0.0):
    """Two rails + ties + ballast crossing the road `dist` metres ahead."""
    x, y, z, h = path.at(path.index_at(dist))
    steel = C.mat("RailSteel", (0.25, 0.22, 0.2), 0.4, 0.8)
    tie = C.mat("Tie", (0.18, 0.13, 0.09), 0.9)
    ballast = C.gravel()
    objs = [C.box("Ballast", x - width / 2, x + width / 2, y - 1.8, y + 1.8, z - 0.25, z - 0.02, ballast, coll)]
    for k in range(int(width / 0.6)):
        tx = x - width / 2 + k * 0.6
        objs.append(C.box("Tie", tx, tx + 0.22, y - 1.3, y + 1.3, z - 0.05, z + 0.02, tie, coll))
    for ry in (-0.72, 0.72):
        objs.append(C.box("Rail", x - width / 2, x + width / 2, y + ry - 0.04, y + ry + 0.04, z, z + 0.06, steel, coll))
    # rubber crossing panels flush with the road
    C.box("CrossingPanel", x - 4, x + 4, y - 1.2, y + 1.2, z - 0.02, z + 0.06, C.mat("Rubber", (0.05, 0.05, 0.05), 0.8), coll)
    rail = C.to_bmesh_join(objs, "Railway")
    rail.rotation_euler[2] = math.radians(angle)
    return rail


def cross_road(path, dist, side="both", width=7.0, length=80.0, coll=None, snow=0.0, wet=0.0):
    """Side road meeting the main road `dist` metres ahead (T or cross)."""
    x, y, z, h = path.at(path.index_at(dist))
    a = C.asphalt(wet, snow)
    if side in ("both", "right"):
        C.box("SideRoadR", x, x + length, y - width / 2, y + width / 2, z - 0.25, z - 0.002, a, coll)
    if side in ("both", "left"):
        C.box("SideRoadL", x - length, x, y - width / 2, y + width / 2, z - 0.25, z - 0.002, a, coll)
    # stop bar on the near side of the main road is not needed (main road has priority)
    return y
