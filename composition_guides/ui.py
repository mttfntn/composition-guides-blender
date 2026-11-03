# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import BoolProperty
from bpy.types import AddonPreferences, Operator, Panel

from .properties import GUIDES, tag_redraw_all

_LABELS = {gid: label for gid, label, _d, _c in GUIDES}
_FRAMING = {"safe_areas", "crop"}   # left alone by "All On"


def _prefs(context):
    addon = context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def _guide_row(layout, s, gid):
    """Toggle (plus color when per-guide colors are on). Returns an options column."""
    row = layout.row(align=True)
    row.prop(s, "show_" + gid)
    if s.use_guide_colors:
        sub = row.row(align=True)
        sub.ui_units_x = 2.5
        sub.prop(s, "color_" + gid, text="")
    col = layout.column(align=True)
    col.active = getattr(s, "show_" + gid)
    return col


def _indent(col):
    split = col.split(factor=0.08)
    split.label(text="")
    return split.column(align=True)


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class VIEW3D_OT_composition_guides_view_camera(Operator):
    bl_idname = "view3d.composition_guides_view_camera"
    bl_label = "Look Through Camera"
    bl_description = "Switch this viewport to the guide camera view"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == 'VIEW_3D'

    def execute(self, context):
        s = context.scene.composition_guides
        cam = s.camera if s.camera is not None else context.scene.camera
        if cam is None:
            self.report({'WARNING'}, "The scene has no camera")
            return {'CANCELLED'}
        if context.scene.camera != cam:
            context.scene.camera = cam
        rv3d = context.region_data or context.space_data.region_3d
        rv3d.view_perspective = 'CAMERA'
        return {'FINISHED'}


class VIEW3D_OT_composition_guides_all(Operator):
    bl_idname = "view3d.composition_guides_all"
    bl_label = "Set All Guides"
    bl_description = "Turn every guide on (except the framing guides) or off"
    bl_options = {'REGISTER', 'UNDO'}

    state: BoolProperty(default=False, options={'SKIP_SAVE'})

    def execute(self, context):
        s = context.scene.composition_guides
        for gid in _LABELS:
            if self.state and gid in _FRAMING:
                continue
            setattr(s, "show_" + gid, self.state)
        tag_redraw_all(context)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Sidebar panels
# ---------------------------------------------------------------------------

class _SidebarPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Composition"


class VIEW3D_PT_composition_guides(_SidebarPanel, Panel):
    bl_label = "Composition Guides"

    def draw_header(self, context):
        self.layout.prop(context.scene.composition_guides, "enabled", text="")

    def draw(self, context):
        layout = self.layout
        s = context.scene.composition_guides
        layout.active = s.enabled

        col = layout.column(align=True)
        col.prop(s, "camera", icon='CAMERA_DATA')
        cam = s.camera or context.scene.camera
        if cam is None:
            col.label(text="No active camera", icon='ERROR')
        col.operator(VIEW3D_OT_composition_guides_view_camera.bl_idname, icon='VIEW_CAMERA')
        col.prop(s, "show_outside_camera")

        row = layout.row(align=True)
        row.operator(VIEW3D_OT_composition_guides_all.bl_idname, text="All On").state = True
        row.operator(VIEW3D_OT_composition_guides_all.bl_idname, text="All Off").state = False


class VIEW3D_PT_composition_guides_style(_SidebarPanel, Panel):
    bl_label = "Style"
    bl_parent_id = "VIEW3D_PT_composition_guides"

    def draw(self, context):
        layout = self.layout
        s = context.scene.composition_guides
        layout.active = s.enabled
        col = layout.column()
        row = col.row()
        row.active = not s.use_guide_colors
        row.prop(s, "color")
        col.prop(s, "use_guide_colors")
        col.prop(s, "opacity")
        col.prop(s, "line_width")
        col.prop(s, "shadow")


class VIEW3D_PT_composition_guides_grids(_SidebarPanel, Panel):
    bl_label = "Grids & Markers"
    bl_parent_id = "VIEW3D_PT_composition_guides"

    def draw(self, context):
        layout = self.layout
        s = context.scene.composition_guides
        layout.active = s.enabled

        _guide_row(layout, s, "thirds")
        _guide_row(layout, s, "phi")

        opts = _indent(_guide_row(layout, s, "grid"))
        row = opts.row(align=True)
        row.prop(s, "grid_cols")
        row.prop(s, "grid_rows")

        opts = _indent(_guide_row(layout, s, "center"))
        opts.prop(s, "center_full")
        sub = opts.row()
        sub.active = not s.center_full
        sub.prop(s, "center_size")

        opts = _indent(_guide_row(layout, s, "corners"))
        opts.prop(s, "corners_size")


