# EmbossForge V0.2 mechanical plan

This milestone establishes the reusable mechanical platform around the already-working die generator.

## Cartridge interface goals

The cartridge interface must:

- accept a matched upper/lower die pair without tools
- force a known orientation
- prevent swapping upper/lower halves accidentally where practical
- locate the die concentrically and repeatably
- transfer embossing force through broad printed surfaces, not through retention magnets
- remain printable on the FlashForge Adventurer 5M
- expose all fit dimensions as parameters

Initial reference dimensions:

- die diameter: 42 mm
- die base thickness: 3 mm
- cartridge outer width: 52 mm
- cartridge outer depth: 58 mm
- cartridge body thickness: 6 mm before die pocket/retention features
- nominal slide clearance: 0.25 mm for the 0.4 mm nozzle profile

These are prototype values and will be replaced by measured values after calibration prints.

## Press concept

V0.2 uses a compact lever press with:

- rigid base
- two side cheeks
- steel or hardware-store pivot bolt
- long lever handle
- guided upper ram
- upper cartridge receiver
- lower cartridge receiver
- mechanical hard stop so the die pair cannot be over-crushed accidentally

The first press is intentionally conservative rather than elegant. Geometry remains fully parametric so lever ratio, throat depth, pivot size, and cartridge position can be changed after the first physical test.

## Calibration before finalizing fits

Generate and print a calibration pack before treating any fit values as final:

1. slide/slot clearances
2. round plug/pocket clearances
3. emboss relief depths
4. male/female XY clearances
5. fine line and fine gap features

The preferred fit is the smallest clearance that assembles repeatedly without force after cooling.

## Astra/Codex boundary

Astra/Codex should not be asked to invent or rewrite the parametric model from scratch.

Use it only after source-generated parts exist locally, for example:

- load the generated STEP/STL assembly in Blender or another local 3D tool
- inspect collisions and alignment
- verify cartridge insertion/removal is visually plausible
- assess lever ergonomics and access
- produce diagnostic screenshots/renders
- make only minimal source-code corrections tied to a concrete issue

This keeps expensive agent usage focused on local 3D inspection rather than ordinary coding.
