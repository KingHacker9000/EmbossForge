# EmbossForge V0.2 mechanical plan

This milestone establishes the reusable mechanical platform around the already-working die generator.

## Cartridge interface

V0.2 uses a **universal sliding cartridge**. The same cartridge geometry is printed twice: one for the lower male insert and one for the upper female insert.

The cartridge:

- accepts a 42 mm keyed die insert
- uses a hidden +Y tab on the die base to lock angular orientation
- slides on captured lateral rails into a universal receiver
- opens from the +Y/front side for quick changes
- includes a finger scallop so the die insert can be removed
- keeps the die pocket and receiver clearances parametric

The upper cartridge/receiver assembly is rotated 180 degrees about **Y**, not X. That keeps the front insertion direction unchanged. The female artwork generator therefore pre-mirrors the female cavity in X.

Current prototype dimensions:

- die diameter: 42 mm
- die base thickness: 3 mm
- die key: 6.0 x 2.5 mm
- cartridge body: 52 x 58 x 6 mm
- die-pocket per-side clearance: 0.15 mm
- receiver slide per-side clearance: 0.25 mm
- receiver height: 6.5 mm

These are development defaults and must be tuned with calibration prints before final release.

## Press architecture

The initial free-sliding printed-ram concept was replaced with a **two-rod guided platen** because it is simpler, more repeatable, and avoids a wide upper receiver colliding with printed guide walls.

The V0.2 press contains:

- 130 x 155 x 12 mm printed base
- two printed side cheeks
- printed top bridge
- two 8 mm smooth vertical guide rods
- sliding printed upper platen
- universal lower and upper cartridge receivers
- two printed stop sleeves around the guide rods
- 205 mm printed lever
- transverse contact roller under the lever
- main M6-class pivot
- M5-class roller pin

All unique printed parts fit inside the FlashForge Adventurer 5M 220 mm build envelope. The lever closes approximately horizontal and opens upward; it does not need to swing below the table/base plane.

### Hard stop

The two guide-rod stop sleeves sit between the base and platen and define the minimum platen position. Their generated height is derived from the requested closed die-face gap. This is intentionally simple and physically inspectable.

### Lever contact

The lever does not scrape directly across the platen. A small transverse roller between two short lever ears contacts the platen. Two shallow reliefs in the platen give the ears clearance through the opening arc.

## Automatic geometry QA

`embossforge mechanics` now performs a CadQuery collision check in both the fully open and nominally closed states before considering the mechanical pack valid.

It also exports:

- STL files for printing
- STEP files for engineering inspection
- `mechanics_manifest.json`
- `assembly_layout.json`
- hardware lengths and quantities

The current default generated assembly has no unintended printed-part intersections in either checked state.

## Calibration before printing the full press

Run:

```powershell
embossforge calibrate
```

The calibration pack tests:

1. fit/clearance values
2. emboss relief depth
3. male/female XY clearance

Use the smallest mechanical clearance that assembles repeatedly after cooling, and choose emboss settings using the actual paper stock.

## Astra/Codex boundary

Astra/Codex should **not** recreate the CAD from scratch.

After `embossforge mechanics`, the repo already includes `blender/import_assembly.py`, which loads the generated assembly and hardware preview into Blender. Astra's eventual job should be limited to local 3D QA such as:

- inspect the open and closed assemblies visually
- check cartridge access and removal
- assess handle/lever ergonomics
- identify awkward interference not captured by static solid collision checks
- inspect slicer orientation/support needs
- suggest minimal source-code changes tied to concrete issues

This keeps expensive GPT-6 Astra usage focused on the tasks that actually benefit from a local 3D environment.
