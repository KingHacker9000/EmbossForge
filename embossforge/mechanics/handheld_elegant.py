from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path
from typing import Any

from ..config import DieSpec
from .cad import export_part
from .handheld_compact import HandLeverSpec, hand_lever_spec, standard_handheld_die_spec


PLA_DENSITY_G_CM3 = 1.24


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            'CadQuery is required for lever-press generation. Install with: pip install -e ".[cad]"'
        ) from exc
    return cq


def elegant_lever_spec(*, die_pocket_clearance_mm: float = 0.15) -> HandLeverSpec:
    spec = hand_lever_spec(die_pocket_clearance_mm=die_pocket_clearance_mm)
    spec.validate(standard_handheld_die_spec())
    return spec


def _keyed_cut(die: DieSpec, spec: HandLeverSpec, depth_mm: float, z0: float):
    cq = _cq()
    clear = spec.die_pocket_clearance_mm
    circle = cq.Workplane("XY").circle((die.diameter_mm + 2 * clear) / 2).extrude(depth_mm)
    overlap = 0.5
    tab_depth = die.key_depth_mm + overlap + 2 * clear
    tab_y = die.diameter_mm / 2 + (die.key_depth_mm - overlap) / 2
    tab = (
        cq.Workplane("XY")
        .center(0, tab_y)
        .rect(die.key_width_mm + 2 * clear, tab_depth)
        .extrude(depth_mm)
    )
    return circle.union(tab).translate((0, spec.die_center_y_mm, z0))


def _polygon_extrude(plane: str, points: list[tuple[float, float]], distance: float, *, both: bool = False):
    cq = _cq()
    if len(points) < 3:
        raise ValueError("profile requires at least three points")
    return cq.Workplane(plane).polyline(points).close().extrude(distance, both=both)


def _tapered_oval_xy(
    center_y: float,
    y_radius: float,
    rear_halfwidth: float,
    front_halfwidth: float,
    height: float,
    *,
    samples: int = 96,
):
    points: list[tuple[float, float]] = []
    for i in range(samples):
        a = 2.0 * math.pi * i / samples
        y = center_y + y_radius * math.sin(a)
        blend = (y - (center_y - y_radius)) / (2.0 * y_radius)
        halfwidth = rear_halfwidth + (front_halfwidth - rear_halfwidth) * blend
        x = halfwidth * math.cos(a)
        points.append((x, y))
    return _polygon_extrude("XY", points, height)


def _ellipse_yz(
    center_y: float,
    center_z: float,
    radius_y: float,
    radius_z: float,
    width: float,
    *,
    x_center: float = 0.0,
    samples: int = 96,
):
    points = [
        (
            center_y + radius_y * math.cos(2.0 * math.pi * i / samples),
            center_z + radius_z * math.sin(2.0 * math.pi * i / samples),
        )
        for i in range(samples)
    ]
    return _polygon_extrude("YZ", points, width / 2.0, both=True).translate((x_center, 0, 0))


def _lever_profile(spec: HandLeverSpec):
    samples = 80
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    rear_y = -155.0
    front_y = 8.0
    for i in range(samples + 1):
        t = i / samples
        y = rear_y + (front_y - rear_y) * t
        zc = 19.0 * (1.0 - t) ** 1.15
        radius = 9.0 + 2.6 * (1.0 - t) ** 4 + 1.5 * t**5
        upper.append((y, zc + radius))
        lower.append((y, zc - radius))
    return _polygon_extrude("YZ", upper + list(reversed(lower)), spec.lever_width_mm / 2.0, both=True)


def _yz_capsule(y0: float, y1: float, z: float, radius: float, width: float):
    cq = _cq()
    yc = (y0 + y1) / 2.0
    length = abs(y1 - y0)
    bar = (
        cq.Workplane("YZ")
        .center(yc, z)
        .rect(max(length, 0.01), 2.0 * radius)
        .extrude(width / 2.0, both=True)
    )
    for y in (y0, y1):
        cap = (
            cq.Workplane("YZ")
            .center(y, z)
            .circle(radius)
            .extrude(width / 2.0, both=True)
        )
        bar = bar.union(cap)
    return bar