class VIEW3D_PT_composition_guides_golden(_SidebarPanel, Panel):
    bl_label = "Golden Ratio"
    bl_parent_id = "VIEW3D_PT_composition_guides"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        s = context.scene.composition_guides
        layout.active = s.enabled

        opts = _indent(_guide_row(layout, s, "golden_triangle"))
        opts.prop(s, "triangle_flip")

        opts = _indent(_guide_row(layout, s, "diagonal_phi"))
        opts.prop(s, "diagonal_phi_diagonals")

        _guide_row(layout, s, "spiral")
        opts = _guide_row(layout, s, "golden_sections")
        opts.active = s.show_spiral or s.show_golden_sections
        opts = _indent(opts)
        opts.prop(s, "spiral_orient", text="")
        row = opts.row(align=True)
        row.prop(s, "spiral_flip_h", toggle=True)
        row.prop(s, "spiral_flip_v", toggle=True)
        opts.prop(s, "spiral_turns")


class VIEW3D_PT_composition_guides_armatures(_SidebarPanel, Panel):
    bl_label = "Diagonals & Armatures"
    bl_parent_id = "VIEW3D_PT_composition_guides"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        s = context.scene.composition_guides
        layout.active = s.enabled

        opts = _indent(_guide_row(layout, s, "dynamic_symmetry"))
        opts.prop(s, "dynsym_reciprocals")
        opts.prop(s, "dynsym_edge_lines")
        opts.prop(s, "dynsym_eye_lines")

        opts = _indent(_guide_row(layout, s, "harmonic"))
        row = opts.row(align=True)
        row.prop(s, "harmonic_reciprocals", toggle=True)
        row.prop(s, "harmonic_rhombus", toggle=True)

        _guide_row(layout, s, "baroque")
        _guide_row(layout, s, "sinister")
        _guide_row(layout, s, "diagonal_method")


class VIEW3D_PT_composition_guides_framing(_SidebarPanel, Panel):
    bl_label = "Framing"
    bl_parent_id = "VIEW3D_PT_composition_guides"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        s = context.scene.composition_guides
        layout.active = s.enabled

        opts = _indent(_guide_row(layout, s, "safe_areas"))
        opts.prop(context.scene.safe_areas, "title", text="Title")
        opts.prop(context.scene.safe_areas, "action", text="Action")

        opts = _indent(_guide_row(layout, s, "crop"))
        opts.prop(s, "crop_preset", text="")
        if s.crop_preset == 'CUSTOM':
            opts.prop(s, "crop_custom")
        opts.prop(s, "crop_dim")
        opts.prop(s, "crop_fit_guides")


# ---------------------------------------------------------------------------
# Header popover
# ---------------------------------------------------------------------------

class VIEW3D_PT_composition_guides_popover(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Composition Guides"
    bl_ui_units_x = 11

    def draw(self, context):
        layout = self.layout
        s = context.scene.composition_guides
        layout.prop(s, "enabled")
        col = layout.column(align=True)
        col.active = s.enabled
        for gid, _label, _d, _c in GUIDES:
            col.prop(s, "show_" + gid)
        layout.separator()
        col = layout.column(align=True)
        col.active = s.enabled
        col.prop(s, "opacity")
        col.prop(s, "line_width")
        row = layout.row(align=True)
        row.operator(VIEW3D_OT_composition_guides_all.bl_idname, text="All Off").state = False
        row.operator(VIEW3D_OT_composition_guides_view_camera.bl_idname, text="", icon='VIEW_CAMERA')


def draw_header_button(self, context):
    prefs = _prefs(context)
    if prefs is not None and not prefs.show_header_button:
        return
    s = getattr(context.scene, "composition_guides", None)
    if s is None:
        return
    row = self.layout.row(align=True)
    row.prop(s, "enabled", text="", icon='MESH_GRID')
    row.popover(panel="VIEW3D_PT_composition_guides_popover", text="")


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

class CompositionGuidesPreferences(AddonPreferences):
    bl_idname = __package__

    show_header_button: BoolProperty(
        name="Header Button",
        description="Show a guides toggle and popover in the 3D viewport header",
        default=True,
        update=lambda self, context: tag_redraw_all(context),
    )

    def draw(self, context):
        self.layout.prop(self, "show_header_button")


classes = (
    CompositionGuidesPreferences,
    VIEW3D_OT_composition_guides_view_camera,
    VIEW3D_OT_composition_guides_all,
    VIEW3D_PT_composition_guides,
    VIEW3D_PT_composition_guides_style,
    VIEW3D_PT_composition_guides_grids,
    VIEW3D_PT_composition_guides_golden,
    VIEW3D_PT_composition_guides_armatures,
    VIEW3D_PT_composition_guides_framing,
    VIEW3D_PT_composition_guides_popover,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_HT_header.append(draw_header_button)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_header_button)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
