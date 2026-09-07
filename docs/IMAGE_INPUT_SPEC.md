# Image input interpretation specification

**Status:** Accepted vNext design contract. This document extends `RELIEF_MODE_SPEC.md` by defining how EmbossForge interprets raster/SVG artwork before binary or variable-depth geometry generation.

The key rule is simple:

> **An image that looks three-dimensional is not automatically a height map.**

Metallic medallion renders, AI-generated bas-relief previews, bevelled logos, and shaded illustrations often contain highlights, cast shadows, ambient occlusion, and material reflections. Those pixels describe **lighting**, not necessarily physical height. Directly mapping their grayscale values to Z would create false grooves, bumps, halos, and paper-cutting ridges.

EmbossForge should support these images, but must interpret them intentionally.

---

## 1. Two independent concepts

Do not overload one mode selector with two different meanings.

### Geometry mode

```text
binary
relief
```

- `binary` is the current constant-height emboss behavior.
- `relief` is variable-depth height-field behavior from `RELIEF_MODE_SPEC.md`.

### Source interpretation

```text
flat-artwork
height-map
shaded-reference
```

These describe what the uploaded pixels *mean*.

A shared generation request should eventually carry both values explicitly.

---

## 2. Flat artwork

Use `flat-artwork` for logos, silhouettes, line art, high-contrast PNGs, ordinary SVGs, and designs whose visual tones are not intended to encode Z height.

Typical behavior:

```text
flat-artwork + binary -> current threshold/vector/extrude pipeline
```

A future advanced path may allow flat artwork to be assigned multiple generated relief tiers, but ordinary flat artwork must not silently become a literal grayscale height map.

---

## 3. True height maps

Use `height-map` only when grayscale was deliberately authored as geometry.

Default EmbossForge convention:

```text
white = zero relief
black = maximum relief
```

This is the `dark-high` polarity defined by the variable-depth relief specification. The user may explicitly reverse polarity.

Characteristics of a good height map:

- orthographic / front-on;
- no perspective;
- no cast shadows;
- no specular highlights;
- no metallic shading;
- no ambient-occlusion-style darkening unless that darkening is intentionally a higher physical surface;
- background is a known zero-relief value;
- gradients represent intended surface ramps, not illumination;
- details respect the target printer's physical resolution.

When the user explicitly chooses **Treat grayscale as height**, EmbossForge may map the image deterministically to relief according to `RELIEF_MODE_SPEC.md`.

---

## 4. Shaded / 3D-looking references

Use `shaded-reference` for images such as:

- AI-generated metallic medallions;
- rendered bas-relief art;
- bevelled/embossed Photoshop-style graphics;
- 3D renders with directional lighting;
- grayscale art containing obvious highlights and shadows;
- photographs of carvings, coins, or embossed surfaces.

These inputs are supported, but **raw luminance must not be treated as literal height by default**.

### Why direct grayscale mapping fails

A raised petal may contain:

```text
bright highlight -> midtone -> dark shadow
```

although the entire petal is physically above the background. A direct tone-to-height conversion would therefore make one edge high and the shadowed edge low, creating a groove that never existed in the intended design.

The same problem affects:

- bevel highlights;
- contact shadows;
- dark outlines;
- shiny metal reflections;
- artificial depth-of-field or vignettes;
- drop shadows around text and rings.

---

## 5. Desktop behavior for ambiguous PNGs

EmbossForge may analyze an image and make a recommendation, but must not silently choose an interpretation that changes geometry semantics.

When an uploaded image has substantial grayscale variation, show a small interpretation card:

```text
How should EmbossForge use this image?

[ Simple artwork ]
Make a constant-height emboss from the design shape.

[ Convert 3D-looking artwork to relief ]  Recommended when detected
Remove visual shading and derive printable depth levels.

[ Treat grayscale as exact height ]
Use pixel tone directly as Z height. Choose only for a real height map.
```

If the image appears to be a shaded render, show:

> This looks like a rendered or shaded relief. Highlights and shadows are not reliable depth. EmbossForge can derive a printable relief map instead.

The recommendation is advisory. The user remains in control.

---

## 6. Shaded-reference conversion contract

The goal is **not** to reconstruct the exact original 3D object from one image. That problem is ambiguous.

The goal is to create a visually faithful, printer-aware emboss design whose depth structure matches the major motifs.

A first deterministic conversion pipeline should conceptually perform:

1. **Background isolation**
   - identify transparent/near-uniform background;
   - suppress drop shadows outside the intended motif.

2. **Illumination normalization**
   - remove broad lighting gradients/vignettes where practical;
   - reduce highlight/shadow variation inside a visually coherent region.

3. **Region and edge extraction**
   - preserve motif boundaries, text, rings, petals, wing cells, leaves, etc.;
   - avoid interpreting every internal lighting gradient as geometry.

4. **Printer-aware detail filtering**
   - remove or merge features below `min_feature_mm`;
   - close gaps below `min_gap_mm` when auto-repair is enabled;
   - suppress high-frequency texture that cannot survive the selected nozzle/profile.

