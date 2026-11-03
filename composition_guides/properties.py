# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
)
from bpy.types import PropertyGroup

# (id, label, description, default color)
GUIDES = (
    ("thirds", "Rule of Thirds", "Divide the frame in thirds", (1.0, 1.0, 1.0, 1.0)),
    ("phi", "Phi Grid", "Rule of thirds using the golden ratio (0.382 / 0.618)", (1.0, 0.85, 0.3, 1.0)),
    ("grid", "Custom Grid", "Evenly spaced grid with a custom number of rows and columns", (0.7, 0.7, 0.7, 1.0)),
    ("center", "Center Cross", "Mark the center of the frame", (1.0, 1.0, 1.0, 1.0)),
    ("corners", "Corner Marks", "Bracket marks on the frame corners", (1.0, 1.0, 1.0, 1.0)),
    ("golden_triangle", "Golden Triangle", "Diagonal plus perpendiculars from the other corners", (1.0, 0.6, 0.2, 1.0)),
    ("diagonal_phi", "Diagonal Phi Grid", "Lines from each corner to the golden points of the opposite side", (0.9, 0.5, 1.0, 1.0)),
    ("spiral", "Fibonacci Spiral", "Golden (Fibonacci) spiral fitted to the frame", (1.0, 0.8, 0.2, 1.0)),
    ("golden_sections", "Golden Rectangles", "Nested golden rectangles the spiral is built on", (1.0, 0.8, 0.2, 1.0)),
    ("dynamic_symmetry", "Dynamic Symmetry", "Diagonals and reciprocals (Hambidge armature)", (0.3, 0.85, 1.0, 1.0)),
    ("harmonic", "Harmonic Armature", "Diagonals, reciprocals and the midpoint rhombus", (0.4, 1.0, 0.6, 1.0)),
    ("baroque", "Baroque Diagonal", "Bottom-left to top-right diagonal", (1.0, 0.45, 0.45, 1.0)),
    ("sinister", "Sinister Diagonal", "Top-left to bottom-right diagonal", (1.0, 0.45, 0.45, 1.0)),
    ("diagonal_method", "Diagonal Method (45°)", "45 degree lines from each corner", (0.5, 0.7, 1.0, 1.0)),
    ("safe_areas", "Safe Areas", "Title and action safe areas (uses the scene safe area settings)", (0.6, 0.9, 0.9, 1.0)),
    ("crop", "Aspect Crop", "Show a crop for another aspect ratio inside the render frame", (1.0, 0.3, 0.3, 1.0)),
)

CROP_PRESETS = (
    ("2.39", "2.39:1 Anamorphic", ""),
    ("2.0", "2:1 Univisium", ""),
    ("1.85", "1.85:1 Flat", ""),
    ("1.7778", "16:9", ""),
    ("1.5", "3:2", ""),
    ("1.3333", "4:3", ""),
    ("1.25", "5:4", ""),
    ("1.0", "1:1 Square", ""),
    ("0.8", "4:5 Portrait", ""),
    ("0.5625", "9:16 Vertical", ""),
    ("CUSTOM", "Custom", "Use a custom ratio"),
)

SPIRAL_ORIENT = (
    ("AUTO", "Auto", "Follow the frame orientation"),
    ("HORIZONTAL", "Horizontal", "Long side of the spiral follows the frame width"),
    ("VERTICAL", "Vertical", "Long side of the spiral follows the frame height"),
)


def tag_redraw_all(context=None):
    wm = (context or bpy.context).window_manager
    if wm is None:
        return
    for window in wm.windows:
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _redraw(self, context):
    tag_redraw_all(context)


def _poll_camera(self, obj):
    return obj.type == 'CAMERA'


