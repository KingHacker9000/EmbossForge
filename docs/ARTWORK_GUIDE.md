# Artwork guide

EmbossForge accepts SVG directly and can vectorize common raster formats such as PNG and JPG. The generator then creates matched male/female geometry with configurable clearance and cavity depth.

The **current implemented artwork path is binary**: foreground artwork is embossed at one constant relief height. A planned vNext **variable-depth grayscale relief** mode is specified in [RELIEF_MODE_SPEC.md](RELIEF_MODE_SPEC.md).

Raster/image interpretation is specified separately in [IMAGE_INPUT_SPEC.md](IMAGE_INPUT_SPEC.md). That distinction matters because an image that *looks* embossed is not necessarily a true height map.

Agents creating artwork for EmbossForge should use [`skills/embossforge-design/SKILL.md`](../skills/embossforge-design/SKILL.md).

---

## Three kinds of image input

EmbossForge should distinguish these concepts:

### 1. Flat artwork

Examples:

- clean SVG logos;
- silhouettes;
- line art;
- ordinary high-contrast PNGs;
- monograms.

Use the current binary path unless the user deliberately assigns multiple relief levels.

### 2. True height maps

A height map was authored so grayscale represents physical Z height.

EmbossForge's planned default convention is:

```text
white = zero relief
black = maximum relief
```

A machine height map should have no lighting, cast shadows, specular highlights, perspective, or metallic rendering.

### 3. Shaded / 3D-looking references

Examples:

- AI-generated silver medallions;
- rendered bas-relief artwork;
- bevelled Photoshop-style logos;
- photographs of coins or carvings.

These are useful inputs, but their grayscale tones include **lighting** as well as shape. EmbossForge should accept them and offer **Convert 3D-looking artwork to relief**, not silently treat raw luminance as literal depth.

Full behavior: [IMAGE_INPUT_SPEC.md](IMAGE_INPUT_SPEC.md).

---

## Best input format for current binary mode

Prefer SVG whenever possible. A clean vector logo or silhouette gives the most predictable result.

Raster input works best when it is:

- high contrast;
- dark artwork on a light background;
- free of photographic texture;
- large enough that edges are not pixelated;
- simple enough to survive the target nozzle width.

Use `--invert` when the foreground is light and the background is dark.

## Design for embossing, not just for the screen

An image can look excellent on a monitor and still be a poor embossing design. Very thin lines, tiny islands, narrow gaps, and delicate serif details may merge or disappear when printed.

For the current FlashForge Adventurer 5M / 0.4 mm development profile, treat roughly **0.50 mm** as the current conservative minimum feature width and **0.45 mm** as the current profile minimum gap until calibration proves otherwise. These are printer/profile guidance, not universal paper-safety guarantees.

Fine details may improve with a 0.25 mm nozzle.

## SVG coordinate handling

EmbossForge canonicalizes non-zero and negative SVG `viewBox` origins before OpenSCAD import. This avoids a class of failures where the imported artwork is shifted and circular clipping leaves only a small sliver of the design.

If an SVG still renders incorrectly, reduce it to a minimal file and open an issue with:

- the original artwork;
- the generated normalized SVG;
- the generated SCAD file;
- a screenshot of the slicer preview.

## Raster conversion in current binary mode

Raster artwork is thresholded and traced into filled vector contours. Useful controls:

```text
--threshold 160
--invert
```

Lower/higher thresholds change which pixels are treated as foreground. The current raster tracer is intentionally simple and is expected to improve before 1.0.

---

## Planned variable-depth grayscale relief

The accepted vNext design extends artwork semantics so grayscale can become actual emboss height/depth instead of being discarded by thresholding.

Examples:

```text
black      -> strongest relief
mid gray   -> medium relief
light gray -> shallow relief
white      -> zero relief
```

The default proposed polarity is **dark = high relief**, preserving the current mental model that dark artwork is active. Users will be able to explicitly reverse that mapping.

This enables artwork such as:

- a deep outer seal ring and a shallower inner ring;
- layered monograms;
- coarse textures;
- stepped decorative relief;
- smooth gradients where printer resolution supports them.