5. **Relief synthesis**
   - assign a small number of broad, meaningful relief tiers by default;
   - preserve intentional large-scale ramps;
   - round/soften dangerous needle-like peaks and knife-edge ridges unless the user disables repair.

6. **Validation**
   - run the same printability and paper-risk heuristics as direct relief mode.

7. **User confirmation**
   - show the **derived height map / relief preview** before final STL generation;
   - never hide the fact that the input was interpreted rather than used literally.

The offline converter should be deterministic. Optional agent-assisted conversion may produce a better height map, but official geometry generation must still consume an explicit, inspectable height map.

---

## 7. Detail-density behavior

EmbossForge should accept highly ornate images rather than rejecting them just because they are ambitious.

However, the target physical scale matters.

For example, a 42 mm medallion containing dozens of tiny beads, engraved leaf veins, rose-petal microtexture, thin antennae, and fine background damask may contain far more detail than a 0.4 mm FDM nozzle can reproduce.

Expected behavior:

```text
upload accepted
      |
      v
analysis
      |
      +--> printable as-is
      |
      +--> caution: some details will merge/disappear
      |
      +--> high detail-density warning
               |
               +--> auto-simplify / filter
               +--> change nozzle/profile
               +--> continue intentionally
```

Warnings are preferable to arbitrary rejection.

---

## 8. What should happen with ornate AI medallion images

For a shaded butterfly/floral medallion image:

1. Accept the PNG/JPG.
2. Detect that it has substantial continuous shading and likely rendered relief characteristics.
3. Recommend **Convert 3D-looking artwork to relief**.
4. Remove the white background as zero relief.
5. Preserve major structures such as the circular rings, butterfly silhouette, wing compartments, flowers, leaves, and monogram.
6. Flatten lighting artifacts inside those regions.
7. Reduce sub-nozzle surface noise and overly fine ornamental texture according to the selected printer profile.
8. Synthesize stepped relief levels (proposed FDM default: 6) or continuous relief if selected.
9. Show the resulting machine height map and a relief preview.
10. Run paper-risk/printability analysis.
11. Generate only after the user confirms or overrides warnings.

The more visually simplified the source image is, the more faithfully this deterministic conversion can work. Extremely ornate photorealistic renders may benefit from an agent-authored height map instead.

---

## 9. Agent-assisted conversion

EmbossForge should provide a repository skill for image-capable LLM agents:

`skills/embossforge-design/SKILL.md`

The preferred agent workflow is:

```text
user request / shaded reference
          |
          v
LLM image/design agent
          |
          +--> machine height map (no lighting)
          +--> optional pretty preview render
          |
          v
EmbossForge relief backend
```

A pretty metallic preview should never be the only machine artifact when the agent is capable of producing a true height map.

---

## 10. Proposed API / CLI fields

These are additive future fields and must not break existing calls.

```text
source_interpretation = flat-artwork | height-map | shaded-reference
```

Proposed CLI flag:

```text
--source flat|heightmap|shaded
```

Examples:

```powershell
# Current-style image
embossforge die logo.png --source flat

# Explicit machine-authored height map
embossforge die seal_heightmap.png --mode relief --source heightmap

# Shaded AI/rendered medallion
embossforge die medallion.png --mode relief --source shaded
```

If `--source` is omitted, compatibility behavior remains current/default. Detection may print a suggestion but must not silently alter semantics.

---

## 11. Manifest additions

Schema v2 relief manifests should record source interpretation and any conversion step:

```json
{
  "artwork_processing": {
    "source_interpretation": "shaded-reference",
    "interpretation_source": "user-confirmed",
    "derived_heightmap": "medallion_heightmap.png",
    "conversion": {
      "method": "deterministic-shaded-reference-v1",
      "auto_simplify": true,
      "detail_filter_mm": 0.5,
      "lighting_normalization": true
    }
  }
}
```

If an external agent created the height map, the manifest may record that it was supplied as an authored height map; EmbossForge should not invent model/provider provenance it cannot verify.

---

## 12. Detection is never authority

Image classification is heuristic.

Possible signals include:

- number/distribution of gray levels;
- broad smooth luminance gradients;
- highlight/shadow pairs around edges;
- near-white uniform background;
- repeated bevel-like gradients;
- fine texture spectrum;
- alpha/background structure.

These signals may justify a recommendation such as `likely shaded-reference`, but the user or API caller selects the interpretation.

---

## 13. Compatibility requirements

- Existing binary PNG/SVG behavior remains unchanged by default.
- Existing CLI commands remain valid.
- A true height map is never silently run through shaded-reference flattening.
- A shaded render is never silently treated as literal height.
- UI, CLI, and Python API use the same source-interpretation enum and conversion backend.
- Derived height maps are saved so the conversion can be inspected and reproduced.
- Paper-risk overrides remain explicit and auditable.
- No rendered-reference conversion may be described as recovering the object's "true depth" from one image.

This document is the canonical source-interpretation extension to `RELIEF_MODE_SPEC.md`.