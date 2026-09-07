# EmbossForge

EmbossForge is an open-source parametric paper embosser and automatic matched-die generator for 3D printing.

The goal is simple: provide artwork and a few physical specifications, and generate a reusable embossing system with interchangeable male/female die cartridges.

## Current status

The artwork/die pipeline works, and the V0.2 mechanical prototype is now source-generated as well.

Current capabilities:

- SVG and raster artwork normalization
- automatic matched male/female emboss dies
- keyed die carriers so rotational alignment is deterministic
- safe circular artwork clipping for arbitrary designs
- configurable female XY clearance and cavity depth
- OpenSCAD + STL die output
- printer/emboss calibration coupons
- universal interchangeable cartridge + receiver geometry
- parametric rod-guided lever press in CadQuery
- STEP + STL mechanical exports
- generated hardware/assembly manifest
- automatic open/closed CadQuery collision checks
- Blender assembly loader for visual QA without rebuilding the model by hand

**Important:** outputs generated before the keyed-carrier update should be regenerated before printing. The current die interface and female orientation logic are different from the earliest V0.1 prototype files.

## Tool philosophy

EmbossForge deliberately uses more than one 3D tool:

- **CadQuery**: source of truth for precision mechanical geometry, dimensions, fits, cartridges, press parts, and STEP/STL export.
- **OpenSCAD**: reproducible backend for artwork relief dies and calibration pieces.
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

The current 42 mm insert has a hidden orientation tab on the carrier base. Artwork is clipped to the safe circular emboss area, and the female cavity is generated with configurable lateral/depth clearance.

The upper cartridge uses the same physical cartridge/receiver geometry as the lower one and is installed by rotating it 180 degrees about Y. The generator compensates by mirroring the female artwork in X before extrusion.

## Generate calibration artifacts

```powershell
embossforge calibrate
```

This creates a mechanical clearance coupon plus matched male/female emboss matrices. Use these before treating prototype tolerances as final for a particular nozzle, filament, and paper stock.

See [`docs/CALIBRATION.md`](docs/CALIBRATION.md).

## Generate the V0.2 mechanical pack

```powershell
embossforge mechanics
```

Output is written to `build/mechanics/` and includes:

- `base.step` / `base.stl`
- `side_cheek.step` / `side_cheek.stl` — print two
- `top_bridge.step` / `top_bridge.stl`
- `lever.step` / `lever.stl`
- `contact_roller.step` / `contact_roller.stl`
- `platen.step` / `platen.stl`
- `stop_sleeve.step` / `stop_sleeve.stl` — print two
- `receiver.step` / `receiver.stl` — print two
- `cartridge.step` / `cartridge.stl` — print two
- `assembly_layout.json`
- `mechanics_manifest.json`

The generator validates the open and nominally closed assemblies for unintended printed-part intersections before accepting the pack.

### V0.2 press architecture

The current prototype uses:

- 130 × 155 × 12 mm printed base
- two printed side cheeks
- printed top bridge
- two 8 mm smooth steel guide rods
- sliding upper platen
- universal top/bottom cartridge receivers
- two printed stop sleeves around the guide rods
- 205 mm lever
- transverse roller under the lever rather than sliding plastic-on-plastic contact
- M6-class main pivot
- M5-class roller pin

All unique printable parts are designed to fit individually inside the FlashForge Adventurer 5M's 220 mm build envelope.

The exact hardware lengths are written into `mechanics_manifest.json` from the same dimensional model, so the manifest—not this README—is the source to use when buying/cutting hardware.

## Optional Blender visual QA

After generating the mechanical pack, Blender can load the source-generated assembly directly:

```powershell
blender --python blender\import_assembly.py -- build\mechanics open
```

or:

```powershell
blender --python blender\import_assembly.py -- build\mechanics closed
```

This exists specifically so a human or GPT-6 Astra/Codex can inspect the real generated assembly without spending agent time recreating geometry. Blender is not the dimensional source of truth.

## Target printer

Primary development printer:

- FlashForge Adventurer 5M
- 220 × 220 × 220 mm build volume
- 0.4 mm nozzle for first prototypes
- 0.25 mm nozzle as a later precision profile

## Roadmap

### V0.2 — mechanical validation

- [x] keyed interchangeable die-carrier standard
- [x] universal cartridge + receiver
- [x] calibration generator
- [x] parametric rod-guided CadQuery lever press
- [x] STEP/STL export
- [x] generated assembly metadata
- [x] open/closed solid collision checks
- [x] Blender assembly loader
- [ ] print calibration coupons
- [ ] tune AD5M 0.4 mm clearances from physical measurements
- [ ] print first cartridge/receiver pair
- [ ] visually inspect generated assembly in Blender/local CAD
- [ ] print and physically validate the press at low force

### V0.3 — artwork intelligence

- raster-to-vector cleanup improvements
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

See [`AGENTS.md`](AGENTS.md). GPT-6 Astra/Codex usage is intentionally reserved for tasks that genuinely benefit from the user's local GUI/3D environment. Ordinary Python, tests, documentation, and parametric geometry should be implemented directly in source code first.

## Safety / prototype warning

The current press geometry is a prototype. Do not apply large forces until the printed parts, pivot hardware, hard stops, and failure modes have been physically inspected. Keep fingers away from the die gap while operating the press. Printed plastic can fail suddenly under load. Begin emboss tests with low force and wear eye protection during early mechanical testing.

## Licensing

Software is currently released under the MIT License. A dedicated open-hardware license for final mechanical designs can be added when the hardware interface stabilizes.
