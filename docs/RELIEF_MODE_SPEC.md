# Variable-depth grayscale relief specification

**Status:** Accepted design specification for a future EmbossForge vNext implementation. This document defines behavior and compatibility requirements; it does **not** mean grayscale relief is implemented in the current release.

EmbossForge currently treats artwork as binary geometry: a point is either embossed at one fixed relief height or left at the die surface. A 3D printer can do more than that. This specification extends the system with a variable-depth **relief mode** where grayscale tone can control emboss height/depth while keeping the existing binary workflow unchanged.

The intended result is that a user can create effects such as a strong outer ring, a softer inner ring, layered crests, shallow textures, or continuously varying relief without manually modeling a 3D surface.

---

## 1. Goals

The first grayscale-relief implementation must:

1. map grayscale artwork to a deterministic 2D height field;
2. generate a matched male/female die pair from that field;
3. preserve the existing binary generator and its defaults;
4. expose simple controls in the desktop app while keeping advanced controls optional;
5. warn about printability and paper-damage risk without unnecessarily blocking expert users;
6. record every relief and validation decision in the manifest;
7. keep CLI, desktop, and Python API behavior on the same shared backend;
8. remain printer/profile aware;
9. be reproducible from source artwork + manifest;
10. leave room for generated rings, textures, and composited relief layers later.

## 2. Non-goals for the first implementation

The first implementation does not need to:

- simulate paper with finite-element analysis;
- guarantee that a design cannot tear paper;
- infer exact material properties from GSM alone;
- replace a slicer;
- create arbitrary sculptural bas-relief from a photograph using AI;
- make Blender the geometry source of truth;
- change the existing mechanical cartridge standard.

Safety analysis is intentionally heuristic and warning-oriented until more physical calibration data exists.

---

## 3. Backward-compatibility contract

This feature must be additive.

### Existing behavior that must remain unchanged

- `embossforge die artwork.svg` remains binary by default.
- Existing SVG/raster binary preprocessing remains available.
- Existing `DieSpec.relief_height_mm` semantics remain valid in binary mode.
- Existing paper presets, printer profiles, key orientation, and female X-mirror behavior remain valid.
- Existing output names remain valid.
- Existing callers of `generate_die()` that do not request relief mode must generate equivalent binary geometry.
- Existing manifests without `schema_version` are treated as schema v1.

### New behavior is opt-in

A design enters grayscale relief mode only when the user explicitly selects it in the UI/API/CLI. The application may *suggest* relief mode when it detects meaningful grayscale variation, but it must not silently switch modes.

---

## 4. Terminology

**Binary mode**  
Current EmbossForge behavior. Artwork is converted to a foreground mask and extruded at one constant height.

**Relief mode**  
Artwork tone is converted to a variable height field.

**Height map**  
A normalized scalar field `R(x, y)` in the range `[0, 1]` representing requested local emboss intensity.

**Male relief**  
The positive surface displacement on the male die.

**Female cavity**  
The corresponding recessed surface on the female die, expanded/offset to accommodate paper and printer clearance.

**Paper-risk warning**  
An advisory about likely tearing, puncturing, excessive strain, or poor emboss quality. It may be overridden.

**Geometry error**  
An invalid or impossible model, such as a cavity breaking through the die base. Geometry errors are not overrideable.

---

## 5. Artwork modes

The shared generation request gains an explicit artwork mode:

```text
binary
relief
```

`binary` remains the default.

### 5.1 Binary mode

No semantic change. The current threshold/vector/extrude path stays intact.

### 5.2 Relief mode

Relief mode renders the source artwork to an internal grayscale height map before 3D geometry generation.

Supported source classes should remain the same as the desktop app accepts today:

- SVG
- PNG
- JPG/JPEG
- WEBP
- BMP
- TIFF

SVG relief mode must render fills, strokes, opacity, and gradients into the intermediate grayscale field rather than relying on OpenSCAD's color-insensitive SVG import.

Transparent pixels are treated as zero relief unless a future explicit background option says otherwise.

---

## 6. Tone-to-height mapping

Let rendered grayscale luminance be `L(x, y)` in `[0, 1]`, where `0` is black and `1` is white.

The default polarity preserves the current user expectation that dark artwork is the active design:

```text
R0(x, y) = 1 - L(x, y)
```

An explicit polarity control allows:

```text
dark-high   # default
light-high
```

### 6.1 Gamma

Tone response may be adjusted before quantization:

```text
R1 = clamp(R0, 0, 1) ** gamma
```

Default `gamma = 1.0`.

Gamma is a design control, not a color-management promise.

