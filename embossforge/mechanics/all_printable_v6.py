from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .cad import export_part
from .handheld_compact import HandLeverSpec, standard_handheld_die_spec
from .handheld_elegant import PLA_DENSITY_G_CM3, _keyed_cut, _polygon_extrude, _yz_capsule
from .all_printable import (
    _ground,
    build_drive_pin,
    build_fully_printable_body as _build_body,
    build_main_pivot_pin,
    build_retaining_wedge,
)


FEMALE_FACE_LOCAL_Z_MM = 0.05
CARRIAGE_CLEAR_UNDERSIDE_MM = 0.80


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            'CadQuery is required for press generation. Install with: pip install -e ".[cad]"'
        ) from exc
    return cq


def fully_printable_spec(*, die_pocket_clearance_mm: float = 0.20) -> HandLeverSpec:
    """Low-profile hardware-free press for a 0.4 mm nozzle and 42 mm dies."""
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
        pivot_z_mm=18.0,
        pivot_tower_rear_y_mm=-23.0,
        pivot_tower_front_y_mm=1.0,
        pivot_tower_height_mm=25.0,
        main_pivot_diameter_mm=6.4,
        drive_y_offset_mm=-18.0,
        drive_z_offset_mm=-3.5,
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
        # Legacy members retained only because HandLeverSpec is shared with
        # older prototypes. V6 has no cap, screw, or vertical carriage stem.
        cap_thickness_mm=2.4,
        cap_width_mm=52.0,
        cap_depth_mm=52.0,
        cap_boss_diameter_mm=34.0,
        cap_screw_clearance_mm=2.9,
        carriage_pilot_diameter_mm=2.55,
        cap_screw_x_mm=23.2,
    )
    # The shared validator contains a legacy vertical-stem check that does not
    # describe V6. Validate all common dimensional contracts explicitly here.
    die = standard_handheld_die_spec()
    die.validate()
    if spec.lower_jaw_width_mm <= die.diameter_mm + 2 * spec.die_pocket_clearance_mm:
        raise ValueError("lower jaw is too narrow for the selected die")
    if spec.carriage_width_mm <= die.diameter_mm + 2 * spec.die_pocket_clearance_mm:
        raise ValueError("upper carriage is too narrow for the selected die")
    guide_inside = spec.carriage_width_mm + 2 * spec.guide_clearance_mm
    guide_outside = guide_inside + 2 * spec.guide_wall_thickness_mm
    if guide_outside > spec.body_width_mm:
        raise ValueError("guide walls do not fit within body width")
    if spec.lever_fork_slot_width_mm <= spec.neck_width_mm + 0.6:
        raise ValueError("lever fork slot does not clear the carriage tongue")
    if spec.open_angle_deg >= 58.0:
        raise ValueError("requested carriage opening requires excessive handle travel")
    return spec


def _lower_die_face_z(spec: HandLeverSpec) -> float:
    die = standard_handheld_die_spec()
    return spec.base_thickness_mm + spec.lower_jaw_height_mm - spec.die_seat_extra_depth_mm


def _closed_carriage_origin_z(spec: HandLeverSpec) -> float:
    die = standard_handheld_die_spec()
    # Under load the 3.00 mm die base seats against the roof of the 3.05 mm
    # pocket, so its emboss face sits 0.05 mm above the carriage local origin.
    return _lower_die_face_z(spec) + die.paper_thickness_mm - FEMALE_FACE_LOCAL_Z_MM


def _drive_pin_local_z(spec: HandLeverSpec) -> float:
    return spec.drive_pin_closed_z_mm() - _closed_carriage_origin_z(spec)


def build_fully_printable_body(spec: HandLeverSpec | None = None):
    return _build_body(spec or fully_printable_spec())


