# Changelog

All notable changes to EmbossForge are documented here.

The project remains pre-1.0. Interfaces, dimensions, and generated geometry may change between prototype revisions.

## 0.2.0 — software-complete relief pipeline

### Added

- automatic matched male/female die generation from SVG and raster artwork
- keyed die-carrier orientation
- FlashForge Adventurer 5M prototype profile with positive/negative feature and effective line-width metadata
- paper presets and printer-profile validation in the generation flow
- shared `embossforge.generator` service used by CLI and desktop UI
- guided PySide6 desktop app with drag/drop artwork, preview, printer/paper controls, validation status, and output-folder access
- `embossforge gui` and `embossforge-gui` launch paths
- self-contained Windows packaging workflow using PyInstaller, bundled OpenSCAD, portable ZIP, and Inno Setup installer
- printer/emboss calibration artifacts
- parametric CadQuery press, cartridges, receivers, assembly metadata, STEP/STL export, and open/closed collision checks
- low-filament miniature press, fit coupon, and micro butterfly matched-die smoke tests
- dedicated `micro-press` / **Micro Embosser** sized to the already-printed 16 mm butterfly-test die contract, with a 58 × 65 mm base, 80 mm lever, exact keyed cartridge pockets, staged filament-saving print order, and CI collision/export coverage
- deterministic variable-depth raster height-map backend
- stepped and continuous grayscale-to-height mapping with configurable maximum depth, gamma, polarity, dead zone, smoothing, and sampling quality
- shared canonical male height field from which the female relief is derived with paper thickness, XY clearance, and extra-depth allowance
- printer-aware sub-resolution filtering so incompatible positive/negative features are not independently preserved
- structured validation findings separating hard geometry/mating failures from experimental paper-risk warnings
- explicit paper-risk override that cannot bypass geometry or die-to-die interference failures
- exported-STL nominal closure collision verification using OpenSCAD
- manifest schema v2 with source semantics, relief parameters, sampling information, validation results, and provenance
- explicit source interpretations: `flat-artwork`, `height-map`, and `shaded-reference`
- deterministic shaded-reference converter (`deterministic-shaded-reference-v1`) that suppresses broad illumination, isolates motifs, synthesizes emboss-oriented relief, and preserves the derived height map, preview, and mask
- desktop two-stage shaded-reference workflow: derive/validate preview first, then explicitly accept it before final STL rendering
- advisory continuous-shading detection that recommends the shaded-reference path without silently changing source semantics
- CI coverage for variable-depth STL rendering, manifest v2, closure validation, shaded-reference conversion, the Micro Embosser, and the vNext Windows desktop window
- Windows release validation for binary and variable-depth STL generation
- `skills/embossforge-design/SKILL.md` for image-capable LLM agents creating manufacturable EmbossForge artwork/height maps

### Fixed

- SVG normalization for non-zero/negative `viewBox` origins that could shift imported artwork and leave only a clipped sliver
- butterfly smoke-test geometry now uses deterministic OpenSCAD primitives instead of depending on SVG import placement
- packaged builds discover bundled `tools/openscad/openscad.exe` before looking for a system install
- light-high relief polarity regression test now samples relative positions after printer-aware resampling
- shaded-reference motif segmentation preserves enclosed regions across bright/specular highlights rather than interpreting them as background holes

### Validation status

Software/CAD validation covers binary generation, true height maps, shaded-reference derivation, matched height fields, printer-aware filtering, hard closure checks, Micro Embosser open/closed printed-part collision checks, and Windows desktop construction. Variable-depth physical emboss quality and the Micro Embosser mechanism are not yet claimed as physically validated.

### Physically validated

- 2026-09-07: 16 mm **binary** butterfly matched die pair printed successfully on a FlashForge Adventurer 5M with a 0.4 mm nozzle and produced a visible emboss on ordinary notebook paper.

The next physical validation milestones are the butterfly-compatible Micro Embosser and a small multi-height/stepped relief coupon when material is available. See `docs/PHYSICAL_VALIDATION.md`.
