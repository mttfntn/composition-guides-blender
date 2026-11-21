# Composition Guides for Blender

[![Blender](https://img.shields.io/badge/Blender-5.3-E87D0D?logo=blender&logoColor=white)](https://www.blender.org/download/)
[![Release](https://img.shields.io/badge/release-v1.0.0-blue)](https://github.com/mttfntn/composition-guides-blender/releases/latest)
[![Tests](https://github.com/mttfntn/composition-guides-blender/actions/workflows/tests.yml/badge.svg)](https://github.com/mttfntn/composition-guides-blender/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-GPL--3.0--or--later-green)](LICENSE)
[![Python](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)](composition_guides)

Composition guides fitted to your camera frame, shown in the 3D viewport and switched on and off from a panel.

The guides are drawn as a viewport overlay, so they work with **every render engine** (Eevee, Cycles, Workbench, Octane, Redshift, ...) and in every shading mode, Rendered included. They never appear in your final renders.

They follow the camera frame exactly:
- render resolution and pixel aspect
- sensor fit
- lens shift
- zoom and pan of the camera view

So they always line up with the camera border (passepartout).

**Requires Blender 5.3.** No other version is supported.

## Installation
1. Download `composition_guides-<version>.zip` from the [latest release](https://github.com/mttfntn/composition-guides-blender/releases/latest).
2. In Blender, open **Edit › Preferences › Get Extensions**.
3. Open the **▾** menu at the top right, choose **Install from Disk…** and pick the zip.
4. The add-on is enabled automatically. If not, enable it under **Add-ons**.

To update, install the new zip the same way. It replaces the old version.

## Usage
1. Press **N** in the 3D viewport and open the **Composition** tab. You can also use the grid button in the viewport header for quick toggles.
2. Look through the camera with **Numpad 0** or the **Look Through Camera** button.
3. Tick the guides you want.

### Panel layout
| Section | Starts | Contents |
|---|---|---|
| Composition Guides | open | Master on/off, camera choice, Look Through Camera, **All On / All Off** |
| Style | open | Shared color or a color per guide, opacity (default **0.4**), line width, shadow |
| Grids & Markers | open | Rule of Thirds, Phi Grid, Custom Grid, Center Cross, Corner Marks |
| Golden Ratio | collapsed | Golden Triangle, Diagonal Phi Grid, Fibonacci Spiral, Golden Rectangles |
| Diagonals & Armatures | collapsed | Dynamic Symmetry, Harmonic Armature, Baroque / Sinister diagonals, Diagonal Method |
| Framing | collapsed | Safe Areas, Aspect Crop |

**All On** turns on every guide except the Framing ones (Safe Areas and Aspect Crop). **All Off** turns everything off.

## Guides
- **Rule of Thirds**: the frame split in thirds.
- **Phi Grid**: the rule of thirds at the golden ratio (0.382 / 0.618).
- **Custom Grid**: any number of rows and columns.
- **Center Cross**: a small marker or a full crosshair.
- **Corner Marks**: brackets on the frame corners.
- **Golden Triangle**: a diagonal plus perpendiculars from the other two corners. It can be flipped.
- **Diagonal Phi Grid**: lines from each corner to the golden points on the opposite side.
- **Fibonacci Spiral**: a golden spiral fitted to the frame. Orientation can be Auto, Horizontal or Vertical, and it can be flipped on X and Y. The number of steps is adjustable.
- **Golden Rectangles**: the nested rectangles the spiral is built on.
- **Dynamic Symmetry**: diagonals and reciprocals, with optional edge lines and eye lines.
- **Harmonic Armature**: diagonals, reciprocals and the midpoint rhombus.
- **Baroque / Sinister Diagonal**: each diagonal on its own.
- **Diagonal Method (45°)**: 45° lines from every corner.
- **Safe Areas**: title-safe and action-safe margins, using the scene's own values.
- **Aspect Crop**: a crop for another ratio inside the render frame. Ratios are 2.39, 2, 1.85, 16:9, 3:2, 4:3, 5:4, 1:1, 4:5, 9:16 or custom. It can dim the area outside the crop and fit every other guide inside it.

Angles are computed in real frame proportions, so perpendiculars and 45° lines stay correct for any aspect ratio.

## Options
- **Camera**: use a specific camera instead of the scene camera.
- **Outside Camera View**: also draw the guides on the camera frame in the normal perspective view.
- **Shadow**: a dark outline under the lines so they stay readable over bright images.

Settings are saved in the .blend file. The header button can be turned off in the add-on preferences.

## For developers
- [HANDOVER.md](HANDOVER.md): how the project works, how to change, test and release it.
- [AGENTS.md](AGENTS.md): the same, compact, for AI coding assistants.

Quick commands:
```
python tests/test_geometry.py
blender --background --factory-startup --python tests/test_blender.py
python build.py
```

## License
[GPL-3.0-or-later](LICENSE), © Matteo Fontana.
