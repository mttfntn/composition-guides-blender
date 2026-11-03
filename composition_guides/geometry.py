# SPDX-License-Identifier: GPL-3.0-or-later
"""
Pure-math generators for composition guides (no bpy imports).

Every generator receives the frame aspect ratio (width / height) and returns a
list of line segments ``((u1, v1), (u2, v2))`` in normalized frame space, where
(0, 0) is the bottom-left corner of the frame and (1, 1) the top-right one.

Internally the geometry is built in "frame units" (width = aspect, height = 1)
so that angles such as perpendiculars and 45 degree lines are correct in
pixels for any aspect ratio, then normalized.
"""

import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0
INV_PHI = 1.0 / PHI            # 0.618...
INV_PHI2 = 1.0 - INV_PHI       # 0.381...

_EPS = 1e-9


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(segs, w, h):
    return [((x1 / w, y1 / h), (x2 / w, y2 / h)) for (x1, y1), (x2, y2) in segs]


def _corners(w, h):
    """Bottom-left, bottom-right, top-right, top-left."""
    return (0.0, 0.0), (w, 0.0), (w, h), (0.0, h)


def _foot(p, a, b):
    """Foot of the perpendicular from p onto the line through a and b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)
    return (a[0] + dx * t, a[1] + dy * t)


def _ray_exit(p, d, w, h):
    """Point where the ray p + t*d (t > 0) leaves the rectangle [0,w]x[0,h]."""
    ts = []
    if d[0] > _EPS:
        ts.append((w - p[0]) / d[0])
    elif d[0] < -_EPS:
        ts.append(-p[0] / d[0])
    if d[1] > _EPS:
        ts.append((h - p[1]) / d[1])
    elif d[1] < -_EPS:
        ts.append(-p[1] / d[1])
    ts = [t for t in ts if t > _EPS]
    t = min(ts) if ts else 0.0
    return (p[0] + d[0] * t, p[1] + d[1] * t)


def _inward(c, d, w, h):
    """Flip direction d so that it points from corner c into the frame."""
    cx, cy = w * 0.5 - c[0], h * 0.5 - c[1]
    if d[0] * cx + d[1] * cy < 0.0:
        return (-d[0], -d[1])
    return d


def _reciprocals(w, h):
    """
    Reciprocal lines of the dynamic symmetry armature: from each corner,
    perpendicular to the diagonal that does not pass through that corner,
    extended until it meets the frame edge.
    """
    bl, br, tr, tl = _corners(w, h)
    segs = []
    # Diagonal BL->TR has direction (w, h); its perpendicular is (h, -w).
    for c in (tl, br):
        d = _inward(c, (h, -w), w, h)
        segs.append((c, _ray_exit(c, d, w, h)))
    # Diagonal TL->BR has direction (w, -h); its perpendicular is (h, w).
    for c in (bl, tr):
        d = _inward(c, (h, w), w, h)
        segs.append((c, _ray_exit(c, d, w, h)))
    return segs


def _diagonals(w, h):
    bl, br, tr, tl = _corners(w, h)
    return [(bl, tr), (tl, br)]


def _vlines(xs):
    return [((x, 0.0), (x, 1.0)) for x in xs]


def _hlines(ys):
    return [((0.0, y), (1.0, y)) for y in ys]


def _dedup(values, tol=1e-6):
    out = []
    for v in values:
        if all(abs(v - o) > tol for o in out):
            out.append(v)
    return out


def remap(segs, rect):
    """Map normalized segments into the sub-rectangle (u0, v0, u1, v1)."""
    u0, v0, u1, v1 = rect
    du, dv = u1 - u0, v1 - v0
    return [((u0 + a[0] * du, v0 + a[1] * dv), (u0 + b[0] * du, v0 + b[1] * dv))
            for a, b in segs]


def rect_outline(rect):
    u0, v0, u1, v1 = rect
    return [((u0, v0), (u1, v0)), ((u1, v0), (u1, v1)),
            ((u1, v1), (u0, v1)), ((u0, v1), (u0, v0))]


# ---------------------------------------------------------------------------
# Grids
# ---------------------------------------------------------------------------

def rule_of_thirds(aspect):
    t = (1.0 / 3.0, 2.0 / 3.0)
    return _vlines(t) + _hlines(t)


def phi_grid(aspect):
    t = (INV_PHI2, INV_PHI)
    return _vlines(t) + _hlines(t)


def custom_grid(aspect, cols, rows):
    xs = [i / cols for i in range(1, cols)]
    ys = [i / rows for i in range(1, rows)]
    return _vlines(xs) + _hlines(ys)


# ---------------------------------------------------------------------------
# Golden ratio
# ---------------------------------------------------------------------------

def golden_triangle(aspect, flip=False):
    """A diagonal plus perpendiculars from the two remaining corners."""
    w, h = aspect, 1.0
    bl, br, tr, tl = _corners(w, h)
    if not flip:
        a, b, others = bl, tr, (tl, br)
    else:
        a, b, others = tl, br, (bl, tr)
    segs = [(a, b)] + [(c, _foot(c, a, b)) for c in others]
    return _normalize(segs, w, h)


def diagonal_phi(aspect, diagonals=True):
    """
    Lines from each corner to the golden point on the opposite side, forming
    two crossings on the vertical centre line at the phi heights.
    """
    w, h = aspect, 1.0
    bl, br, tr, tl = _corners(w, h)
    lo, hi = h * INV_PHI2, h * INV_PHI
    segs = [
        (tl, (w, lo)), (tr, (0.0, lo)),
        (bl, (w, hi)), (br, (0.0, hi)),
    ]
    if diagonals:
        segs += _diagonals(w, h)
    return _normalize(segs, w, h)


def _golden_squares(turns):
    """
    Yield (square, cut_segment, arc_center, start_angle) for the golden
    rectangle [0, PHI] x [0, 1], cutting squares left, top, right, bottom...
    """
    x0, y0, x1, y1 = 0.0, 0.0, PHI, 1.0
    for i in range(turns):
        s = min(x1 - x0, y1 - y0)
        k = i % 4
        if k == 0:      # square on the left
            cut = ((x0 + s, y0), (x0 + s, y1))
            center = (x0 + s, y0)
            x0 += s
        elif k == 1:    # square on top
            cut = ((x0, y1 - s), (x1, y1 - s))
            center = (x0, y1 - s)
            y1 -= s
        elif k == 2:    # square on the right
            cut = ((x1 - s, y0), (x1 - s, y1))
            center = (x1 - s, y1)
            x1 -= s
        else:           # square at the bottom
            cut = ((x0, y0 + s), (x1, y0 + s))
            center = (x1, y0 + s)
            y0 += s
        start = math.pi - i * (math.pi / 2.0)
        yield s, cut, center, start


def _orient(segs, aspect, orient, flip_h, flip_v):
    """
    Map segments from golden-rectangle space ([0, PHI] x [0, 1]) to normalized
    frame space, applying orientation and flips.
    """
    transpose = orient == 'VERTICAL' or (orient == 'AUTO' and aspect < 1.0)
    out = []
    for seg in segs:
        pts = []
        for x, y in seg:
            u, v = x / PHI, y
            if transpose:
                # Rotate 90 degrees so the long side follows the frame height.
                u, v = 1.0 - v, u
            if flip_h:
                u = 1.0 - u
            if flip_v:
                v = 1.0 - v
            pts.append((u, v))
        out.append(tuple(pts))
    return out


def golden_spiral(aspect, turns=10, orient='AUTO', flip_h=False, flip_v=False,
                  arc_steps=24):
    """Fibonacci / golden spiral made of quarter arcs, stretched to the frame."""
    segs = []
    for s, _cut, (cx, cy), start in _golden_squares(turns):
        prev = None
        for j in range(arc_steps + 1):
            a = start - (math.pi / 2.0) * (j / arc_steps)
            p = (cx + s * math.cos(a), cy + s * math.sin(a))
            if prev is not None:
                segs.append((prev, p))
            prev = p
    return _orient(segs, aspect, orient, flip_h, flip_v)


def golden_rectangles(aspect, turns=10, orient='AUTO', flip_h=False, flip_v=False):
    """The nested golden-rectangle subdivision that the spiral is built on."""
    segs = [cut for _s, cut, _c, _a in _golden_squares(turns)]
    return _orient(segs, aspect, orient, flip_h, flip_v)


# ---------------------------------------------------------------------------
# Diagonals / armatures
# ---------------------------------------------------------------------------

def baroque_diagonal(aspect):
    return [((0.0, 0.0), (1.0, 1.0))]


def sinister_diagonal(aspect):
    return [((0.0, 1.0), (1.0, 0.0))]


def dynamic_symmetry(aspect, reciprocals=True, edge_lines=True, eye_lines=False):
    w, h = aspect, 1.0
    bl, br, tr, tl = _corners(w, h)
    segs = _diagonals(w, h)
    recips = _reciprocals(w, h)
    if reciprocals:
        segs += recips
    norm = _normalize(segs, w, h)

    xs, ys = [], []
    if edge_lines:
        # Verticals / horizontals where the reciprocals meet the frame edge.
        for _c, (px, py) in recips:
            if abs(py) < 1e-6 or abs(py - h) < 1e-6:
                xs.append(px / w)
            else:
                ys.append(py / h)
    if eye_lines:
        # Through the "eyes": where reciprocals cross the diagonals.
        for c in (tl, br):
            fx, fy = _foot(c, bl, tr)
            xs.append(fx / w)
            ys.append(fy / h)
        for c in (bl, tr):
            fx, fy = _foot(c, tl, br)
            xs.append(fx / w)
            ys.append(fy / h)
    xs = [x for x in _dedup(xs) if 1e-6 < x < 1.0 - 1e-6]
    ys = [y for y in _dedup(ys) if 1e-6 < y < 1.0 - 1e-6]
    return norm + _vlines(xs) + _hlines(ys)


def harmonic_armature(aspect, reciprocals=True, rhombus=True):
    w, h = aspect, 1.0
    segs = _diagonals(w, h)
    if reciprocals:
        segs += _reciprocals(w, h)
    if rhombus:
        b, r, t, l = (w / 2, 0.0), (w, h / 2), (w / 2, h), (0.0, h / 2)
        segs += [(b, r), (r, t), (t, l), (l, b)]
    return _normalize(segs, w, h)


def diagonal_method(aspect):
    """45 degree lines from each corner (Edwin Westhoff's diagonal method)."""
    w, h = aspect, 1.0
    segs = []
    for c in _corners(w, h):
        d = (math.copysign(1.0, w * 0.5 - c[0]), math.copysign(1.0, h * 0.5 - c[1]))
        segs.append((c, _ray_exit(c, d, w, h)))
    return _normalize(segs, w, h)


# ---------------------------------------------------------------------------
# Markers / framing
# ---------------------------------------------------------------------------

def center_cross(aspect, size=0.03, full=False):
    if full:
        return _vlines((0.5,)) + _hlines((0.5,))
    w, h = aspect, 1.0
    r = size * min(w, h)
    cx, cy = w / 2, h / 2
    segs = [((cx - r, cy), (cx + r, cy)), ((cx, cy - r), (cx, cy + r))]
    return _normalize(segs, w, h)


def corner_marks(aspect, size=0.05):
    w, h = aspect, 1.0
    r = size * min(w, h)
    segs = []
    for cx, cy in _corners(w, h):
        sx = 1.0 if cx == 0.0 else -1.0
        sy = 1.0 if cy == 0.0 else -1.0
        segs.append(((cx, cy), (cx + sx * r, cy)))
        segs.append(((cx, cy), (cx, cy + sy * r)))
    return _normalize(segs, w, h)


def safe_area_rect(margin_x, margin_y):
    """Blender-style safe area: margins are the total fraction per axis."""
    mx, my = margin_x * 0.5, margin_y * 0.5
    return (mx, my, 1.0 - mx, 1.0 - my)


def crop_rect(aspect, ratio):
    """Largest centred rectangle of the given aspect ratio inside the frame."""
    if ratio <= 0.0:
        return (0.0, 0.0, 1.0, 1.0)
    if ratio < aspect:
        fw = ratio / aspect
        return ((1.0 - fw) / 2.0, 0.0, (1.0 + fw) / 2.0, 1.0)
    fh = aspect / ratio
    return (0.0, (1.0 - fh) / 2.0, 1.0, (1.0 + fh) / 2.0)


def outside_quads(rect):
    """Quads (as 4-point tuples) covering the frame area outside rect."""
    u0, v0, u1, v1 = rect
    quads = []
    if u0 > 1e-6:
        quads.append(((0, 0), (u0, 0), (u0, 1), (0, 1)))
    if u1 < 1 - 1e-6:
        quads.append(((u1, 0), (1, 0), (1, 1), (u1, 1)))
    if v0 > 1e-6:
        quads.append(((u0, 0), (u1, 0), (u1, v0), (u0, v0)))
    if v1 < 1 - 1e-6:
        quads.append(((u0, v1), (u1, v1), (u1, 1), (u0, 1)))
    return quads
