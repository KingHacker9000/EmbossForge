# EmbossForge

EmbossForge is an open-source parametric paper embosser and automatic matched-die generator for 3D printing.

The goal is simple: provide artwork and a few physical specifications, and generate a reusable embossing system with interchangeable male/female die cartridges.

## Current status

V0.1 already supports:

- SVG artwork input
- normalized artwork generation
- automatic matched male/female OpenSCAD dies
- STL export through OpenSCAD
- printer-aware defaults for the FlashForge Adventurer 5M
- manifest generation for reproducibility
- a CLI and test suite

V0.2 mechanical source is now in progress and includes a first parametric cartridge/receiver interface and conservative CadQuery lever-press generator. These are **prototype geometries** that must be calibrated and physically validated before normal use.

## Tool philosophy

EmbossForge deliberately uses more than one 3D tool:

- **CadQuery**: source of truth for precision mechanical geometry, dimensions, fits, cartridges, press parts, and STEP/STL export.
- **OpenSCAD**: simple reproducible backend for artwork relief dies and calibration pieces.
- **Blender**: visual QA, ergonomics, presentation renders, moving-assembly inspection, and artistic geometry when useful.
- **Python**: CLI, artwork preprocessing, validation, printer/paper profiles, orchestration, and automation.

This keeps the project reproducible and parameter-driven while still taking advantage of modern agent-assisted 3D workflows.

## Development setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[cad,dev]"
```

Check the environment:

```powershell
embossforge doctor
pytest -q
```

## Generate a die pair

```powershell
embossforge die examples\embossforge_mark.svg
```

Typical output:

```text
build/
└── embossforge_mark/
    ├── embossforge_mark_normalized.svg
    ├── embossforge_mark_male.scad
    ├── embossforge_mark_female.scad
    ├── embossforge_mark_male.stl
    ├── embossforge_mark_female.stl
    └── embossforge_mark_manifest.json
```

The female die is generated with configurable lateral clearance and extra cavity depth so it is not simply a mathematically exact negative of the male relief.

## Default die geometry

The current example uses a 42 mm round die with:

- 3.0 mm base thickness
- 0.65 mm male relief
- 0.20 mm female XY clearance
- 0.20 mm additional female cavity depth
- 0.10 mm nominal paper thickness
- 3.0 mm artwork margin

These are development defaults, not final manufacturing constants. EmbossForge includes calibration work as a first-class part of the roadmap so values can be tuned to the actual printer, material, nozzle, and paper stock.

## Target printer

Primary development printer:

- FlashForge Adventurer 5M
- 220 x 220 x 220 mm build volume
- 0.4 mm nozzle for first prototypes
- 0.25 mm nozzle as a later precision profile

## Roadmap

### V0.2 — mechanical platform

- standardized interchangeable cartridge pair
- keyed orientation and anti-misassembly geometry
- calibration generator for XY clearance, relief depth, paper gap, and fine-feature limits
- parametric CadQuery press/lever mechanism
- STEP and STL exports for mechanical parts
- assembly coordinates and diagnostic renders

### V0.3 — artwork intelligence

- raster-to-vector cleanup
- minimum printable feature checks
- automatic line/gap repair
- text and circular-seal layout generator
- paper presets
- printer/nozzle profiles

### V0.4 — polished user workflow

- one-command project builds
- generated assembly instructions
- optional local GUI
- print/slicer guidance
- release-ready model packs

## Agent policy

See [`AGENTS.md`](AGENTS.md). The short version: Astra/Codex is intentionally reserved for tasks that truly need the user's local GUI/3D environment. Ordinary Python, tests, documentation, and most parametric geometry should be implemented directly in source code first.

## Safety / prototype warning

The current press geometry is a prototype. Do not apply large forces until the printed parts, pivot hardware, hard stops, and failure modes have been physically inspected. Keep fingers away from the die gap while operating the press. Printed plastic can fail suddenly under load.

## Licensing

Software is currently released under the MIT License. A dedicated open-hardware license for final mechanical designs can be added when the hardware interface stabilizes.
