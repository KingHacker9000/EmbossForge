# Contributing to EmbossForge

EmbossForge is an open-source hardware/software project for generating matched paper-embossing dies and a reusable interchangeable press.

## Development setup

Python 3.11 is the reference environment.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[cad,dev]"
pytest -q
```

OpenSCAD is required for rendering artwork dies. CadQuery is required for mechanical models. Blender is optional and is used for visual QA rather than as the dimensional source of truth.

## Design rules

1. Keep mechanical geometry parametric. Do not hand-edit generated STL/STEP files.
2. Preserve a single source of truth for every dimension.
3. Treat printer fit tolerances as measured values, not universal constants.
4. Matched male/female dies must preserve orientation and paper clearance.
5. New mechanical changes should retain open/closed collision validation where applicable.
6. Keep all printable parts within the target printer build envelope unless the design explicitly targets a different printer.
7. Prefer small calibration or smoke-test prints before large prototypes.

## Tests

Run:

```text
pytest -q
```

For changes to the CLI or generators, also run the relevant command manually. Examples:

```text
embossforge doctor
embossforge butterfly-test
embossforge fit-coupon
embossforge mechanics
```

Do not commit generated `build/` artifacts unless a release process explicitly calls for them.

## Artwork changes

Artwork import is one of the highest-risk parts of the project because SVGs can use different viewBox origins, transforms, units, strokes, clipping paths, and nested geometry. Every artwork bug fix should include a regression test with a minimal representative input.

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

See `AGENTS.md`. Agent use is welcome, but generated mesh edits are not a substitute for parametric source changes and tests.