### 6.2 Dead zone / background suppression

Very light compression artifacts should not automatically create microscopic relief. A configurable zero threshold may suppress values near zero:

```text
if R1 < zero_threshold:
    R1 = 0
```

The desktop default should be conservative and visually explained. Lossless SVG/PNG artwork may use zero or near-zero suppression.

### 6.3 Continuous and stepped relief

Two depth styles are defined:

```text
continuous
stepped
```

For stepped mode with `N >= 2` levels:

```text
R = round(R1 * (N - 1)) / (N - 1)
```

The proposed first FDM-friendly UI default for relief mode is **stepped, 6 levels**, while continuous remains available. This is a workflow default, not a claim that six levels is optimal for every printer.

### 6.4 Physical height

The male displacement field is:

```text
Hmale(x, y) = R(x, y) * max_relief_mm
```

A future optional `minimum_active_relief_mm` may lift nonzero regions, but the first implementation should keep the mapping simple unless physical tests demonstrate a need.

`max_relief_mm` is separate from the existing binary `relief_height_mm` at the API level, even if the UI initially seeds it from the same profile/default value.

---

## 7. Sampling and resolution

Relief mode requires an intermediate raster representation even when the input is SVG.

The sampling resolution must be derived from physical die size and printer/profile resolution, not from an arbitrary fixed pixel count.

The internal sampler should target multiple samples across the smallest printer-resolvable feature. The exact factor belongs to implementation/profile policy, but must be deterministic and stored in the manifest.

The pipeline must avoid generating meshes so dense that ordinary desktop generation becomes impractical. Downsampling is acceptable when the requested source resolution exceeds useful printer resolution.

---

## 8. Relief compositing model

The architecture should treat the final relief as a composed height field, even if the first release only exposes artwork relief.

Conceptually:

```text
artwork relief
    + optional structural profile
    + optional texture layer
              |
              v
      composition policy
              |
              v
      final clamped relief
```

The first implementation may support only the artwork layer while reserving manifest/API structure for additional layers.

### Planned structural profile layers

Examples:

- outer ring with stronger relief;
- inner ring with softer relief;
- center plateau;
- radial falloff;
- border bevel.

### Planned texture layers

Examples:

- stipple;
- linen-like texture;
- radial rays;
- crosshatch;
- user-supplied grayscale texture map.

Default future composition should be explicit rather than magical. Candidate modes are `max`, `add + clamp`, and `replace/mask`. No implementation should silently change relief amplitude when layers are added.

---

## 9. Matched male/female geometry

The matched pair must continue to originate from one source field and one orientation transform.

### 9.1 Male

The male die surface is the carrier/base plus `Hmale(x, y)`.

### 9.2 Female

The female die must remain more permissive than an exact negative.

The current binary system uses:

- X/Y artwork clearance;
- paper thickness;
- extra cavity depth;
- X mirror for the flipped upper cartridge.

Relief mode preserves those concepts.

A first implementation may define the female cavity field using a printer-aware lateral expansion of the male height map followed by vertical accommodation:

```text
Hexpanded = local_max_or_morphological_dilation(Hmale, radius = female_xy_clearance_mm)
Hfemale_cavity = Hexpanded + paper_thickness_mm + female_extra_depth_mm
```

The vertical allowance applies only inside the active/dilated relief region, not across the entire die face.

The female field is mirrored/oriented using the same established cartridge transform as binary mode.

This dilation-based approach is intentionally practical for v1. A later implementation may use true 3D/normal offsets if testing proves they materially improve paper behavior on steep surfaces.

### 9.3 Base breakthrough remains a hard error

The deepest female cavity must remain strictly shallower than the printable female base. A relief request that breaks through the die base is invalid and must not be bypassed by a paper-risk override.

---

## 10. Validation model

Validation is split into **hard geometry errors** and **overridable risk warnings**.

### 10.1 Hard geometry errors

These prevent generation and cannot be bypassed:

- invalid/empty artwork;
- NaN/infinite height values;
- zero/negative physical dimensions;
- female cavity breaks through the base;
- carrier exceeds printer build volume;
- malformed relief settings;
- impossible layer/step count;
- mesh generation failure/non-manifold output when the backend requires manifold solids.

### 10.2 Printability warnings

These are advisory and may be overridden:

- features narrower than printer-profile `min_feature_mm`;
- gaps below printer-profile `min_gap_mm`;
- relief changes smaller than useful Z resolution;
- excessive mesh detail relative to nozzle/layer resolution;
- small isolated islands/spikes likely to print poorly.

### 10.3 Paper-risk warnings

