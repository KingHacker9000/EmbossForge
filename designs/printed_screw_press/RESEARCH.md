# Original all-PLA screw press: research and architecture decision

Research date: 11 September 2026. This design does not reuse the repository's
existing press, cartridge, or linkage geometry. The die format and its upper
installation transform are the only inherited interfaces. External hardware: **0**.

## Evidence and its limits

* [FlashForge AD5M manufacturer specifications](https://www.flashforge.com/products/adventurer-5m):
  220 × 220 × 220 mm build volume, 0.4 mm nozzle option, and PLA compatibility.
  Its headline travel speed is not a structural-part printing recommendation.
* [Trodat Ideal Seal 970041](https://www.trodat.net/uk/en/products/b2c/c1/at-work/c2/trodat-seal-presses/c3/trodat-seal-presses/p/970041):
  a portable/desktop seal press with removable insert, 40 mm maximum plate,
  and a stated 80–160 gsm paper range. Useful evidence for the application and
  replaceable insert workflow; the manufacturer does not publish jaw force here.
* [Trodat/Fred Lake cast-iron desk seal](https://www.fredlake.com/products/2in-cast-iron-desk-seal-w-choice-of-stock-%280-extra%29-or-custom-%2840-extra%29-logo):
  heavier stock and longer reach are served by a much heavier frame and straight
  vertical motion. Its metal construction is not transferable to PLA by copying
  dimensions.
* [Sizzix sandwich instructions](https://www.sizzix.com/pages/sizzix-sandwich-instructions)
  and [Big Shot](https://www.sizzix.com/products/sizzix-big-shot-machine-only):
  roller craft presses depend on the correct plate/folder stack. They are useful
  for wide flexible embossing folders, but rolling contact is a poor match for
  two rigid circular dies that must remain registered throughout engagement.
* [Open Press Project](https://openpressproject.com/): a real printed printmaking
  press and active maker project. The rolling-printmaking principle is relevant;
  its existence does not prove this new platen press's load rating. No project CAD
  was copied. Some linked maker-hosted pages were unavailable to automated access.
* [Cederb's embossing press](https://www.printables.com/model/253050-embossing-press):
  the indexed maker description identifies a mostly printed toggle press used
  for diplomas. The original page could not be fully retrieved, so assembly and
  durability claims from mirrors were not treated as verified design inputs.
* [Gerecht et al., 2021, printable planetary roller screw](https://www.mdpi.com/2227-7080/9/2/24):
  physical tests used PETG; PLA was used for preliminary examples. The reported
  direct screw averaged 403.5 N maximum, while the roller screw maintained about
  160 lbf and began de-meshing above about 200 lbf. A later test stripped threads.
  These are mechanism feasibility and failure-mode evidence, **not a rating for
  this PLA design**. Complex roller gearing adds too many sensitive interfaces
  for this application.
* [Guden: hinge-pin retention](https://www.guden.com/blog/490/hinges-and-hardware-101-how-to-retain-a-hinge-pin):
  axial retention must be deliberate. This design avoids power pivots entirely;
  its pressure foot has a flange and bolted keeper, and its fasteners have actual
  modeled threads and heads. It does not depend on loose pins staying in holes.
* [Prusa FDM design guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135):
  supports, layer orientation, nozzle-width walls, and fit allowance must be
  considered during modeling. About 0.3 mm is a useful starting moving clearance,
  not a universal tolerance. Clearance is deliberately taken up at the guide;
  coupons precede a full print.
* [Prusament PLA technical data](https://prusament.com/wp-content/uploads/2022/10/PLA_Prusament_TDS_2021_10_EN.pdf):
  density 1.24 g/cm³, typical modulus about 2.3 GPa, reported interlayer adhesion
  17 ± 3 MPa, and heat-deflection temperature about 55 °C. These particular test
  conditions do not certify generic PLA. Calculations use reduced properties and
  forbid sustained clamping and warm service.

* [Delić et al., 2017, paper embossing with FDM tooling](https://jged.uns.ac.rs/index.php/jged/article/download/514/590/1261):
  60 × 60 mm PLA male/female dies with 1 mm relief and 30-degree chamfers were
  tested using an instrumented load frame. The lowest tested force, 1,000 N,
  worked for the lighter offset and coated papers. Other stocks needed up to
  1,750 N. The study did not establish the minimum below 1,000 N. Gross-area
  scaling gives 1,000 × pi × 21² / 3,600 = 385 N for a 42 mm disc. This is only
  an order-of-magnitude estimate: raised-feature coverage is not held constant.

No reliable universal jaw-force specification for a 42 mm ordinary-paper seal
was found. Industrial tissue, hot embossing, leather stamping, and die cutting
are different processes; their pressures cannot be assigned directly to this
press. The chosen 300–500 N working **target** is an explicit engineering
assumption, informed by the paper experiment and printed-actuator tests. Dense art,
large solid areas, hard stock, or inadequate die clearance may exceed it.

## Architecture comparison

| Approach | Benefit | Main concern under these constraints | Decision |
|---|---|---|---|
| Handheld lever / hinged jaws | Fast, compact | Arcuate die entry, pin bearing/shear, spring return, hand effort | Reject |
| Guided toggle | High endpoint advantage, rapid cycling | Printed pivots, dead-center sensitivity, overload and pinch zones | Viable second choice |
| Eccentric cam | Few parts, quick stroke | Wear at concentrated contact; force depends sharply on angle and stack | Reject |
| Roller craft press | Lower instantaneous contact area | Roll bending and torsion; rigid matched discs may tilt or move | Reject |
| Planetary roller screw | Demonstrated printed force amplification | Timing, roller retention, tooth de-meshing, many wear surfaces | Reject |
| Large coarse screw + guided ram | Adjustable closure, reversible drive, broad load paths | Thread/thrust friction and slower cycling | **Selected** |

The selected machine has an original two-piece C-frame, printed power nut and
handwheel/screw, captive pressure foot, adjustable dovetail-guided ram, and two
removable die trays. Thread and thrust wear parts are independently replaceable.
The split frame permits assembly of a captured guide without trapped parts and
puts the frame's bending load in the printing plane. Tie bolts close the split;
each C half carries its own portion of the embossing load.

## Quantitative design targets

* One sheet of ordinary 80–120 gsm paper first; roughly 0.08–0.15 mm caliper.
  Caliper and fiber behavior matter more than gsm alone.
* Current 42 mm diameter, 3 mm base, 6 × 2.5 mm +Y-key die interface.
* Nominal demonstration closure: 0.10 mm face separation. It is not an automatic
  stop or a promise of safe clearance for every generated relief.
* 10 mm working opening, continuously adjustable by a 6 mm-lead screw.
* 300–500 N target intermittent force; 750 N calculation case, not proof load.
* Handwheel radius 80 mm. Approximately 35–75 N tangential hand force for 500 N
  output over the assumed dry friction range; verify experimentally.
* No external hardware, structural glue, purchased spring, or metal reinforcement.
* All production STL files supplied in their intended printing orientation.

## Outstanding physical evidence

Thread friction, breakaway torque, guide straightness and wear, clamp repeatability,
frame compliance, fatigue, actual paper quality, and comfortable hand force must
be established on a printed machine. CAD interference checks cannot establish
these. The repository's earlier 16 mm hand-pressed die test is not validation of
this machine or of a 42 mm embossing force requirement.
