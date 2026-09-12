"""Compact power-thread fit trials for the all-PLA screw press.

These coupons preserve the production 28 mm / 6 mm-lead thread geometry and
clearance rules, but remove the large sacrificial diamond block used by the
original research prototype. They are fit tests only, not load tests.
"""
from pathlib import Path

import cadquery as cq

import model

out = model.OUT / "fit_trials"
out.mkdir(parents=True, exist_ok=True)

# Three turns of production thread are enough to expose binding, elephant-foot,
# and gross clearance problems without printing a full power screw.
SCREW_THREAD_LENGTH_MM = 14.0
NUT_HEIGHT_MM = 12.0
NUT_HEX_DIAMETER_MM = 44.0
GRIP_HEIGHT_MM = 4.0
GRIP_HEX_DIAMETER_MM = 38.0

screw = model.thread(28, 6, SCREW_THREAD_LENGTH_MM)
grip = (
    cq.Workplane("XY")
    .polygon(6, GRIP_HEX_DIAMETER_MM)
    .extrude(GRIP_HEIGHT_MM)
    .translate((0, 0, -GRIP_HEIGHT_MM))
)
screw = screw.union(grip).translate((0, 0, GRIP_HEIGHT_MM))
cq.exporters.export(
    screw,
    str(out / "power_thread_test_screw.stl"),
    tolerance=.035,
    angularTolerance=.12,
)

for clearance in [.2, .3, .4]:
    nut = cq.Workplane("XY").polygon(6, NUT_HEX_DIAMETER_MM).extrude(NUT_HEIGHT_MM)
    nut = nut.cut(model.thread(28, 6, NUT_HEIGHT_MM, clearance, .18))
    cq.exporters.export(
        nut,
        str(out / f"power_thread_test_nut_radial_{clearance:.1f}.stl"),
        tolerance=.035,
        angularTolerance=.12,
    )

(out / "READ_ME.txt").write_text(
    "COMPACT POWER-THREAD FIT TEST\n\n"
    "Print power_thread_test_screw.stl and power_thread_test_nut_radial_0.3.stl first.\n"
    "Recommended: 0.16 mm layers, 6 walls, 100% infill, supports OFF, ironing OFF, 100% scale.\n"
    "The compact coupon uses exactly the production 28 mm / 6 mm-lead thread profile and fit allowance; "
    "only the surrounding sacrificial plastic and engagement length were reduced.\n"
    "The screw must turn through the nut by fingers without a wrench, cracked layers, or severe wobble.\n"
    "If 0.3 mm is too tight or too loose, try the 0.4 or 0.2 variant respectively.\n"
    "Failure means do not print the full press yet. Correct flow/elephant foot first; if a different "
    "clearance is required, apply that same allowance to the production power nut and rerun validation.\n"
    "These coupons are fit tests only and are not proof-load samples.\n"
)

print(f"Compact fit trials exported to: {out}")
