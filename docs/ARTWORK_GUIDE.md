# Artwork guide

EmbossForge accepts SVG directly and can vectorize common raster formats such as PNG and JPG. The generator then creates matched male/female geometry with configurable clearance and cavity depth.

## Best input format

Prefer SVG whenever possible. A clean vector logo or silhouette gives the most predictable result.

Raster input works best when it is:

- high contrast
- dark artwork on a light background
- free of photographic texture
- large enough that edges are not pixelated
- simple enough to survive the target nozzle width

Use `--invert` when the foreground is light and the background is dark.

## Design for embossing, not just for the screen

An image can look excellent on a monitor and still be a poor embossing design. Very thin lines, tiny islands, narrow gaps, and delicate serif details may merge or disappear when printed.

For the current FlashForge Adventurer 5M / 0.4 mm development profile, treat roughly 0.5 mm as a conservative minimum feature width until calibration proves otherwise. Fine details may improve with a 0.25 mm nozzle.

## SVG coordinate handling

EmbossForge canonicalizes non-zero and negative SVG `viewBox` origins before OpenSCAD import. This avoids a class of failures where the imported artwork is shifted and circular clipping leaves only a small sliver of the design.

If an SVG still renders incorrectly, reduce it to a minimal file and open an issue with:

- the original artwork
- the generated normalized SVG
- the generated SCAD file
- a screenshot of the slicer preview

## Raster conversion

Raster artwork is thresholded and traced into filled vector contours. Useful controls:

```text
--threshold 160
--invert
```

Lower/higher thresholds change which pixels are treated as foreground. The current raster tracer is intentionally simple and is expected to improve before 1.0.

## Orientation

The current circular die carrier has a hidden orientation tab. Male and female geometry are generated to account for the upper die being installed flipped relative to the lower die. Do not independently rotate one generated insert unless you also understand and compensate for that transform.

## Before spending filament

Always inspect the slicer preview. The silhouette or lettering should be clearly recognizable before printing. For a new artwork pipeline change, use a small die first rather than immediately generating the full 42 mm production-size insert.
