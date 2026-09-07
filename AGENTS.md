# EmbossForge agent guide

EmbossForge is an open-source parametric paper-embosser system. It turns artwork into matched male/female 3D-printable dies and also contains a reusable cartridge/press platform.

This file is the canonical guide for Codex, Claude, Copilot, and other coding/3D agents working in this repository.

## What users should experience

Normal users should not need to understand Python, OpenSCAD, CadQuery, or Blender.

Primary user paths:

1. **Desktop app**: drop/select artwork -> choose die/paper/printer settings -> generate files -> open output folder.
2. **CLI**: `embossforge die ...` and the calibration/mechanics commands.
3. **Python API**: `embossforge.generator.DieGenerationRequest` + `generate_die()` for integrations/agents.

The desktop app and CLI must use the **same generation backend**. Never duplicate die-generation rules in UI code.

## Repository map

- `embossforge/generator.py` — UI/CLI-neutral matched-die generation service.
- `embossforge/gui.py` — PySide6 desktop UI only; presentation and request collection belong here.
- `embossforge/cli.py` — CLI adapter only; avoid putting geometry logic here.
- `embossforge/artwork.py` — SVG/raster normalization and vectorization.
- `embossforge/scad_backend.py` — reproducible binary die relief generation and OpenSCAD invocation.
- `embossforge/config.py` — die specs, printer profiles, paper presets.
- `embossforge/mechanics/` — CadQuery cartridge and press source geometry.
- `blender/` — visual QA/import tooling; not dimensional source of truth.
- `profiles/` — human-editable printer profiles.
- `tests/` — regression tests.
- `docs/RELIEF_MODE_SPEC.md` — canonical accepted contract for planned grayscale/variable-depth relief work.
- `docs/IMAGE_INPUT_SPEC.md` — canonical source-interpretation contract for flat artwork, true height maps, and shaded/3D-looking references.
- `skills/embossforge-design/SKILL.md` — design skill for agents creating manufacturable EmbossForge artwork/height maps.
- `docs/PHYSICAL_VALIDATION.md` — real printed validation record. Never infer physical validation from CAD/tests.
- `packaging/` — desktop release entry points and installer definitions.
- `.github/workflows/release-windows.yml` — self-contained Windows app/release build.

## Source of truth

- Mechanical geometry must be generated from source code. Do not hand-edit generated STL/STEP/3MF files.
- Python + CadQuery are the primary source of truth for precision mechanical parts.
- OpenSCAD is the reproducible backend for current **binary** artwork relief dies and small calibration artifacts.
- A future variable-depth relief backend may use a deterministic height-map/mesh path when that is more appropriate than OpenSCAD. User-facing behavior must still be driven by shared typed request/config objects and recorded in the manifest.
- Blender is for visual inspection, presentation, ergonomic exploration, animation, and complex artistic geometry. It is not the dimensional source of truth for production parts.
- Generated build outputs are disposable unless explicitly being packaged as release artifacts.

## Design invariants

- Units are millimetres unless explicitly stated otherwise.
- Male and female dies are a matched pair. Any orientation/clearance change must preserve mating geometry.
- The female die is intentionally not an exact negative: paper thickness, XY clearance, and extra cavity depth matter.
- Keyed carriers must remain rotationally deterministic.
- A shared cartridge-interface change must update all compatible parts and tests.
- Printer-sensitive clearances stay explicit parameters; never hide them in arbitrary mesh edits.
- Never treat a scaled miniature as proof of full-size strength.
- Physical validation must be recorded separately from software/CAD validation.

## Variable-depth relief contract

Before implementing grayscale/height-map relief, read **`docs/RELIEF_MODE_SPEC.md` in full**. It is the canonical architecture contract until explicitly superseded.

Critical invariants:

