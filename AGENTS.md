# EmbossForge agent rules

EmbossForge is a physical engineering project. Preserve dimensions and reproducibility over visual improvisation.

## Source of truth
- Parametric/mechanical CAD: Python + CadQuery.
- Artwork-to-die conversion: Python orchestration + OpenSCAD boolean/offset backend for V0.1.
- Generated STL/STEP/3MF files are artifacts, never hand-edited source.
- Blender is for visual/mechanical inspection, assembly studies, ergonomics, renders, and tasks requiring the user's desktop environment.

## GPT-6 Astra / Codex budget
Use Codex/Astra only when work materially benefits from desktop/3D interaction. Do not spend agent time rewriting Python, docs, tests, CLI code, or configuration that can be handled directly in-repo.

## Current printer target
- FlashForge Adventurer 5M
- Build volume: 220 x 220 x 220 mm
- Prototype nozzle: 0.4 mm
- Precision target later: 0.25 mm

## Mechanical rules
- All critical dimensions must be parameters.
- Never assume a nominal sliding fit is printable; expose clearance as a parameter.
- Die artwork must never touch the outside edge of an insert.
- Female die geometry must include XY clearance and additional cavity depth for paper.
- Add calibration coupons before tightening final tolerances.
- Prefer hardware pins/bolts for highly loaded pivots over printed pins.

## Before merging a geometry change
1. Regenerate affected models.
2. Run tests.
3. Verify there are no non-manifold or zero-thickness regions.
4. Check print orientation and unsupported overhangs.
5. Record any new printer-dependent dimension as a profile parameter.
