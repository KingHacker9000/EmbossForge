# Engineering calculations and design limits

The original coarse screw and guided ram were selected over lever, toggle, cam,
and roller alternatives for controllable closure, positive reopening, and broad
printed load-bearing surfaces. See `RESEARCH.md` for the cited comparison.

**External hardware required: 0. Target intermittent force: 300–500 N.**
The 750 N case below is a calculation case, not a tested capacity or instruction
to load the machine to that force.

## Force and mechanical advantage

A directly relevant paper experiment used 60 × 60 mm PLA embossing dies and
reported 1,000 N for lighter stock. Gross-area scaling to a 42 mm circle gives
385 N. This is only a scale estimate: the patterns, active feature area and
paper behavior differ. [Delić et al., 2017](https://jged.uns.ac.rs/index.php/jged/article/download/514/590/1261).

For mean thread diameter d=26 mm, lead l=6 mm, flank half-angle a=45°, and
lambda=atan(l/(pi*d)), the raising torque is estimated as:

    T_thread = F*d/2 * (tan(lambda)+mu*sec(a))/(1-mu*sec(a)*tan(lambda))
    T_foot = F*mu*8 mm
    hand force = (T_thread+T_foot)/80 mm

The foot term assumes uniform pressure over its 12 mm radius. Dry friction
mu=0.15–0.35 is an assumption, not a measured property of these prints.

| Output target | Hand force, mu=.15 | mu=.25 | mu=.35 |
|---|---:|---:|---:|
| 300 N | 18.6 N | 28.9 N | 39.3 N |
| 500 N | 31.1 N | 48.1 N | 65.4 N |
| 750 N calculation only | 46.6 N | 72.2 N | 98.1 N |

The frictionless force ratio is 83.8:1; the friction-inclusive estimate is
7.6–16.1:1. Thread engagement is 28 mm, about 4.67 turns. The predicted
self-locking friction threshold is about 0.052, below the assumed dry range.
Do not infer a safe output from hand force or change lubrication to increase it.

## Load path and screening stresses

Wheel torque → screw flanks → power nut → underside nut flange → both C-frame
arms/spines → lower support → male/paper/female → upper tray/ram → flat screw
foot. The keeper and guide adjusters carry return/positioning loads, not the
main compression load. The tie bolts hold two independently load-bearing C
halves together; they are not highly loaded power pivots.

Screening assumptions: solid PLA, effective E=1,800 MPa, frame width 72 mm,
upper arm thickness 28 mm, lower arm 32 mm, spine depth 40 mm, 36 mm cantilever
reach to the spine front, 80 mm spine working height. A factor of 2.5 is applied
to the upper arm's nominal stress as a notch/geometry allowance. A factor of 3
is applied to average thread shear for uneven load distribution. These are
simple beam/area calculations, **not finite-element analysis**.

| Quantity | 500 N | 750 N calculation |
|---|---:|---:|
| Upper-arm nominal bending | 1.91 MPa | 2.87 MPa |
| Upper arm with 2.5× allowance | 4.78 MPa | 7.18 MPa |
| Spine nominal bending | 1.46 MPa | 2.19 MPa |
| Thread shear with 3× concentration | 1.42 MPa | 2.13 MPa |
| Foot compression | 1.11 MPa | 1.66 MPa |
| Nut-flange bearing | 0.67 MPa | 1.01 MPa |
| Approximate elastic opening | 0.17 mm | 0.26 mm |

The selected screening allowables are 8 MPa in-plane and 5 MPa interlayer shear.
They are deliberately below typical manufacturer's test data, but are not a
statistical material qualification. Real infill quality, layer bonding, voids,
notches and creep can defeat these assumptions. The split-frame seam and load
distribution around the nut pocket are not fully represented in the beam model.

The power screw has a 24 mm root: about 1.1 MPa axial compression at 500 N.
At the high-friction 500 N case, simple root torsional shear is about 1.93 MPa.
The 6 mm nut flange distributes reaction over about 744 mm². The printed wheel
has six broad 14 × 10 mm spokes and a 12 mm radial rim; grip near spoke/rim
junctions and never attach an extension. Tie-bolt root diameter is 11 mm;
finger-tight assembly preload is modest compared with its cross-sectional area.

Highest concerns are arm/spine corners, the nut's first engaged threads, flange
roots, screw-foot wear, and wheel spoke/rim junctions. Load-bearing C profiles
are printed flat so frame bending tension stays within layers. The screw is
printed upright for round threads; axial compression is favorable, but torsion
and thread-root shear still require sound layer bonding.

The guide has deliberate clearance plus screw take-up. Tray slides do not define
precision alignment alone: the solid common gauge aligns their pockets before
locking. Dies are biased against the same physical circular/key datums, then
friction-clamped. The small wedge screws must remain light finger clamps.

## Unvalidated assumptions

No physical force, cyclic life, paper quality, die retention, guide wear or frame
deflection has been measured. The calculated frame opening is comparable with
paper thickness; continuous screw adjustment accommodates displacement, but
uneven seating or rotation can still cause an uneven impression. Begin with the
supplied shallow test dies, not dense relief or heavy stock.

The machine has a positive opening stop, but **no automatic closing-force or
closing-depth limiter**. Use only light initial hand force and stop at an even
impression. No claim of universal paper safety or physical readiness is made.
The numerical source is `source/engineering.py`, with results in
`validation/engineering_calculations.json`.
