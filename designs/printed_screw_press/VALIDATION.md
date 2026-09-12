# Validation record — revision A

This is a completed CAD design package for a first physical article, not a
physically certified press. Actual exported STL surfaces were inspected.

## Completed checks

* All 16 mechanism/tool STL types: watertight, consistent winding, one connected
  component, positive volume, placed on the bed and within 220 × 220 × 220 mm.
* CadQuery solids: valid, one solid per printable part.
* CAD pairwise interference checks at 0, 2.5, 5, 7.5 and 10 mm ram opening:
  no intersection above the 0.03 mm³ numerical threshold.
* Independent mesh Booleans with the actual working male and female dies:
  zero pair overlap at nominal closure and fully open; no interference with
  mechanism components above that threshold.
* Both tray removal paths: 23 sampled positions over 110 mm, with the relevant
  tray retainer removed; no interference above the threshold.
* A 210 mm-wide, 0.15 mm paper envelope inserted through five front positions
  with the press open: no mechanism interference.
* The common 16 mm gauge fits both pockets at 9.9 mm nominal opening.
* Nominal male and female axes both at X=0.3, Y=0 mm, with the +Y keys aligned.
  Actual commissioning pair has 9.65 mm clearance above its male relief when open.
* Dedicated opening posts meet the nut flange at Z=106 mm and 10 mm ram lift.
  The captive foot includes reversal take-up; the upper die does not rely on a
  return spring or a loose pin to reopen.
* Part printing orientations and support-sensitive surfaces were reviewed in
  the delivered STL montage. A wrong frame-bed orientation and thin clamp horns
  were corrected before final export.
* Assembly order accommodates the captured guide before the split frame closes.
  Bolts have printed threaded nuts or sockets; all required retaining parts are
  present. Replaceable dies use the expressly documented friction clamp.

The sampled checks are not continuous-contact dynamics or a deformation analysis.
Guide motion is prismatic; the screw is translated and rotated with its true
6 mm lead. The wheel's full circular sweep remains above the frame. Frame
distortion, FDM dimensional error and wear are outside the rigid CAD check.

## Working die pair

The included diamond-and-dot pair was generated through the existing shared
`generate_die()` backend with mating enforcement enabled. It uses a 42 mm body,
3 mm base, 0.45 mm binary relief, 0.20 mm XY cavity allowance and 0.10 mm nominal
paper separation. Exported-STL closure passed without a risk override.

The backend labels complex SVG preflight as **partial**, not full slicer
equivalence. Inspect both dies in the layer preview. An earlier attempt using
the repository's original logo failed closure; that rejected pair is deliberately
excluded from this package. No geometry failure was overridden.

## Repository/runtime checks

The unchanged repository suite reported **73 passed**; package compilation and
the legacy mechanics export also completed. The legacy press output was only a
regression check and is not included or used as this design's geometry.

This Windows environment reports process exit code 1 on shutdown even for a
standalone `import cadquery; print(...)` after successful completion. The CAD
scripts and pytest show the same shutdown behavior. Consequently, this record
does not claim a clean process-exit/CI result. Completed JSON reports, exported
geometry, independent mesh checks and test assertion results were inspected
directly. Mesh Boolean empty-volume warnings do not indicate positive overlap.

## Not yet validated

Actual slicing/support success; layer adhesion of the user's PLA; comfortable
input force; friction-to-force relationship; guide/tray repeatability after
printing; pull-out resistance of die clamps; frame stiffness under load; fatigue;
thread wear; and a clean embossed paper result. No completed physical test is
claimed. Use the manual's fit trials and gradual commissioning procedure first.

Per-part printability decisions are in `MANUAL.md`. Machine-readable evidence:
`geometry_review.json`, `assembly_service_checks.json`, `overhang_screening.json`
and `engineering_calculations.json` inside `validation/`.