def build_elegant_body(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    spec = spec or elegant_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    base = _tapered_oval_xy(
        center_y=-1.0,
        y_radius=61.0,
        rear_halfwidth=23.0,
        front_halfwidth=31.5,
        height=spec.base_thickness_mm,
    )

    lower = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(28.0)
        .extrude(spec.lower_jaw_height_mm)
        .translate((0, 0, spec.base_thickness_mm))
    )
    body = base.union(lower)

    cheek_t = spec.guide_wall_thickness_mm
    guide_inner_x = spec.carriage_width_mm / 2 + spec.guide_clearance_mm
    cheek_x = guide_inner_x + cheek_t / 2

    for sign in (-1, 1):
        outer = _ellipse_yz(-1.0, 29.0, 54.0, 30.0, cheek_t, x_center=sign * cheek_x)
        inner = _ellipse_yz(8.0, 25.0, 41.0, 17.0, cheek_t + 2.0, x_center=sign * cheek_x)
        cheek = outer.cut(inner)

        trim = (
            cq.Workplane("XY")
            .box(spec.body_width_mm + 20.0, 150.0, 20.0, centered=(True, True, False))
            .translate((0, 0, -20.0))
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

        accent_x = sign * (cheek_x + cheek_t / 2 - 0.4)
        accent = _ellipse_yz(2.0, 37.0, 20.0, 3.0, 0.8, x_center=accent_x)
        body = body.cut(accent)

    stop_h = spec.closed_carriage_bottom_z_mm(die) - spec.base_thickness_mm
    for sign in (-1, 1):
        stop = (
            cq.Workplane("XY")
            .center(sign * (spec.carriage_width_mm / 2 - 4.0), 8.5)
            .box(6.0, 7.0, stop_h, centered=(True, True, False))
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

    pivot = (
        cq.Workplane("YZ")
        .center(spec.pivot_y_mm, spec.pivot_z_mm)
        .circle(spec.main_pivot_diameter_mm / 2)
        .extrude(spec.body_width_mm + 4, both=True)
    )
    return body.cut(pivot)


def build_elegant_upper_carriage(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    spec = spec or elegant_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    plate = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(28.0)
        .extrude(spec.carriage_thickness_mm)
    )
    ears = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(spec.carriage_width_mm, 18.0, spec.carriage_thickness_mm, centered=(True, True, False))
    )
    carriage = plate.union(ears)
    carriage = carriage.cut(_keyed_cut(die, spec, spec.carriage_thickness_mm + 0.4, -0.2))

    stem_y = spec.drive_pin_world_y_mm()
    plate_rear = spec.die_center_y_mm - 28.0
    neck_center = (plate_rear + stem_y) / 2.0
    neck_len = abs(plate_rear - stem_y) + 12.0
    neck = (
        cq.Workplane("XY")
        .center(0, neck_center)
        .ellipse(7.0, neck_len / 2.0)
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
            .extrude(5.5)
            .translate((0, 0, spec.carriage_thickness_mm - 5.5))
        )
        carriage = carriage.cut(pilot)
    return carriage


def build_elegant_upper_cap(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    spec = spec or elegant_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    cap = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(27.0)
        .extrude(spec.cap_thickness_mm)
    )
    ears = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(56.0, 12.0, spec.cap_thickness_mm, centered=(True, True, False))
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


def build_elegant_lever(spec: HandLeverSpec | None = None):
    spec = spec or elegant_lever_spec()
    spec.validate(standard_handheld_die_spec())
    cq = _cq()

    lever = _lever_profile(spec)

    slot_y0 = spec.lever_fork_rear_mm - 3.0
    slot_y1 = spec.lever_fork_front_mm + 2.0
    slot = (
        cq.Workplane("XY")
        .box(spec.lever_fork_slot_width_mm, slot_y1 - slot_y0, 40.0, centered=(True, True, True))
        .translate((0, (slot_y0 + slot_y1) / 2.0, -1.0))
    )
    lever = lever.cut(slot)

    pivot = (
        cq.Workplane("YZ")
        .circle(spec.main_pivot_diameter_mm / 2)
        .extrude(spec.lever_width_mm + 4, both=True)
    )
    lever = lever.cut(pivot)

    drive = _yz_capsule(
        spec.drive_y_offset_mm - 1.6,
        spec.drive_y_offset_mm + 1.6,
        spec.drive_z_offset_mm,
        spec.drive_pin_diameter_mm / 2.0,
        spec.lever_width_mm + 4.0,
    )
    lever = lever.cut(drive)

    for sign in (-1, 1):
        x = sign * (spec.lever_width_mm / 2.0 - 0.45)
        recess = _ellipse_yz(-108.0, 17.0, 38.0, 5.2, 0.9, x_center=x)
        lever = lever.cut(recess)
    return lever


def build_elegant_assembly(
    spec: HandLeverSpec | None = None,
    die: DieSpec | None = None,
    *,
    state: str = "closed",
) -> dict[str, Any]:
    if state not in {"open", "closed"}:
        raise ValueError("state must be open or closed")
    spec = spec or elegant_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)

    carriage_z = spec.closed_carriage_bottom_z_mm(die)
    angle = 0.0
    if state == "open":
        carriage_z += spec.open_travel_mm
        angle = -spec.open_angle_deg

    lever = build_elegant_lever(spec).translate((0, spec.pivot_y_mm, spec.pivot_z_mm))
    if angle:
        lever = lever.rotate(
            (0, spec.pivot_y_mm, spec.pivot_z_mm),
            (1, spec.pivot_y_mm, spec.pivot_z_mm),
            angle,
        )
    return {
        "body": build_elegant_body(spec, die),
        "upper_carriage": build_elegant_upper_carriage(spec, die).translate((0, 0, carriage_z)),
        "lever": lever,
    }


