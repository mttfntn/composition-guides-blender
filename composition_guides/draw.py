# SPDX-License-Identifier: GPL-3.0-or-later
"""
Viewport overlay drawing.

The guides are drawn with the gpu module in a POST_PIXEL draw handler, on top
of whatever the viewport shows, so they work with every render engine
(Eevee, Cycles, Workbench, Octane, Redshift, ...) and every shading mode.

The camera frame comes from Camera.view_frame(), which accounts for the render
resolution, pixel aspect, sensor fit and lens shift, so in camera view the
guides match the camera border (passepartout) exactly.
"""

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from . import geometry

_handle = None
_shaders = {}

_SHADOW = (0.0, 0.0, 0.0)


def _builtin_shader(key, *names):
    """First available built-in shader from names (names changed in Blender 4.0)."""
    if key not in _shaders:
        shader, used = None, None
        for name in names:
            try:
                shader, used = gpu.shader.from_builtin(name), name
                break
            except (ValueError, TypeError, SystemError):
                continue
        _shaders[key] = shader
        _shaders[key + "_name"] = used
    return _shaders[key]


def _line_shader():
    return _builtin_shader("line", "POLYLINE_UNIFORM_COLOR", "3D_POLYLINE_UNIFORM_COLOR")


def _flat_shader():
    return _builtin_shader("flat", "UNIFORM_COLOR", "2D_UNIFORM_COLOR")


def _flat_is_2d():
    # Blender < 4.0 only has the 2D_ variant, which takes 2D positions.
    _flat_shader()
    return _shaders.get("flat_name") == "2D_UNIFORM_COLOR"


def _guide_camera(context, settings):
    if settings.camera is not None and settings.camera.type == 'CAMERA':
        return settings.camera
    space = context.space_data
    if space is not None and getattr(space, "use_local_camera", False) and space.camera:
        cam = space.camera
    else:
        cam = context.scene.camera
    if cam is None or cam.type != 'CAMERA':
        return None
    return cam


class _FrameProjector:
    """Maps normalized frame coordinates (u, v) to region pixels."""

    def __init__(self, scene, cam, region, rv3d):
        frame = cam.data.view_frame(scene=scene)
        xs = [v.x for v in frame]
        ys = [v.y for v in frame]
        self.x0, self.x1 = min(xs), max(xs)
        self.y0, self.y1 = min(ys), max(ys)
        self.z = frame[0].z
        self.matrix = rv3d.perspective_matrix @ cam.matrix_world
        self.half_w = region.width * 0.5
        self.half_h = region.height * 0.5

    @property
    def aspect(self):
        h = self.y1 - self.y0
        return (self.x1 - self.x0) / h if h > 0.0 else 1.0

    def point(self, u, v):
        x = self.x0 + (self.x1 - self.x0) * u
        y = self.y0 + (self.y1 - self.y0) * v
        co = self.matrix @ Vector((x, y, self.z, 1.0))
        if co.w <= 1e-6:
            return None     # behind the viewer
        return (self.half_w + self.half_w * co.x / co.w,
                self.half_h + self.half_h * co.y / co.w)

    def segments(self, segs):
        coords = []
        for a, b in segs:
            pa = self.point(*a)
            pb = self.point(*b)
            if pa is None or pb is None:
                continue
            coords.append((pa[0], pa[1], 0.0))
            coords.append((pb[0], pb[1], 0.0))
        return coords

    def triangles(self, quads):
        coords = []
        for quad in quads:
            pts = [self.point(*p) for p in quad]
            if None in pts:
                continue
            a, b, c, d = [(p[0], p[1], 0.0) for p in pts]
            coords += [a, b, c, a, c, d]
        return coords


