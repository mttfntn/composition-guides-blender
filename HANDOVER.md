# Handover: Composition Guides for Blender

## What this is
A Blender add-on (extension format) that draws composition guides inside the camera frame in the 3D viewport. Examples are the rule of thirds, the phi grid, the golden triangle, dynamic symmetry and the Fibonacci spiral. The user switches them on and off from a sidebar panel.

It's an overlay drawn with Blender's `gpu` module, so it works with every render engine, including Octane, and never appears in renders.

- Repository: https://github.com/mttfntn/composition-guides-blender (private)
- Author: Matteo Fontana. License: GPL-3.0-or-later.
- Not a fork, so there is no upstream to merge from.

## What you need
- **Blender 5.3** (the only supported version). The manifest enforces it: `blender_version_min = "5.3.0"`, `blender_version_max = "5.4.0"`.
- Any Python 3 for the math tests (`geometry.py` has no Blender imports).
- `git`. `gh` (GitHub CLI) is optional, for checking CI and releases.

## How the code is organized
| Path | What it does |
|---|---|
| `composition_guides/__init__.py` | Package entry: imports modules, `register()`/`unregister()` in order properties → ui → draw. Reload block for "Reload Scripts". |
| `composition_guides/blender_manifest.toml` | Extension metadata: id, version, supported Blender versions, license. **The version lives here.** |
| `composition_guides/geometry.py` | Pure math. Each guide is a function `f(aspect, options) → [((u1,v1),(u2,v2)), ...]` in normalized frame space (0..1, origin bottom-left). No `bpy`. |
| `composition_guides/properties.py` | `GUIDES` list (id, label, tooltip, default color) and the settings `PropertyGroup` stored as `scene.composition_guides`. Generates `show_<id>` and `color_<id>` per guide. |
| `composition_guides/draw.py` | The viewport draw handler: finds the camera, projects the frame, builds guide layers, draws with GPU shaders. |
| `composition_guides/ui.py` | Sidebar panels (N › Composition), header button and popover, operators (Look Through Camera, All On/Off), add-on preferences. |
| `tests/test_geometry.py` | Math checks, plain Python. |
| `tests/test_blender.py` | Checks inside Blender: defaults, All On/Off, collapsed panels, frame fitting, every guide builds, re-registration. |
| `build.py` | Builds `dist/composition_guides-<version>.zip` (extension layout plus LICENSE). |
| `.github/workflows/tests.yml` | CI: math tests, Blender 5.3 tests, build and validate. Runs on push to `main`, PRs and manual runs. |
| `.github/workflows/release.yml` | On a `vX.Y.Z` tag: run the tests, build, and publish a GitHub release with the zip. |
| `.github/scripts/get-blender.sh` | Downloads Blender 5.3.0 for CI, with mirrors, retries and a SHA-256 check. |

## How the main feature works
1. `draw.register()` adds one `POST_PIXEL` draw handler to `SpaceView3D`. Blender calls `draw_callback()` on every viewport redraw.
2. `draw_callback()` returns early unless guides are enabled and the viewport is in camera view (or **Outside Camera View** is on).
3. **Camera**: the panel's override, else the viewport's local camera, else `scene.camera` (`_guide_camera`).
4. **Frame**: `_FrameProjector` calls `camera.data.view_frame(scene=scene)`. That gives the camera-space rectangle Blender itself uses for the camera border. It includes resolution, pixel aspect, sensor fit and shift.
5. Every guide point `(u, v)` becomes a 3D point on that rectangle and is projected with `region_data.perspective_matrix @ camera.matrix_world`. This is exact in camera view and outside it. Points behind the viewer are dropped.
6. `build_layers()` asks `geometry.py` for each enabled guide.
   - If **Aspect Crop** with **Fit Guides to Crop** is on, the other guides are built for the crop's aspect and remapped into the crop rectangle.
   - Safe areas and corner marks always use the full frame.