- Binary mode remains the default and existing binary commands/API calls must keep their behavior.
- Relief mode is opt-in; grayscale detection may suggest it but must never silently enable it.
- Grayscale semantics, gamma, stepping, polarity, and all paper/printer accommodations belong in shared backend data models, not UI code.
- CLI, GUI, and Python API must build the same relief request/specification and call the same generator.
- The female relief field must derive from the same male source field plus explicit clearance/paper/depth accommodations and the established cartridge orientation transform.
- Paper-risk analysis is heuristic and warning-oriented. `caution`/`high` paper-risk findings are overrideable; impossible geometry is not.
- A user override must be explicit and recorded in the generated manifest.
- Missing manifest `schema_version` means v1. New relief work may introduce schema v2 only by preserving existing top-level manifest fields documented in the relief spec.
- Do not claim grayscale relief is physically validated until an actual printed relief test is recorded in `docs/PHYSICAL_VALIDATION.md`.
- Do not couple relief-mode implementation to radial rings/textures. The architecture should allow those layers later, but direct grayscale-to-height functionality lands first.

If implementation choices conflict with the spec, update the spec intentionally in the same change and explain the compatibility impact. Do not silently diverge.

## Raster/source interpretation contract

Before adding automatic PNG/JPG interpretation, read **`docs/IMAGE_INPUT_SPEC.md`**.

Geometry mode and source interpretation are separate concepts.

Geometry modes:

```text
binary
relief
```

Source interpretations:

```text
flat-artwork
height-map
shaded-reference
```

Critical invariants:

- A metallic/shaded/3D-looking render is **not** automatically a height map.
- Do not map highlights, cast shadows, specular reflections, or ambient-occlusion shading directly to Z unless the user explicitly chooses literal height-map interpretation.
- Image detection may recommend an interpretation but must never silently change geometry semantics.
- `shaded-reference` conversion means synthesizing a manufacturable derived height map, not claiming to reconstruct true 3D depth from one image.
- Derived height maps must be preserved as inspectable output/provenance.
- A user-authored true height map must not be silently flattened through shaded-reference conversion.
- UI, CLI, and Python API must share the same source-interpretation enum and backend.

For ornate AI-generated medallion artwork, prefer an explicit machine height map over trying to use the pretty rendered image directly.

## Artwork-generation skill for agents

When an agent is asked to **create, redesign, simplify, or convert artwork for EmbossForge**, read:

```text
skills/embossforge-design/SKILL.md
```

The core rule is:

> Generate machine geometry artwork separately from presentation artwork.

For variable-depth designs, the preferred output pair is:

```text
<name>_heightmap.png   # machine input: unlit, orthographic grayscale
<name>_preview.png     # optional attractive visualization
```

Do not provide a metallic/shaded preview as the only file and label it a height map.

The skill defines:

- physical-scale feature guidance;
- current AD5M / 0.4 mm profile minima;
- white-zero / dark-high height-map convention;
- circular composition guidance;
- butterfly/floral/monogram hierarchy;
- relief-level design guidance;
- text/monogram rules;
- paper-friendly geometry heuristics;
- shaded-reference conversion rules;
- a reusable image-generation prompt template.

## Target reference hardware

- FlashForge Adventurer 5M
- 220 x 220 x 220 mm build volume
- current validated nozzle: 0.4 mm
- precision profile may later target 0.25 mm
- PLA is the current physical-validation material

These are defaults/reference targets, not assumptions that should prevent supporting other printers.

## Required development loop

For normal Python/backend changes:

```text
python -m compileall -q embossforge
pytest -q
```

For die-generation changes, also regenerate a smoke artifact. If OpenSCAD is installed:

```text
embossforge butterfly-test --out build/smoke-butterfly
```

For mechanical changes:

```text
pytest -q
embossforge mechanics --out build/mechanics
```

Then inspect generated assembly metadata/collision validation. A visual Blender pass is useful for geometry that cannot be confidently reviewed numerically.

For future relief-mode changes, additionally satisfy the testing contract in `docs/RELIEF_MODE_SPEC.md`, including binary backward-compatibility, tone mapping, male/female pairing, risk-report behavior, and manifest schema coverage.

