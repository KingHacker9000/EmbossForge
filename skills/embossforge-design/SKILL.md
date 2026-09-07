---
name: embossforge-design
description: Create manufacturable artwork and true grayscale height maps for EmbossForge paper-embosser dies. Use when an agent is asked to design, simplify, convert, or regenerate artwork for EmbossForge, especially butterfly/floral seals, monograms, logos, bookplates, decorative rings, and variable-depth relief.
---

# EmbossForge artwork design skill

Use this skill when creating or converting artwork that will become a physical EmbossForge die.

The goal is **not** to make the prettiest on-screen render. The goal is to make artwork whose geometry survives conversion into a matched male/female 3D-printed embossing pair at the requested physical size.

Read these repository contracts when available:

- `docs/ARTWORK_GUIDE.md`
- `docs/RELIEF_MODE_SPEC.md`
- `docs/IMAGE_INPUT_SPEC.md`
- `docs/MATING_VALIDATION_SPEC.md`
- `AGENTS.md`

---

## 1. Ask or infer the physical target

Important inputs:

- die diameter in mm;
- printer/profile;
- nozzle diameter;
- paper type/thickness;
- desired mode: simple binary emboss or variable-depth relief;
- desired motif/text;
- whether the user wants a decorative preview render in addition to machine artwork.

If exact values are unavailable, use repository defaults only as provisional assumptions and state them in the result metadata/prompt notes.

Do not design only in pixels. Always reason about the final physical die size.

---

## 2. Preferred deliverables

When the user wants variable-depth relief, produce **two distinct visual artifacts when possible**:

```text
<name>_heightmap.png   # machine input
<name>_preview.png     # optional pretty visualization
```

The machine height map is authoritative.

The preview may use metallic shading, highlights, shadows, perspective, or presentation effects, but **none of those visual effects may leak into the machine height map**.

If only one image can be produced, prioritize the machine height map.

For simple binary embossing, a clean SVG is preferred when the agent can create vector output.

---

## 3. EmbossForge height-map convention

Default polarity:

```text
white = zero relief / die surface
black = maximum requested relief
```

This is EmbossForge `dark-high` convention.

Intermediate gray values represent intermediate physical height.

Example normalized tiers:

```text
255  white       0% relief
220  very light  ~15% relief
180  light       ~30% relief
135  medium      ~50% relief
90   dark        ~65% relief
45   very dark   ~82% relief
0    black       100% relief
```

These are design examples, not required exact quantization values. EmbossForge may later quantize the map according to printer/profile settings.

Never add decorative shading to a machine height map.

---

## 4. Machine height maps must be unlit

A good machine height map is:

- orthographic / front-on;
- square or otherwise explicitly framed;
- flatly encoded grayscale;
- free of directional lighting;
- free of cast shadows;
- free of drop shadows;
- free of metallic reflections;
- free of specular highlights;
- free of ambient-occlusion shading unless that tone is intentional geometry;
- free of perspective;
- free of depth-of-field blur;
- free of decorative vignettes.

Bad machine-map prompt language:

```text
silver coin
metallic
studio lighting
realistic shadows
engraved chrome
dramatic highlights
photorealistic medallion
```

Those are appropriate only for the optional preview image.

Preferred machine-map language:

```text
orthographic grayscale displacement map
no lighting
no shadows
no material rendering
white background = zero height
black = maximum relief
broad smooth geometric height regions
machine-readable height field
```

---

## 5. Design at physical scale

Use the target die diameter to judge every feature.

For the current FlashForge Adventurer 5M / 0.4 mm prototype profile, the repository currently uses approximately:

```text
minimum feature: 0.50 mm
minimum gap:     0.45 mm
```

Treat those as current profile guidance, not universal laws or guaranteed paper-safety values.

Prefer major ridges, outlines, stems, text strokes, and ring walls to be comfortably above the absolute minimum when possible.

Useful conversion:

```text
pixels_per_mm = image_width_px / die_diameter_mm
required_pixels = physical_feature_mm * pixels_per_mm
```

Example: for a 1024 px image intended for a 42 mm die,

```text
1024 / 42 ~= 24.4 px/mm
0.50 mm ~= 12 px
```

A 2-3 px decorative line may look elegant on screen and disappear completely on the printed die.

### Paired positive/negative printability

EmbossForge does not print a design only once: the same motif must survive as a **positive feature on one die and a matching negative accommodation on the other**.

A thin line can be especially dangerous because a slicer may retain it as a single extrusion on the male while deleting the matching female groove as an unprintably narrow negative gap. That creates a die pair that cannot close.

When designing artwork:

- do not judge only whether a positive stroke can print;
- keep intended matching grooves/counters wide enough to survive the selected profile's negative-feature limit;
- avoid tiny counters and narrow channels that may close on one side;
- prefer broad ridges and generous clearances over hairlines;
- if a detail is below resolution, simplify/remove it rather than relying on asymmetric slicer behavior.

The canonical requirement is in `docs/MATING_VALIDATION_SPEC.md`. Final generation must validate predicted male/female closure after printer-aware canonicalization.

---

## 6. Composition rules for circular seals

For round dies:

- keep important geometry inside roughly the inner 85-90% of the diameter unless a deliberate border uses the outer region;
- maintain a clean physical margin between artwork and carrier edge;
- use strong radial hierarchy;
- keep the central motif readable at thumbnail size;
- prefer one or two dominant focal elements over uniform micro-detail everywhere;
- make borders broad enough to print cleanly;
- avoid extremely dense bead chains unless bead diameter and spacing survive the target nozzle;
- keep fine stems/antennae thicker than screen-only artwork would normally use.

For butterfly/floral/monogram seals, a robust hierarchy is:

