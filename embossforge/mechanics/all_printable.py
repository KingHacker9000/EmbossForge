from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path
from typing import Any

from .cad import export_part
from .handheld_compact import HandLeverSpec, standard_handheld_die_spec
from .handheld_elegant import PLA_DENSITY_G_CM3, _keyed_cut, _polygon_extrude, _yz_capsule


UPPER_DIE_FACE_LOCAL_Z_MM = 1.0


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            'CadQuery is required for press generation. Install with: pip install -e ".[cad]"'
        ) from exc
    return cq


def fully_printable_spec(*, die_pocket_clearance_mm: float = 0.20) -> HandLeverSpec:
    """Support-free-ish PLA press built around the existing standard 42 mm dies.

    The mechanism deliberately uses no threaded fasteners, metal rods, bearings,
    nuts, springs, or other purchased hardware. Two printed slotted pins and two
    identical printed wedges retain the linkage. Two small printed push-pegs
    retain the upper-die cap.
    """

    spec = HandLeverSpec(
        body_width_mm=64.0,
        body_rear_y_mm=-50.0,
        body_front_y_mm=58.0,
        base_thickness_mm=6.0,
        die_center_y_mm=28.0,
        lower_jaw_width_mm=54.0,
        lower_jaw_depth_mm=54.0,
        lower_jaw_height_mm=4.0,
        die_pocket_clearance_mm=die_pocket_clearance_mm,
        die_seat_extra_depth_mm=0.05,
        removal_notch_radius_mm=4.5,
        carriage_width_mm=52.0,
        carriage_depth_mm=52.0,
        carriage_thickness_mm=6.0,
        guide_clearance_mm=0.45,
        guide_wall_thickness_mm=5.0,
        guide_front_y_mm=54.0,
        guide_rear_y_mm=2.0,
        guide_height_mm=24.0,
        pivot_y_mm=-12.0,
        pivot_z_mm=32.0,
        pivot_tower_rear_y_mm=-23.0,
        pivot_tower_front_y_mm=-1.0,
        pivot_tower_height_mm=40.0,
        main_pivot_diameter_mm=6.4,
        drive_y_offset_mm=-18.0,
        drive_z_offset_mm=-7.0,
        drive_pin_diameter_mm=5.4,
        drive_pin_clearance_mm=0.40,
        open_travel_mm=10.0,
        lever_width_mm=20.0,
        lever_thickness_mm=9.0,
        lever_fork_height_mm=16.0,
        lever_rear_length_mm=145.0,
        lever_fork_rear_mm=-31.0,
        lever_fork_front_mm=13.0,
        lever_fork_slot_width_mm=11.8,
        stem_width_mm=10.6,
        stem_depth_mm=14.0,
        stem_top_margin_mm=4.0,
        neck_width_mm=10.6,
        cap_thickness_mm=2.4,
        cap_width_mm=52.0,
        cap_depth_mm=52.0,
        cap_boss_diameter_mm=34.0,
        cap_screw_clearance_mm=2.9,
        carriage_pilot_diameter_mm=2.55,
        cap_screw_x_mm=23.2,
    )
    spec.validate(standard_handheld_die_spec())
    return spec


