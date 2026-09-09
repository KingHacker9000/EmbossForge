from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path
from typing import Any

from .cad import export_part
from .handheld_compact import HandLeverSpec, standard_handheld_die_spec
from .handheld_elegant import (
    PLA_DENSITY_G_CM3,
    _ellipse_yz,
    _keyed_cut,
    _polygon_extrude,
    _tapered_oval_xy,
    _yz_capsule,
)


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            'CadQuery is required for lever-press generation. Install with: pip install -e ".[cad]"'
        ) from exc
    return cq


def lean_test_spec(*, die_pocket_clearance_mm: float = 0.18) -> HandLeverSpec:
    """Compact low-material press that still accepts the full 42 mm die contract.

    This is intentionally not a uniform scale of the full elegant press: the die
    interface stays full size while the surrounding frame, guide walls and lever
    are reduced for a cheap first mechanism test.
    """

    spec = HandLeverSpec(
        body_width_mm=60.0,
        body_rear_y_mm=-47.0,
        body_front_y_mm=51.0,
        base_thickness_mm=4.5,
        die_center_y_mm=23.0,
        lower_jaw_width_mm=51.0,
        lower_jaw_depth_mm=47.0,
        lower_jaw_height_mm=3.5,
        die_pocket_clearance_mm=die_pocket_clearance_mm,
        die_seat_extra_depth_mm=0.05,
        removal_notch_radius_mm=4.0,
        carriage_width_mm=50.0,
        carriage_depth_mm=46.0,
        carriage_thickness_mm=6.0,
        guide_clearance_mm=0.35,
        guide_wall_thickness_mm=4.0,
        guide_front_y_mm=48.0,
        guide_rear_y_mm=3.0,
        guide_height_mm=30.0,
        pivot_y_mm=-8.0,
        pivot_z_mm=37.0,
        pivot_tower_rear_y_mm=-34.0,
        pivot_tower_front_y_mm=3.0,
        pivot_tower_height_mm=48.0,
        main_pivot_diameter_mm=6.4,
        drive_y_offset_mm=-18.0,
        drive_z_offset_mm=-6.0,
        drive_pin_diameter_mm=5.2,
        drive_pin_clearance_mm=0.50,
        open_travel_mm=11.0,
        lever_width_mm=18.0,
        lever_thickness_mm=8.0,
        lever_fork_height_mm=15.0,
        lever_rear_length_mm=125.0,
        lever_fork_rear_mm=-30.0,
        lever_fork_front_mm=10.0,
        lever_fork_slot_width_mm=11.8,
        stem_width_mm=10.5,
        stem_depth_mm=15.0,
        stem_top_margin_mm=3.5,
        neck_width_mm=10.5,
        cap_thickness_mm=2.2,
        cap_width_mm=50.0,
        cap_depth_mm=43.0,
        cap_boss_diameter_mm=36.0,
        cap_screw_clearance_mm=3.3,
        carriage_pilot_diameter_mm=2.6,
        cap_screw_x_mm=21.0,
    )
    spec.validate(standard_handheld_die_spec())
    return spec