These are advisory and may be overridden:

- unusually large maximum relief for the selected paper/profile;
- abrupt local height change / steep slope;
- narrow tall ridges that behave like cutting edges;
- tiny isolated high peaks that may puncture paper;
- dense deep texture;
- excessive curvature / rapid direction changes;
- high relief very near the design boundary;
- female clearance unusually small for selected paper thickness.

These warnings do **not** claim to predict tearing with certainty.

### 10.4 Loose, profile-driven thresholds

Paper-risk thresholds belong in material/printer calibration policy rather than being universal constants in geometry code.

Until enough physical test data exists:

- thresholds should be deliberately permissive;
- warnings should say `experimental heuristic`;
- the app must not claim a design is "safe" merely because no warning fired;
- physical validation data should be used to tune profiles over time.

Existing printer values such as `min_feature_mm`, `min_gap_mm`, and recommended clearance are appropriate sources for printability checks.

Future paper/profile fields may include advisory values such as:

```text
recommended_max_relief_mm
recommended_max_local_slope
recommended_min_ridge_width_mm
recommended_texture_pitch_mm
```

They may be `null`/unknown until calibrated.

---

## 11. Risk report contract

Every relief generation should produce a structured validation report, embedded in the main manifest and optionally emitted as a separate JSON file for tooling.

Each finding should have at least:

```json
{
  "code": "paper.narrow_high_ridge",
  "severity": "caution",
  "overridable": true,
  "metric": 0.42,
  "threshold": 0.50,
  "units": "mm",
  "message": "A narrow raised ridge may crease or cut thin paper.",
  "recommendation": "Widen the ridge, reduce relief, or continue intentionally."
}
```

Severity vocabulary:

```text
info
caution
high
error
```

`error` is reserved for non-overrideable invalid geometry. `high` is still overrideable when it represents paper/quality risk rather than impossible geometry.

---

## 12. User override behavior

Users must be allowed to generate intentionally aggressive tooling.

### Desktop

If only `info/caution` findings exist, generation may proceed with visible warnings.

If one or more `high` overridable findings exist, the Generate action opens a concise confirmation step:

> This design has a high paper-damage risk according to experimental heuristics. You can reduce relief/change the artwork, or generate it anyway.

Actions:

```text
Go back and adjust
Generate anyway
```

Do not bury the override behind developer settings.

### CLI

Proposed flag:

```text
--allow-risky
```

Without it, high-risk findings return a nonzero exit before final STL generation while still writing/printing the diagnostic report when practical.

Caution-level findings do not require the flag.

### Manifest

Record:

```json
"validation": {
  "highest_severity": "high",
  "override_used": true,
  "findings": []
}
```

This makes intentionally risky output auditable and reproducible.

---

## 13. Desktop UX specification

Relief mode must fit the simplified guided desktop workflow rather than reintroducing a dense CAD control panel.

### Artwork step

After artwork is loaded, show an **Emboss style** choice:

```text
Simple emboss      # binary, default
Variable depth     # grayscale relief
```

If the app detects multiple meaningful grayscale tones it may show a small suggestion:

> This artwork contains multiple tones. Variable depth can use them as emboss heights.

Do not auto-switch.

### Variable-depth controls

Keep the primary controls compact:

- Maximum relief
- Depth style: Stepped / Continuous
- Levels (only when Stepped)
- Tone direction: Darker = deeper / Lighter = deeper

A single **More relief controls** disclosure may expose:

- gamma;
- zero threshold;
- smoothing;
- sampling/quality preset;
- future composition/profile options.

### Preview

The artwork preview should gain a relief visualization when variable depth is selected:

- preserve the original artwork preview;
- add a clear depth legend from `0` to `max_relief_mm`;
- optionally use a false-color or shaded-relief preview instead of relying only on raw grayscale;
- clearly distinguish zero-relief background from shallow relief.

A future true 3D preview is desirable but not required for the first implementation.

### Validation panel

Warnings should appear near Generate, summarized in plain language:

```text
2 cautions
• Fine texture may not resolve with a 0.4 mm nozzle.
• One steep ridge may crease thin paper.

Review details
```

Do not expose raw derivative/curvature terminology unless the user expands technical details.

---

## 14. CLI specification

Existing commands remain valid.

Proposed relief usage:

```powershell
embossforge die crest.png \
  --mode relief \
  --relief-max 0.80 \
  --relief-style stepped \
  --relief-levels 6 \
  --relief-gamma 1.0 \
  --relief-polarity dark-high \
  --paper copy
```

Continuous example:

