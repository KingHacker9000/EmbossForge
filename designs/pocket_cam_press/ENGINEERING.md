# Engineering record — Pocket Cam42

## Research and architecture decision

Research informed mechanical principles; no downloaded press CAD was copied. The design started with the42mm die interface, the130×80×45mm maximum storage envelope, fewer than six parts, zero external hardware and ordinary paper. The smaller110×70×35mm/75g ideals were not reached.

| Approach considered | Compactness/count | Force and alignment | PLA/printing concern | Decision |
|---|---|---|---|---|
| Direct thumb clamp | Excellent,1–3 parts | Essentially1:1 force | Comfortable force may be insufficient for a large patterned die | Reject as primary mechanism |
| Simple hinged pliers | Good,2 jaws plus retained pivot | Typically2–4:1 in this footprint; faces approach at an angle | Hinge clearance and angled relief entry | Reject for a general matched42mm pair |
| Compound lever/toggle | Fair, usually5–8 distinct links/joints | High final force; can drive a parallel carrier | Several heavily loaded printed pivots, adjustment/over-center sensitivity | Reject for part count and assembly |
| Whole-press living hinge/flexure | Excellent part count | Can guide motion; useful travel requires strain | Repeated load-bearing PLA flexure fatigue; modulus affects closure | Reject as main load path; use only small static die clamps |
| Small screw | Fair size,4–6 parts | Parallel, adjustable, high force | Slower operation and threads; user explicitly rejected screw architecture | Reject |
| Rollers/craft folder press | Poor within this brief | Progressive contact can lower instantaneous force | Rigid removable circular dies require a different transport system | Reject |
| **Eccentric cam plus guided carrier** | **Five pieces;114×78.5×44.5mm** | **Continuous force amplification; parallel dies, no adjustment screws** | Cam friction, bearing wear and C-frame compliance | **Selected** |

Trodat's Ideal Seal supports removable matched inserts in a commercial handheld/desktop product, and lists80–160gsm paper. Its published specification does not give jaw force, and its metal construction is not evidence that a printed copy would work. [Trodat primary product page](https://www.trodat.net/uk/en/products/b2c/c1/at-work/c2/trodat-seal-presses/c3/trodat-seal-presses/p/970041)

Sizzix's different platform/folder sandwiches illustrate how sensitive roller embossing is to stack geometry. The Open Press Project establishes practical small printed roller printmaking presses, but does not establish hardware-free compatibility with these rigid circular dies. [Sizzix sandwich instructions](https://www.sizzix.com/pages/sizzix-sandwich-instructions), [Open Press Project](https://openpressproject.com/)