```text
outer structural ring          strong/high
main butterfly outline/body    strong/high
large wing cells               medium-high
large flowers / leaves         medium-high
secondary scrollwork           medium
background ornament            shallow
fine texture                    very shallow or omitted
monogram                        strong and broad
```

This produces visual depth without requiring every detail to reach maximum relief.

---

## 7. Variable-depth design rules

Prefer a small number of meaningful relief bands rather than random grayscale noise.

Good relief variation:

- strong outer ring;
- slightly lower inner ring;
- medium flower petals;
- broad butterfly wing cells at several levels;
- shallow background damask;
- a raised monogram;
- gentle broad ramps on large leaves/petals.

Avoid:

- one-pixel height changes;
- isolated black specks;
- narrow maximum-height ridges;
- dense deep stipple;
- abrupt black/white zigzags at sub-nozzle scale;
- tiny bead chains packed edge-to-edge;
- relief encoded only by simulated light and shadow.

For FDM-oriented artwork, broad stepped levels are usually easier to reproduce than subtle photorealistic shading.

---

## 8. Paper-friendly geometry guidance

EmbossForge performs its own validation, and physical paper behavior is not fully predictable from artwork alone. Still, design agents should avoid needlessly aggressive geometry.

Prefer:

- rounded transitions;
- broad ridges;
- gradual ramps on large features;
- sufficient spacing between tall neighboring features;
- shallow microtexture;
- consistent border widths.

Be cautious with:

- needle-like peaks;
- knife-edge ridges;
- narrow maximum-height outlines;
- extremely steep local height jumps;
- deep texture covering most of the die;
- high relief directly adjacent to another opposing high relief region.

Do not claim that a design is guaranteed not to tear paper.

---

## 9. Text and monograms

Text must be designed as physical geometry.

Prefer:

- bold serif or sturdy display serif;
- generous counters;
- thick stems;
- simplified terminals;
- clear spacing around nearby ornament.

Avoid:

- hairline serifs;
- very thin script;
- microscopic counters;
- outlines whose stroke width is below printer guidance.

For an initial such as `M`, the character should remain recognizable after a strong blur/downsample test.

---

## 10. Converting a shaded reference image

If the user provides a metallic/shaded bas-relief image, **do not simply desaturate it and call it a height map**.

Instead:

1. identify major semantic/visual regions;
2. ignore specular highlights and cast shadows;
3. reconstruct the intended motif as broad height regions;
4. simplify details below printer resolution;
5. preserve text, rings, major petals, leaves, wing cells, and silhouette;
6. assign deliberate grayscale heights;
7. output a clean machine height map;
8. optionally create a separate shaded preview from that height map.

When exact 3D depth cannot be inferred, choose a clean, manufacturable interpretation rather than pretending to recover true geometry.

---

## 11. Complexity reduction

If a reference is too ornate for the target printer, simplify in this order:

1. remove background microtexture;
2. merge tiny repeated dots/beads;
3. thicken fine stems and antennae;
4. enlarge narrow gaps;
5. simplify tiny petal/leaf vein detail;
6. reduce number of relief tiers;
7. preserve silhouette, monogram, major flowers, major rings, and wing structure last.

The user should recognize the design even if the finest decoration is removed.

---

## 12. Self-check before returning artwork

Verify:

- [ ] machine map is orthographic;
- [ ] no lighting/shadows/specular effects appear in the machine map;
- [ ] background value is unambiguous;
- [ ] polarity is stated;
- [ ] major features fit within the intended die boundary;
- [ ] fine positive features are physically plausible for the stated nozzle/profile;
- [ ] corresponding negative spaces/grooves are also physically plausible for the stated profile;
- [ ] no detail depends on a slicer preserving one side while erasing its mate;
- [ ] text remains readable at small size;
- [ ] no accidental isolated high pixels exist;
- [ ] gradients are geometric, not decorative lighting;
- [ ] optional preview is clearly separate from machine height data;
- [ ] no claim of paper safety is made without physical validation.

---

## 13. Recommended prompt template for image-generation agents

Adapt this template to the user's requested motif:

> Create a **machine-readable orthographic grayscale height map** for a circular 3D-printed paper embosser die. Final die diameter: **{DIE_MM} mm**. Target nozzle: **{NOZZLE_MM} mm**. White is **zero relief** and black is **maximum relief**. Use broad, deliberate grayscale height regions only. **No lighting, no cast shadows, no metallic rendering, no highlights, no perspective, no ambient-occlusion shading, and no decorative background gradients.** Keep all important details physically large enough for the target nozzle, including both positive strokes and the matching negative spaces that must exist on the opposing die. Use a strong outer ring, readable central motif, sturdy text/monogram, and shallow secondary ornament. Smooth dangerous needle-like peaks and avoid hairline ridges. Output only the height map on a clean white background.

Example motif addition:

> Center a symmetrical butterfly with broad wing cells. Add simplified roses and leaves around the lower sides and a large serif `M` near the bottom. Keep the butterfly silhouette dominant. Use approximately 5-6 meaningful height tiers: outer ring strongest, butterfly outline/body strong, wing cells and roses medium-high, leaves medium, background ornament shallow.

For a separate visual preview, make a second image from the same geometry and explicitly label it as a preview; metallic lighting is allowed only there.

---

## 14. Output notes for agents

When returning files or instructions, state:

```text
intended EmbossForge mode: relief
source interpretation: height-map
polarity: dark-high
intended die diameter: <mm>
target nozzle/profile: <value>
```

If the output is only a visual reference rather than a true height map, state:

```text
source interpretation: shaded-reference
```

Never mislabel a shaded render as a machine height map.