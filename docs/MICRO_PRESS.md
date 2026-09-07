# Micro Embosser

The Micro Embosser is the smallest functional EmbossForge press and is designed specifically around the **16 mm `butterfly-test` die pair**.

It exists for one purpose: reuse the already-printed butterfly male/female dies to validate a real lever press, cartridge alignment, and light embossing before spending material on the larger miniature or full-size press.

## Generate it

```powershell
embossforge micro-press
```

Default output:

```text
build/micro-press/
  micro_press_manifest.json
  mechanics/
    base.stl
    side_cheek.stl
    top_bridge.stl
    lever.stl
    contact_roller.stl
    platen.stl
    stop_sleeve.stl
    receiver.stl
    cartridge.stl
    *.step
    assembly_layout.json
    mechanics_manifest.json
```

The pack does **not** regenerate the butterfly dies. It is meant to accept the pair created by:

```powershell
embossforge butterfly-test
```

## Exact die compatibility

The cartridge contract is tied directly to `micro_butterfly_spec()` rather than duplicating the dimensions:

- die diameter: **16.0 mm**
- die base thickness: **1.8 mm**
- orientation key width: **3.5 mm**
- orientation key depth: **1.5 mm**
- nominal butterfly relief: **0.45 mm**

Default cartridge pocket clearance is **0.18 mm per side**. If the already-printed die is unusually tight or loose, regenerate with:

```powershell
embossforge micro-press --die-clearance 0.22
```

Do not scale the STL to fix die fit. Change the explicit clearance parameter instead so the model remains reproducible.

## Size

Nominal micro-press dimensions are approximately:

- base: **58 × 65 × 5 mm**
- lever: **80 mm**
- cartridge body: **22 × 24 × 3.2 mm**
- guide rods: **3 mm diameter**
- nominal lever ratio: about **4.7:1**

It is smaller than the existing `mini-test` press and is not a uniform scale of the full mechanism. Printer-sensitive fit clearances remain realistic absolute dimensions.

## Hardware

Use:

- 2 × **3 mm smooth guide rods** (exact generated length is in `micro_press_manifest.json`)
- 1 × **M3-class bolt or smooth pin** for the main lever pivot
- 1 × **M2.5-class bolt or smooth pin** for the contact roller

Smooth steel rod is preferred for the guide rods. The micro press is intentionally low-force; do not use thin printed guide rods as evidence that the full mechanism is safe under load.

## Filament-saving print order

Do not print the entire press first.

1. Print **one `cartridge.stl`**.
2. Let it cool and try the already-printed 16 mm butterfly die in the keyed pocket.
3. The die should seat without force and should not rattle excessively.
4. If fit is good, print the second cartridge and **two `receiver.stl` copies**.
5. Confirm the cartridges slide into the receivers without binding.
6. Only then print the remaining press parts.

This sequence makes the smallest possible print answer the highest-risk fit question before more material is committed.

## Assembly orientation

- Put the **male butterfly die** in the lower cartridge.
- Put the **female butterfly die** in the upper cartridge.
- Seat each rectangular orientation tab in the matching keyed pocket.
- Do not independently rotate either die.
- The upper receiver/cartridge is installed flipped using the same 180° transform as the full EmbossForge mechanism.

The generated `assembly_layout.json` contains the exact open/closed transforms used by collision validation and Blender inspection.

## First use

Use ordinary printer/notebook paper first.

1. Insert both cartridges fully against their receiver stops.
2. Place one sheet between the dies.
3. Lower the lever slowly until the dies begin to engage.
4. Apply only enough force to form the butterfly.
5. Release and inspect the paper before increasing force.

The butterfly pair itself has already physically embossed notebook paper successfully. The **Micro Embosser mechanism has not yet been physically validated**, so treat its first print as a low-force prototype.

## What success proves

A successful Micro Embosser test validates:

- existing 16 mm die-to-cartridge fit;
- cartridge-to-receiver fit;
- male/female orientation;
- guide/platen alignment;
- lever and roller motion;
- the ability of the press architecture to emboss using the known-good butterfly pair.

It does **not** validate the strength of the full-size press.
