"""Scene checks and ground snapping for the G1 question images (run inside Blender).

Rules enforced here, for every scene template:
  * nothing (tree, pole, building) stands on asphalt, a shoulder or a sidewalk
    -> check_placement() fails the render
  * every tree/pole sits on the ground: no gap under it, no buried trunk
    -> snap_to_ground() + check_grounded()
  * no road, side road or ramp stops inside the frame -> check_road_ends()
"""
import bpy
from mathutils import Vector

# paved surfaces nothing may stand on (object name before any ".001" suffix)
ROAD_SURFACES = ("Road", "RoadR", "RoadL", "Shoulder", "Walk", "SideRoadR", "SideRoadL", "OnRamp", "RoadMerge",
                 "RoadRound", "RoundaboutRoad", "CrossingPanel", "CrossingRamp", "RoadHump", "Curb")
# surfaces that count as "the ground" an object may sit on
GROUND_SURFACES = ROAD_SURFACES + ("Ground", "Terrain", "Field", "Verge", "Lawn", "Blvd", "Island", "IslandTop",
                                   "Median", "IslandNose", "IslandNoseCurb", "IslandCurb", "Driveway", "RockCut", "Embankment", "Bank", "Ballast", "Roundabout",
                                   "RoundaboutIsland", "RoundaboutApron", "Gore", "Splitter", "Landing", "PorchDeck")
# things that stand on the ground: trees, poles, masts, buildings
PLACED = ("Tree", "tree_deciduous", "Post_", "XingMast", "StreetLight", "Streetlight", "LampPost", "Pole", "House",
          "Garage", "SignalPole", "MastPole", "Hedge", "Abutment")
EMBED = 0.02          # tree feet sink this far into the ground (m): no gap, no buried trunk


def base(o):
    return o.name.split(".")[0]


def is_tree(o):
    if o.type == "MESH" and o.name.startswith("TreeProto"):
        return False
    return base(o).startswith(("Tree", "tree_deciduous")) or o.get("g1_kind", "").startswith("tree")


def is_placed(o):
    if o.type == "MESH" and o.name.startswith("TreeProto"):
        return False
    return base(o).startswith(PLACED) or o.get("g1_kind", "").startswith("tree")


def surface_tris(names):
    """World-space XY triangles of the named surfaces: [(object, xy (N,3,2), z (N,3))]."""
    import numpy as np
    out = []
    bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.type != "MESH" or base(o) not in names or o.hide_render:
            continue
        me = o.data
        me.calc_loop_triangles()
        mw = o.matrix_world
        co = np.array([tuple(mw @ v.co) for v in me.vertices], dtype=np.float64).reshape(-1, 3)
        tris = np.array([t.vertices[:] for t in me.loop_triangles], dtype=np.int64).reshape(-1, 3)
        if not len(tris):
            continue
        a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
        keep = np.abs(np.cross(b - a, c - a)[:, 2]) > 1e-9      # drop vertical walls (no XY area)
        out.append((o, np.stack([a[keep, :2], b[keep, :2], c[keep, :2]], axis=1),
                    np.stack([a[keep, 2], b[keep, 2], c[keep, 2]], axis=1)))
    return out


def inside(tri_xy, p):
    """Boolean array: is XY point p inside each triangle."""
    import numpy as np
    a, b, c = tri_xy[:, 0], tri_xy[:, 1], tri_xy[:, 2]
    v0, v1, v2 = c - a, b - a, np.asarray(p) - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    den = np.where(np.abs(den) < 1e-12, 1e-12, den)
    u = (d11 * d20 - d01 * d21) / den
    v = (d00 * d21 - d01 * d20) / den
    return (u >= 0) & (v >= 0) & (u + v <= 1)