For source-interpretation changes, test at minimum:

- a near-binary PNG;
- a true authored height map;
- a shaded metallic/bas-relief reference;
- a white-background ornate design with high detail density;
- behavior when detection disagrees with an explicit user choice.

## Desktop UI rules

The desktop app should remain intentionally simple:

- one obvious artwork drop/select surface;
- a preview;
- common settings visible;
- advanced settings secondary/collapsible;
- one primary `Generate matched die pair` action;
- clear success/error state;
- direct `Open output folder` action;
- no CAD vocabulary unless it is genuinely necessary to the user.

For future variable-depth relief:

- keep **Simple emboss** as the default;
- expose **Variable depth** as an explicit emboss-style choice;
- show only maximum relief, depth style, levels, and tone direction by default;
- keep gamma/threshold/sampling controls behind a secondary disclosure;
- summarize warnings in plain language near Generate;
- do not call a design "safe" merely because no heuristic warning fired.

For ambiguous shaded uploads, prefer a small interpretation card rather than another dense settings panel:

```text
Simple artwork
Convert 3D-looking artwork to relief
Treat grayscale as exact height
```

If the app thinks the image is shaded, explain why literal grayscale can be misleading. Recommendation is advisory; the user chooses.

Do not make users install developer dependencies when using official binary releases. Official Windows bundles should include the OpenSCAD runtime needed for current STL generation.

UI work must not change geometry behavior independently of the generator service.

## Release rules

Source installs:

```text
pip install -e ".[cad,gui,dev]"
embossforge gui
```

Official Windows builds are generated by `.github/workflows/release-windows.yml` and should produce:

- `EmbossForge-Windows-x64-portable.zip`
- `EmbossForge-Setup-Windows-x64.exe`

The portable/installer distribution bundles OpenSCAD under `tools/openscad/`; `find_openscad()` knows how to locate it in frozen builds.

Never commit generated PyInstaller `build/` or `dist/` directories.

## Agent usage policy

Conserve expensive GUI/computer-use/3D-agent runs. Ordinary code, docs, tests, manifests, parametric formulas, and package/release configuration should be edited directly in source.

Use a high-cost 3D/computer-use agent only when the task genuinely needs the user's local graphical environment, for example:

- visually inspect generated press assemblies in Blender/FreeCAD;
- test moving mechanisms or ergonomics;
- inspect complex artistic geometry;
- validate slicer behavior or local printer workflow;
- diagnose a problem that cannot be resolved from source geometry/tests/renders.

Image-generation agents may be valuable for **authoring machine height maps**, but they must follow `skills/embossforge-design/SKILL.md`. A pretty render is not dimensional source data.

When invoking a high-cost local 3D agent, keep the task narrow:

`inspect -> identify concrete issue -> minimal source correction -> regenerate -> verify`

Do not ask an agent to rebuild already-parametric geometry by hand in Blender.

## Before declaring a task complete

Check the relevant subset of:

1. `pytest -q` passes.
2. Generated artifacts are non-empty and dimensionally plausible.
3. CLI and desktop use the shared generator service.
4. No generated binaries/STLs were accidentally committed as source.
5. User-facing changes are reflected in README/docs when needed.
6. Claims about physical performance are backed by `docs/PHYSICAL_VALIDATION.md`, not by inference.
7. Release changes preserve a path for non-developer users to run the app without manual Python/OpenSCAD setup.
8. Relief-mode work preserves binary behavior and follows `docs/RELIEF_MODE_SPEC.md`.
9. Risk warnings and overrides are recorded in manifests; impossible geometry is never bypassed by `allow-risky` behavior.
10. Raster/source interpretation follows `docs/IMAGE_INPUT_SPEC.md` and never silently confuses a shaded render with a true height map.
11. Artwork-generating agents follow `skills/embossforge-design/SKILL.md` and separate machine maps from preview renders.
