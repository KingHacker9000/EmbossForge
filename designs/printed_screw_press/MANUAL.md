# All-PLA 42 mm screw embosser — manufacturing and assembly manual

**Revision A, 11 September 2026. CAD-reviewed first physical prototype.**

External hardware required: **0**. All screws, nuts, retaining parts, pressure
foot, guide adjusters, and assembly gauge are printed. No structural glue,
springs, magnets, bearings, rods, or metal reinforcement are required.

This package contains finished editable CAD and exported parts. Its strength,
wear life, and emboss quality have **not** been physically validated. Start with
the fit trials and the commissioning procedure below. A successful CAD check is
not a load rating or evidence of a clean paper impression.

![Open press](images/open.png)

## Files and quantities

`stl/` contains the mechanism and gauge in their **printing** orientations.
`step/` contains the same individual editable solids in those orientations.
`assemblies/closed.step`, `open.step`, and `exploded.step` contain named assembly
components. Assembly STL files ending `VIEW_ONLY` are visualization files;
do not slice an assembled machine as one object.

The two actual commissioning dies are in `test_dies/diamond_commissioning/`.
Print the male and female STL once each, backs on the bed and artwork upward.
The generic die envelopes in assembly STEP files have no artwork and are not
the commissioning dies.

| ID | Part | Quantity | Function |
|---|---|---:|---|
| 01 | Frame left | 1 | One complete in-plane C load path; integral locating pegs |
| 02 | Frame right | 1 | Second C load path; matching locating holes |
| 03 | Power nut | 1 | Anti-rotation diamond seat and underside reaction flange |
| 04 | Power screw and handwheel | 1 | 28 mm printed thread, integral foot and 160 mm wheel |
| 05 | Guided ram | 1 | Non-rotating upper support and opening stops |
| 06 | Lower die tray | 1 | Keyed die pocket, radial clamp and sliding mount |
| 07 | Upper die tray | 1 | Corresponding opposite-facing holder; correctly handed thread |
| 08 | Die clamp wedge | 2 | Frictional side grip without obstructing working faces |
| 09 | Die clamp screw | 2 | Small, low-load wedge actuator |
| 10 | Foot keeper | 1 | Captures the enlarged screw foot for reopening |
| 11 | Keeper screw | 2 | Retains keeper with real printed threads |
| 12 | Guide adjuster | 2 | Takes up guide clearance against the rear datum |
| 13 | Tray retainer | 2 | Clamps and positively retains removable trays |
| 14 | Frame tie bolt | 3 | Holds frame halves together |
| 15 | Frame tie nut | 3 | Positive threaded retention of tie bolts |
| 16 | Alignment gauge — tool | 1 | Registers both tray pockets before locking mounts |
| — | Commissioning male/female dies | 1 each | Working diamond-and-dot test pattern |

There are 24 mechanism pieces, two working dies, and one printed setup tool:
**27 printed pieces total**. Fit-trial pieces are additional sacrificial samples.
Machine-readable part dimensions, solid volumes, and quantities are in `BOM.csv`
and `bom.json` (mechanism/gauge); the die generator manifest identifies the pair.

## Printer and slicing

Target: FlashForge Adventurer 5M, **220 × 220 × 220 mm**, 0.4 mm nozzle,
ordinary unfilled PLA. Use a clean PEI plate. Keep the machine at normal room
temperature; PLA is unsuitable for a hot car, radiator, or heated embossing.

Use the supplied STL orientation at 100% scale. Scaling changes the die fit,
thread pitch, and guide geometry. Never scale a nut independently to fix fit.

| Setting | Starting recommendation |
|---|---|
| Layer height | Frame/ram/trays 0.20 mm; screws/nuts/wedges 0.16 mm; dies 0.15 mm |
| First layer | Same height or 0.20 mm for the structure; 0.15 mm for both dies |
| Line width | About 0.45 mm; 0.4 mm nozzle |
| Walls | 8 for frame and ram; 6 for other parts; solid small fasteners |
| Infill | **100% alternating rectilinear for this first article** |
| Top/bottom | At least 6 layers; full solid fill is still required |
| Nozzle | Start at 215–220 °C, within the actual filament manufacturer's range |
| Bed | 55–60 °C |
| Outer walls | 30–40 mm/s; thread exteriors 25–30 mm/s |
| Internal solid fill | 50–65 mm/s; cap volumetric flow around 6 mm³/s initially |
| Acceleration | About 1,500–2,500 mm/s²; lower for long guide screws |
| Cooling | Normal PLA cooling after the first layers; strong bridge cooling |
| Elephant-foot compensation | Start around 0.15–0.20 mm, verify on fit trials |
| Brim | 5–6 mm on trays, ram, guide adjusters and tie bolts |
| Seam | Away from guide faces and die pocket seating surfaces when possible |
| Ironing | Off on threads, sliding surfaces, and dies |
| Supports | Per-part guidance below; never fill all thread bores indiscriminately |

