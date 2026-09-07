# Changelog

All notable changes to EmbossForge will be documented here.

The project is currently pre-1.0. Interfaces, dimensions, and generated geometry may change between prototype revisions.

## Unreleased

### Added

- automatic matched male/female die generation from SVG and raster artwork
- keyed die-carrier orientation
- FlashForge Adventurer 5M prototype profile
- paper presets and printer-profile validation in the generation flow
- shared `embossforge.generator` service used by CLI and desktop UI
- minimalist PySide6 desktop app with drag/drop artwork, preview, common settings, advanced settings, generation status, and output-folder access
- `embossforge gui` and `embossforge-gui` launch paths
- self-contained Windows packaging workflow using PyInstaller
- portable Windows ZIP layout with bundled OpenSCAD runtime
- Inno Setup Windows installer definition
- expanded `AGENTS.md` repository/validation/release guide for LLM coding and 3D agents
- desktop-app documentation and third-party notices
- continuous Windows GUI smoke coverage
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
- packaged builds can discover the bundled `tools/openscad/openscad.exe` runtime before looking for a system install

### Physically validated

- 2026-09-07: 16 mm butterfly matched die pair printed successfully on a FlashForge Adventurer 5M with a 0.4 mm nozzle and produced a visible emboss on ordinary notebook paper

See `docs/PHYSICAL_VALIDATION.md` for test details.
