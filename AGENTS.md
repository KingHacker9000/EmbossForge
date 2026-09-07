# EmbossForge agent policy

EmbossForge is an open-source, parametric paper-embosser system and automatic matched-die generator.

## Source of truth

- Mechanical geometry must be generated from source code. Do not hand-edit generated STL/STEP/3MF files.
- Python + CadQuery are the primary source of truth for precision mechanical parts.
- OpenSCAD is used where it is the simplest reproducible backend for die relief generation and small calibration artifacts.
- Blender is for visual inspection, presentation, ergonomic exploration, and complex artistic geometry; it is not the dimensional source of truth for production parts.

## Agent usage policy

GPT-6 Astra/Codex usage should be conserved. Do not spend Astra time rewriting ordinary Python, documentation, tests, or simple parametric CAD that can be authored directly in the repository.

Use Astra/Codex only when the task genuinely benefits from access to the local PC/GUI/3D environment, for example:

1. Open generated STEP/STL assemblies in Blender/CadQuery/FreeCAD and visually inspect alignment, interference, accessibility, and ergonomics.
2. Exercise or animate moving assemblies in Blender.
3. Inspect unusually complex or artistic input geometry that is awkward to diagnose from code/renders alone.
4. Validate local application integration, slicer behavior, or printer-specific workflows that require the user's installed software.

When using Astra/Codex, keep the task narrow. Prefer: inspect -> identify concrete issue -> make minimal source-code correction -> regenerate -> verify.

## Design rules

- Target printer: FlashForge Adventurer 5M, 220 x 220 x 220 mm build volume.
- Default prototype nozzle: 0.4 mm. Precision profile may target 0.25 mm.
- Default units: millimetres.
- All fits, relief depths, paper gaps, pivot diameters, cartridge dimensions, and safety margins must be named parameters.
- A change to a shared cartridge interface must update all compatible parts and tests.
- Prefer hardware-store fasteners/shafts for pivots over printed pins where practical.
- Never assume theoretical printer tolerances are sufficient; calibration artifacts are first-class outputs.

## Required validation

Before considering a mechanical change complete:

1. Run `pytest -q`.
2. Regenerate affected geometry.
3. Verify generated solids are valid/non-empty and dimensions match the configured specification.
4. For mating parts, generate/inspect the assembly or diagnostic cross-section.
5. Do not commit generated build outputs unless the repository documentation explicitly asks for release artifacts.