def footprint(o):
    """Ground footprint sample points (XY) of a placed object."""
    import math as m
    if o.type == "EMPTY":              # tree instance: trunk radius ~0.45 m x scale
        r = 0.45 * max(o.scale)
        t = o.matrix_world.translation
        return [(t.x + r * m.cos(k * m.pi / 4), t.y + r * m.sin(k * m.pi / 4)) for k in range(8)] + [(t.x, t.y)]
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    zmin = min(p.z for p in pts)
    lo = [p for p in pts if p.z < zmin + 0.5]
    x0, x1 = min(p.x for p in lo), max(p.x for p in lo)
    y0, y1 = min(p.y for p in lo), max(p.y for p in lo)
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    if base(o).startswith("Tree"):      # trunk, not the canopy
        r = 0.35 * max(o.scale)
        x0, x1, y0, y1 = xm - r, xm + r, ym - r, ym + r
    return [(x0, y0), (x0, y1), (x1, y0), (x1, y1), (xm, ym), (xm, y0), (xm, y1), (x0, ym), (x1, ym)]


def check_placement():
    """Reject any object whose footprint overlaps a road / shoulder / sidewalk.
    The surface on top at each footprint point decides, so a sign post on a
    raised island (which sits over the road strip) is fine."""
    bpy.context.view_layer.update()
    bad = []
    for o in bpy.data.objects:
        if not is_placed(o) or o.hide_render or base(o).endswith("_root"):
            continue
        pts = footprint(o)
        if o.type != "EMPTY" and not base(o).startswith(("Tree", "Post_", "Pole", "StreetLight", "Streetlight", "XingMast")):
            # buildings/hedges: only the middle of the footprint (they may touch a sidewalk edge)
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            pts = [(cx, cy), ((cx + min(xs)) / 2, cy), ((cx + max(xs)) / 2, cy), (cx, (cy + min(ys)) / 2), (cx, (cy + max(ys)) / 2)]
        z0 = o.matrix_world.translation.z
        for pt in pts:
            hit = ground_hit(pt[0], pt[1], z_from=z0 + 60.0)
            if hit is not None and base(hit[1]) in ROAD_SURFACES and not (base(hit[1]) == "Curb" and not base(o).startswith("Tree")):
                bad.append(f"{o.name} at ({pt[0]:.1f}, {pt[1]:.1f}) stands on {hit[1].name}")
                break
    if bad:
        raise SystemExit("placement: " + "; ".join(bad[:8]) + (f" (+{len(bad) - 8} more)" if len(bad) > 8 else ""))
    return 0


def _cast_down(x, y, z_from, loops):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    start = Vector((x, y, z_from))
    for _ in range(loops):
        hit, loc, _n, _i, ob, _m = sc.ray_cast(dg, start, Vector((0, 0, -1)))
        if not hit:
            return None
        if base(ob) in GROUND_SURFACES:
            return loc.z, ob
        start = loc + Vector((0, 0, -0.005))
    return None


def ground_hit(x, y, z_from=60.0):
    """(z, object) of the first ground-type surface under (x, y), or None.
    Tries from just above the object first (cheap), then from high up."""
    h = _cast_down(x, y, z_from - 58.0, 60)
    return h if h else _cast_down(x, y, z_from, 800)


def ground_z(x, y, z_from=60.0):
    """Height of the first ground-type surface under (x, y)."""
    h = ground_hit(x, y, z_from)
    return h[0] if h else None


def snap_to_ground():
    """Put every tree exactly on the surface under it, feet EMBED m in."""
    bpy.context.view_layer.update()
    n = 0
    for o in bpy.data.objects:
        if o.hide_render or o.parent is not None or not is_tree(o) or base(o).endswith("_root"):
            continue
        t = o.matrix_world.translation
        z = ground_z(t.x, t.y, z_from=t.z + 60.0)
        if z is None:
            continue
        o.location.z += (z - EMBED) - t.z
        n += 1
    bpy.context.view_layer.update()
    return n