### Grayscale artwork should communicate intentional height

When designing specifically for variable-depth mode, use tone as structure rather than decorative shading.

Good examples:

- large regions at clearly different gray values;
- broad transitions rather than one-pixel gradients;
- coarse texture whose pitch is meaningful at the physical die size;
- a small number of intentional height levels for FDM printing;
- a white zero-height background with darker geometric relief regions.

Riskier examples:

- photographic noise;
- compression artifacts;
- very fine grain;
- narrow bright/dark halos from sharpening;
- tiny high-contrast speckles;
- abrupt tall ridges thinner than the printer can resolve;
- metallic highlights and shadows being mistaken for geometry.

Relief mode will include a zero/dead-zone threshold so near-white noise does not necessarily become microscopic relief.

### Shaded renders are references, not height maps

A realistic gray/metallic butterfly medallion can contain a bright highlight on one edge of a raised wing cell and a dark shadow on the other edge. The physical wing cell may be at one consistent height, so mapping those light/shadow pixels directly to Z would invent false geometry.

For such images, the planned workflow is:

```text
shaded PNG
   |
   v
source interpretation: shaded-reference
   |
   v
lighting/detail normalization
   |
   v
derived machine height map
   |
   v
user preview + validation
   |
   v
matched dies
```

The original image remains preserved as provenance; the derived height map is the machine geometry input.

### Agent-authored height maps

When an image-capable LLM/agent is available, the preferred workflow for ornate designs is to ask it to produce a **true unlit height map** and, optionally, a separate decorative preview.

Repository skill:

```text
skills/embossforge-design/SKILL.md
```

The skill teaches agents to:

- design in physical millimetres rather than only pixels;
- keep details printable for the target nozzle;
- use white as zero relief and dark tones as increasing relief by default;
- avoid cast shadows/highlights in machine maps;
- separate preview renders from machine geometry;
- simplify ornate floral/butterfly/monogram designs without losing their identity;
- avoid claiming paper safety without physical validation.

### SVG grayscale semantics

Variable-depth SVGs cannot be handled by the current color-insensitive OpenSCAD import alone. Relief mode is specified to render SVG fills, strokes, opacity, and gradients to an internal grayscale height map first.

That means SVG color/tone will become meaningful in relief mode, while current binary SVG behavior remains unchanged.

### Stepped versus continuous relief

The vNext specification defines:

- **Stepped relief** — tones are quantized to a fixed number of physical heights. Proposed first FDM-friendly default: six levels.
- **Continuous relief** — tone maps continuously to height.

Stepped relief is expected to be easier to reason about on ordinary FDM printers. Continuous mode remains available for users who intentionally want smoother surfaces.

### Paper-damage warnings

Variable-height dies can create sharper local slopes, narrow tall ridges, or deep textures that may crease, puncture, or tear paper.

EmbossForge's planned validator will warn about those conditions using experimental, profile-driven heuristics. These warnings are **not guarantees of safety** and are intended to remain overrideable when the user deliberately wants aggressive tooling.

Impossible geometry, such as a female cavity cutting through the base, remains a hard error and cannot be bypassed.

Full relief behavior: [RELIEF_MODE_SPEC.md](RELIEF_MODE_SPEC.md).

Full raster/source interpretation behavior: [IMAGE_INPUT_SPEC.md](IMAGE_INPUT_SPEC.md).

---

## Orientation

The current circular die carrier has a hidden orientation tab. Male and female geometry are generated to account for the upper die being installed flipped relative to the lower die. Do not independently rotate one generated insert unless you also understand and compensate for that transform.

The same orientation invariant applies to future variable-depth relief: both surfaces must originate from one source height field and the established upper-cartridge transform.

## Before spending filament

Always inspect the slicer preview. The silhouette or lettering should be clearly recognizable before printing. For a new artwork pipeline change, use a small die first rather than immediately generating the full 42 mm production-size insert.

For future variable-depth relief, physical validation should begin with small stepped-depth/ring coupons before large or intricate designs. Software/CAD success alone is not evidence that a relief pattern will emboss cleanly or avoid tearing paper.