def _box_xy(width: float, depth: float, height: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    cq = _cq()
    return (
        cq.Workplane("XY")
        .box(width, depth, height, centered=(True, True, False))
        .translate((x, y, z))
    )


def _lower_die_face_z(spec: HandLeverSpec) -> float:
    die = standard_handheld_die_spec()
    platform_top = spec.base_thickness_mm + spec.lower_jaw_height_mm
    pocket_depth = die.base_thickness_mm + spec.die_seat_extra_depth_mm
    return platform_top - pocket_depth + die.base_thickness_mm


def _closed_carriage_origin_z(spec: HandLeverSpec) -> float:
    die = standard_handheld_die_spec()
    target_female_face = _lower_die_face_z(spec) + die.paper_thickness_mm
    return target_female_face - UPPER_DIE_FACE_LOCAL_Z_MM


def _drive_pin_local_z(spec: HandLeverSpec) -> float:
    return spec.drive_pin_closed_z_mm() - _closed_carriage_origin_z(spec)


def build_fully_printable_body(spec: HandLeverSpec | None = None):
    spec = spec or fully_printable_spec()
    die = standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    # Open ladder-like base: two rails + front/rear ties + a solid die island.
    rail_w = 6.0
    rail_y = (spec.body_rear_y_mm + spec.body_front_y_mm) / 2.0
    rail_d = spec.body_front_y_mm - spec.body_rear_y_mm
    body = _box_xy(rail_w, rail_d, spec.base_thickness_mm, x=-(spec.body_width_mm - rail_w) / 2, y=rail_y)
    body = body.union(_box_xy(rail_w, rail_d, spec.base_thickness_mm, x=(spec.body_width_mm - rail_w) / 2, y=rail_y))
    body = body.union(_box_xy(spec.body_width_mm, 7.0, spec.base_thickness_mm, y=spec.body_front_y_mm - 3.5))
    body = body.union(_box_xy(spec.body_width_mm, 9.0, spec.base_thickness_mm, y=spec.body_rear_y_mm + 4.5))

    platform = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(27.0)
        .extrude(spec.base_thickness_mm + spec.lower_jaw_height_mm)
    )
    body = body.union(platform)

    # Broad vertical guide rails. They are only 24 mm high and 5 mm thick so
    # a 0.4 mm nozzle can print them as stable walls rather than skinny towers.
    guide_inner_x = spec.carriage_width_mm / 2.0 + spec.guide_clearance_mm
    guide_x = guide_inner_x + spec.guide_wall_thickness_mm / 2.0
    guide_depth = spec.guide_front_y_mm - spec.guide_rear_y_mm
    guide_y = (spec.guide_front_y_mm + spec.guide_rear_y_mm) / 2.0
    for sign in (-1, 1):
        body = body.union(
            _box_xy(
                spec.guide_wall_thickness_mm,
                guide_depth,
                spec.guide_height_mm,
                x=sign * guide_x,
                y=guide_y,
                z=spec.base_thickness_mm,
            )
        )
        # 45-degree-ish gusset block at the rear of each guide.
        gusset = (
            cq.Workplane("YZ")
            .polyline(
                [
                    (spec.guide_rear_y_mm - 10.0, spec.base_thickness_mm),
                    (spec.guide_rear_y_mm + 5.0, spec.base_thickness_mm),
                    (spec.guide_rear_y_mm + 5.0, spec.base_thickness_mm + 18.0),
                ]
            )
            .close()
            .extrude(spec.guide_wall_thickness_mm / 2.0, both=True)
            .translate((sign * guide_x, 0, 0))
        )
        body = body.union(gusset)

    # Compact central pivot ears: the pin spans only ~32 mm, not the full body.
    tower_t = 5.0
    lever_clear = 1.0
    tower_x = spec.lever_width_mm / 2.0 + lever_clear + tower_t / 2.0
    tower_depth = spec.pivot_tower_front_y_mm - spec.pivot_tower_rear_y_mm
    tower_y = (spec.pivot_tower_front_y_mm + spec.pivot_tower_rear_y_mm) / 2.0
    for sign in (-1, 1):
        tower = _box_xy(
            tower_t,
            tower_depth,
            spec.pivot_tower_height_mm - spec.base_thickness_mm,
            x=sign * tower_x,
            y=tower_y,
            z=spec.base_thickness_mm,
        )
        body = body.union(tower)

    pivot = (
        cq.Workplane("YZ")
        .center(spec.pivot_y_mm, spec.pivot_z_mm)
        .circle(spec.main_pivot_diameter_mm / 2.0)
        .extrude(40.0, both=True)
    )
    body = body.cut(pivot)

    # Existing 42 mm keyed male drops directly into this pocket.
    pocket_depth = die.base_thickness_mm + spec.die_seat_extra_depth_mm
    pocket_z = spec.base_thickness_mm + spec.lower_jaw_height_mm - pocket_depth
    body = body.cut(_keyed_cut(die, spec, pocket_depth + 0.08, pocket_z))
    notch = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm + die.diameter_mm / 2.0)
        .circle(spec.removal_notch_radius_mm)
        .extrude(pocket_depth + 0.6)
        .translate((0, 0, pocket_z))
    )
    return body.cut(notch)


