# Artwork guide

EmbossForge supports three explicit artwork semantics. Choosing the right one matters because pixels that look three-dimensional are not necessarily physical height.

Agents creating artwork should also read [`skills/embossforge-design/SKILL.md`](../skills/embossforge-design/SKILL.md).

## 1. Flat artwork

Use **Simple emboss** / `binary` mode for SVG logos, silhouettes, line art, monograms, and ordinary high-contrast raster images. Foreground geometry receives one relief height.

SVG is preferred when possible. Raster input works best when it is high contrast, clean, large enough to avoid pixelated edges, and simple enough to survive the selected nozzle. `--invert` handles light artwork on a dark background.

When a printer profile is selected, raster artwork is canonicalized against the profile's positive-feature and negative-gap limits **before** the male and female are derived. This prevents the two halves from independently losing different tiny details.

## 2. True height maps

Use **Variable depth → True height map** when grayscale was intentionally authored as geometry.

Default machine convention:

```text
white = zero relief
black = maximum relief
mid gray = intermediate relief
```

The polarity can be reversed explicitly. A machine height map should not contain decorative lighting, cast shadows, specular highlights, perspective shading, or metallic rendering.

Relief controls include maximum depth, stepped/continuous mapping, number of stepped levels, gamma, zero/dead-zone, smoothing, sampling quality, and printer-aware sub-resolution filtering.

For ordinary FDM work, stepped relief is usually easier to reason about. Continuous mode is available when the source and printer justify smoother height changes.

## 3. Shaded / 3D-looking references

Use **Variable depth → 3D-looking / shaded reference** for AI-generated silver medallions, rendered bas-relief, bevelled artwork, photographs of coins/carvings, or other images whose tones contain both shape and lighting.

EmbossForge does **not** map raw luminance directly to Z. The deterministic `shaded-reference` converter:

1. estimates the background from alpha or image borders;
2. isolates the coherent motif and preserves enclosed regions across bright highlights;
3. applies printer-aware cleanup;
4. removes broad illumination trends;
5. uses motif boundaries, distance, and stable local structure to synthesize emboss-oriented relief;
6. writes an explicit derived machine height map, visual relief preview, and foreground mask;
7. feeds that derived map into the same matched-relief backend as a true height map.

The manifest records method `deterministic-shaded-reference-v1` and explicitly states that the result is **interpreted emboss relief, not reconstructed true 3D depth**.

The desktop app performs this as a two-stage workflow: derive and validate the preview first, then require the user to accept that preview before rendering final STLs.

Full source behavior: [IMAGE_INPUT_SPEC.md](IMAGE_INPUT_SPEC.md).

## Design for physical printing

An image can look excellent on screen and still be a poor embossing tool. Thin lines, narrow gaps, isolated peaks, and delicate serif/floral details can merge, vanish, or become puncture points.

For the current FlashForge Adventurer 5M / 0.4 mm profile, the present conservative metadata is approximately:

- positive feature: 0.50 mm minimum;
- negative gap: 0.45 mm minimum;
- profile-specific effective line width and XY compensation are also modeled.

These are development/profile limits, not universal values and not paper-safety guarantees.

### Good relief artwork

- broad, intentional height regions;
- a small number of meaningful depth tiers;
- coarse texture with physical pitch large enough for the nozzle;
- shallow transitions rather than needle-like peaks;
- white/zero background around the active relief where appropriate.

### Risky relief artwork

- photographic noise or compression artifacts;
- very fine grain;
- sharpening halos;
- isolated bright/dark speckles;
- tall narrow ridges;
- raw metallic highlights/shadows treated as literal geometry.

## SVG handling

Binary SVG import is implemented and normalizes non-zero/negative `viewBox` origins before OpenSCAD import.

Variable-depth SVG tone/gradient rendering is **not** currently the machine path. For multi-depth SVG artwork, export an authored raster height map and use `height-map`; ordinary SVG artwork should remain in binary mode.

## Matched-pair invariant

Both halves must originate from one canonical source field. EmbossForge adds paper thickness, female XY clearance, and extra cavity depth to derive the female, then checks height-field accommodation and—when STLs are rendered—nominal exported-mesh closure.

A hard mating/geometry error cannot be bypassed with the paper-risk override. Experimental paper-risk warnings can be accepted deliberately.

## Orientation

The circular carrier has a hidden orientation tab. Upper geometry is mirrored/transformed for installation relative to the lower die. Do not independently rotate one generated insert.

## Before spending filament

Inspect the slicer preview and use a small test first. Binary embossing has a recorded physical success. Variable-depth and shaded-reference geometry are software/CAD validated but still require dedicated multi-height physical calibration before being described as physically proven.

See [RELIEF_MODE_SPEC.md](RELIEF_MODE_SPEC.md), [IMAGE_INPUT_SPEC.md](IMAGE_INPUT_SPEC.md), and [PHYSICAL_VALIDATION.md](PHYSICAL_VALIDATION.md).
