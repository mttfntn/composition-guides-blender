# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Composition Guides",
    "author": "Matteo Fontana",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "3D Viewport > Sidebar (N) > Composition, and viewport header",
    "description": "Camera-fitted composition guides (thirds, phi, golden triangle, "
                   "dynamic symmetry, Fibonacci spiral...) for every render engine",
    "category": "3D View",
}

if "bpy" in locals():
    import importlib
    importlib.reload(geometry)
    importlib.reload(properties)
    importlib.reload(draw)
    importlib.reload(ui)

import bpy  # noqa: E402,F401

from . import geometry, properties, draw, ui  # noqa: E402

_modules = (properties, ui, draw)


def register():
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