def build_fully_printable_upper_carriage(spec: HandLeverSpec | None = None):
    spec = spec or fully_printable_spec()
    die = standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    # Main plate intentionally starts at Z=1 mm. The die face rests on the
    # 0.6..1.0 mm annular support lip, making its face flush with the plate
    # underside instead of recessed behind plastic.
    plate = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(spec.carriage_width_mm / 2.0)
        .extrude(spec.carriage_thickness_mm - 1.0)
        .translate((0, 0, 1.0))
    )
    plate = plate.cut(_keyed_cut(die, spec, spec.carriage_thickness_mm + 0.5, 0.8))

    clear = spec.die_pocket_clearance_mm
    lip_outer = die.diameter_mm / 2.0 + clear - 0.18
    lip_inner = die.diameter_mm / 2.0 - 2.0
    lip = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(lip_outer)
        .circle(lip_inner)
        .extrude(0.4)
        .translate((0, 0, 0.6))
    )
    key_support = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm + die.diameter_mm / 2.0 + die.key_depth_mm / 2.0 - 0.35)
        .rect(die.key_width_mm + 0.4, max(1.2, die.key_depth_mm - 0.4))
        .extrude(0.4)
        .translate((0, 0, 0.6))
    )
    carriage = plate.union(lip).union(key_support)

    # Rear neck and vertical stem for the simple two-pin linkage.
    stem_y = spec.drive_pin_world_y_mm()
    plate_rear = spec.die_center_y_mm - spec.carriage_width_mm / 2.0
    neck_y = (plate_rear + stem_y) / 2.0
    neck_depth = abs(plate_rear - stem_y) + 10.0
    neck = _box_xy(spec.neck_width_mm, neck_depth, spec.carriage_thickness_mm - 1.0, y=neck_y, z=1.0)
    carriage = carriage.union(neck)

    pin_z = _drive_pin_local_z(spec)
    stem_h = pin_z + (spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2.0 + spec.stem_top_margin_mm - 1.0
    stem = _box_xy(spec.stem_width_mm, spec.stem_depth_mm, stem_h, y=stem_y, z=1.0)
    carriage = carriage.union(stem)

    drive_bore = (
        cq.Workplane("YZ")
        .center(stem_y, pin_z)
        .circle((spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2.0)
        .extrude(spec.stem_width_mm + 4.0, both=True)
    )
    carriage = carriage.cut(drive_bore)

    # Two simple vertical push-peg holes retain the cap; no screw threads.
    for sign in (-1, 1):
        peg_hole = (
            cq.Workplane("XY")
            .center(sign * spec.cap_screw_x_mm, spec.die_center_y_mm)
            .circle(spec.carriage_pilot_diameter_mm / 2.0)
            .extrude(spec.carriage_thickness_mm + 1.0)
        )
        carriage = carriage.cut(peg_hole)
    return carriage


def build_fully_printable_upper_cap(spec: HandLeverSpec | None = None):
    spec = spec or fully_printable_spec()
    cq = _cq()

    cap = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(25.0)
        .extrude(spec.cap_thickness_mm)
    )
    # Underside boss presses the female die's flat back against the support lip.
    boss = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(spec.cap_boss_diameter_mm / 2.0)
        .extrude(2.0)
        .translate((0, 0, -2.0))
    )
    cap = cap.union(boss)
    for sign in (-1, 1):
        hole = (
            cq.Workplane("XY")
            .center(sign * spec.cap_screw_x_mm, spec.die_center_y_mm)
            .circle(spec.cap_screw_clearance_mm / 2.0)
            .extrude(spec.cap_thickness_mm + 0.4)
        )
        cap = cap.cut(hole)
    return cap


def _lever_profile(spec: HandLeverSpec):
    rear_y = -150.0
    front_y = 10.0
    samples = 80
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    for i in range(samples + 1):
        t = i / samples
        y = rear_y + (front_y - rear_y) * t
        zc = 14.0 * (1.0 - t) ** 1.15
        radius = 7.2 + 1.8 * (1.0 - t) ** 3 + 1.0 * t**5
        upper.append((y, zc + radius))
        lower.append((y, zc - radius))
    return _polygon_extrude("YZ", upper + list(reversed(lower)), spec.lever_width_mm / 2.0, both=True)


