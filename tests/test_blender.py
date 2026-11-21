"""
Checks that need Blender (registration, settings, operators, camera fitting).

Run headless:
    blender --background --factory-startup --python tests/test_blender.py
Exits with code 1 on failure.
"""

import os
import sys
import traceback

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import composition_guides as cg  # noqa: E402

G = [g[0] for g in cg.properties.GUIDES]


def _projector(scene, cam, rx, ry):
    """Projector for a fake viewport that looks exactly through the camera."""
    scene.render.resolution_x, scene.render.resolution_y = rx, ry
    dg = bpy.context.evaluated_depsgraph_get()
    proj = cam.calc_matrix_camera(dg, x=rx, y=ry)

    class RV3D:
        perspective_matrix = proj @ cam.matrix_world.inverted()

    class Region:
        width, height = rx, ry

    return cg.draw._FrameProjector(scene, cam, Region, RV3D)


def test_defaults():
    s = bpy.context.scene.composition_guides
    assert s.enabled
    assert abs(s.opacity - 0.4) < 1e-6
    assert tuple(s.color)[3] == 1.0
    assert all(getattr(s, "color_" + g)[3] == 1.0 for g in G)
    assert [g for g in G if getattr(s, "show_" + g)] == ["thirds"]


def test_all_on_skips_framing():
    s = bpy.context.scene.composition_guides
    bpy.ops.view3d.composition_guides_all(state=True)
    assert not s.show_safe_areas and not s.show_crop
    assert all(getattr(s, "show_" + g) for g in G if g not in ("safe_areas", "crop"))
    bpy.ops.view3d.composition_guides_all(state=False)
    assert not any(getattr(s, "show_" + g) for g in G)
    s.show_thirds = True


def test_collapsed_panels():
    closed = {c.__name__ for c in cg.ui.classes if 'DEFAULT_CLOSED' in getattr(c, "bl_options", ())}
    assert closed == {"VIEW3D_PT_composition_guides_golden",
                      "VIEW3D_PT_composition_guides_armatures",
                      "VIEW3D_PT_composition_guides_framing"}, closed


def test_frame_matches_camera_border():
    scene = bpy.context.scene
    cam = scene.camera
    for fit in ("AUTO", "HORIZONTAL", "VERTICAL"):
        cam.data.sensor_fit = fit
        cam.data.shift_x, cam.data.shift_y = 0.13, -0.07
        for rx, ry in ((1920, 1080), (1080, 1920), (1000, 1000), (2048, 858)):
            p = _projector(scene, cam, rx, ry)
            got = [p.point(u, v) for u, v in ((0, 0), (1, 0), (1, 1), (0, 1))]
            want = [(0, 0), (rx, 0), (rx, ry), (0, ry)]
            err = max(abs(a - b) for g, w in zip(got, want) for a, b in zip(g, w))
            assert err < 0.01, (fit, rx, ry, got)
            assert abs(p.aspect - rx / ry) < 1e-4
    cam.data.shift_x = cam.data.shift_y = 0.0


def test_every_guide_builds():
    scene = bpy.context.scene
    s = scene.composition_guides
    p = _projector(scene, scene.camera, 1920, 1080)
    for g in G:
        setattr(s, "show_" + g, True)
    for preset, *_ in cg.properties.CROP_PRESETS:
        s.crop_preset = preset
        layers = cg.draw.build_layers(s, p.aspect, scene)
        assert {gid for gid, _segs, _q in layers} == set(G)
        for gid, segs, quads in layers:
            assert p.segments(segs), gid
            for (u1, v1), (u2, v2) in segs:
                assert all(-1e-6 <= c <= 1 + 1e-6 for c in (u1, v1, u2, v2)), gid
    for g in G:
        setattr(s, "show_" + g, g == "thirds")


def test_reregister():
    cg.unregister()
    cg.register()


def main():
    cg.register()
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok  ", name)
            except Exception:  # noqa: BLE001 - report every failing test
                failed += 1
                print("FAIL", name)
                traceback.print_exc()
    cg.unregister()
    print("BLENDER TESTS", "FAILED" if failed else "PASSED")
    sys.exit(1 if failed else 0)


main()
