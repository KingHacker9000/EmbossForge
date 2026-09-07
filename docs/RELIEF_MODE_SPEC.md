# Variable-depth grayscale relief specification

**Status:** Implemented software/CAD contract in EmbossForge 0.2. Dedicated variable-depth physical emboss calibration is still pending, so this document does not claim paper/quality validation.

Binary mode remains backward-compatible and is still the default. Relief mode is opt-in and uses an explicit sampled height field shared by the male/female pair.

## Goals and invariants

The implemented relief path:

1. maps raster grayscale to a deterministic normalized height field;
2. supports authored true height maps and deterministic shaded-reference interpretation;
3. derives both dies from one canonical printer-aware field;
4. keeps paper thickness, XY clearance, extra female depth, and upper-die mirror explicit;
5. separates hard geometry/mating failures from experimental paper-risk findings;
6. records processing, sampling, validation, and source provenance in schema-v2 manifests;
7. uses the same backend from desktop, CLI, Python API, and CI;
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

Then:

```text
R1 = clamp(R0, 0, 1) ** gamma
if R1 < zero_threshold:
    R1 = 0
```

Stepped relief with `N >= 2`:

```text
R = round(R1 * (N - 1)) / (N - 1)
```

Continuous relief uses `R = R1`.

Physical male displacement:

```text
Hmale = R * max_relief_mm
```

Current FDM-oriented default is stepped relief with six levels. This is a workflow default, not a universal optimum.

## Sampling and printer-aware canonicalization

Sampling resolution is derived from physical artwork size plus the selected printer's nozzle/minimum-feature metadata. Draft/balanced/fine quality presets change samples per useful feature while keeping deterministic limits on field size.

When enabled, positive relief islands/features below the selected profile's useful resolution are removed from the **shared canonical field** before female derivation. This avoids independently simplified halves.

## Female derivation

The female is intentionally more permissive than an exact negative.

Conceptually:

```text
expanded = local_max/dilation(Hmale, female_xy_clearance_mm)
female_cavity = expanded + paper_thickness_mm + female_extra_depth_mm
```

Vertical allowance applies only to active/dilated relief regions. The female is then mirrored using the established upper-cartridge transform.

The deepest cavity must remain below the female base. Breakthrough is a hard non-overridable error.

## True height maps

The default machine convention is:

```text
white = zero relief
black = maximum relief
```

A true height map should contain intentional geometry rather than decorative lighting. SVG tone/gradient rendering is not currently a direct variable-depth machine path; export an authored raster height map instead.

## Shaded references

`shaded-reference` uses `deterministic-shaded-reference-v1` rather than naïve brightness→Z mapping. It estimates background, isolates the motif, preserves coherent interiors across specular highlights, applies printer-aware cleanup, suppresses broad illumination, and synthesizes emboss-oriented relief from motif distance and stable local structure.

It writes an explicit derived machine height map, relief preview, and foreground mask. The manifest states that the result is **interpreted emboss relief, not reconstructed true 3D depth**.

Desktop users must review/accept the derived preview before final STL rendering. See [IMAGE_INPUT_SPEC.md](IMAGE_INPUT_SPEC.md).

## Validation model

### Hard errors — cannot be bypassed

- invalid/empty artwork;
- invalid dimensions/settings;
- female base breakthrough;
- build-volume violation;
- failed solid/STL generation;
- height-field accommodation failure;
- predicted nominal exported-STL die-to-die interference.

### Experimental printability/paper-risk findings

Examples:

- sub-resolution positive detail;
- isolated high peaks;
- steep local transitions;
- dense/deep relief;
- profile-limited detail likely to merge/disappear.

Findings use:

```text
info
caution
high
error
```

`high` paper/quality risk is overrideable with `allow_risky=True` / `--allow-risky`. `error` and other hard mating/geometry failures are not. No-warning output is never described as guaranteed paper-safe.

## Closure verification

EmbossForge performs layered validation:

```text
source/profile preflight
        ↓
canonical height-field accommodation
        ↓
SCAD/STL generation
        ↓
nominal exported-STL closure collision check
```

The final check transforms the upper die into nominal closure and asks OpenSCAD for intersection geometry. A meaningful die-to-die collision is a non-overridable failure.

## Desktop UX

Primary relief controls:

- maximum relief;
- stepped / continuous;
- levels (stepped only);
- tone direction.

Advanced controls include gamma, dead zone, smoothing, sampling quality, printer-aware filtering, base/margin/clearance, and paper-risk override.

Validation is summarized near Generate. Shaded references add the explicit derived-preview acceptance stage described above.

## CLI

Height map:

```powershell
embossforge die crest.png `
  --mode relief `
  --source-interpretation height-map `
  --relief-max 0.35 `
  --relief-style stepped `
  --relief-levels 6 `
  --paper copy `
  --profile profiles\flashforge_adventurer_5m.toml
```

Shaded reference:

```powershell
embossforge die medallion.png `
  --mode relief `
  --source-interpretation shaded-reference `
  --relief-max 0.35 `
  --paper copy `
  --profile profiles\flashforge_adventurer_5m.toml
```

High paper-risk override:

```powershell
embossforge die aggressive.png --mode relief --source-interpretation height-map --allow-risky
```

Relevant implemented flags also include `--relief-gamma`, `--relief-polarity`, `--relief-zero-threshold`, `--relief-smoothing`, `--relief-quality`, and `--keep-subresolution-relief`.

## Python API

```python
from pathlib import Path
from embossforge.generator import DieGenerationRequest, generate_die
from embossforge.relief import ArtworkMode, ReliefSpec, ReliefStyle, SourceInterpretation

result = generate_die(
    DieGenerationRequest(
        artwork=Path("crest.png"),
        output_root=Path("build"),
        artwork_mode=ArtworkMode.RELIEF,
        source_interpretation=SourceInterpretation.HEIGHT_MAP,
        relief=ReliefSpec(
            max_relief_mm=0.35,
            style=ReliefStyle.STEPPED,
            levels=6,
        ),
        printer_profile=profile,
        paper_preset="copy",
    )
)
```

Existing requests without relief fields remain binary.

## Manifest schema v2

Relief manifests preserve:

- original artwork and source interpretation;
- resolved printer/paper/clearance sources;
- relief mapping settings;
- sampling size and physical sample pitch;
- validation findings and override status;
- shaded-reference derivation provenance where applicable;
- all output artifact paths generated by the backend.

Legacy manifests without `schema_version` remain schema-v1 artifacts.

## Current implementation boundary

Implemented now:

- raster height maps;
- stepped and continuous relief;
- printer-aware filtering;
- matched variable-height male/female SCAD/STL;
- shaded-reference deterministic interpretation;
- structured risk/closure validation;
- desktop, CLI, API, CI, and Windows packaging integration.

Not claimed as physically validated yet:

- optimal relief depth/level spacing for different papers;
- paper tear/crease thresholds;
- multi-height emboss quality on the reference printer.

Future enhancements such as generated radial profiles, composited texture layers, variable-depth SVG gradient rasterization, and richer 3D preview are additive conveniences, not blockers for the implemented 0.2 core relief pipeline.