def _lever_window(spec: HandLeverSpec):
    rear_y = -139.0
    front_y = -44.0
    samples = 56
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    for i in range(samples + 1):
        y = rear_y + (front_y - rear_y) * i / samples
        t = (y + 150.0) / 160.0
        zc = 14.0 * (1.0 - t) ** 1.15
        outer = 7.2 + 1.8 * (1.0 - t) ** 3 + 1.0 * t**5
        inner = max(outer - 3.0, 2.2)
        upper.append((y, zc + inner))
        lower.append((y, zc - inner))
    return _polygon_extrude("YZ", upper + list(reversed(lower)), spec.lever_width_mm / 2.0 + 1.0, both=True)


def build_fully_printable_lever(spec: HandLeverSpec | None = None):
    spec = spec or fully_printable_spec()
    spec.validate(standard_handheld_die_spec())
    cq = _cq()

    lever = _lever_profile(spec).cut(_lever_window(spec))

    # Fork around the carriage stem.
    slot_y0 = spec.lever_fork_rear_mm - 3.0
    slot_y1 = spec.lever_fork_front_mm + 2.0
    slot = (
        cq.Workplane("XY")
        .box(spec.lever_fork_slot_width_mm, slot_y1 - slot_y0, 34.0, centered=(True, True, True))
        .translate((0, (slot_y0 + slot_y1) / 2.0, -1.0))
    )
    lever = lever.cut(slot)

    pivot = (
        cq.Workplane("YZ")
        .circle(spec.main_pivot_diameter_mm / 2.0)
        .extrude(spec.lever_width_mm + 4.0, both=True)
    )
    lever = lever.cut(pivot)

    drive = _yz_capsule(
        spec.drive_y_offset_mm - 1.3,
        spec.drive_y_offset_mm + 1.3,
        spec.drive_z_offset_mm,
        spec.drive_pin_diameter_mm / 2.0,
        spec.lever_width_mm + 4.0,
    )
    return lever.cut(drive)


def build_slotted_pin(*, shaft_diameter_mm: float, shaft_length_mm: float, head_diameter_mm: float):
    """Vertical-print pin with a rectangular cotter slot near the tip."""
    cq = _cq()
    head_t = 2.4
    shaft = (
        cq.Workplane("XY")
        .circle(shaft_diameter_mm / 2.0)
        .extrude(shaft_length_mm)
        .translate((0, 0, head_t))
    )
    head = cq.Workplane("XY").circle(head_diameter_mm / 2.0).extrude(head_t)
    pin = shaft.union(head)
    slot_z = head_t + shaft_length_mm - 4.0
    slot = (
        cq.Workplane("XZ")
        .center(0, slot_z)
        .rect(2.4, 5.0)
        .extrude(shaft_diameter_mm + 2.0, both=True)
    )
    return pin.cut(slot)


def build_main_pivot_pin(spec: HandLeverSpec | None = None):
    spec = spec or fully_printable_spec()
    # Two 5 mm ears + 22 mm center gap + small axial clearance.
    return build_slotted_pin(shaft_diameter_mm=5.9, shaft_length_mm=33.5, head_diameter_mm=10.0)


def build_drive_pin(spec: HandLeverSpec | None = None):
    spec = spec or fully_printable_spec()
    return build_slotted_pin(shaft_diameter_mm=4.9, shaft_length_mm=23.0, head_diameter_mm=8.5)


def build_retaining_wedge():
    cq = _cq()
    points = [(0.0, -2.4), (11.0, -1.3), (11.0, 1.3), (0.0, 2.4)]
    return cq.Workplane("XY").polyline(points).close().extrude(2.0)


def build_cap_peg():
    """Small barbed push-rivet; print two vertically with the head on the bed."""
    cq = _cq()
    head = cq.Workplane("XY").circle(2.8).extrude(1.4)
    shaft = cq.Workplane("XY").circle(1.20).extrude(7.0).translate((0, 0, 1.4))
    barb = (
        cq.Workplane("XY")
        .circle(1.45)
        .circle(1.05)
        .extrude(0.8)
        .translate((0, 0, 6.6))
    )
    return head.union(shaft).union(barb)