7. Drawing:
   - one `POLYLINE_UNIFORM_COLOR` batch per guide, drawn twice (a dark wider shadow, then the line)
   - the crop dimming uses `UNIFORM_COLOR` triangles
   - color = guide color (or the shared color) × opacity

## How to make a change
- **New guide**:
  1. Add a function to `geometry.py`.
  2. Add an entry to `GUIDES` in `properties.py`. That creates `show_<id>`/`color_<id>`.
  3. Add a branch in `draw.build_layers()`.
  4. Add a `_guide_row(...)` in the right panel in `ui.py`.
  5. Add options as properties on `_SettingsDefinition`.
  6. Extend the tests.
- **Panels**: class docstrings become tooltips in Blender, so use `#` comments on operator and panel classes, not docstrings.
- Keep `geometry.py` free of `bpy`, so it stays testable with plain Python.
- **Bump the version** in `blender_manifest.toml` before releasing.

## How to run the tests
```
python tests/test_geometry.py
"C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --factory-startup --python tests/test_blender.py
```
Both print `ok`/`FAIL` per test and exit non-zero on failure.

**Isolation**: to keep your own Blender profile untouched while testing, set these to a scratch folder first:
- `BLENDER_USER_CONFIG`
- `BLENDER_USER_SCRIPTS`
- `BLENDER_USER_EXTENSIONS`

To check the real package the way a user installs it:
```
python build.py
blender --command extension validate dist/composition_guides-<version>.zip
blender --command extension install-file -r user_default -e dist/composition_guides-<version>.zip
```
Run the install with the scratch environment variables set.

## How to make a release
1. Update `version` in `composition_guides/blender_manifest.toml`, and the release badge in `README.md` (the repo is private, so the badge is static).
2. Commit and push to `main`, then wait for the **Tests** workflow to pass.
3. Create an **annotated** tag whose message is the release notes, and push it:
   ```
   git tag -a v1.2.3 -m "What changed..."
   git push origin v1.2.3
   ```
4. The **Release** workflow tests, builds, checks the tag matches the manifest version, and publishes the release with the zip.
   - A lightweight tag (no `-a`) fails on purpose.
   - A tag that doesn't match the manifest version fails too.

## Bringing in updates from an original project
None: this project is not a fork.

## Supporting a new Blender version
1. In `blender_manifest.toml`, change `blender_version_min`/`max`.
2. In `.github/scripts/get-blender.sh`, change `VERSION`, `SERIES` and `SHA256`. The checksum comes from `https://download.blender.org/release/BlenderX.Y/blender-X.Y.Z.sha256`.
3. In `tests.yml`, change the cache key.
4. Update the README badge.

## Things to know
- On Blender 5.3 (Vulkan), the shader names are `POLYLINE_UNIFORM_COLOR` and `UNIFORM_COLOR`. The old `2D_`/`3D_` names raise `ValueError`.
- `view_frame(scene=scene)` is what makes the guides match the camera border. Don't recompute the frame by hand.
- New property defaults only apply to new scenes and files. Saved .blend files keep the values they stored.
- Blender remembers panels a user opened or closed, so `DEFAULT_CLOSED` only affects the first time a panel is shown.
- `properties.py` builds the PropertyGroup with `type()` so the generated per-guide annotations are reliable.
- CI caches only the Blender tarball (about 400 MB) and uploads no workflow artifacts. The zip is published only as a release asset. Your account artifact quota was full in Nov 2026, which is why the upload step was removed.

## Known limits
- Viewport only: the guides are not rendered into images.
- Panoramic cameras get the rectangle guides on the frame, not a panoramic projection.
- The spiral and golden rectangles are stretched to the frame aspect, like Photoshop's and Lightroom's overlays. They are not a true golden rectangle unless the frame is 1.618:1.
- Outside camera view, a segment with an endpoint behind the viewer is dropped, not clipped.