def validate_elegant_clearance(
    spec: HandLeverSpec | None = None,
    die: DieSpec | None = None,
    *,
    tolerance_mm3: float = 1e-3,
) -> dict[str, list[tuple[str, str, float]]]:
    spec = spec or elegant_lever_spec()
    die = die or standard_handheld_die_spec()
    report: dict[str, list[tuple[str, str, float]]] = {}
    for state in ("closed", "open"):
        parts = build_elegant_assembly(spec, die, state=state)
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


def _solid_mass_g(part: Any) -> float:
    return float(part.val().Volume()) / 1000.0 * PLA_DENSITY_G_CM3


def export_elegant_lever_press_pack(
    out_dir: str | Path,
    *,
    die_pocket_clearance_mm: float = 0.15,
) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    die = standard_handheld_die_spec()
    spec = elegant_lever_spec(die_pocket_clearance_mm=die_pocket_clearance_mm)

    parts = {
        "body": build_elegant_body(spec, die),
        "upper_carriage": build_elegant_upper_carriage(spec, die),
        "upper_backing_cap": build_elegant_upper_cap(spec, die),
        "lever": build_elegant_lever(spec),
    }
    outputs: dict[str, str] = {}
    for name, part in parts.items():
        for ext in ("stl", "step"):
            outputs[f"{name}_{ext}"] = str(export_part(part, out / f"{name}.{ext}"))

    collisions = validate_elegant_clearance(spec, die)
    if collisions["closed"] or collisions["open"]:
        raise RuntimeError(
            "Elegant handheld assembly contains unintended printed-part collisions:\n"
            + json.dumps(collisions, indent=2)
        )

    assembly = {
        "coordinate_system": "+Y is the paper insertion nose; +Z is up",
        "die_orientation": {
            "lower_male": "face up; key +Y/front",
            "upper_female": "face down after 180-degree Y flip; key +Y/front",
        },
        "closed": {
            "upper_carriage_z_mm": spec.closed_carriage_bottom_z_mm(die),
            "handle_angle_deg_x": 0.0,
        },
        "open": {
            "upper_carriage_z_mm": spec.closed_carriage_bottom_z_mm(die) + spec.open_travel_mm,
            "handle_angle_deg_x": -spec.open_angle_deg,
        },
    }
    layout = out / "assembly_layout.json"
    layout.write_text(json.dumps(assembly, indent=2) + "\n", encoding="utf-8")
    outputs["assembly_layout"] = str(layout)

    masses = {name: round(_solid_mass_g(part), 2) for name, part in parts.items()}
    manifest = {
        "mode": "full-size-elegant-handheld-lever-embosser-v3",
        "design_language": "curved premium desk embosser; sculpted oval cheeks; round platens; sweeping lever",
        "status": "CAD/software prototype; physical strength validation still required",
        "compatible_die_command": "embossforge die <artwork> --diameter 42",
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
        },
        "hardware": {
            "main_pivot": "1 x M6 bolt / 6 mm smooth pin",
            "drive_pin": "1 x M5 bolt / 5 mm smooth pin",
            "upper_die_cap": "2 x M3 x ~10 mm screws",
        },
        "printed_quantities": {"body": 1, "upper_carriage": 1, "upper_backing_cap": 1, "lever": 1},
        "collision_validation": collisions,
        "assembly": assembly,
        "outputs": outputs,
    }
    manifest_path = out / "lever_press_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    outputs["manifest"] = str(manifest_path)
    return outputs
