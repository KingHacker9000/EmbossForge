# EmbossForge agent guide

EmbossForge is an open-source parametric paper-embosser system. It turns artwork into matched male/female 3D-printable dies and contains a reusable cartridge/press platform.

This is the canonical guide for coding and 3D agents working in the repository.

## User paths

1. Desktop: artwork → source/emboss style → paper/printer → validation → matched files.
2. CLI: `embossforge die ...` plus calibration/mechanics commands.
3. Python: `DieGenerationRequest` + `generate_die()`.

Desktop, CLI, CI, and agents must use the **same generation backend**. Never duplicate geometry rules in UI code.

## Repository map

- `embossforge/generator.py` — shared matched-die orchestration.
- `embossforge/gui.py` — base polished PySide6 UI.
- `embossforge/gui_vnext.py` — official 0.2 desktop flow, including shaded-reference preview acceptance.
- `embossforge/cli.py` — CLI adapter.
- `embossforge/artwork.py` — binary SVG/raster normalization.
- `embossforge/heightmap.py` — canonical raster relief field and female surface derivation.
- `embossforge/shaded_reference.py` — deterministic shaded-reference interpretation.
- `embossforge/relief.py` — relief/source enums, specs, and validation types.
- `embossforge/relief_backend.py` — variable-height OpenSCAD/PNG surface generation.
- `embossforge/mating.py` — printer-aware pair preflight and exported-STL closure verification.
- `embossforge/validation.py` — height-field accommodation and experimental paper-risk heuristics.
- `embossforge/scad_backend.py` — binary geometry and OpenSCAD execution.
- `embossforge/config.py` — die specs, printer profiles, paper presets.
- `embossforge/mechanics/` — CadQuery cartridge/press geometry.
- `blender/` — visual QA only; not dimensional source of truth.
- `profiles/` — printer profiles.
- `tests/` — regression tests.
- `docs/RELIEF_MODE_SPEC.md` — implemented relief contract.
- `docs/IMAGE_INPUT_SPEC.md` — implemented source-interpretation contract.
- `docs/MATING_VALIDATION_SPEC.md` — printer-aware matched-pair contract.
- `skills/embossforge-design/SKILL.md` — artwork/height-map design rules for agents.
- `docs/PHYSICAL_VALIDATION.md` — actual printed validation. Never infer physical validation from CAD/tests.
- `packaging/` and `.github/workflows/release-windows.yml` — Windows desktop packaging.

## Source of truth

- Mechanical dimensions come from Python/CadQuery source.
- Binary artwork geometry comes from the shared Python/OpenSCAD path.
- Variable-depth geometry comes from the explicit canonical raster height field + OpenSCAD surface backend.
- Shaded references must first become an explicit derived height map; raw lighting is not dimensional source data.
- Blender is inspection/presentation, not production geometry authority.
- Generated STL/STEP/build outputs are disposable unless deliberately packaged as release artifacts.

## Matched-pair invariants

- Units are millimetres unless stated otherwise.
- Male and female are a coordinated pair; never simplify/filter them independently.
- The female includes paper thickness, XY clearance, and extra cavity depth.
- Build one printer-aware canonical target, then derive both halves from it.
- A positive feature surviving while its matching negative disappears is a compatibility failure.
- Predicted nominal die-to-die interference is a hard error and can never be bypassed by `allow_risky`.
- Upper/lower orientation and mirror transforms must remain deterministic.
- Printer-sensitive clearances stay explicit and profile-driven.
- Physical validation is separate from software/CAD validation.

## Relief contract

Binary remains the default. Relief is explicit and additive.

Valid source combinations:

```text
binary + flat-artwork
relief + height-map
relief + shaded-reference
```

Critical rules:

- true height maps use authored grayscale as geometry;
- shaded references use `deterministic-shaded-reference-v1`, not naïve brightness→Z;
- the converter writes an inspectable derived height map, preview, and foreground mask;
- shaded-reference output must never be described as recovered true 3D depth;
- desktop shaded references require preview acceptance before final STL rendering;
- gamma, stepping, polarity, smoothing, sampling, paper/profile accommodation, and validation belong in shared backend data models;
- female relief derives from the exact canonical male field plus explicit accommodations;
- hard geometry/closure failures are non-overrideable;
- high experimental paper-risk findings may be intentionally overridden and must be recorded in the manifest;
- no warning is proof of paper safety;
- variable-depth geometry must not be claimed physically validated until a real multi-height print is recorded in `docs/PHYSICAL_VALIDATION.md`.

Read `docs/RELIEF_MODE_SPEC.md`, `docs/IMAGE_INPUT_SPEC.md`, and `docs/MATING_VALIDATION_SPEC.md` before changing these paths.

## Artwork-generation policy

When creating/redesigning/simplifying EmbossForge artwork, read:

```text
skills/embossforge-design/SKILL.md
```

Prefer separate machine and presentation artifacts:

```text
<name>_heightmap.png   # unlit machine geometry
<name>_preview.png     # optional attractive render
```

Do not label a metallic/shaded preview as a true height map.

## Reference hardware

- FlashForge Adventurer 5M
- 220 × 220 × 220 mm
- current physically validated nozzle: 0.4 mm
- PLA used in the recorded binary physical validation

These are reference defaults, not restrictions on other printers.

## Development loop

Normal backend changes:

```text
python -m compileall -q embossforge
pytest -q
```

Die changes should also render a smoke artifact when OpenSCAD is available. CI already includes binary and real variable-depth STL smoke paths plus closure checks.

Mechanical changes:

```text
pytest -q
embossforge mechanics --out build/mechanics
```

Source-interpretation changes should cover at least flat raster, true height map, shaded reference, ornate/detail-dense input, and explicit-choice behavior.

Matched-die changes should cover thin positives, matching negative gaps, tiny counters, close ridges, orientation/mirror mismatch, profile/nozzle variation, and proof that `allow_risky` cannot bypass mating incompatibility.

## Desktop rules

Keep the app guided rather than CAD-like:

- one obvious artwork surface;
- Simple emboss default;
- explicit Variable depth mode;
- explicit True height map vs 3D-looking/shaded reference choice;
- common controls visible, advanced controls secondary;
- plain-language validation near Generate;
- derived shaded-reference preview before final STL generation;
- no silent semantic switching;
- direct output-folder access.

Official desktop entrypoints are `embossforge.gui_vnext:main` and `packaging/desktop_entry.py`.

## Release rules

Source:

```text
pip install -e ".[cad,gui,dev]"
embossforge gui
```

Windows release workflow should produce:

```text
EmbossForge-Windows-x64-portable.zip
EmbossForge-Setup-Windows-x64.exe
```

The bundle carries OpenSCAD under `tools/openscad/`. Do not commit PyInstaller `build/` or `dist/` output.

## Expensive-agent policy

Use local GUI/3D agents only when a task genuinely needs the user's graphical environment: assembly visual inspection, slicer behavior, moving-mechanism/ergonomic QA, or complex artistic geometry. Ordinary source, tests, docs, manifests, formulas, and packaging should be handled directly.

A high-cost visual pass should stay narrow:

```text
inspect → concrete issue → minimal source correction → regenerate → verify
```

Do not rebuild already-parametric geometry by hand in Blender.

## Before declaring work complete

Check the relevant subset:

1. `pytest -q` passes.
2. Binary and relief smoke artifacts are non-empty and plausible.
3. Rendered pairs pass printer-aware/height-field/exported-STL closure validation.
4. CLI and desktop call the shared generator.
5. No generated binaries were accidentally committed as source.
6. README/docs reflect user-facing behavior.
7. Windows packaging still gives non-developer users a self-contained path.
8. Risk override never bypasses invalid mating/geometry.
9. Shaded references and true height maps are never silently confused.
10. Physical claims are backed only by `docs/PHYSICAL_VALIDATION.md`.