def build_lean_test_body(spec: HandLeverSpec | None = None):
    spec = spec or lean_test_spec()
    die = standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    base = _tapered_oval_xy(
        center_y=1.5,
        y_radius=48.0,
        rear_halfwidth=18.5,
        front_halfwidth=29.0,
        height=spec.base_thickness_mm,
    )
    lower = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(25.5)
        .extrude(spec.lower_jaw_height_mm)
        .translate((0, 0, spec.base_thickness_mm))
    )
    body = base.union(lower)

    cheek_t = spec.guide_wall_thickness_mm
    guide_inner_x = spec.carriage_width_mm / 2 + spec.guide_clearance_mm
    cheek_x = guide_inner_x + cheek_t / 2
    for sign in (-1, 1):
        outer = _ellipse_yz(-1.5, 25.0, 43.0, 25.0, cheek_t, x_center=sign * cheek_x)
        inner = _ellipse_yz(5.0, 22.0, 33.0, 14.0, cheek_t + 2.0, x_center=sign * cheek_x)
        cheek = outer.cut(inner)
        trim = (
            cq.Workplane("XY")
            .box(spec.body_width_mm + 12.0, 120.0, 18.0, centered=(True, True, False))
            .translate((0, 0, -18.0))
        )
        cheek = cheek.cut(trim)

        guide_d = spec.guide_front_y_mm - spec.guide_rear_y_mm
        guide_y = (spec.guide_front_y_mm + spec.guide_rear_y_mm) / 2
        guide = (
            cq.Workplane("XY")
            .center(sign * cheek_x, guide_y)
            .box(cheek_t, guide_d, spec.guide_height_mm, centered=(True, True, False))
            .translate((0, 0, spec.base_thickness_mm))
        )
        body = body.union(cheek).union(guide)

    stop_h = spec.closed_carriage_bottom_z_mm(die) - spec.base_thickness_mm
    for sign in (-1, 1):
        stop = (
            cq.Workplane("XY")
            .center(sign * (spec.carriage_width_mm / 2 - 3.5), 7.5)
            .box(5.0, 6.0, stop_h, centered=(True, True, False))
            .translate((0, 0, spec.base_thickness_mm))
        )
        body = body.union(stop)

    pocket_depth = die.base_thickness_mm + spec.die_seat_extra_depth_mm
    pocket_z = spec.base_thickness_mm + spec.lower_jaw_height_mm - pocket_depth
    body = body.cut(_keyed_cut(die, spec, pocket_depth + 0.05, pocket_z))
    notch = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm + die.diameter_mm / 2)
        .circle(spec.removal_notch_radius_mm)
        .extrude(pocket_depth + 0.5)
        .translate((0, 0, pocket_z))
    )
    body = body.cut(notch)

    # Hollow the non-load-bearing rear floor while preserving a bottom skin,
    # top skin, perimeter rail and the entire die-support area.
    rear_pocket = (
        cq.Workplane("XY")
        .center(0, -22.0)
        .box(36.0, 48.0, 2.6, centered=(True, True, False))
        .translate((0, 0, 0.9))
    )
    body = body.cut(rear_pocket)

    pivot = (
        cq.Workplane("YZ")
        .center(spec.pivot_y_mm, spec.pivot_z_mm)
        .circle(spec.main_pivot_diameter_mm / 2)
        .extrude(spec.body_width_mm + 4.0, both=True)
    )
    return body.cut(pivot)


def build_lean_test_upper_carriage(spec: HandLeverSpec | None = None):
    spec = spec or lean_test_spec()
    die = standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    plate = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(25.5)
        .extrude(spec.carriage_thickness_mm)
    )
    ears = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(spec.carriage_width_mm, 15.0, spec.carriage_thickness_mm, centered=(True, True, False))
    )
    carriage = plate.union(ears)
    carriage = carriage.cut(_keyed_cut(die, spec, spec.carriage_thickness_mm + 0.4, -0.2))

    stem_y = spec.drive_pin_world_y_mm()
    plate_rear = spec.die_center_y_mm - 25.5
    neck_center = (plate_rear + stem_y) / 2
    neck_len = abs(plate_rear - stem_y) + 10.0
    neck = (
        cq.Workplane("XY")
        .center(0, neck_center)
        .ellipse(5.8, neck_len / 2)
        .extrude(spec.carriage_thickness_mm)
    )
    carriage = carriage.union(neck)

    pin_z = spec.stem_pin_local_z_mm(die)
    stem_h = (
        pin_z
        + (spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2
        + spec.stem_top_margin_mm
        - spec.carriage_thickness_mm
    )
    stem = (
        cq.Workplane("XY")
        .center(0, stem_y)
        .box(spec.stem_width_mm, spec.stem_depth_mm, stem_h, centered=(True, True, False))
        .translate((0, 0, spec.carriage_thickness_mm))
    )
    carriage = carriage.union(stem)

    bore = (
        cq.Workplane("YZ")
        .center(stem_y, pin_z)
        .circle((spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2)
        .extrude(spec.stem_width_mm + 4, both=True)
    )
    carriage = carriage.cut(bore)

    for sign in (-1, 1):
        pilot = (
            cq.Workplane("XY")
            .center(sign * spec.cap_screw_x_mm, spec.die_center_y_mm)
            .circle(spec.carriage_pilot_diameter_mm / 2)
            .extrude(5.0)
            .translate((0, 0, spec.carriage_thickness_mm - 5.0))
        )
        carriage = carriage.cut(pilot)
    return carriage


def build_lean_test_upper_cap(spec: HandLeverSpec | None = None):
    spec = spec or lean_test_spec()
    die = standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    cap = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(24.8)
        .extrude(spec.cap_thickness_mm)
    )
    ears = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(50.0, 9.0, spec.cap_thickness_mm, centered=(True, True, False))
    )
    cap = cap.union(ears)
    boss = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(spec.cap_boss_diameter_mm / 2)
        .extrude(spec.cap_boss_height_mm(die))
        .translate((0, 0, spec.cap_thickness_mm))
    )
    cap = cap.union(boss)
    for sign in (-1, 1):
        hole = (
            cq.Workplane("XY")
            .center(sign * spec.cap_screw_x_mm, spec.die_center_y_mm)
            .circle(spec.cap_screw_clearance_mm / 2)
            .extrude(spec.cap_thickness_mm + 0.5)
        )
        cap = cap.cut(hole)
    return cap


