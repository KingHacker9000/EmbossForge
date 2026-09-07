# First print quickstart

This guide is intentionally conservative. It starts with the smallest physically validated EmbossForge article before asking a new user to spend filament on the press.

## 1. Verify the toolchain

```powershell
embossforge doctor
pytest -q
```

## 2. Generate the physically validated smoke test

```powershell
embossforge butterfly-test
```

Load both generated STL files into your slicer at **100% scale**:

```text
build/butterfly-test/micro_butterfly_male.stl
build/butterfly-test/micro_butterfly_female.stl
```

Reference settings that worked on the FlashForge Adventurer 5M with a 0.4 mm nozzle:

- PLA
- 0.20 mm layer height
- 2 shells
- 10% grid infill
- supports off
- raft off
- 225 °C nozzle
- 55 °C bed

The successful development print was estimated by FlashPrint at about 0.96 g for the pair and about two minutes of print time.

## 3. Inspect before printing

The male should visibly contain a raised butterfly and the female should contain the matching recessed butterfly. If the slicer preview shows only a sliver, partial shape, or unexpected geometry, stop and report the input/output rather than printing.

## 4. Test the emboss

After the parts cool:

1. place ordinary paper between the working faces
2. align the orientation tabs
3. squeeze gently between two flat hard surfaces, or use a small clamp/flat-jaw tool
4. inspect both sides of the paper under angled light

This tiny pair is a light functional test, not a strength test.

## 5. Continue in increasing cost order

Once the butterfly works:

```text
embossforge fit-coupon
embossforge calibrate
embossforge mini-test
embossforge mechanics
```

Do not jump directly to the full press when working with an uncalibrated printer/material combination. Measure fit first, then spend filament on larger parts.

See `docs/PHYSICAL_VALIDATION.md` for the known physical test record.