def build_fully_printable_assembly(spec: HandLeverSpec | None = None, *, state: str = "closed") -> dict[str, Any]:
    if state not in {"open", "closed"}:
        raise ValueError("state must be open or closed")
    spec = spec or fully_printable_spec()
    die = standard_handheld_die_spec()
    spec.validate(die)

    carriage_z = _closed_carriage_origin_z(spec)
    angle = 0.0
    if state == "open":
        carriage_z += spec.open_travel_mm
        angle = -spec.open_angle_deg

    lever = build_fully_printable_lever(spec).translate((0, spec.pivot_y_mm, spec.pivot_z_mm))
    if angle:
        lever = lever.rotate(
            (0, spec.pivot_y_mm, spec.pivot_z_mm),
            (1, spec.pivot_y_mm, spec.pivot_z_mm),
            angle,
        )

    cap = build_fully_printable_upper_cap(spec).translate((0, 0, carriage_z + spec.carriage_thickness_mm))
    return {
        "body": build_fully_printable_body(spec),
        "upper_carriage": build_fully_printable_upper_carriage(spec).translate((0, 0, carriage_z)),
        "upper_die_cap": cap,
        "lever": lever,
    }


def validate_fully_printable_clearance(
    spec: HandLeverSpec | None = None,
    *,
    tolerance_mm3: float = 1e-3,
) -> dict[str, list[tuple[str, str, float]]]:
    spec = spec or fully_printable_spec()
    report: dict[str, list[tuple[str, str, float]]] = {}
    # Cap intentionally clamps the carriage and is excluded from collision-pair
    # testing. Body/carriage/lever must remain mutually collision-free.
    for state in ("closed", "open"):
        parts = build_fully_printable_assembly(spec, state=state)
        names = ["body", "upper_carriage", "lever"]
        collisions: list[tuple[str, str, float]] = []
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                try:
                    volume = float(parts[left].intersect(parts[right]).val().Volume())
                except Exception:
                    volume = 0.0
                if volume > tolerance_mm3:
                    collisions.append((left, right, volume))
        report[state] = collisions
    return report


def _ground(part: Any):
    zmin = float(part.val().BoundingBox().zmin)
    return part.translate((0, 0, -zmin))


def _print_oriented_lever(spec: HandLeverSpec):
    # Lay the broad YZ face on the bed. Maximum printed height becomes the
    # lever width (~20 mm) instead of the tall curved assembly profile.
    return _ground(build_fully_printable_lever(spec).rotate((0, 0, 0), (0, 1, 0), 90.0))


def _solid_mass_g(part: Any) -> float:
    return float(part.val().Volume()) / 1000.0 * PLA_DENSITY_G_CM3


