"""Small power-thread fit trials, printed before the large structural parts."""
import json
import cadquery as cq
import model

out=model.OUT/"fit_trials"
out.mkdir(exist_ok=True)
sample=model.thread(28,6,20).union(model.cyl(22,6,(0,0,-6)))
sample=sample.translate((0,0,6))
cq.exporters.export(sample,str(out/"power_thread_test_screw.stl"),tolerance=.035,angularTolerance=.12)
for clearance in [.2,.3,.4]:
    ring=model.diamond(28,0,18).cut(model.thread(28,6,18,clearance,.18))
    cq.exporters.export(ring,str(out/f"power_thread_test_nut_radial_{clearance:.1f}.stl"),tolerance=.035,angularTolerance=.12)
(out/"READ_ME.txt").write_text(
    "Print the test screw and the 0.3 mm radial-clearance nut first, at 0.16 mm layers, "
    "6 walls and 100% infill. No scaling, supports or ironing. 0.2 and 0.4 variants "
    "are optional alternatives. The screw should turn by fingers without splitting "
    "or wobbling heavily. Failure means do not print the full press yet. Correct "
    "flow/elephant foot first; if a different clearance is needed, change the POWER "
    "NUT cutter radial allowance in model.py, regenerate, and rerun review.py. "
    "Do not globally scale either part. Then print both production trays, wedges, "
    "clamp screws, and the alignment gauge to verify the small clamp thread, die "
    "seating and grip before committing to the frame. These trials are not load tests.\n")
print("Fit trials exported")