These are conservative starting settings, not a tested FlashPrint/Orca profile
or ready-to-run G-code. Check the complete layer preview. At 100% infill, an
over-extruding profile can accumulate material and spoil both strength and fit.
Do not substitute the printer's advertised maximum speed for these settings.

### Orientation and local support review

Every part fits the build volume. The largest XY part is the 160 mm handwheel.
Brims still fit on the 220 mm bed when the listed parts are printed individually.

| Part | Supplied orientation and reason | Support/feature inspection |
|---|---|---|
| 01, 02 | Broad **outer C face down**; bending and spine tension lie in the layer plane | No large bridge. Nut/guide cuts use diagonal faces. Left locating pegs point upward; do not invert it onto those pegs. |
| 03 | Diamond flange down; thread axis vertical | 45° thread flanks, 6 mm flange. No support inside threads. |
| 04 | Handwheel down; screw points upward | Broad bed contact; load is compression through a 24 mm root. Foot taper grows at 45°. No supports. |
| 05 | Front face down; 68 × 42.9 mm maximum footprint envelope, 84 mm tall | Guide bores are vertical in this orientation. Inspect the small horizontal keeper-thread roofs and pressure-pocket rim. Use only accessible local supports if the slicer predicts failed overhangs; remove them fully before assembly. Opening-stop posts are not bed supports. |
| 06, 07 | Rear edge down, die-pocket floor vertical | Dovetail runs in the print direction. Short pocket-rim/clamp-pocket bridges need slow bridge settings. Local accessible rim support may be needed; keep supports off the flat die-bearing floor. Use a brim. |
| 08 | Broad wedge base down | Main toe is about 2 mm thick; thin nonfunctional horns have been removed. No support. |
| 09, 11, 13 | Hex head down; thread axis vertical | Small thread crests can be one extrusion wide, but load-carrying roots are broader. No supports. |
| 10 | Flat keeper down | 4 mm thick; open-sided neck slot. No supports. |
| 12 | Hex head down | 8 mm shank, 91 mm tall with head; use a 6 mm brim, low acceleration, and print separately from parts that might cause nozzle strikes. This is a low-force adjuster, not a power pin. |
| 14 | Hex head down | 11 mm thread root and 94 mm total height. Brim, modest speed. Only light lateral assembly preload is intended. |
| 15 | Flat hex face down | Short vertical thread; no supports. |
| 16 | Large keyed circular end down | Solid, 16 mm high. No supports. Do not mistake this gauge for an embossing die. |
| Test dies | Back down, artwork up, same settings for both | Broad binary ridges; inspect negative grooves as carefully as positive ridges. No supports. |

Support cleanup is limited to accessible surfaces. If a thread will not turn with
its matching printed fastener, correct the fit/profile and reprint that part;
forcing it or using a metal tap is not an assembly requirement.

## Before the large print

1. Print the power-thread test screw and default 0.3 mm-clearance test nut in
   `fit_trials/`. They must turn by fingers without a wrench, binding or cracked
   layers. Optional 0.2 and 0.4 mm trial nuts diagnose fit; choosing one requires
   regenerating the production power nut with that same allowance.
2. Print the trays, wedges, clamp screws and gauge. Confirm that the gauge fully
   seats against each flat pocket floor. Do not use a rocking or warped floor.
3. Check the small clamp screw turns freely before inserting its wedge. It is a
   light finger clamp, with roughly 2 mm available thread engagement, not a
   structural tightening screw. Do not force or wrench it.
4. Deburr only strings and first-layer flare. Do not sand away guide datums,
   change die diameters, or enlarge all holes arbitrarily.

## Assembly

Use the exploded STEP/image and part IDs. The open side is the **front** (−Y);
both die key slots point toward the rear (+Y).

![Exploded assembly](images/exploded.png)

1. **Build the drive on the bench.** Screw 04 through nut 03, flange below the
   nut. The foot passes through its bore. Put the foot in ram 05's circular top
   pocket. Slide keeper 10 in from the front around the 16 mm neck, then install
   both keeper screws 11 from above. Snug by fingers. The screw should rotate
   while the ram stays still. The keeper retains the larger foot when lifting.