def export_fully_printable_press_pack(
    out_dir: str | Path,
    *,
    die_pocket_clearance_mm: float = 0.20,
) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    spec = fully_printable_spec(die_pocket_clearance_mm=die_pocket_clearance_mm)
    die = standard_handheld_die_spec()

    collisions = validate_fully_printable_clearance(spec)
    if collisions["closed"] or collisions["open"]:
        raise RuntimeError(
            "Fully printable press contains unintended printed-part collisions:\n"
            + json.dumps(collisions, indent=2)
        )

    assembly_parts = {
        "body": build_fully_printable_body(spec),
        "upper_carriage": build_fully_printable_upper_carriage(spec),
        "upper_die_cap": build_fully_printable_upper_cap(spec),
        "lever": build_fully_printable_lever(spec),
        "main_pivot_pin": build_main_pivot_pin(spec),
        "drive_pin": build_drive_pin(spec),
        "retaining_wedge": build_retaining_wedge(),
        "cap_peg": build_cap_peg(),
    }
    print_parts = dict(assembly_parts)
    print_parts["lever"] = _print_oriented_lever(spec)

    outputs: dict[str, str] = {}
    for name, part in print_parts.items():
        outputs[f"{name}_stl"] = str(export_part(_ground(part), out / f"{name}.stl"))
    for name, part in assembly_parts.items():
        outputs[f"{name}_step"] = str(export_part(part, out / f"{name}.step"))

    closed = build_fully_printable_assembly(spec, state="closed")
    opened = build_fully_printable_assembly(spec, state="open")
    cq = _cq()
    closed_compound = cq.Compound.makeCompound([shape.val() for shape in closed.values()])
    open_compound = cq.Compound.makeCompound([shape.val() for shape in opened.values()])
    outputs["assembly_closed_step"] = str(export_part(cq.Workplane(obj=closed_compound), out / "assembly_closed.step"))
    outputs["assembly_open_step"] = str(export_part(cq.Workplane(obj=open_compound), out / "assembly_open.step"))

    masses = {name: round(_solid_mass_g(part), 2) for name, part in assembly_parts.items()}
    quantities = {
        "body": 1,
        "upper_carriage": 1,
        "upper_die_cap": 1,
        "lever": 1,
        "main_pivot_pin": 1,
        "drive_pin": 1,
        "retaining_wedge": 2,
        "cap_peg": 2,
    }
    estimated_solid_total = sum(masses[name] * qty for name, qty in quantities.items())
    assembly = {
        "coordinate_system": "+Y is the paper-insertion nose; +Z is up",
        "existing_die_compatibility": "standard 42 mm EmbossForge keyed male/female dies; no new dies required",
        "steps": [
            "Drop the existing male die face-up into the keyed lower pocket.",
            "Place the existing female die face-down into the keyed upper carriage from above.",
            "Place upper_die_cap over the female die and press two cap_peg parts through the matching holes.",
            "Slide the upper carriage between the two guide walls with its stem pointing toward the rear pivot.",
            "Place the lever fork around the carriage stem.",
            "Align the main pivot holes, insert main_pivot_pin, then lock it with one retaining_wedge through the pin slot.",
            "Align the lever/carriage drive holes, insert drive_pin, then lock it with the second retaining_wedge.",
            "Raise/lower the handle by hand before inserting paper; nothing should bind.",
        ],
        "print_notes": {
            "nozzle": "0.4 mm",
            "supports": "off; parts are authored for support-free or minimal-bridge printing",
            "body_carriage_cap": "0.24-0.28 mm layers, 3 walls, 10-15% infill",
            "lever": "print exported lever.stl as-is; it is already laid on its broad side",
            "pins_pegs_wedges": "0.20 mm layers, 4 walls, 100% infill, print slower than the large parts",
            "speed": "for this prototype keep outer walls around 60-80 mm/s and small parts around 40-60 mm/s",
        },
    }
    layout = out / "assembly_layout.json"
    layout.write_text(json.dumps(assembly, indent=2) + "\n", encoding="utf-8")
    outputs["assembly_layout"] = str(layout)

    manifest = {
        "mode": "all-3d-printable-42mm-lever-embosser-v4",
        "status": "CAD/software prototype; first physical validation pending",
        "design_goals": [
            "all functional hardware is printed",
            "0.4 mm nozzle compatible",
            "existing 42 mm keyed dies fit directly",
            "no threads, screws, nuts, rods, bearings, or metal hardware",
            "low, broad print orientations instead of tall skinny structures",
        ],
        "exact_die_contract_mm": {
            "diameter": die.diameter_mm,
            "base_thickness": die.base_thickness_mm,
            "key_width": die.key_width_mm,
            "key_depth": die.key_depth_mm,
        },
        "press": asdict(spec),
        "derived": {
            "lower_die_face_z_mm": _lower_die_face_z(spec),
            "closed_upper_carriage_origin_z_mm": _closed_carriage_origin_z(spec),
            "open_handle_angle_deg": spec.open_angle_deg,
            "open_travel_mm": spec.open_travel_mm,
            "nominal_lever_ratio": spec.nominal_lever_ratio,
            "solid_pla_mass_upper_bound_by_unique_part_g": masses,
            "solid_pla_mass_total_with_quantities_g": round(estimated_solid_total, 2),
        },
        "printed_quantities": quantities,
        "external_hardware_required": [],
        "collision_validation": collisions,
        "assembly": assembly,
        "outputs": outputs,
    }
    manifest_path = out / "all_printable_press_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    outputs["manifest"] = str(manifest_path)
    return outputs
