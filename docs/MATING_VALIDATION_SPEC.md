# Matched-die manufacturability and closure specification

**Status:** Accepted cross-cutting design contract. This applies to both current/future binary dies and variable-depth relief dies.

A mathematically matched male/female pair is not enough. The selected printer/nozzle/slicer can change what is actually printable. A thin positive ridge may survive on the male as one extrusion line while the corresponding negative cavity is too narrow for the slicer to preserve, producing a smooth female surface. The resulting pair may look valid in CAD but physically cannot close.

EmbossForge must therefore validate the **effective printable pair**, not only the ideal source geometry.

---

## 1. Core invariant

> Every male feature that is expected to enter the female die must have a corresponding **printable** female accommodation at the selected printer/nozzle settings, with the configured paper and clearance allowances.

The inverse also matters: female positive structures / male recess relationships must remain mutually printable whenever a design contains them.

Normal matched-pair generation must not knowingly emit a pair predicted to interfere at nominal closure.

Paper-risk warnings may be overridden. **Predicted die-to-die interference is a hard compatibility error and is not covered by `--allow-risky`.**

---

## 2. Why ideal CAD validation is insufficient

Consider a very thin SVG line:

```text
ideal source
male:    narrow raised ridge
female:  narrow matching groove
```

At a 0.4 mm nozzle, the slicer may produce:

```text
predicted print
male:    one printable extrusion line
female:  groove omitted / closed because it is below printable negative width
```

Then, at closure:

```text
male ridge  ->  solid female surface
                 ^ collision
```

The same class of failure can happen with:

- thin strokes;
- tiny islands;
- narrow slots;
- sharp corners;
- small counters inside text;
- close parallel lines;
- tiny grayscale relief terraces;
- narrow high ridges;
- female cavities that collapse after nozzle-aware filtering.

---

## 3. Printer-aware effective geometry

EmbossForge should distinguish:

```text
ideal geometry
    |
    v
printer-aware canonical geometry
    |
    v
predicted printable envelope
    |
    v
matched-pair closure validation
```

The printer-aware stage uses the active profile, including at minimum:

- nozzle diameter;
- effective line width when known;
- layer height;
- minimum printable positive feature width;
- minimum printable negative gap/cavity width;
- XY dimensional/clearance assumptions;
- future slicer-specific compensation when available.

Current profile fields such as `min_feature_mm`, `min_gap_mm`, `nozzle_mm`, and recommended die clearance are valid starting inputs. Future profiles may add explicit `line_width_mm`, `min_negative_feature_mm`, and XY compensation values.

---

## 4. Generate the female from the printable male target

A critical architecture rule:

> Do not independently simplify the male and female from the original artwork.

That can create asymmetric feature loss.

Preferred flow:

```text
source artwork / height field
        |
        v
canonicalize to printable male target
        |
        +--> male geometry
        |
        +--> derive female accommodation from the SAME canonical target
                  + paper allowance
                  + XY clearance
                  + extra depth
                  + minimum printable negative-feature enforcement
```

If a source feature is below the selected printer's positive-feature limit, policy may:

1. widen/repair the feature and derive both dies from the repaired geometry;
2. remove the feature from both dies;
3. keep it only when a higher-resolution printer/profile makes it printable.

The system must not silently keep a male feature while deleting the corresponding female accommodation.

---

## 5. Positive and negative feature rules

For every relevant 2D cross-section / relief level:

### Positive feature check

A male ridge/island expected to print must meet the selected profile's printable positive width, or be repaired/removed consistently.

### Negative feature check

The corresponding female cavity/gap, **after applying clearance**, must remain at or above the selected profile's printable negative width.

A useful conceptual condition is:

```text
female_printable_width >= max(
    male_effective_width + 2 * required_xy_clearance,
    printer_min_negative_feature_width
)
```

The exact formula may become more sophisticated for corners, curves, anisotropic slicer behavior, or variable-height relief, but the invariant remains.

### Bidirectional check

Do not only validate male-positive -> female-negative features. Where geometry contains the opposite relationship, apply the same reasoning in reverse.

---

## 6. Closure-envelope validation

After printer-aware canonicalization, EmbossForge must perform a nominal mating test.

Conceptually:

1. orient the upper and lower dies using the real cartridge transform;
2. place them at intended closed position;
3. account for selected paper thickness / designed vertical allowance;
4. compare the **predicted printable solid envelopes**;
5. detect plastic-to-plastic interference outside allowed tolerance.

For binary dies, this can begin with robust 2D morphology plus Z envelopes.

For variable-depth relief, validation should consider all relevant height levels / a sampled 3D field, because a cavity may fit at one level but interfere at another.

A later implementation may use voxel/SDF or mesh collision methods. Backend choice is flexible; the closure invariant is not.

---

## 7. Validation severities

### Hard compatibility errors — generation blocked

Examples:

- a retained male feature has no printable female cavity;
- a female recess collapses below the selected nozzle/profile resolution while the opposing male feature remains;
- predicted printable envelopes intersect at nominal closure beyond tolerance;
- orientation/mirroring causes the pair not to mate;
- required cavity enlargement would break through the female base;
- canonicalization produces an invalid/non-manifold pair.

These are **not overrideable via paper-risk controls**.

