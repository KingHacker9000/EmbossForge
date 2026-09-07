# EmbossForge

Open-source parametric embosser tooling and an automatic matched-die generator for 3D printing.

EmbossForge's goal is simple: give it artwork and physical specifications, and get a printable male/female embossing die pair without remodeling the artwork by hand.

## Current V0.1 scope

- SVG input directly.
- PNG/JPG/BMP/TIFF/WEBP input via automatic vector contour tracing.
- Parametric round die diameter, base thickness, artwork margin, relief height, paper thickness, female XY clearance, and female extra depth.
- Automatic male relief generation.
- Automatic female recessed cavity generation with clearance.
- OpenSCAD source + STL export.
- Windows/macOS/Linux OpenSCAD discovery.
- Local toolchain doctor command.
- FlashForge Adventurer 5M prototype profile.

The reusable press, keyed interchangeable cartridge standard, calibration coupons, STEP/3MF export, and visual Blender inspection workflow come next.

## Why both CadQuery and OpenSCAD?

CadQuery is the source of truth for precise mechanical parts such as the press, lever, cartridge interfaces, pins, stops, and holders. OpenSCAD is currently used as the artwork boolean backend because its 2D `import()` + `offset()` + `linear_extrude()` pipeline makes arbitrary SVG relief generation compact and reproducible.

Blender is intentionally not the dimensional source of truth. It is reserved for visual inspection, assembly/ergonomic iteration, renders, and desktop-interactive work where GPT-6 Astra/Codex provides the most value.

## Install

Requires Python 3.11+ and OpenSCAD. CadQuery is recommended for upcoming mechanical CAD work.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -e .[cad,dev]
embossforge doctor
```

If OpenSCAD is installed in the normal Windows location (`C:\\Program Files\\OpenSCAD\\openscad.exe`) it does not have to be added to PATH.

## Generate a die pair

```bash
embossforge die my_logo.svg
```

This creates a build folder containing normalized artwork, male/female OpenSCAD source, male/female STL files, and a JSON manifest.

Example with specifications:

```bash
embossforge die my_logo.png \
  --diameter 42 \
  --relief 0.65 \
  --paper-thickness 0.10 \
  --clearance 0.20 \
  --margin 3
```

For light artwork on a dark image:

```bash
embossforge die logo.png --invert
```

Generate source without calling OpenSCAD:

```bash
embossforge die logo.svg --scad-only
```

## Important V0.1 assumptions

The default arrangement is a lower male die and an upper female die. The female artwork is mirrored in Y before its cavity is generated so that flipping the upper die to face the lower die restores alignment. This will be replaced by a mechanically keyed cartridge orientation standard in the next hardware milestone.

Raster tracing is designed for logos, line art, monograms, seals, and high-contrast artwork. Photographs need a separate height-map relief mode and are not treated as ordinary embossing artwork.

## FlashForge Adventurer 5M

The initial profile is `profiles/flashforge_adventurer_5m.toml` and targets the user's 0.4 mm nozzle for prototypes. Final minimum feature sizes and die clearance will be calibrated from physical test coupons rather than assumed from nominal printer precision.

## Roadmap

1. Calibration coupon generator for relief height, XY clearance, line width, and gap.
2. Keyed interchangeable die-insert standard.
3. Parametric CadQuery press and lever mechanism.
4. STEP and 3MF generation.
5. Artwork printability analysis + automatic repair suggestions.
6. 0.25 mm precision profile.
7. Blender assembly/import/render tooling for Astra visual inspection.
8. Optional local GUI/web UI.

## License

MIT. Contributions and derivative designs are welcome.