```powershell
embossforge die texture.png --mode relief --relief-style continuous --relief-max 0.60
```

Risk override:

```powershell
embossforge die aggressive.png --mode relief --allow-risky
```

Proposed flags:

```text
--mode binary|relief
--relief-max <mm>
--relief-style stepped|continuous
--relief-levels <int>
--relief-gamma <float>
--relief-polarity dark-high|light-high
--relief-zero-threshold <0..1>
--allow-risky
```

Do not repurpose current flags in a way that changes existing binary command semantics.

---

## 15. Python API specification

The current `DieGenerationRequest` remains the entry point.

Additive request shape (illustrative):

```python
from embossforge.relief import ReliefSpec

request = DieGenerationRequest(
    artwork=Path("crest.png"),
    output_root=Path("build"),
    diameter_mm=42,
    paper_preset="copy",
    printer_profile=profile,
    artwork_mode="relief",
    relief=ReliefSpec(
        max_relief_mm=0.8,
        style="stepped",
        levels=6,
        gamma=1.0,
        polarity="dark-high",
    ),
    allow_risky=False,
)
```

Binary callers that omit `artwork_mode` and `relief` must continue to work unchanged.

Suggested new internal value objects:

```text
ReliefSpec
HeightMap
ValidationFinding
ValidationReport
```

UI and CLI must construct these objects and call the shared generator. They must not implement independent relief formulas.

---

## 16. Manifest schema v2

Current manifests have no explicit schema version. Readers should treat a missing value as v1.

New generators should add:

```json
"schema_version": 2
```

The following existing top-level keys must remain present for compatibility:

```text
name
artwork
spec
derived
orientation
outputs
```

New top-level sections:

```json
{
  "schema_version": 2,
  "artwork_processing": {},
  "relief": {},
  "validation": {}
}
```

### Example relief manifest fragment

```json
{
  "schema_version": 2,
  "relief": {
    "mode": "relief",
    "style": "stepped",
    "levels": 6,
    "max_relief_mm": 0.8,
    "gamma": 1.0,
    "polarity": "dark-high",
    "zero_threshold": 0.02,
    "sampling": {
      "width_px": 512,
      "height_px": 512,
      "mm_per_sample": 0.0703
    }
  },
  "validation": {
    "highest_severity": "caution",
    "override_used": false,
    "heuristic_version": 1,
    "findings": []
  }
}
```

For binary mode, schema v2 may still include:

```json
"relief": { "mode": "binary" }
```

while preserving the existing `spec.relief_height_mm` behavior.

---

## 17. Relief-mode output artifacts

Binary output names stay unchanged.

Relief mode should additionally preserve the processed height field so generation is inspectable:

```text
<name>_heightmap.png
<name>_relief_preview.png        # optional but recommended
<name>_validation.json           # optional separate copy; manifest remains canonical
```

The height-map artifact must use a documented mapping so reopening it does not depend on display color management. If 8-bit precision proves insufficient for smooth continuous relief, the implementation may use 16-bit grayscale while keeping preview images ordinary 8-bit assets.

STL/SCAD output naming remains:

```text
<name>_male.stl
<name>_female.stl
<name>_male.scad
<name>_female.scad
<name>_manifest.json
```

If OpenSCAD cannot represent the relief surface efficiently enough, the backend may add a new deterministic mesh/CAD implementation. That does not change the user-facing contract, and OpenSCAD remains supported for binary mode.

---

## 18. Backend architecture

Do not force variable-depth logic into the current binary SVG extrusion functions.

Recommended architecture:

```text
artwork input
   |
   +--> binary processor ------> binary relief backend ----+
   |                                                    |
   +--> relief renderer -------> height-map backend -----+--> matched-pair assembly/export
                                    |
                                    +--> validation
```

Suggested modules/names are flexible, but responsibilities should remain separated:

```text
embossforge/artwork.py                 existing binary/common input work
embossforge/relief.py                  ReliefSpec + mapping/composition
embossforge/heightmap.py               sampling/height-field representation
embossforge/relief_backend.py          variable-height solid generation
embossforge/validation.py              printability + paper-risk findings
embossforge/generator.py               orchestration/shared public service
```

The exact file split may change during implementation; the separation of concerns is the invariant.

---

## 19. Testing contract

Before relief mode is considered implemented, tests must cover at least:

### Backward compatibility

- existing binary tests remain green;
- default request still selects binary mode;
- known binary smoke artifact remains dimensionally equivalent within current tolerances;
- v1 manifests remain readable by any new manifest reader.

### Tone mapping