def _lever_profile(spec: HandLeverSpec):
    rear_y = -128.0
    front_y = 7.0
    samples = 72
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    for i in range(samples + 1):
        t = i / samples
        y = rear_y + (front_y - rear_y) * t
        zc = 15.0 * (1.0 - t) ** 1.15
        radius = 7.0 + 2.0 * (1.0 - t) ** 4 + 1.1 * t**5
        upper.append((y, zc + radius))
        lower.append((y, zc - radius))
    return _polygon_extrude("YZ", upper + list(reversed(lower)), spec.lever_width_mm / 2, both=True)


def _lever_lightening_window(spec: HandLeverSpec):
    rear_y = -119.0
    front_y = -39.0
    samples = 52
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    for i in range(samples + 1):
        y = rear_y + (front_y - rear_y) * i / samples
        t = (y + 128.0) / 135.0
        zc = 15.0 * (1.0 - t) ** 1.15
        outer_radius = 7.0 + 2.0 * (1.0 - t) ** 4 + 1.1 * t**5
        radius = max(outer_radius - 3.0, 1.8)
        upper.append((y, zc + radius))
        lower.append((y, zc - radius))
    return _polygon_extrude("YZ", upper + list(reversed(lower)), spec.lever_width_mm / 2 + 1.0, both=True)


def build_lean_test_lever(spec: HandLeverSpec | None = None):
    spec = spec or lean_test_spec()
    spec.validate(standard_handheld_die_spec())
    cq = _cq()

    lever = _lever_profile(spec).cut(_lever_lightening_window(spec))
    slot_y0 = spec.lever_fork_rear_mm - 3.0
    slot_y1 = spec.lever_fork_front_mm + 2.0
    slot = (
        cq.Workplane("XY")
        .box(spec.lever_fork_slot_width_mm, slot_y1 - slot_y0, 34.0, centered=(True, True, True))
        .translate((0, (slot_y0 + slot_y1) / 2, -1.0))
    )
    lever = lever.cut(slot)

    pivot = (
        cq.Workplane("YZ")
        .circle(spec.main_pivot_diameter_mm / 2)
        .extrude(spec.lever_width_mm + 4.0, both=True)
    )
    lever = lever.cut(pivot)
    drive = _yz_capsule(
        spec.drive_y_offset_mm - 1.4,
        spec.drive_y_offset_mm + 1.4,
        spec.drive_z_offset_mm,
        spec.drive_pin_diameter_mm / 2,
        spec.lever_width_mm + 4.0,
    )
    return lever.cut(drive)


def build_lean_test_assembly(spec: HandLeverSpec | None = None, *, state: str = "closed") -> dict[str, Any]:
    if state not in {"open", "closed"}:
        raise ValueError("state must be open or closed")
    spec = spec or lean_test_spec()
    die = standard_handheld_die_spec()
    carriage_z = spec.closed_carriage_bottom_z_mm(die)
    angle = 0.0
    if state == "open":
        carriage_z += spec.open_travel_mm
        angle = -spec.open_angle_deg

    lever = build_lean_test_lever(spec).translate((0, spec.pivot_y_mm, spec.pivot_z_mm))
    if angle:
        lever = lever.rotate(
            (0, spec.pivot_y_mm, spec.pivot_z_mm),
            (1, spec.pivot_y_mm, spec.pivot_z_mm),
            angle,
        )
    return {
        "body": build_lean_test_body(spec),
        "upper_carriage": build_lean_test_upper_carriage(spec).translate((0, 0, carriage_z)),
        "lever": lever,
    }


def validate_lean_test_clearance(spec: HandLeverSpec | None = None, *, tolerance_mm3: float = 1e-3):
    spec = spec or lean_test_spec()
    report: dict[str, list[tuple[str, str, float]]] = {}
    for state in ("closed", "open"):
        parts = build_lean_test_assembly(spec, state=state)
        names = list(parts)
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


def _axial_pin(*, shaft_diameter_mm: float, shaft_length_mm: float, head_diameter_mm: float, head_thickness_mm: float):
    cq = _cq()
    shaft = cq.Workplane("YZ").circle(shaft_diameter_mm / 2).extrude(shaft_length_mm / 2, both=True)
    head = (
        cq.Workplane("YZ")
        .circle(head_diameter_mm / 2)
        .extrude(head_thickness_mm)
        .translate((-shaft_length_mm / 2 - head_thickness_mm, 0, 0))
    )
    return shaft.union(head)


def _axial_retainer(*, outer_diameter_mm: float, bore_diameter_mm: float, thickness_mm: float):
    cq = _cq()
    return (
        cq.Workplane("YZ")
        .circle(outer_diameter_mm / 2)
        .circle(bore_diameter_mm / 2)
        .extrude(thickness_mm)
    )