Developer/debug tooling may export intermediate geometry for diagnosis, but it must not present such output as a validated usable die pair.

### Repairable printability findings

Examples:

- thin line can be safely widened in both dies;
- tiny isolated feature can be removed from both dies;
- narrow female groove can be enlarged while preserving intended design sufficiently.

The UI should explain what was repaired and preserve repair metadata in the manifest.

### Advisory quality / paper-risk warnings

These remain separate and may be overrideable:

- fine detail may look soft;
- relief may crease thin paper;
- texture may merge;
- high local slope may increase tear risk.

A pair can be mechanically compatible yet still carry quality/paper-risk warnings.

---

## 8. Auto-repair policy

Auto-repair should be **paired**, never side-specific.

Preferred repair priorities:

```text
1. preserve fit / closure
2. preserve major motif topology
3. preserve readable text and primary outlines
4. preserve secondary detail where resolution allows
5. drop micro-detail before risking incompatible dies
```

Examples:

- widen a 0.25 mm source stroke to the profile's printable positive width, then derive a suitably wider female cavity;
- remove a tiny decorative dot from both dies instead of allowing it on only one side;
- enlarge a small text counter on the source/canonical model so both dies preserve the opening.

Every automatic repair should be reproducible and recorded.

---

## 9. UI contract

Before final generation, the desktop app should show a concise compatibility result such as:

```text
Die fit check
✓ Male features printable for 0.4 mm nozzle
✓ Female cavities printable for 0.4 mm nozzle
✓ Predicted pair closes with selected clearance

3 tiny details were widened automatically
[Review changes]
```

If closure fails:

```text
Cannot generate a compatible die pair

A 0.31 mm male ridge would print, but its matching female cavity
is below the 0.45 mm printable-gap limit for this profile.

Suggested fixes:
• allow EmbossForge to widen the feature
• simplify the artwork
• use a finer nozzle/profile
```

Do not reduce this to a vague `detail too small` warning when the actual issue is mating incompatibility.

---

## 10. CLI / API behavior

Normal generation should run compatibility validation automatically.

Future structured result fields should include something like:

```json
"mating_validation": {
  "status": "pass",
  "profile": "FlashForge Adventurer 5M / 0.4 mm prototype",
  "minimum_positive_feature_mm": 0.50,
  "minimum_negative_feature_mm": 0.45,
  "predicted_min_clearance_mm": 0.20,
  "repairs": [],
  "interferences": []
}
```

If validation fails, the API should return/raise a structured compatibility failure before presenting final output as usable.

A future `--no-auto-repair` may disable repair, but it should cause incompatible geometry to fail rather than allowing mismatched output.

---

## 11. Manifest requirements

Future schema v2+ manifests should preserve:

- printer profile used;
- nozzle / line-width assumptions;
- positive/negative feature thresholds;
- canonicalization/repair operations;
- minimum predicted mating clearance;
- closure-validation result;
- any detected interference regions/metrics;
- whether validation was analytic, raster/morphological, voxel, mesh, or slicer-backed.

This lets a later agent or user understand why a feature was widened/removed and what assumptions made the pair valid.

---

## 12. Testing contract

At minimum, add regression cases for:

1. **Thin positive line retained by male, negative groove too small in female** — must be repaired or rejected; never silently pass.
2. Thin feature removed from both dies — pass.
3. Thin feature widened consistently in both dies — pass.
4. Tiny text counter that collapses in one side — repair/reject consistently.
5. Two close parallel ridges whose female cavities merge — validate intended topology / warn or repair.
6. Orientation/mirror mismatch — hard fail.
7. Binary butterfly smoke test — continues to pass.
8. Variable-depth narrow high ridge — female relief accommodation remains printable at all relevant levels.
9. Selected finer nozzle/profile makes a previously invalid feature valid.
10. `allow-risky` does not bypass mating incompatibility.

---

## 13. Optional slicer-backed validation

The first implementation does not need to embed a full slicer. A deterministic printer-profile approximation is acceptable and should be conservative.

However, the architecture should allow a stronger future validation tier:

```text
Tier 1: profile-aware geometric/morphological preflight
Tier 2: optional slicer-backed toolpath analysis
```

If a supported slicer can expose toolpaths/G-code, EmbossForge may compare what each die would actually print and detect cases where a groove disappears or a ridge is widened by extrusion rules.

Slicer-backed results must record the slicer/profile/version in the manifest.

---

## 14. Relationship to other specs

This contract is cross-cutting:

- `ARTWORK_GUIDE.md` — design should respect printable positive and negative features.
- `RELIEF_MODE_SPEC.md` — variable-height dies must satisfy closure at all relevant relief levels.
- `IMAGE_INPUT_SPEC.md` — interpreted/shaded artwork must be canonicalized before matched-pair generation.
- `skills/embossforge-design/SKILL.md` — artwork-generating agents should avoid details that force one-sided feature loss.
- `AGENTS.md` — agents must never declare a pair valid based only on ideal CAD geometry.

The long-term definition of a successful EmbossForge generation is therefore:

> **The requested design is representable on the selected printer, both dies remain printable after profile-aware canonicalization, and the predicted printed pair can mate at nominal closure with the configured paper/clearance allowances.**
