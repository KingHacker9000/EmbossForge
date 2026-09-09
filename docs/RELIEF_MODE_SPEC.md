# Variable-depth grayscale relief specification

**Status:** Implemented software/CAD contract in EmbossForge 0.2. The first 42 mm variable-depth physical article exposed two important shortcomings in the earlier model: relief tiers were too shallow for the target FDM process, and paper thickness was incorrectly counted both in press closure and female cavity depth. The backend now uses the corrected engagement model below. Further physical tuning is still ongoing.

Binary mode remains backward-compatible and is still the default. Relief mode is opt-in and uses an explicit sampled height field shared by the male/female pair.

## Goals and invariants

The implemented relief path:

1. maps raster grayscale to a deterministic normalized height field;
2. supports authored true height maps and deterministic shaded-reference interpretation;
3. derives both dies from one canonical printer-aware field;
4. keeps paper thickness, XY clearance, extra female Z clearance, and upper-die mirror explicit;
5. validates both **accommodation** and **engagement** so a female cavity cannot silently be so deep that the pair closes without embossing;
6. separates hard geometry/mating failures from experimental paper-risk findings;
7. records processing, sampling, validation, and source provenance in schema-v2 manifests;
8. leaves binary behavior unchanged for existing callers.

## Modes and source semantics

Geometry:

```text
binary
relief
```

Source interpretation:

```text
flat-artwork
height-map
shaded-reference
```

Valid core combinations are:

```text
binary + flat-artwork
relief + height-map
relief + shaded-reference
```

The application may recommend a source interpretation but never silently changes it.

## Tone-to-height mapping

Let input luminance be `L` in `[0,1]`.

Default polarity (`dark-high`):

```text
R0 = 1 - L
```

Reverse polarity (`light-high`):

```text
R0 = L
```

Then gamma/dead-zone processing is applied. A variable-depth job can additionally specify `min_relief_mm`, an FDM-oriented floor for non-zero geometry.

For stepped relief, zero/background remains exactly zero and active pixels are mapped only to printable physical tiers between `min_relief_mm` and `max_relief_mm`.

For the current Adventurer 5M / 0.4 mm physical-development path, the recommended first aggressive calibration is:

```text
background   0.00 mm
shallow      0.40 mm
medium       0.80 mm
strong       1.20 mm
```

At a 0.20 mm slice height these correspond to 0, 2, 4, and 6 nominal layers. This is intentionally much more substantial than the earlier fractional-layer relief experiment.

The Python API keeps `min_relief_mm=0` by default for authored-height-map/backward compatibility. The CLI supplies an FDM-oriented floor unless explicitly overridden with `--relief-min`.

## Sampling and printer-aware canonicalization

Sampling resolution is derived from physical artwork size plus the selected printer's nozzle/minimum-feature metadata. Draft/balanced/fine quality presets change samples per useful feature while keeping deterministic limits on field size.

When enabled, positive relief islands/features below the selected profile's useful resolution are removed from the **shared canonical field** before female derivation. This avoids independently simplified halves.

## Correct female derivation

The female is derived from the same canonical male field with XY expansion for printer clearance.

Conceptually:

```text
expanded = local_max/dilation(Hmale, female_xy_clearance_mm)
female_cavity = expanded + female_extra_depth_mm
```

**Paper thickness is deliberately not added to `female_cavity`.** The nominal closed press already separates the two flat die faces by the selected paper thickness. Adding paper thickness again to the cavity double-counts it and creates an air gap that can allow a pair to close without forcing the paper into the female geometry.

The resulting local male-to-female space while paper is installed is therefore approximately:

```text
paper_thickness_mm + female_extra_depth_mm
```

`female_extra_depth_mm` is a small manufacturing/fit allowance, not a second paper allowance. For the current 42 mm FDM development pair, approximately 0.03–0.05 mm is the intended starting range rather than the earlier 0.20 mm default.