2. **Install the guide adjusters.** Insert both long adjusters 12 from the ram's
   front holes. They pass through clearance bores and thread into the rear guide
   tongue. Initially leave their tips flush with or slightly short of the rear
   tongue face.
3. **Close the frame around the drive.** Lay frame 01 on its broad outer side.
   Place half the nut's diamond seat in its top recess and half the ram's guide
   tongue in the rear guide channel. Nut flange sits **below** the upper arm.
   Fit frame 02 over the two locating pegs. This split-frame step is necessary;
   a captured dovetail cannot be forced into the assembled frame from the front.
4. Insert three tie bolts 14 through the frame and install nuts 15. Tighten only
   enough to close the seam without rocking. Do not use a wrench or stretch the
   printed bolts. Main embossing force runs through the two C profiles, not
   across these bolts as pivot shear.
5. Stand the machine on its broad bottom. Hold the base while turning the wheel.
   Adjust the two guide screws alternately until side/back play is removed, then
   ease them very slightly if travel drags. The tips bear on the rear channel
   wall and push the angled guide faces against their matching datums. Check the
   whole stroke, not one position. There should be no perceptible lateral knock.
6. Slide tray 06 into the lower dovetail from the front. Slide tray 07 into the
   ram's underside dovetail, die pocket facing downward and key slot still at
   the rear. Install retainers 13 through the recessed front corner holes,
   lower retainer downward and upper retainer upward. Leave them slightly loose
   for alignment. Trays seat against the rear stops.
7. Put one wedge 08 in each side pocket and fit its clamp screw 09. The raised
   toe faces the circular die pocket. The same wedge works in both trays; flip
   it so its recessed screw-head side faces the die working face.
8. **Register the trays using gauge 16.** With no actual dies installed, open
   nearly fully and insert the 16 mm keyed gauge into both die pockets. Lightly
   close until both flat back seats contact it (about 9.9 mm nominal opening).
   Bias the gauge toward the fixed circular side opposite each wedge and bias
   its tab to that same side of each key slot. Snug the wedges and then the tray
   retainers. Do not generate embossing force against the solid gauge. Reopen,
   loosen the wedges, and remove it. Keep the tray retainers locked.
9. Check smooth reopening and the positive opening stops. Two ram posts contact
   the nut flange at 10 mm ram lift. Stop at first light contact; do not tighten
   against the stop. The captured foot has about 0.55 mm reversal take-up before
   it lifts the ram. No return spring is needed.

All parts can be installed before their enclosing part is fitted. No press-fit
pin, hidden hardware, welded joint, or trapped printed-in-place mechanism is
part of the assembly sequence.

## Die installation and changing artwork

The required die body remains Ø42 × 3 mm with a 6 mm-wide, 2.5 mm-deep +Y tab.
The pockets are Ø42.6 mm and 2.5 mm deep: a nominal die's flat working face
stands 0.5 mm proud. The side wedge grips the base without covering artwork.

Open fully. Loosen a clamp screw just enough to retract its wedge; insert the
die and seat its back flat. Push the circle toward the fixed pocket side
**opposite the wedge**. Also rotate the tab gently toward that same side of the
key slot before tightening. This deliberate seating removes angular clearance;
the loose key slot by itself is not a precision angular datum.

Install male below and female above. Both tabs remain toward the back. The
upper die uses the backend's **180° rotation about Y**, with its face downward;
do not independently mirror artwork or rotate its tab toward the front.

Tighten the small wedge screws with fingertips only. Verify that the upper die
does not drop or shift under a gentle pull. Its retention is an explicit
**friction clamp**, not a hidden face lip or claimed form-lock. Inspect it often;
an oily surface, damaged tab, or loose clamp can reduce grip.

For easier access, withdraw a tray after removing its retaining screw. If either
tray is removed or its mounting retainer is loosened, repeat the gauge alignment
procedure before embossing. Swapping only the dies in locked trays preserves
the mount setting. Remove and clean lint before reseating a die.

## Using the press and the first paper tests

* First use the supplied shallow diamond-and-dot pair and one ordinary sheet.
  The dot makes an accidental orientation error visible.
* Paper enters from the open front and may extend sideways beyond the frame.
  The die center is roughly 35 mm in front of the ram's rear guide face at paper
  height. This is a short-reach edge embosser, not a machine that reaches the
  middle of an unfolded A4 sheet.
