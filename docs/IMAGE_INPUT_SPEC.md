# Image input interpretation specification

**Status:** Implemented in EmbossForge 0.2. Physical validation of variable-depth output is still pending.

The key rule is:

> **An image that looks three-dimensional is not automatically a height map.**

Metallic medallion renders, AI-generated bas-relief previews, bevelled logos, and photographs contain lighting as well as shape. Raw luminance therefore must not be silently interpreted as literal Z.

## Independent concepts

Geometry mode:

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

`DieGenerationRequest` carries both concepts. The desktop, CLI, and Python service share the same enums and backend.

## Flat artwork

`flat-artwork + binary` is the backward-compatible default for ordinary SVGs, logos, silhouettes, line art, monograms, and high-contrast raster artwork.

With a printer profile selected, raster artwork is canonicalized against printer positive/negative feature limits before either die is derived.

## True height maps

Use `height-map` only when grayscale was deliberately authored as physical relief. Default convention:

```text
white = zero relief
black = maximum relief
```

The polarity is reversible. A proper machine height map should be front-on, have a known zero background, and avoid decorative highlights, shadows, metallic shading, or perspective.

## Shaded / 3D-looking references

Use `shaded-reference` for rendered or photographic material whose tones include illumination.

EmbossForge implements `deterministic-shaded-reference-v1`. Its purpose is not single-image 3D reconstruction. It creates an emboss-oriented relief interpretation whose major motif structure is stable and whose machine input is explicit and inspectable.

The converter performs:

1. background estimation from alpha or border statistics;
2. motif segmentation;
3. preservation of enclosed motif regions across bright/specular highlights for opaque renders;
4. printer-aware mask cleanup;
5. broad illumination suppression;
6. structural analysis from motif distance, local contrast, and stable edges;
7. emboss relief synthesis;
8. export of a derived machine height map, a visual relief preview, and a foreground mask;
9. the same shared height-map quantization/filtering, female derivation, and validation as authored height maps.

The manifest records:

- method `deterministic-shaded-reference-v1`;
- the derived artifact paths;
- sampling/background statistics;
- the explicit claim `interpreted emboss relief; not reconstructed true 3D depth`.

## Desktop confirmation

The desktop never silently changes semantics. Continuous shading may trigger an advisory recommendation, but the user chooses the interpretation.

For a shaded reference, the desktop first generates the derived map with STL rendering disabled, validates it, displays the relief preview, and changes the primary action to **Accept preview & generate STLs**. Changing settings invalidates that acceptance and regenerates the preview.

True height maps do not go through shaded-reference flattening.

## CLI/API behavior

Examples:

```powershell
# ordinary flat artwork
embossforge die logo.png --paper copy

# authored machine height map
embossforge die seal_heightmap.png --mode relief --source-interpretation height-map --relief-max 0.35

# rendered/AI medallion
embossforge die medallion.png --mode relief --source-interpretation shaded-reference --relief-max 0.35
```

API callers use `ArtworkMode.RELIEF` plus either `SourceInterpretation.HEIGHT_MAP` or `SourceInterpretation.SHADED_REFERENCE`.

The CLI cannot visually approve an intermediate image, so headless automation should inspect the preserved derived preview or enforce its own review policy.

## Detail density

Ornate artwork is accepted rather than arbitrarily rejected, but features still have to survive the target physical scale. Printer-aware filtering, structured findings, and paper-risk heuristics may report that detail will merge/disappear or that steep/isolated relief may be aggressive for paper.

Warnings are preferable to silent geometry divergence. Hard mating/geometry errors remain non-overridable.

## Agent-authored maps

For especially ornate shaded references, an image-capable design agent may produce a better unlit machine height map plus a separate pretty preview. See `skills/embossforge-design/SKILL.md`.

When such a true map is supplied, use `height-map`; do not run it through shaded-reference interpretation. EmbossForge does not invent model/provider provenance it cannot verify.

## Detection is advisory only

`looks_continuously_shaded()` uses grayscale-distribution signals only to improve desktop guidance. It never changes `source_interpretation` automatically.

## Compatibility requirements

- binary behavior remains the default;
- existing binary commands remain valid;
- true height maps are never silently flattened as shaded references;
- shaded references are never silently treated as literal height;
- derived shaded-reference maps are preserved for inspection/reproduction;
- source semantics and risk overrides are recorded in schema-v2 manifests;
- no shaded-reference conversion is described as recovering true depth from one image.

This document is the source-interpretation contract for [RELIEF_MODE_SPEC.md](RELIEF_MODE_SPEC.md).