The female is mirrored using the established upper-cartridge transform. The deepest cavity must remain below the female base. Breakthrough is a hard non-overridable error.

## True height maps

The machine convention is:

```text
white = zero relief
black = maximum relief
```

A true height map should contain intentional geometry rather than decorative lighting. For a 42 mm / 0.4 mm nozzle emboss, broad separated regions normally reproduce much better than highly detailed metallic-render artwork.

## Shaded references

`shaded-reference` is an interpretation path, not literal depth reconstruction. It estimates a motif and writes a derived machine height map, preview, and foreground mask.

For critical/expensive physical tests, inspect the derived height map carefully. If an agent/user has already authored a clean machine height map, use `height-map` directly instead of re-interpreting it as a shaded reference.

## Validation model

### Hard errors — cannot be bypassed

- invalid/empty artwork;
- invalid dimensions/settings;
- female base breakthrough;
- build-volume violation;
- failed solid/STL generation;
- female height-field accommodation shortfall;
- incorrect female maximum Z allowance;
- incorrect peak engagement gap;
- predicted nominal exported-STL die-to-die interference.

### Experimental printability/paper-risk findings

Examples:

- sub-resolution positive detail;
- isolated high peaks;
- steep local transitions;
- dense/deep relief;
- profile-limited detail likely to merge/disappear.

`high` paper/quality risk is overrideable with `allow_risky=True` / `--allow-risky`. Hard mating/geometry errors are not.

## Closure and engagement verification

EmbossForge now distinguishes two different failure cases:

```text
1. accommodation failure
   female too shallow/narrow -> plastic interference

2. engagement failure
   female unnecessarily too deep -> pair closes, but paper is not driven into the cavity
```

Validation is layered:

```text
source/profile preflight
        ↓
canonical height-field accommodation + engagement
        ↓
SCAD/STL generation
        ↓
nominal exported-STL collision check
```

A collision-free STL pair alone is not sufficient evidence of a useful emboss.

## CLI

Recommended direct height-map starting point for the Adventurer 5M / 0.4 mm nozzle:

```powershell
embossforge die crest_heightmap.png `
  --mode relief `
  --source-interpretation height-map `
  --diameter 42 `
  --base 3 `
  --relief-max 1.20 `
  --relief-min 0.40 `
  --relief-style stepped `
  --relief-levels 4 `
  --paper copy `
  --clearance 0.20 `
  --extra-depth 0.03 `
  --relief-quality draft `
  --profile profiles\flashforge_adventurer_5m.toml `
  --allow-risky
```

Use `--relief-min 0` when you intentionally want the full authored 0..max continuous/shallow response rather than the FDM-oriented active-height floor.

## Python API

```python
from pathlib import Path
from embossforge.generator import DieGenerationRequest, generate_die
from embossforge.relief import ArtworkMode, ReliefSpec, ReliefStyle, SourceInterpretation

result = generate_die(
    DieGenerationRequest(
        artwork=Path("crest_heightmap.png"),
        output_root=Path("build"),
        artwork_mode=ArtworkMode.RELIEF,
        source_interpretation=SourceInterpretation.HEIGHT_MAP,
        relief=ReliefSpec(
            max_relief_mm=1.20,
            min_relief_mm=0.40,
            style=ReliefStyle.STEPPED,
            levels=4,
        ),
        female_extra_depth_mm=0.03,
        paper_preset="copy",
    )
)
```

## Physical status

Physically validated:

- the simple 16 mm binary/chunky butterfly matched-die concept embossed ordinary notebook paper.

Physically failed and superseded:

- the first 42 mm variable-depth Butterfly-M article using shallow relief and the old double-counted female Z allowance produced essentially no useful paper mark.

Still to validate physically:

- the corrected 0.4/0.8/1.2 mm stepped relief recipe;
- best `female_extra_depth_mm` across papers;
- paper tear/crease thresholds;
- intricate multi-tier artwork quality.

See `PHYSICAL_VALIDATION.md` for dated observations.