def build_layers(settings, aspect, scene):
    """
    Return a list of (guide_id, segments, fill_quads) in normalized frame
    space for every enabled guide.
    """
    s = settings
    layers = []
    inner = (0.0, 0.0, 1.0, 1.0)
    inner_aspect = aspect

    if s.show_crop:
        ratio = s.crop_ratio()
        rect = geometry.crop_rect(aspect, ratio)
        quads = geometry.outside_quads(rect) if s.crop_dim > 0.0 else []
        layers.append(("crop", geometry.rect_outline(rect), quads))
        if s.crop_fit_guides:
            inner, inner_aspect = rect, ratio

    def add(gid, segs, relative=True):
        if relative:
            segs = geometry.remap(segs, inner)
        layers.append((gid, segs, []))

    a = inner_aspect
    if s.show_thirds:
        add("thirds", geometry.rule_of_thirds(a))
    if s.show_phi:
        add("phi", geometry.phi_grid(a))
    if s.show_grid:
        add("grid", geometry.custom_grid(a, s.grid_cols, s.grid_rows))
    if s.show_golden_triangle:
        add("golden_triangle", geometry.golden_triangle(a, s.triangle_flip))
    if s.show_diagonal_phi:
        add("diagonal_phi", geometry.diagonal_phi(a, s.diagonal_phi_diagonals))
    if s.show_golden_sections:
        add("golden_sections", geometry.golden_rectangles(
            a, s.spiral_turns, s.spiral_orient, s.spiral_flip_h, s.spiral_flip_v))
    if s.show_spiral:
        add("spiral", geometry.golden_spiral(
            a, s.spiral_turns, s.spiral_orient, s.spiral_flip_h, s.spiral_flip_v))
    if s.show_dynamic_symmetry:
        add("dynamic_symmetry", geometry.dynamic_symmetry(
            a, s.dynsym_reciprocals, s.dynsym_edge_lines, s.dynsym_eye_lines))
    if s.show_harmonic:
        add("harmonic", geometry.harmonic_armature(
            a, s.harmonic_reciprocals, s.harmonic_rhombus))
    if s.show_baroque:
        add("baroque", geometry.baroque_diagonal(a))
    if s.show_sinister:
        add("sinister", geometry.sinister_diagonal(a))
    if s.show_diagonal_method:
        add("diagonal_method", geometry.diagonal_method(a))
    if s.show_center:
        add("center", geometry.center_cross(a, s.center_size, s.center_full))
    if s.show_corners:
        add("corners", geometry.corner_marks(aspect, s.corners_size), relative=False)
    if s.show_safe_areas:
        sa = scene.safe_areas
        segs = []
        for mx, my in (tuple(sa.title), tuple(sa.action)):
            if mx > 0.0 or my > 0.0:
                segs += geometry.rect_outline(geometry.safe_area_rect(mx, my))
        add("safe_areas", segs, relative=False)
    return layers


def _draw_lines(shader, coords, color, width, viewport, poly):
    if not coords:
        return
    batch = batch_for_shader(shader, 'LINES', {"pos": coords})
    shader.bind()
    shader.uniform_float("color", color)
    if poly:
        shader.uniform_float("viewportSize", viewport)
        shader.uniform_float("lineWidth", width)
    batch.draw(shader)


def draw_callback():
    context = bpy.context
    scene = context.scene
    settings = getattr(scene, "composition_guides", None)
    if settings is None or not settings.enabled:
        return
    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return
    if rv3d.view_perspective != 'CAMERA' and not settings.show_outside_camera:
        return
    cam = _guide_camera(context, settings)
    if cam is None:
        return

    try:
        proj = _FrameProjector(scene, cam, region, rv3d)
    except (AttributeError, ValueError, ZeroDivisionError):
        return

    layers = build_layers(settings, proj.aspect, scene)
    if not layers:
        return

    line_shader = _line_shader()
    flat_shader = _flat_shader()
    if flat_shader is None:
        return
    poly = line_shader is not None
    if not poly:
        line_shader = flat_shader

    ui_scale = context.preferences.system.ui_scale
    width = settings.line_width * ui_scale
    viewport = (float(region.width), float(region.height))
    opacity = settings.opacity

    def color_for(gid):
        if settings.use_guide_colors:
            c = getattr(settings, "color_" + gid)
        else:
            c = settings.color
        return (c[0], c[1], c[2], c[3] * opacity)

    flat_2d = _flat_is_2d()
    batches = []
    for gid, segs, quads in layers:
        coords = proj.segments(segs)
        tris = proj.triangles(quads)
        if flat_2d:
            tris = [(x, y) for x, y, _z in tris]
            if not poly:
                coords = [(x, y) for x, y, _z in coords]
        batches.append((color_for(gid), coords, tris))

    gpu.state.blend_set('ALPHA')

    # Dimmed areas (crop mask)
    dim = settings.crop_dim * opacity
    for _color, _coords, tris in batches:
        if tris:
            batch = batch_for_shader(flat_shader, 'TRIS', {"pos": tris})
            flat_shader.bind()
            flat_shader.uniform_float("color", (0.0, 0.0, 0.0, dim))
            batch.draw(flat_shader)

    if not poly:
        gpu.state.line_width_set(width)

    if settings.shadow:
        shadow_w = width + 2.0 * ui_scale
        if not poly:
            gpu.state.line_width_set(shadow_w)
        for color, coords, _tris in batches:
            _draw_lines(line_shader, coords, _SHADOW + (color[3] * 0.45,),
                        shadow_w, viewport, poly)
        if not poly:
            gpu.state.line_width_set(width)

    for color, coords, _tris in batches:
        _draw_lines(line_shader, coords, color, width, viewport, poly)

    if not poly:
        gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')


def register():
    global _handle
    if _handle is None:
        _handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback, (), 'WINDOW', 'POST_PIXEL')


def unregister():
    global _handle
    if _handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
    _shaders.clear()