class _SettingsDefinition:
    # Plain class used as a template; the registered PropertyGroup is built below.

    enabled: BoolProperty(
        name="Show Guides",
        description="Draw composition guides in the 3D viewport",
        default=True, update=_redraw,
    )
    show_outside_camera: BoolProperty(
        name="Outside Camera View",
        description="Also draw the guides on the camera frame when not looking through the camera",
        default=False, update=_redraw,
    )
    camera: PointerProperty(
        name="Camera",
        description="Camera to use for the guides (empty: the active scene camera)",
        type=bpy.types.Object, poll=_poll_camera, update=_redraw,
    )

    # Style
    color: FloatVectorProperty(
        name="Color", subtype='COLOR', size=4, min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0), update=_redraw,
    )
    use_guide_colors: BoolProperty(
        name="Color per Guide",
        description="Use an individual color for every guide",
        default=False, update=_redraw,
    )
    opacity: FloatProperty(
        name="Opacity", min=0.0, max=1.0, default=0.4,
        subtype='FACTOR', update=_redraw,
    )
    line_width: FloatProperty(
        name="Line Width", min=0.5, max=10.0, default=1.5, update=_redraw,
    )
    shadow: BoolProperty(
        name="Shadow",
        description="Draw a dark outline under the lines so they stay readable on bright images",
        default=True, update=_redraw,
    )

    # Grid / markers
    grid_cols: IntProperty(name="Columns", min=1, max=64, default=4, update=_redraw)
    grid_rows: IntProperty(name="Rows", min=1, max=64, default=4, update=_redraw)
    center_size: FloatProperty(
        name="Size", min=0.005, max=0.5, default=0.03, subtype='FACTOR', update=_redraw,
    )
    center_full: BoolProperty(
        name="Full Crosshair", description="Draw lines across the whole frame",
        default=False, update=_redraw,
    )
    corners_size: FloatProperty(
        name="Size", min=0.005, max=0.5, default=0.05, subtype='FACTOR', update=_redraw,
    )

    # Golden ratio
    triangle_flip: BoolProperty(name="Flip", default=False, update=_redraw)
    diagonal_phi_diagonals: BoolProperty(
        name="Main Diagonals", default=True, update=_redraw,
    )
    spiral_orient: EnumProperty(
        name="Orientation", items=SPIRAL_ORIENT, default='AUTO', update=_redraw,
    )
    spiral_flip_h: BoolProperty(name="Flip X", default=False, update=_redraw)
    spiral_flip_v: BoolProperty(name="Flip Y", default=False, update=_redraw)
    spiral_turns: IntProperty(name="Steps", min=1, max=16, default=10, update=_redraw)

    # Armatures
    dynsym_reciprocals: BoolProperty(name="Reciprocals", default=True, update=_redraw)
    dynsym_edge_lines: BoolProperty(
        name="Edge Lines",
        description="Vertical/horizontal lines where the reciprocals meet the frame edge",
        default=True, update=_redraw,
    )
    dynsym_eye_lines: BoolProperty(
        name="Eye Lines",
        description="Vertical/horizontal lines through the points where reciprocals cross the diagonals",
        default=False, update=_redraw,
    )
    harmonic_reciprocals: BoolProperty(name="Reciprocals", default=True, update=_redraw)
    harmonic_rhombus: BoolProperty(name="Rhombus", default=True, update=_redraw)

    # Crop
    crop_preset: EnumProperty(
        name="Ratio", items=CROP_PRESETS, default="2.39", update=_redraw,
    )
    crop_custom: FloatProperty(
        name="Custom Ratio", min=0.1, max=10.0, default=2.0, update=_redraw,
    )
    crop_dim: FloatProperty(
        name="Dim Outside", min=0.0, max=1.0, default=0.6,
        subtype='FACTOR', update=_redraw,
    )
    crop_fit_guides: BoolProperty(
        name="Fit Guides to Crop",
        description="Draw the other guides relative to the crop instead of the full frame",
        default=True, update=_redraw,
    )

    def crop_ratio(self):
        if self.crop_preset == 'CUSTOM':
            return self.crop_custom
        return float(self.crop_preset)


# One "show_<id>" toggle and "color_<id>" color per guide. The class is built
# with type() so the generated annotations work on every Python version.
_annotations = dict(_SettingsDefinition.__annotations__)
for _gid, _label, _desc, _col in GUIDES:
    _annotations["show_" + _gid] = BoolProperty(
        name=_label, description=_desc, default=(_gid == "thirds"), update=_redraw,
    )
    _annotations["color_" + _gid] = FloatVectorProperty(
        name=_label + " Color", subtype='COLOR', size=4, min=0.0, max=1.0,
        default=_col, update=_redraw,
    )

CompositionGuidesSettings = type("CompositionGuidesSettings", (PropertyGroup,), {
    "__annotations__": _annotations,
    "crop_ratio": _SettingsDefinition.crop_ratio,
})


def register():
    bpy.utils.register_class(CompositionGuidesSettings)
    bpy.types.Scene.composition_guides = PointerProperty(type=CompositionGuidesSettings)


def unregister():
    del bpy.types.Scene.composition_guides
    bpy.utils.unregister_class(CompositionGuidesSettings)