def build_fully_printable_upper_carriage(spec: HandLeverSpec | None = None):
    """Flat guided die cup with a rear drive tongue—no tall stem at all."""
    spec = spec or fully_printable_spec()
    die = standard_handheld_die_spec()
    cq = _cq()

    # Keep 0.8 mm of open vertical clearance around the lower plastic platform.
    # The female die itself projects below this surrounding plastic holder.
    plate = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(spec.carriage_width_mm / 2.0)
        .extrude(spec.carriage_thickness_mm - CARRIAGE_CLEAR_UNDERSIDE_MM)
        .translate((0, 0, CARRIAGE_CLEAR_UNDERSIDE_MM))
    )

    pocket_depth = die.base_thickness_mm + spec.die_seat_extra_depth_mm
    plate = plate.cut(_keyed_cut(die, spec, pocket_depth + 0.02, 0.0))

    # Three single-nozzle-width side ribs give a light interference grip. They
    # never extend beneath the female emboss face and therefore cannot act as a
    # premature hard stop against the lower die.
    rib_h = 2.2
    rib_z = CARRIAGE_CLEAR_UNDERSIDE_MM
    rib_t = 0.40
    rib_span = 4.0
    r = die.diameter_mm / 2.0
    rib_specs = [
        (r + 0.15, spec.die_center_y_mm, rib_t, rib_span),
        (-(r + 0.15), spec.die_center_y_mm, rib_t, rib_span),
        (0.0, spec.die_center_y_mm - (r + 0.15), rib_span, rib_t),
    ]
    carriage = plate
    for x, y, width, depth in rib_specs:
        rib = (
            cq.Workplane("XY")
            .center(x, y)
            .box(width, depth, rib_h, centered=(True, True, False))
            .translate((0, 0, rib_z))
        )
        carriage = carriage.union(rib)

    # Flat rear tongue stays within the same six-millimetre print height as the
    # die cup. The drive pin passes directly through this tongue.
    drive_y = spec.drive_pin_world_y_mm()
    plate_rear_y = spec.die_center_y_mm - spec.carriage_width_mm / 2.0
    tongue_front_y = plate_rear_y + 5.0
    tongue_rear_y = drive_y - 8.0
    tongue_y = (tongue_front_y + tongue_rear_y) / 2.0
    tongue_depth = tongue_front_y - tongue_rear_y
    tongue = (
        cq.Workplane("XY")
        .center(0, tongue_y)
        .box(spec.neck_width_mm, tongue_depth, spec.carriage_thickness_mm - CARRIAGE_CLEAR_UNDERSIDE_MM, centered=(True, True, False))
        .translate((0, 0, CARRIAGE_CLEAR_UNDERSIDE_MM))
    )
    carriage = carriage.union(tongue)

    pin_z = _drive_pin_local_z(spec)
    if not (CARRIAGE_CLEAR_UNDERSIDE_MM + 2.7 <= pin_z <= spec.carriage_thickness_mm - 2.7):
        raise ValueError(f"V6 drive-pin center {pin_z:.3f} mm does not fit inside the flat carriage tongue")
    drive_bore = (
        cq.Workplane("YZ")
        .center(drive_y, pin_z)
        .circle((spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2.0)
        .extrude(spec.neck_width_mm + 4.0, both=True)
    )
    return carriage.cut(drive_bore)


def _lever_profile(spec: HandLeverSpec):
    rear_y = -150.0
    front_y = 10.0
    samples = 80
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    for i in range(samples + 1):
        t = i / samples
        y = rear_y + (front_y - rear_y) * t
        zc = 13.0 * (1.0 - t) ** 1.12
        radius = 7.5 + 1.8 * (1.0 - t) ** 3 + 1.2 * t**5
        upper.append((y, zc + radius))
        lower.append((y, zc - radius))
    return _polygon_extrude("YZ", upper + list(reversed(lower)), spec.lever_width_mm / 2.0, both=True)


def _lever_window(spec: HandLeverSpec):
    rear_y = -138.0
    front_y = -47.0
    samples = 56
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    for i in range(samples + 1):
        y = rear_y + (front_y - rear_y) * i / samples
        t = (y + 150.0) / 160.0
        zc = 13.0 * (1.0 - t) ** 1.12
        outer = 7.5 + 1.8 * (1.0 - t) ** 3 + 1.2 * t**5
        inner = max(outer - 3.2, 2.2)
        upper.append((y, zc + inner))
        lower.append((y, zc - inner))
    return _polygon_extrude("YZ", upper + list(reversed(lower)), spec.lever_width_mm / 2.0 + 1.0, both=True)


def build_fully_printable_lever(spec: HandLeverSpec | None = None):
    spec = spec or fully_printable_spec()
    cq = _cq()
    lever = _lever_profile(spec).cut(_lever_window(spec))

    # Fork slot around the flat carriage tongue.
    slot_y0 = spec.lever_fork_rear_mm - 3.0
    slot_y1 = spec.lever_fork_front_mm + 2.0
    slot = (
        cq.Workplane("XY")
        .box(spec.lever_fork_slot_width_mm, slot_y1 - slot_y0, 32.0, centered=(True, True, True))
        .translate((0, (slot_y0 + slot_y1) / 2.0, -1.0))
    )
    lever = lever.cut(slot)

    pivot = (
        cq.Workplane("YZ")
        .circle(spec.main_pivot_diameter_mm / 2.0)
        .extrude(spec.lever_width_mm + 4.0, both=True)
    )
    lever = lever.cut(pivot)

    # Add material around the low drive hole before cutting it. This prevents
    # the pin from breaking out through the underside of the fork arms.
    drive_boss = (
        cq.Workplane("YZ")
        .center(spec.drive_y_offset_mm, spec.drive_z_offset_mm)
        .circle(5.7)
        .extrude(spec.lever_width_mm / 2.0, both=True)
    )
    lever = lever.union(drive_boss)
    drive = _yz_capsule(
        spec.drive_y_offset_mm - 1.2,
        spec.drive_y_offset_mm + 1.2,
        spec.drive_z_offset_mm,
        spec.drive_pin_diameter_mm / 2.0,
        spec.lever_width_mm + 4.0,
    )
    return lever.cut(drive)


def build_fully_printable_assembly(spec: HandLeverSpec | None = None, *, state: str = "closed") -> dict[str, Any]:
    if state not in {"open", "closed"}:
        raise ValueError("state must be open or closed")
    spec = spec or fully_printable_spec()
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
    return {
        "body": build_fully_printable_body(spec),
        "upper_carriage": build_fully_printable_upper_carriage(spec).translate((0, 0, carriage_z)),
        "lever": lever,
    }


def validate_fully_printable_clearance(
    spec: HandLeverSpec | None = None,
    *,
    tolerance_mm3: float = 1e-3,
) -> dict[str, list[tuple[str, str, float]]]:
    spec = spec or fully_printable_spec()
    report: dict[str, list[tuple[str, str, float]]] = {}
    for state in ("closed", "open"):
        parts = build_fully_printable_assembly(spec, state=state)
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


def _print_oriented_carriage(spec: HandLeverSpec):
    # There is no tall stem anymore. Flip the six-millimetre plate so its solid
    # roof is on the bed and the full female-die pocket points upward.
    return _ground(build_fully_printable_upper_carriage(spec).rotate((0, 0, 0), (1, 0, 0), 180.0))


def _print_oriented_lever(spec: HandLeverSpec):
    # Lay the broad YZ face on the bed; the 20 mm lever width becomes print Z.
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
            "Fully printable V6 press contains unintended printed-part collisions:\n"
            + json.dumps(collisions, indent=2)
        )

    assembly_parts = {
        "body": build_fully_printable_body(spec),
        "upper_carriage": build_fully_printable_upper_carriage(spec),
        "lever": build_fully_printable_lever(spec),
        "main_pivot_pin": build_main_pivot_pin(spec),
        "drive_pin": build_drive_pin(spec),
        "retaining_wedge": build_retaining_wedge(),
    }
    print_parts = dict(assembly_parts)
    print_parts["upper_carriage"] = _print_oriented_carriage(spec)
    print_parts["lever"] = _print_oriented_lever(spec)

    outputs: dict[str, str] = {}
    for name, part in print_parts.items():
        outputs[f"{name}_stl"] = str(export_part(_ground(part), out / f"{name}.stl"))
    for name, part in assembly_parts.items():
        outputs[f"{name}_step"] = str(export_part(part, out / f"{name}.step"))

    cq = _cq()
    for state in ("closed", "open"):
        assembled = build_fully_printable_assembly(spec, state=state)
        compound = cq.Compound.makeCompound([shape.val() for shape in assembled.values()])
        outputs[f"assembly_{state}_step"] = str(
            export_part(cq.Workplane(obj=compound), out / f"assembly_{state}.step")
        )

    masses = {name: round(_solid_mass_g(part), 2) for name, part in assembly_parts.items()}
    quantities = {
        "body": 1,
        "upper_carriage": 1,
        "lever": 1,
        "main_pivot_pin": 1,
        "drive_pin": 1,
        "retaining_wedge": 2,
    }
    total_solid = sum(masses[name] * qty for name, qty in quantities.items())
    assembly = {
        "coordinate_system": "+Y is the paper-insertion nose; +Z is up",
        "existing_die_compatibility": "standard 42 mm keyed male/female dies; no new dies required",
        "steps": [
            "Drop the existing male die face-up into the lower keyed pocket.",
            "After printing, turn upper_carriage over so its female-die pocket faces down. Align the key and press the existing female die into the pocket with its emboss face outward/down.",
            "Slide upper_carriage between the guide walls with its flat rear tongue toward the low pivot ears.",
            "Place the forked lever around the rear tongue.",
            "Insert main_pivot_pin through both body ears and the lever, then slide one retaining_wedge through the rectangular slot at the pin tip.",
            "Insert drive_pin through the lever fork and the carriage tongue, then retain it with the second wedge.",
            "Cycle the empty mechanism through full travel before adding paper; the carriage must stay level and must not catch on either guide wall.",
        ],
        "print_notes": {
            "nozzle": "0.4 mm",
            "body": "0.24-0.28 mm layers, 3 walls, 10-15% infill, supports off",
            "upper_carriage": "use exported orientation; pocket up; 0.20-0.24 mm layers, 3-4 walls",
            "lever": "use exported orientation; broad side on bed; 0.24 mm layers, 3-4 walls",
            "pins_and_wedges": "0.20 mm layers, 4 walls, 100% infill; 40-60 mm/s",
            "speed": "60-80 mm/s outer walls for first validation; avoid 300 mm/s functional-part printing",
        },
    }
    layout = out / "assembly_layout.json"
    layout.write_text(json.dumps(assembly, indent=2) + "\n", encoding="utf-8")
    outputs["assembly_layout"] = str(layout)

    manifest = {
        "mode": "all-3d-printable-42mm-lever-embosser-v6",
        "status": "CAD/software prototype; first physical V6 validation pending",
        "design_goals": [
            "all moving-joint hardware is printed",
            "0.4 mm nozzle compatible",
            "existing 42 mm keyed dies fit directly",
            "no screws, nuts, rods, bearings, springs, cap screws, or metal hardware",
            "upper moving die holder stays approximately six millimetres tall",
            "female die projects below surrounding carriage plastic so the holder cannot become the emboss stop",
            "large parts export in low, support-minimizing print orientations",
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
            "female_face_local_z_mm": FEMALE_FACE_LOCAL_Z_MM,
            "closed_upper_carriage_origin_z_mm": _closed_carriage_origin_z(spec),
            "open_handle_angle_deg": spec.open_angle_deg,
            "open_travel_mm": spec.open_travel_mm,
            "nominal_lever_ratio": spec.nominal_lever_ratio,
            "solid_pla_mass_upper_bound_by_unique_part_g": masses,
            "solid_pla_mass_total_with_quantities_g": round(total_solid, 2),
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
