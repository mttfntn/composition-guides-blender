"""Checks for the pure-math guide generators. Run with: python tests/test_geometry.py"""

import importlib.util
import math
import os
import sys

_PATH = os.path.join(os.path.dirname(__file__), "..", "composition_guides", "geometry.py")
_spec = importlib.util.spec_from_file_location("geometry", _PATH)
g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g)

ASPECTS = (16 / 9, 9 / 16, 1.0, 2.39, 4 / 3)
TOL = 1e-6


def inside(segs):
    return all(-TOL <= c <= 1 + TOL for seg in segs for p in seg for c in p)


def to_px(p, aspect):
    return (p[0] * aspect, p[1])


def dot_px(seg_a, seg_b, aspect):
    (a1, a2), (b1, b2) = [tuple(to_px(p, aspect) for p in s) for s in (seg_a, seg_b)]
    da = (a2[0] - a1[0], a2[1] - a1[1])
    db = (b2[0] - b1[0], b2[1] - b1[1])
    return (da[0] * db[0] + da[1] * db[1]) / (math.hypot(*da) * math.hypot(*db))


def test_all_inside():
    for a in ASPECTS:
        for segs in (
            g.rule_of_thirds(a), g.phi_grid(a), g.custom_grid(a, 5, 3),
            g.golden_triangle(a), g.golden_triangle(a, True),
            g.diagonal_phi(a), g.golden_spiral(a), g.golden_rectangles(a),
            g.golden_spiral(a, orient='VERTICAL', flip_h=True, flip_v=True),
            g.dynamic_symmetry(a, True, True, True), g.harmonic_armature(a),
            g.diagonal_method(a), g.center_cross(a), g.corner_marks(a),
        ):
            assert segs and inside(segs), a


def test_grid_values():
    xs = sorted(s[0][0] for s in g.phi_grid(1.5) if s[0][0] == s[1][0])
    assert abs(xs[0] - 0.381966) < 1e-5 and abs(xs[1] - 0.618034) < 1e-5
    xs = sorted(s[0][0] for s in g.rule_of_thirds(1.5) if s[0][0] == s[1][0])
    assert abs(xs[0] - 1 / 3) < TOL and abs(xs[1] - 2 / 3) < TOL


def test_golden_triangle_perpendicular():
    for a in ASPECTS:
        for flip in (False, True):
            diag, p1, p2 = g.golden_triangle(a, flip)
            assert abs(dot_px(diag, p1, a)) < 1e-9
            assert abs(dot_px(diag, p2, a)) < 1e-9


def test_reciprocals_perpendicular():
    for a in ASPECTS:
        segs = g.dynamic_symmetry(a, True, False, False)
        d1, d2, r_tl, r_br, r_bl, r_tr = segs
        for r in (r_tl, r_br):
            assert abs(dot_px(d1, r, a)) < 1e-9
        for r in (r_bl, r_tr):
            assert abs(dot_px(d2, r, a)) < 1e-9


def test_diagonal_method_45():
    for a in ASPECTS:
        for (p1, p2) in g.diagonal_method(a):
            dx = (p2[0] - p1[0]) * a
            dy = p2[1] - p1[1]
            assert abs(abs(dx) - abs(dy)) < 1e-9


def test_spiral_continuous_and_spans_frame():
    segs = g.golden_spiral(16 / 9, turns=10, orient='HORIZONTAL')
    for (_a, b), (c, _d) in zip(segs, segs[1:]):
        assert math.dist(b, c) < 1e-9
    us = [p[0] for s in segs for p in s]
    vs = [p[1] for s in segs for p in s]
    assert min(us) < 1e-9 and max(us) > 1 - 1e-9
    assert min(vs) < 1e-9 and max(vs) > 1 - 1e-9


def test_crop():
    r = g.crop_rect(16 / 9, 2.39)
    w = (r[2] - r[0]) * 16 / 9
    h = r[3] - r[1]
    assert abs(w / h - 2.39) < 1e-9 and r[0] == 0.0
    r = g.crop_rect(16 / 9, 1.0)
    assert abs((r[2] - r[0]) * 16 / 9 / (r[3] - r[1]) - 1.0) < 1e-9
    assert len(g.outside_quads(r)) == 2


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok  ", name)
            except AssertionError as ex:
                failed += 1
                print("FAIL", name, ex)
    sys.exit(1 if failed else 0)
