# SPDX-License-Identifier: GPL-3.0-or-later
"""
Composition Guides: camera-fitted composition guides in the 3D viewport.

Add-on metadata lives in blender_manifest.toml (Blender extension format).
Modules:
    geometry    pure-math guide shapes in normalized frame space (no bpy)
    properties  settings stored on each Scene (scene.composition_guides)
    draw        viewport draw handler: camera frame projection + GPU drawing
    ui          sidebar panels, header popover, operators, preferences
"""

# On "Reload Scripts" Blender reloads this package; reload the submodules too
# so code changes are picked up without restarting.
if "bpy" in locals():
    import importlib
    importlib.reload(geometry)
    importlib.reload(properties)
    importlib.reload(draw)
    importlib.reload(ui)

import bpy  # noqa: E402,F401  (marks the module as loaded for the reload check)

from . import geometry, properties, draw, ui  # noqa: E402

# Registration order: settings first (panels and drawing read them), drawing last.
_modules = (properties, ui, draw)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