def build_printed_main_pivot(spec: HandLeverSpec | None = None):
    spec = spec or lean_test_spec()
    return _axial_pin(
        shaft_diameter_mm=5.90,
        shaft_length_mm=spec.body_width_mm + 2.0,
        head_diameter_mm=10.0,
        head_thickness_mm=2.2,
    )


def build_printed_main_pivot_retainer():
    return _axial_retainer(outer_diameter_mm=9.5, bore_diameter_mm=5.70, thickness_mm=3.0)


def build_printed_drive_pin(spec: HandLeverSpec | None = None):
    spec = spec or lean_test_spec()
    return _axial_pin(
        shaft_diameter_mm=4.90,
        shaft_length_mm=spec.lever_width_mm + 3.0,
        head_diameter_mm=8.0,
        head_thickness_mm=1.8,
    )


def build_printed_drive_retainer():
    return _axial_retainer(outer_diameter_mm=7.5, bore_diameter_mm=4.70, thickness_mm=2.5)


def build_printed_cap_peg():
    cq = _cq()
    shaft = cq.Workplane("XY").circle(1.25).extrude(7.2)
    head = cq.Workplane("XY").circle(2.8).extrude(1.2).translate((0, 0, 7.2))
    tip = cq.Workplane("XY").circle(1.40).extrude(0.8)
    return shaft.union(head).union(tip)


def _solid_mass_g(part: Any) -> float:
    return float(part.val().Volume()) / 1000.0 * PLA_DENSITY_G_CM3


def export_lean_test_press_pack(out_dir: str | Path, *, die_pocket_clearance_mm: float = 0.18) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    spec = lean_test_spec(die_pocket_clearance_mm=die_pocket_clearance_mm)
    die = standard_handheld_die_spec()

    parts = {
        "body": build_lean_test_body(spec),
        "upper_carriage": build_lean_test_upper_carriage(spec),
        "upper_backing_cap": build_lean_test_upper_cap(spec),
        "lever": build_lean_test_lever(spec),
        "main_pivot_pin": build_printed_main_pivot(spec),
        "main_pivot_retainer": build_printed_main_pivot_retainer(),
        "drive_pin": build_printed_drive_pin(spec),
        "drive_pin_retainer": build_printed_drive_retainer(),
        "upper_cap_peg": build_printed_cap_peg(),
    }
    outputs: dict[str, str] = {}
    for name, part in parts.items():
        for ext in ("stl", "step"):
            outputs[f"{name}_{ext}"] = str(export_part(part, out / f"{name}.{ext}"))

    collisions = validate_lean_test_clearance(spec)
    if collisions["closed"] or collisions["open"]:
        raise RuntimeError("Lean test press contains unintended printed-part collisions:\n" + json.dumps(collisions, indent=2))

    masses = {name: round(_solid_mass_g(part), 2) for name, part in parts.items()}
    manifest = {
        "mode": "lean-full-size-42mm-handheld-test-press",
        "purpose": "low-material mechanism test using the user's already-printed standard 42 mm dies",
        "status": "CAD/software prototype; printed PLA pins are test-only",
        "exact_die_contract_mm": {
            "diameter": die.diameter_mm,
            "base_thickness": die.base_thickness_mm,
            "key_width": die.key_width_mm,
            "key_depth": die.key_depth_mm,
        },
        "press": asdict(spec),
        "derived": {
            "open_handle_angle_deg": spec.open_angle_deg,
            "open_travel_mm": spec.open_travel_mm,
            "nominal_lever_ratio": spec.nominal_lever_ratio,
            "solid_pla_mass_upper_bound_g": masses,
            "solid_pla_mass_total_upper_bound_g": round(sum(masses.values()) + masses["upper_cap_peg"], 2),
        },
        "printed_quantities": {
            "body": 1,
            "upper_carriage": 1,
            "upper_backing_cap": 1,
            "lever": 1,
            "main_pivot_pin": 1,
            "main_pivot_retainer": 1,
            "drive_pin": 1,
            "drive_pin_retainer": 1,
            "upper_cap_peg": 2,
        },
        "hardware_policy": {
            "test": "all required retainers/pins are printable in this pack; no metal hardware required",
            "final": "replace printed pivot/drive pins with metal M6/M5 hardware before high-force use",
        },
        "collision_validation": collisions,
        "outputs": outputs,
    }
    manifest_path = out / "lean_test_press_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    outputs["manifest"] = str(manifest_path)
    return outputs


if __name__ == "__main__":
    generated = export_lean_test_press_pack(Path("build") / "lean-lever-press-test")
    print("Generated lean full-size 42 mm test press")
    for key, value in generated.items():
        print(f"  {key}: {value}")