* Hold the base, turn the wheel clockwise viewed from above to close, and remove
  fingers from between the dies before applying pressure. Use fingertips first.
* Before force, check that ridges enter their matching grooves without a hard
  catch. Increase pressure a little at a time. A 1/24 turn is 0.25 mm of screw
  travel; use much smaller movements once contact begins.
* The modeled 0.10 mm face spacing is a reference pose, **not a built-in closing
  stop**. The screw accommodates real base thickness, paper and frame flex.
  Stop if the paper tears, the die shifts, the frame creaks, or a thread skips.
* Open counterclockwise. Remove the paper and compare all sides of the pattern.
  A strong impression at only one edge calls for checking seating/alignment;
  increasing force is not the remedy.
* Release all pressure after each impression. Store open with no clamp load
  between dies. Do not leave PLA under sustained embossing pressure.

The 300–500 N force range is an engineering target, not a measured rating.
There is no torque limiter. Hand feel cannot measure force reliably because dry
printed-thread friction changes with fit and wear. Do not use a handle extension,
body weight, hammer, drill, powered drive, or heated dies.

## Clearances and adjustment

| Interface | Nominal allowance / datum |
|---|---|
| Main power thread | 28 mm major, 24 mm root, 6 mm lead; cutter +0.30 mm radial and +0.18 mm axial per flank |
| Power nut to frame | Diamond vertices 28 vs 28.45 mm; flange 34 vs 34.45 mm |
| Frame locating pegs | Ø8 pegs into Ø8.6 holes; 3 mm engagement, 0.4 mm extra hole depth |
| Tie bolts | Ø14 thread through Ø14.7 frame holes; printed nuts use +0.30 mm radial allowance |
| Guide | Approximately 0.35 mm manufactured allowance, then adjusted into datum contact by screws |
| Tray slides | Several tenths per side; final registration uses the common gauge and locked retainers |
| Die pockets | Ø42.6; keyed slot 6.6 mm wide, reaches Y=23.8 mm |
| Clamp wedge | 0.4 mm each side along Y; 2:1 ideal radial amplification from its ramp |
| Pressure foot | Ø24 in Ø24.7 pocket; 16 mm neck through 16.7 mm keeper slot |
| Small threaded joints | +0.25–0.30 mm radial and +0.14–0.16 mm axial flank allowance |

Thread roughness, elephant foot, die-pocket diameter and flatness, straightness
of the guide, and the two tray fits are the likely printer-specific adjustments.
The gauge and bias-to-datum procedure remove assembly play but do not correct
warped prints or unequal die diameters. If precision seating cannot be achieved,
reprint the affected holder after correcting its local parameter. Never force
misaligned matched dies together.

## Material, time and wear

The CAD solid-volume estimate is about **1.32 kg PLA** for the mechanism and
gauge, plus the test dies, fit trials, brims and any local support. Have roughly
**1.5 kg available** for the first full article, with extra material for rejected
fit samples. This estimate assumes 1.24 g/cm³ and 100% solid material; use the
final slicer estimate for purchasing or scheduling. No verified print-time or
G-code estimate is supplied; it is a multi-plate print whose time depends on the
chosen support, flow and motion profile.

Wear parts: power screw/nut and foot surface; guide-adjuster tips and dovetail
faces; clamp wedges and their small threads; tray retainers; and the dies.
Printed tie bolts can be damaged by excessive tightening. Keep spare wedges,
small screws and a power nut. Replace parts with whitening, cracks, thread dust,
chipped teeth, growing play or persistent binding. Do not lubricate merely to
increase force: it changes the torque/force relationship and can stain paper.

## Safety and physical acceptance

The slow wheel avoids a snapping toggle, but the die gap still pinches. Keep
hands out, hold loose sleeves/hair clear of the wheel, keep children away, and
use eye protection for initial proof-of-function work with brittle PLA. Hold the
base against rotation. Do not carry the assembly by a removable tray.

A first physical article is accepted only after: all threads turn freely; the
ram traverses the whole stroke without knock; both dies remain seated after
reopening; the matched pattern enters correctly; ordinary paper embosses evenly
at comfortable hand force; and inspection after repeated trials shows no cracks,
loosened retainers or growing wear. Start with a few impressions, inspect, then
extend the trial gradually. These checks have **not yet been performed**.

For calculations, evidence, collision/mesh reports and known limits, see
`ENGINEERING.md`, `RESEARCH.md`, and `VALIDATION.md`.