def check_grounded(tol=0.12):
    """Floating / sinking test for trees and poles."""
    bpy.context.view_layer.update()
    bad = []
    for o in bpy.data.objects:
        if o.hide_render or o.parent is not None or not is_placed(o) or base(o).endswith("_root"):
            continue
        if base(o).startswith(("House", "Garage", "Hedge", "Post_", "Abutment")):
            continue
        t = o.matrix_world.translation
        z = ground_z(t.x, t.y, z_from=t.z + 60.0)
        if z is None:
            bad.append(f"{o.name} has no ground under it")
        elif abs(t.z - z) > tol:
            bad.append(f"{o.name} {'floats' if t.z > z else 'sinks'} {abs(t.z - z):.2f} m")
    if bad:
        raise SystemExit("grounding: " + "; ".join(bad[:8]))


def check_road_ends(max_dist=1500.0):
    """No road, side road, ramp or sidewalk may stop inside the frame. Every
    short open edge of such a mesh (a cut-off end) must be hidden: covered by
    another road surface, outside the frame, behind scenery, or farther than
    max_dist (past the horizon, under 3 px)."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = sc.camera
    dg = bpy.context.evaluated_depsgraph_get()
    roads = ("Road", "RoadR", "RoadL", "SideRoadR", "SideRoadL", "OnRamp", "RoadMerge", "RoadRound", "RoundaboutRoad", "Walk")
    surf = surface_tris(ROAD_SURFACES)
    bad = []
    for o in bpy.data.objects:
        if o.type != "MESH" or base(o) not in roads or o.hide_render:
            continue
        me = o.data
        mw = o.matrix_world
        counts, owner = {}, {}
        for p in me.polygons:
            for k in p.edge_keys:
                counts[k] = counts.get(k, 0) + 1
                owner[k] = p
        bedges = [k for k, c in counts.items() if c == 1]
        at_vert = {}
        for k in bedges:
            for v in k:
                at_vert.setdefault(v, []).append(k)
        for k in bedges:
            a, b = mw @ me.vertices[k[0]].co, mw @ me.vertices[k[1]].co
            ln = (a - b).length
            if ln > 16.0 or ln < 0.02:
                continue
            # an END edge turns a corner (> ~50 deg) with the open edges it meets;
            # an edge along the side of the strip continues straight
            d1 = (b - a).normalized()
            corner = False
            for v in k:
                for k2 in at_vert[v]:
                    if k2 == k:
                        continue
                    p2, q2 = mw @ me.vertices[k2[0]].co, mw @ me.vertices[k2[1]].co
                    if (p2 - q2).length < 0.02:
                        continue
                    if abs(d1.dot((q2 - p2).normalized())) < 0.64:
                        corner = True
            if not corner:
                continue
            if abs(a.z - b.z) > 0.2 and ln < 0.6:
                continue                       # a vertical wall edge
            m = (a + b) / 2
            if (m - cam.location).length > max_dist:
                continue
            q = world_to_camera_view(sc, cam, m)
            if q.z <= 0 or not (-0.02 <= q.x <= 1.02 and -0.02 <= q.y <= 1.02):
                continue
            e = b - a
            nrm = Vector((-e.y, e.x, 0))
            if nrm.length < 1e-9:
                continue
            nrm.normalize()
            cen = mw @ owner[k].center
            if (m + nrm * 0.4 - cen).length < (m - nrm * 0.4 - cen).length:
                nrm = -nrm
            out_pt = m + nrm * 0.4
            if any(so is not o and inside(txy, (out_pt.x, out_pt.y)).any() for so, txy, _tz in surf):
                continue                       # joins another road surface
            d = m - cam.location
            hit, loc, _n, _i, ob, _m = sc.ray_cast(dg, cam.location, d.normalized(), distance=max(0.1, d.length - 0.3))
            if hit and base(ob) not in GROUND_SURFACES:
                continue                       # hidden behind scenery
            if hit and loc.z > m.z + 0.05:
                continue                       # buried under terrain (a crest) = hidden
            bad.append(f"{o.name} stops at ({m.x:.0f}, {m.y:.0f}), {d.length:.0f} m away, at frame ({q.x:.2f}, {q.y:.2f})")
            break
    if bad:
        raise SystemExit("road end visible: " + "; ".join(bad[:6]))
