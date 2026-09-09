# Elegant Handheld Lever Embosser V3

`embossforge lever-press` now generates the primary full-size EmbossForge press: a sculpted hand-operated lever embosser built around the standard **42 mm keyed die pair**.

The previous blocky V2 CAD remains in `embossforge/mechanics/handheld_compact.py` as an engineering fallback. The older rod-guided laboratory press remains available through `embossforge mechanics`.

## Design direction

V3 targets the premium curved desk-embosser concept rather than a rectangular laboratory fixture. The visible geometry uses:

- a rounded/tapered pill-shaped base;
- a circular lower die platen;
- two sculpted C-shaped side cheeks with a large central aperture;
- hidden straight precision guide faces inside those curves;
- a round upper die carriage and round backing cap;
- a long sweeping ergonomic lever;
- shallow recessed grip/side accent panels;
- a slightly elongated M5 cam slot so the upper carriage can remain vertically guided while the lever rotates.

The cosmetic shell and the precision mating surfaces are intentionally separated in the CAD. Curves can be refined without silently changing the die-fit contract.

## Generate

```powershell
embossforge lever-press --out build\lever-press
```

Default files:

```text
build/lever-press/
  body.stl
  upper_carriage.stl
  upper_backing_cap.stl
  lever.stl
  body.step
  upper_carriage.step
  upper_backing_cap.step
  lever.step
  assembly_layout.json
  lever_press_manifest.json
```

## Compatible dies

V3 retains the exact standard EmbossForge insert contract:

- diameter: **42.0 mm**
- base thickness: **3.0 mm**
- orientation key: **6.0 × 2.5 mm**
- default socket clearance: **0.15 mm per side**

Generate a compatible pair with:

```powershell
embossforge die artwork.png --diameter 42 --paper copy --profile profiles/flashforge_adventurer_5m.toml
```

Do not scale die or press STLs to solve fit. Regenerate the press instead:

```powershell
embossforge lever-press --die-clearance 0.20
```

## Mechanism

```text
                  curved hand lever
          =============================
                    o M6 pivot
                 [cam slot]
                    o M5 carriage pin
                    |
             round upper platen
                female die ↓
             -----------------
                    paper
             -----------------
                 male die ↑
             round lower platen
          ___ sculpted curved body ___
```

The upper platen is still positively guided near engagement so the die faces remain parallel. Positive closure pads set nominal paper engagement. The M5 carriage pin runs in a short elongated lever slot to tolerate the small fore/aft component of the lever arc rather than forcing the vertical carriage to bind.

## Die loading

The lower male die drops into the keyed recess in the body with artwork facing **up** and the key toward **+Y / the front paper-insertion nose**.

The female die installs face **down** in the upper carriage. Flip the printed female **180° about Y** so its key still points toward the front. The round backing cap clamps it from above.

## Hardware

Prototype hardware remains intentionally ordinary:

- 1 × M6 bolt / ~6 mm smooth pin for the main pivot;
- 1 × M5 bolt / ~5 mm smooth pin for the carriage drive pin;
- 2 × M3 × ~10 mm screws for the upper die backing cap.

The M3 carriage holes are prototype pilot holes intended for plastic self-tapping. Do not over-tighten them.

## Validation status

V3 is required to pass CAD solid checks, open/closed printed-part collision checks, the exact 42 mm die contract, and CLI STL/STEP export in CI before it is treated as software-valid.

It is **not yet physically strength-qualified**. For the first print, slice the body and lever first, inspect material/time and print orientation, verify die seating at 100% scale, then assemble and increase hand force gradually. Record the result in `docs/PHYSICAL_VALIDATION.md` before treating V3 as a proven press.
