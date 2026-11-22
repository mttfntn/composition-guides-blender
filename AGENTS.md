# AGENTS.md: Composition Guides (Blender add-on)

Viewport overlay add-on: composition guides fitted to the camera frame. Blender **5.3 only**. Extension format. Python. GPL-3.0-or-later. Not a fork. Public repo: `github.com/mttfntn/composition-guides-blender`, branch `main`.

## Commands
```
python tests/test_geometry.py                                                      # math, no Blender
blender --background --factory-startup --python tests/test_blender.py              # Blender-side
python build.py                                                                    # -> dist/composition_guides-<ver>.zip
blender --factory-startup --command extension validate dist/composition_guides-<ver>.zip
```
Windows Blender: `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`.

**Isolation** (required): never test in the user's running Blender or real profile. Set `BLENDER_USER_CONFIG`, `BLENDER_USER_SCRIPTS` and `BLENDER_USER_EXTENSIONS` to scratch dirs, and use `--factory-startup`.

## Architecture
- `composition_guides/geometry.py`: pure functions `f(aspect, opts) -> [((u1,v1),(u2,v2))]`, normalized 0..1, origin bottom-left.
  - Built in frame units (w = aspect, h = 1) so angles are right in pixels.
  - **No bpy.**
- `properties.py`:
  - `GUIDES` tuple `(id, label, desc, rgba)` generates `show_<id>`/`color_<id>`.
  - Settings PropertyGroup is built via `type()` from `_SettingsDefinition` annotations.
  - Stored at `Scene.composition_guides`.
- `draw.py`:
  - `POST_PIXEL` handler `draw_callback`, and `_guide_camera` (override > local camera > scene camera).
  - `_FrameProjector`: `cam.data.view_frame(scene)`, then `perspective_matrix @ matrix_world`.
  - `build_layers(settings, aspect, scene) -> [(gid, segs, quads)]` (the crop-fit remap happens here).
  - GPU: `POLYLINE_UNIFORM_COLOR` (lines; shadow pass then line pass, same batch) and `UNIFORM_COLOR` (crop dim tris). Coordinates are 3D pixel `(x, y, 0)`.
- `ui.py`: sidebar panels (category "Composition"), header button + popover, operators `view3d.composition_guides_view_camera` and `view3d.composition_guides_all(state)`, AddonPreferences (`bl_idname = __package__`).
- `__init__.py`: register order is properties → ui → draw; unregister is the reverse.
- **Data flow**: property update → `tag_redraw_all` → `draw_callback` → `build_layers` → `geometry` → project → GPU.

## Rules and pitfalls
- No docstrings on Operator/Panel classes, because they become UI tooltips. Use `#` comments.
- Keep `geometry.py` importable without Blender; the tests load it by file path.
- Don't add fallbacks for old Blender versions. 5.3 only has the shader names above (`2D_*`/`3D_*` raise `ValueError`), and `SpaceView3D.use_local_camera` always exists.
- Don't hand-compute the camera frame: `view_frame(scene=scene)` already handles sensor fit, shift and pixel aspect.
- "All On" must skip `safe_areas` and `crop` (`_FRAMING` in `ui.py`). This is tested.
- Defaults (tested):
  - opacity 0.4, all color alphas 1.0
  - only `thirds` on by default
  - panels Golden Ratio, Diagonals & Armatures and Framing are `DEFAULT_CLOSED`
- The version lives only in `blender_manifest.toml`. `bl_info` was removed on purpose: extensions ignore it.
- Release needs an **annotated** tag `vX.Y.Z` equal to the manifest version.

## How changes were verified (handover pass)
- A behaviour dump (30 camera setups × all guides/options/crop presets → JSON of projected coordinates and defaults) was byte-identical before and after the cleanup. It was also identical between two runs of the same code.
- GPU screenshots of 3 guide configurations were pixel-identical before and after (old copy vs new, separate Blender 5.3 instances, scratch profile).
- Package installed with `extension install-file` into a scratch profile and enabled on restart.
- To repeat: compare outputs of `build_layers` + `_FrameProjector` for the old commit (`git archive <rev>`) and the working tree.

## Release checklist
1. Bump `version` in `composition_guides/blender_manifest.toml` and the static release badge in `README.md`.
2. Run both test commands locally. Commit and push to `main`. Confirm the Tests workflow is green (`gh run list`).
3. `git tag -a vX.Y.Z -m "<notes>"` then `git push origin vX.Y.Z`.
4. Watch the Release workflow (`gh run watch`). Check `gh release view vX.Y.Z` has the zip.

## Git and CI
- Single branch `main`, remote `origin`. Small commits, clear messages.
- `tests.yml` runs on push to main, PRs, manual runs and `workflow_call` (reused by `release.yml`). It downloads Blender 5.3.0 via `.github/scripts/get-blender.sh`, which tries the official server and mirrors, retries, and checks SHA-256. Only the tarball is cached. No workflow artifacts are uploaded (the account artifact quota was full; the zip ships only as a release asset).
- `release.yml` fetches the tag object explicitly (checkout only gets the commit), checks tag = manifest version, uses the tag message as notes, and runs `gh release create`.
- `dist/` and `*.zip` are gitignored. The package is shipped only as a release asset.