- black -> max relief in `dark-high`;
- white -> zero relief in `dark-high`;
- polarity inversion;
- gamma mapping;
- stepped quantization count;
- transparent background -> zero relief;
- deterministic SVG gradient rendering.

### Geometry

- male max height matches requested max relief;
- female uses the same field + configured accommodations;
- female orientation/mirror remains correct;
- no cavity outside active/dilated region;
- base breakthrough is rejected;
- generated solids are non-empty/manifold according to backend guarantees.

### Validation

- narrow feature warning;
- high local slope warning;
- high-risk findings require override in CLI/UI flow;
- `--allow-risky` records override in manifest;
- hard geometry errors cannot be overridden.

### UI/API

- binary is the default mode;
- relief controls only appear when requested;
- CLI and UI requests produce equivalent `ReliefSpec` values;
- manifest contains relief/validation metadata.

---

## 20. Physical validation plan

Relief mode should not be advertised as physically validated merely because the software tests pass.

Suggested staged experiments once filament is available:

1. **Stepped-depth coupon** — several large regions at known depths on one tiny die.
2. **Gradient/ring coupon** — outer ring at high relief, inner ring at medium relief, center at shallow relief.
3. **Slope coupon** — same total depth reached through several transition widths.
4. **Texture coupon** — coarse-to-fine texture pitch and amplitude matrix.
5. **Paper matrix** — copy paper, premium paper, and cardstock presets.
6. Record visible emboss quality, tearing, puncture, buckling, and required force in `docs/PHYSICAL_VALIDATION.md`.

Only observed results belong in physical-validation documentation. Do not convert heuristic thresholds into safety claims.

---

## 21. Rollout plan

### Phase A — data model + compatibility

- add `artwork_mode` and `ReliefSpec`;
- add manifest schema v2 writer/reader behavior;
- keep binary output unchanged;
- add validation-report data model.

**Acceptance:** all existing tests green and new binary manifests remain backward-compatible.

### Phase B — grayscale height-map generation

- deterministic raster/SVG rendering;
- polarity, gamma, threshold;
- stepped + continuous fields;
- height-map artifact output.

**Acceptance:** numeric height-map tests pass before any 3D backend change.

### Phase C — matched 3D relief backend

- male variable-height solid;
- female dilated/offset cavity;
- orientation/key integration;
- STL export and geometry checks.

**Acceptance:** synthetic black/gray/white test produces three measurable heights and a valid mating pair.

### Phase D — risk analysis

- printer-resolution checks;
- slope/ridge/peak/texture heuristics;
- structured warning report;
- override behavior.

**Acceptance:** test fixtures trigger expected findings and hard errors remain non-overrideable.

### Phase E — desktop + CLI UX

- Emboss style selector;
- compact relief controls;
- relief preview/legend;
- warnings/override confirmation;
- new CLI flags.

**Acceptance:** a new user can generate a binary die exactly as before or opt into a grayscale die without seeing advanced CAD terminology.

### Phase F — physical calibration

- print small coupons;
- update profile heuristics from measurements;
- document results;
- do not tighten limits without evidence.

### Phase G — generated profiles/textures

After the core field pipeline is stable:

- outer/inner ring designer;
- generated radial profiles;
- texture overlays;
- composition modes;
- richer preview.

---

## 22. Documentation requirements for implementation PRs

Any implementation of this specification must update the relevant set of:

- `README.md`
- `docs/ARTWORK_GUIDE.md`
- `docs/DESKTOP_APP.md`
- `docs/AGENT_API.md`
- `docs/PHYSICAL_VALIDATION.md` only when a real print was performed
- `AGENTS.md`
- `CHANGELOG.md`

Claims must distinguish **software-supported**, **CAD-validated**, and **physically validated** behavior.

---

## 23. Design principles to preserve

1. **Simple remains simple.** Binary embossing stays the default one-click path.
2. **One backend.** CLI, GUI, and agents use the same formulas and validation service.
3. **Warnings, not paternalism.** Paper-risk heuristics inform users; intentional risky output remains possible.
4. **Impossible geometry is different from risky geometry.** Only the former is a hard stop.
5. **Profiles contain empirical knowledge.** Do not scatter printer/paper thresholds through UI code.
6. **Every generated die is reproducible.** Store the processed height field and all mapping parameters.
7. **Physical claims require physical tests.** A successful mesh is not evidence that paper will survive it.
8. **Do not destabilize binary mode while building relief mode.** Parallel processing paths should converge only at shared pair assembly/export where appropriate.

This document is the canonical architecture contract for EmbossForge variable-depth relief until superseded by a newer versioned specification.