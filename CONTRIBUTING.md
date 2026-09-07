# Contributing to EmbossForge

EmbossForge is an open-source hardware/software project for generating matched paper-embossing dies and a reusable interchangeable press.

## Development setup

Python 3.11 is the reference environment.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[cad,gui,dev]"
pytest -q
```

OpenSCAD is required for rendering artwork dies from a source checkout. CadQuery is required for mechanical models. PySide6 powers the desktop app. Blender is optional and is used for visual QA rather than as the dimensional source of truth.

Launch the desktop app from source with either:

```text
embossforge gui
embossforge-gui
```

## Architecture rule: one backend, multiple front ends

`embossforge.generator.generate_die()` is the shared user-facing generation service.

- desktop UI gathers user choices and calls it
- CLI parses arguments and calls it
- agents/integrations can call it directly from Python

Do not reimplement geometry, paper-clearance logic, printer defaults, or artwork processing in the UI. A setting should mean the same thing everywhere.

## Design rules

1. Keep mechanical geometry parametric. Do not hand-edit generated STL/STEP files.
2. Preserve a single source of truth for every dimension.
3. Treat printer fit tolerances as measured values, not universal constants.
4. Matched male/female dies must preserve orientation and paper clearance.
5. New mechanical changes should retain open/closed collision validation where applicable.
6. Keep all printable parts within the target printer build envelope unless the design explicitly targets a different printer.
7. Prefer small calibration or smoke-test prints before large prototypes.
8. Keep the desktop workflow simple: artwork -> preview -> common settings -> generate -> open output.

## Tests

Run:

```text
python -m compileall -q embossforge
pytest -q
```

For changes to the CLI or generators, also run the relevant command manually. Examples:

```text
embossforge doctor
embossforge butterfly-test
embossforge fit-coupon
embossforge mechanics
```

For desktop UI changes, construct the window locally or rely on the Windows `desktop-smoke` CI job. The release workflow performs another GUI smoke test before packaging.

Do not commit generated `build/`, `dist/`, or PyInstaller artifacts unless a release process explicitly calls for them.

## Artwork changes

Artwork import is one of the highest-risk parts of the project because SVGs can use different viewBox origins, transforms, units, strokes, clipping paths, and nested geometry. Every artwork bug fix should include a regression test with a minimal representative input.

## Desktop UI changes

The UI lives in `embossforge/gui.py` and should remain a thin layer over the generator service.

Prefer:

- one clear primary action
- plain-language labels
- safe defaults
- advanced controls secondary/collapsible
- visible progress and errors
- an obvious route to the generated files

Avoid exposing internal CAD implementation details unless a normal user needs them to make a printing decision.

## Windows packaging

`.github/workflows/release-windows.yml` produces the official Windows packages. It:

1. tests the repository
2. smoke-tests the desktop window
3. builds a PyInstaller one-directory app
4. bundles an OpenSCAD runtime under `tools/openscad/`
5. creates a portable ZIP
6. creates an Inno Setup installer
7. uploads both as workflow artifacts and, on `v*` tags, GitHub Release assets

The `desktop-release-preview` branch exists so packaging can be exercised before creating a public release tag.

## Hardware changes

Clearly separate:

- geometry/fit validation
- low-force functional validation
- strength validation

A miniature or low-infill prototype can prove geometry and motion, but it cannot certify the full-size press for force.

## Pull requests

A useful pull request should explain:

- what changed
- why it changed
- what was tested
- whether physical printing was involved
- any dimensions/tolerances affected
- screenshots or photos when visual/mechanical behavior changed

## Agent-assisted contributions

Read `AGENTS.md` first. Agent use is welcome, but generated mesh edits are not a substitute for parametric source changes and tests. Expensive GUI/3D agents should be reserved for tasks that truly require local graphical inspection.