Two relevant maker listings were identified: Cederb's Embossing Press and Andor's small living-hinge alphabet embosser. Their original pages were inaccessible during this pass, so their durability, successful-print rate, hardware count and detailed CAD were **not verified or treated as proof**. Research did not establish a reliable cycle-life dataset for an entirely PLA,42mm pocket embosser. [Cederb project](https://www.printables.com/model/253050-embossing-press), [Andor project](https://www.printables.com/model/519619-paper-alphabet-embosser-stamp-punch-scalable)

BYU explains the real part-count and precision benefits of compliant mechanisms, while explicitly identifying fatigue and limited motion as design challenges. This supports small occasional-deflection clamps, rather than an untested high-force PLA living hinge. [BYU Compliant Mechanisms Research](https://www.compliantmechanisms.byu.edu/about-compliant-mechanisms)

## Paper force: evidence and limits

Delić et al. tested60×60mm printed PLA embossing tools with approximately1mm relief. Their force trials began at1000N, which produced acceptable results on80gsm offset and90gsm coated paper. **They did not establish that1000N was the minimum necessary force.** Different papers needed different loads. The article is2017, not2021. [Original paper, Journal of Graphic Engineering and Design8(2)](https://jged.uns.ac.rs/index.php/jged/article/download/514/590/1261)

A deliberately crude gross-area comparison gives1000×π×21²/60² ≈385N for42mm. Raised artwork area, edge geometry, female clearance, paper moisture and relief depth make that scaling unsuitable as a guaranteed requirement. A sparse shallow mark can need much less than a dense die. This design therefore targets an initial200–300N experimental operating range for ordinary paper. **Clean embossing of every already-printed die is not established by that assumption.** Increasing press force cannot fix mismatched relief or insufficient paper accommodation.

## Kinematics and mechanical advantage

The cam has11.5mm lobe radius,2.0mm eccentricity and two9mm-wide working bands. The lighter central spool has9.5mm radius; four-millimetre transitions limit printing overhang to approximately45°. The lever offers a practical60mm hand moment arm.

The frame axle center isZ=31.35mm. The14mm axle in14.5mm seats can move0.25mm upward under reaction; another0.25mm is taken up between axle and cam. The assembled CAD deliberately represents these clearances taken up in the load direction. It does not silently treat a loose bearing as zero-clearance.

With cam angleθ measured from its lowest eccentric position:

`carrier back Z = 31.35 + 0.50 - 11.50 - 2 cos(θ)`

The carrier has5mm backing and the upper die a3mm base, so subtract8mm for the upper base working face. Atθ=82.819°, the upper face is12.10mm; the lower face is12.00mm. At180° the upper face is14.35mm: open gap2.35mm. Nominal closure is97.18° of handle rotation, followed by a limited amount of elastic squeeze. Manual lifting of the carrier provides return; a spring is not assumed.

Ignoring friction, instantaneous mechanical advantage is`L/(e sin θ)`: about30 at nominal contact. A more useful approximate balance is:

`F_die ≈ F_hand L / (e sinθ + μ_cam r_contact + μ_bearing r_shaft)`

At contact, using L=60mm, μ=0.15–0.30, r_contact≈11.75mm and r_shaft=7mm gives roughly8–12.5:1. Thus25N hand force suggests about200–313N die force. The assumed friction is not measured. Once the handle is below horizontal, the moment arm of a vertical hand force also decreases. Do not infer unbounded force near cam dead center.

There is1.75mm of additional theoretical cam travel after nominal paper contact. Some is needed for elastic frame/bearing deflection. Rigid die-envelope CAD is only valid through first contact; moving rigid overlapping die solids beyond that is **not** a physical compression simulation. A real load test must determine how far the lever moves for a given impression. Stop if the carrier cocks, the frame whitens or unusually high effort is needed.

## Load path and first-order strength screening

Load travels from hand through the lever and twin cam bands, into the carrier backing, upper die, paper, lower die and frame floor. It returns through the two broad rear columns and overhead cheeks to the axle. The clip only prevents axial withdrawal; it does not carry embossing force.

Screening below uses a250N nominal die force, E≈2.3GPa, about2.25mm perimeters,1.2mm top/bottom skins and15% core. Rectangular-beam estimates include partial core stiffness; they are **not FEA or a rated safety certification**. Short-region contact, fillets, raster direction, local shell continuity and print defects remain uncertain.

| Region | Approximate screening result | Interpretation |
|---|---|---|
| Rear columns,9.7×20mm each | Effective area≈125mm² and bending I≈5100mm⁴; combined axial/bending stress≈9–10MPa | Highest layer-separation concern, because columns print upright |
|9mm frame floor | Effective I≈2960mm⁴ using71mm width; stress≈13MPa for a35mm moment arm | Large in-plane load path; bending/creep likely govern feel |
| Overhead cheeks | Roughly5–8MPa nominal away from hole/corner concentrations | Hole roofs need clean supports and intact perimeters |
|14mm axle with6mm bore | Twin near-support contacts give approximately5–6MPa bending; circular approximation | D flat slightly reduces stiffness; bore saves material with little bending penalty |
|5mm carrier backing | Approximately8MPa transverse bending for a42mm loaded width | Guide/locator fit must prevent edge loading |
| Lever rails around recess | Approximately14MPa at25N hand force, higher with larger forces | Broad rails and continuous web; no thin living hinge |

Estimated frame opening at250N is of order0.8–1.1mm when simplified floor, cheek and column deflections are combined. This is why the cam has overtravel and why a fixed rigid contact pose is not proof of full force. Eccentric or one-sided artwork can increase local deformation. The short prototypes may function at lower forces; no claim of repeated300N endurance is made.

Published PLA data from one filament manufacturer list interlayer strength around17±3MPa and substantially higher in-plane tensile strength, with tests on dense specimens. Those values cannot be assigned directly to an arbitrary15% infill part. The rear-column stress margin is limited and requires a real print test. [Prusament PLA data sheet](https://prusament.com/wp-content/uploads/2022/10/PLA_Prusament_TDS_2021_10_EN.pdf)

The16mm-long,2.5mm-thick clamp beams deflect about0.48mm after nominal seating. `strain≈1.5 δt/L²` gives about0.70%. A cantilever calculation predicts roughly8–13N clamping force, depending on carrier/frame beam height, before print and boundary effects. Friction should readily exceed a die's weight, but paper-peel retention must be physically checked. No axial capture lip interferes with the opposing die.

## Part-by-part design review

All five exported STL files have one connected, watertight, consistently wound positive-volume body, valid source solids, no oversize dimensions, and a broad face at bed height. Dimensions and raw results are in`validation/geometry.json`.

| Part | Printability and walls | Load/layers | Assembly and fit risk |
|---|---|---|---|
| Frame |71×73×44.5mm;9mm floor,9.7mm cheeks; supported arm ledges and14.5mm horizontal bores | Floor and arms carry tension mainly in-layer; rear columns carry some cross-layer tension | Supports must release; integrated tab clamp and rear cones accessible |
| Carrier |51×64.5×8mm;5mm backing,2.7mm cup wall, approximately1.4mm locator socket lips | Broad backing prints flat; clamp bends within layers | Drops into keyed guides before cam; sockets must not bottom before dies contact |
| Cam lever |About78.3×23×50mm in print orientation;2.25mm minimum cam/spool wall and1.2mm grip web | Side printing puts lever bending in-layer; axle runs through full width | Vertical bore needs no support; brim advised; working bands need smooth surfaces |
| Axle |78.5×18×15.5mm;14mm outside,6mm hollow center, broad D flat | Printed lengthwise to avoid a stack of discs in bending |6mm bore roof is a short bridge; head and groove provide positive retention |
| Clip |16×20×2.7mm; broad planar U fork with small rounded-by-slicing bumps | Flexure occurs in layer plane and only on assembly/removal | Small arm deflection; do not spread excessively; snap retention must be inspected |

Closing locators are two2mm-high45° truncated cones, behind the paper edge. They enter before final contact and limit registration error without changing the42mm die interface. Their0.20mm radial clearance still requires a printer-specific check; they are not an assertion of metrology-grade positioning.

## Digital checks and remaining physical work

The source and exported meshes are checked separately. Six states from nominal contact to fully open are examined pairwise; an independent Manifold boolean pass checks the actual oriented STLs after inverse print transforms. A210mm-wide,0.10mm-thick sheet corridor is checked through the throat. Straight assembly-path samples check carrier drop-in, cam drop-in and axle insertion. The clip and die clamps necessarily deflect during assembly; their retention is reviewed analytically and geometrically, not by pretending they pass through rigid solids.

Expected rigid overlaps are the two undeformed tab clamps against their die tabs:6.6mm³ each. They are explicitly reported, not suppressed as an unexplained tolerance. All other nominal part overlaps must be below0.03mm³. The paired die base envelopes have a0.10mm gap at nominal closure. Real artwork was not generated, modified or verified.

There has been no physical validation of support removal, actual fit, force, die adhesion, paper quality, creep, safety factor or service life. These cannot be established from meshes. A first print should demonstrate: free return, full clip retention, flat die seating, smooth locator entry, a clean ordinary-paper impression at modest effort and no whitening/cracks. Record those results before describing this press as reliable or production-ready.

The local CadQuery runtime emits exit code1 during interpreter cleanup even after successful exports/reports; the raw result files and independent pure-mesh checks are the evidence used here. This caveat is not an excuse for failed geometry checks. Existing application/legacy mechanics tests were not rerun for this isolated new design folder, and the die-generation backend was not changed.
