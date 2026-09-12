"""Pocket Cam 42 Revision B split frame.

Physical Revision-A result: carrier/cam/axle/clip printed cleanly; the one-piece
frame failed at long support-dependent horizontal ledges. This file changes only
the frame. It preserves the carrier guides, cam axis, axle seat, closing locators,
42 mm die location, and the already-printed four moving parts.

Run from repo root:
    python designs/pocket_cam_press/frame_rev_b.py

Print ONLY the two generated frame halves. No supports by default.
"""
from pathlib import Path
import json
import cadquery as cq
import trimesh

import model

OUT = Path("build/pocket_cam_press_rev_b")
PEG_R = 2.50
SOCKET_R = 2.65


def _split_friendly_frame():
    """Same frame envelope/mechanism interfaces, but a split-friendly lower die cup."""
    f = model.cyl(27, model.BASE).union(model.box(71, 45, model.BASE, (0, 22.5, 0)))

    # Lower die cup. The old one-piece cantilever clamp crossed X=0 and would be
    # cut in half, so Rev B replaces only that clamp with three short friction ribs.
    f = f.union(model.cyl(24, 3, (0, 0, model.BASE)))
    f = f.union(model.box(29, 14, 3, (0, 25, model.BASE)))
    cavity = model.cyl(model.POCKET_D / 2, 3.2, (0, 0, model.BASE))
    cavity = cavity.union(model.box(model.KEY_W, 4, 3.2, (0, 22, model.BASE)))
    f = f.cut(cavity)
    for x, y, w, d in (
        (21.10, 0, .40, 4.0),
        (-21.10, 0, .40, 4.0),
        (0, -21.10, 4.0, .40),
    ):
        f = f.union(model.box(w, d, 2.2, (x, y, model.BASE + .15)))
    f = f.cut(model.cyl(3.2, model.BASE + .1, (0, -16, -.05)))

    # Keep the proven carrier/closing geometry unchanged.
    for x in (-18, 18):
        f = f.union(model.cyl(4.5, 3, (x, 30, model.BASE)))
        f = f.union(cq.Workplane(obj=cq.Solid.makeCone(3, 1, 2, cq.Vector(x, 30, 12))))
    for side in (-1, 1):
        f = f.union(model.box(9.7, 20, 35.5, (side * 30.65, 35, model.BASE)))
        f = f.union(model.box(9.7, 73, 19.5, (side * 30.65, 8.5, 25)))
        for yy, ll in ((-22, 8), (26, 16)):
            f = f.union(model.box(3.0, ll, 10, (side * 27.3, yy, 15)))
        f = f.union(model.box(3.3, 3, 10, (side * 24.15, 21.5, 15)))

    bore = cq.Workplane("YZ").circle(7.25).extrude(90, both=True)
    bore = bore.cut(model.box(190, 30, 40, (0, 20.75, -20))).translate((0, 0, model.AXIS_Z))
    return f.cut(bore)


def frame_halves():
    f = _split_friendly_frame()
    left = f.intersect(model.box(120, 180, 90, (-60, 10, 0)))
    right = f.intersect(model.box(120, 180, 90, (60, 10, 0)))

    # Three base-seam alignment pegs. The final axle positively ties the upper
    # cheeks together; these pegs register the lower seam during assembly.
    for y, z in ((-8, 4.5), (13, 4.5), (34, 4.5)):
        peg = cq.Workplane("YZ", origin=(-3, y, z)).circle(PEG_R).extrude(8.0)
        lead = (
            cq.Workplane("YZ", origin=(4.2, y, z))
            .circle(PEG_R)
            .workplane(offset=.8)
            .circle(2.15)
            .loft()
        )
        left = left.union(peg).union(lead)
        socket = cq.Workplane("YZ", origin=(-.15, y, z)).circle(SOCKET_R).extrude(5.9)
        right = right.cut(socket)
    return left, right


def _ground(shape):
    b = shape.val().BoundingBox()
    return shape.translate((0, 0, -b.zmin))


def print_halves():
    left, right = frame_halves()
    # Put broad OUTER cheek faces on the bed. Seam/pegs/sockets face upward.
    left = _ground(left.rotate((0, 0, 0), (0, 1, 0), -90))
    right = _ground(right.rotate((0, 0, 0), (0, 1, 0), 90))
    return left, right


def main():
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    (OUT / "step").mkdir(parents=True, exist_ok=True)

    left, right = print_halves()
    parts = {"frame_left": left, "frame_right": right}
    records = []
    for name, part in parts.items():
        assert part.val().isValid() and len(part.solids().vals()) == 1
        cq.exporters.export(part, str(OUT / "stl" / f"{name}.stl"), tolerance=.025, angularTolerance=.10)
        cq.exporters.export(part, str(OUT / "step" / f"{name}.step"))
        mesh = trimesh.load_mesh(OUT / "stl" / f"{name}.stl")
        assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split()) == 1
        records.append({
            "part": name,
            "dimensions_mm": mesh.extents.round(3).tolist(),
            "solid_upper_mass_g": round(float(mesh.volume) * model.DENSITY, 2),
        })

    # Also export an assembled frame-only STEP for visual inspection.
    raw_left, raw_right = frame_halves()
    assy = cq.Assembly(name="Pocket_Cam_42_RevB_split_frame")
    assy.add(raw_left, name="frame_left", color=cq.Color(.25, .36, .48))
    assy.add(raw_right, name="frame_right", color=cq.Color(.31, .43, .55))
    assy.export(str(OUT / "step" / "frame_assembled.step"))

    manifest = {
        "revision": "Pocket-Cam-42-frame-rev-b",
        "reason": "physical Rev-A frame failed at support-dependent horizontal ledges",
        "reuse_existing_prints": ["carrier", "cam_lever", "axle", "axle_clip"],
        "print_now": ["frame_left", "frame_right"],
        "external_hardware_required": 0,
        "supports_for_frame_halves": False,
        "die_contract_mm": {"diameter": 42.0, "base": 3.0, "key_width": 6.0, "key_depth": 2.5},
        "seam": {"peg_radius_mm": PEG_R, "socket_radius_mm": SOCKET_R, "radial_clearance_mm": SOCKET_R - PEG_R},
        "parts": records,
        "print_settings": {
            "layer_height_mm": 0.20,
            "walls": 5,
            "infill_percent": 15,
            "infill": "grid or gyroid",
            "supports": "OFF",
            "brim_mm": "0-4 only if adhesion needs it",
        },
    }
    (OUT / "FRAME_REV_B.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
