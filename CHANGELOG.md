# Changelog

All notable changes to EmbossForge will be documented here.

The project is currently pre-1.0. Interfaces, dimensions, and generated geometry may change between prototype revisions.

## Unreleased

### Added

- automatic matched male/female die generation from SVG and raster artwork
- keyed die-carrier orientation
- FlashForge Adventurer 5M prototype profile
- printer/emboss calibration artifacts
- parametric CadQuery press, cartridges, receivers, and assembly metadata
- open/closed printed-part collision checks
- Blender assembly import workflow
- low-filament miniature press generator
- ultra-low-filament cartridge/receiver fit coupon
- micro butterfly matched-die smoke test
- GitHub Actions CI
- contribution and physical-validation documentation

### Fixed

- SVG normalization for non-zero/negative `viewBox` origins that could shift imported artwork and leave only a clipped sliver
- butterfly smoke-test geometry now uses deterministic OpenSCAD primitives instead of depending on SVG import placement

### Physically validated

- 2026-09-07: 16 mm butterfly matched die pair printed successfully on a FlashForge Adventurer 5M with a 0.4 mm nozzle and produced a visible emboss on ordinary notebook paper

See `docs/PHYSICAL_VALIDATION.md` for test details.
