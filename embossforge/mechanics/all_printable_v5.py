from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .cad import export_part
from .handheld_compact import HandLeverSpec, standard_handheld_die_spec
from .handheld_elegant import PLA_DENSITY_G_CM3, _keyed_cut
from .all_printable import (
    _ground,
    _print_oriented_lever,
    build_drive_pin,
    build_fully_printable_body as _build_body,
    build_fully_printable_lever as _build_lever,
    build_main_pivot_pin,
    build_retaining_wedge,
)


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            'CadQuery is required for press generation. Install with: pip install -e ".[cad]"'
        ) from exc
    return cq


def fully_printable_spec(*, die_pocket_clearance_mm: float = 0.20) -> HandLeverSpec:
    """No-hardware press designed around a 0.4 mm nozzle and the 42 mm dies."""
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
        pivot_z_mm=28.0,
        pivot_tower_rear_y_mm=-23.0,
        pivot_tower_front_y_mm=1.0,
        pivot_tower_height_mm=34.0,
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
        # These legacy cap fields remain valid members of HandLeverSpec but V5
        # deliberately has no cap and does not use them mechanically.
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


def build_fully_printable_body(spec: HandLeverSpec | None = None):
    return _build_body(spec or fully_printable_spec())


def build_fully_printable_lever(spec: HandLeverSpec | None = None):
    return _build_lever(spec or fully_printable_spec())


def build_fully_printable_upper_carriage(spec: HandLeverSpec | None = None):
    """Upper guided jaw with a direct face-flush friction-fit female-die pocket.

    The female die is inserted from the underside until its flat rear face hits
    the pocket roof. The 3.05 mm pocket depth leaves the embossing face almost
    flush with the carriage underside. Three 0.4 mm single-extrusion-width ribs
    reduce the local clearance just enough to stop the inverted die falling out.
    The exported STL is flipped so the pocket faces upward during printing.
    """
    spec = spec or fully_printable_spec()
    die = standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    plate = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(spec.carriage_width_mm / 2.0)
        .extrude(spec.carriage_thickness_mm)
    )

    pocket_depth = die.base_thickness_mm + spec.die_seat_extra_depth_mm
    plate = plate.cut(_keyed_cut(die, spec, pocket_depth + 0.03, -0.02))

    # Three printable side-friction ribs. 0.4 mm is one nominal nozzle width.
    # They contact only the cylindrical side of the die, never its emboss face.
    rib_h = max(2.2, die.base_thickness_mm - 0.35)
    rib_z = 0.15
    rib_t = 0.40
    rib_span = 4.0
    r = die.diameter_mm / 2.0
    ribs = [
        cq.Workplane("XY")
        .center(r + 0.15, spec.die_center_y_mm)
        .box(rib_t, rib_span, rib_h, centered=(True, True, False))
        .translate((0, 0, rib_z)),
        cq.Workplane("XY")
        .center(-(r + 0.15), spec.die_center_y_mm)
        .box(rib_t, rib_span, rib_h, centered=(True, True, False))
        .translate((0, 0, rib_z)),
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm - (r + 0.15))
        .box(rib_span, rib_t, rib_h, centered=(True, True, False))
        .translate((0, 0, rib_z)),
    ]
    carriage = plate
    for rib in ribs:
        carriage = carriage.union(rib)

    stem_y = spec.drive_pin_world_y_mm()
    plate_rear = spec.die_center_y_mm - spec.carriage_width_mm / 2.0
    neck_y = (plate_rear + stem_y) / 2.0
    neck_depth = abs(plate_rear - stem_y) + 10.0
    neck = (
        cq.Workplane("XY")
        .center(0, neck_y)
        .box(spec.neck_width_mm, neck_depth, spec.carriage_thickness_mm, centered=(True, True, False))
    )
    carriage = carriage.union(neck)

    pin_z = spec.stem_pin_local_z_mm(die)
    stem_h = (
        pin_z
        + (spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2.0
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
        .circle((spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2.0)
        .extrude(spec.stem_width_mm + 4.0, both=True)
    )
    return carriage.cut(bore)


def build_fully_printable_assembly(spec: HandLeverSpec | None = None, *, state: str = "closed") -> dict[str, Any]:
    if state not in {"open", "closed"}:
        raise ValueError("state must be open or closed")
    spec = spec or fully_printable_spec()
    die = standard_handheld_die_spec()
    spec.validate(die)

    carriage_z = spec.closed_carriage_bottom_z_mm(die)
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
    part = build_fully_printable_upper_carriage(spec)
    # Turn the underside pocket upward. The solid roof becomes the bed-contact
    # face and the pocket walls/ribs grow upward without a 42 mm bridge.
    return _ground(part.rotate((0, 0, 0), (1, 0, 0), 180.0))


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
            "Turn the upper carriage over, align the female die key, and press the female die face-outward into the keyed pocket until its rear face seats against the pocket roof.",
            "Slide the upper carriage between the guide walls, with its stem toward the rear pivot and female emboss face pointing down.",
            "Place the forked lever around the carriage stem.",
            "Align the main pivot holes, push in main_pivot_pin, and lock it by sliding a retaining_wedge through its rectangular end slot.",
            "Align the lever/carriage drive holes, push in drive_pin, and lock it with the second retaining_wedge.",
            "Cycle the empty mechanism by hand; the carriage must slide without catching before paper is inserted.",
        ],
        "print_notes": {
            "nozzle": "0.4 mm",
            "body": "0.24-0.28 mm layers, 3 walls, 10-15% infill, supports off",
            "upper_carriage": "use exported orientation; pocket faces upward, 0.20-0.24 mm layers, 3 walls",
            "lever": "use exported orientation; broad side on bed, 0.24-0.28 mm layers, 3 walls",
            "pins_and_wedges": "0.20 mm layers, 4 walls, 100% infill; 40-60 mm/s",
            "speed": "avoid the 300 mm/s prototype speed for this first mechanical validation; use 60-80 mm/s outer walls",
        },
    }
    layout = out / "assembly_layout.json"
    layout.write_text(json.dumps(assembly, indent=2) + "\n", encoding="utf-8")
    outputs["assembly_layout"] = str(layout)

    manifest = {
        "mode": "all-3d-printable-42mm-lever-embosser-v5",
        "status": "CAD/software prototype; first physical validation pending",
        "design_goals": [
            "all functional linkage hardware is printed",
            "0.4 mm nozzle compatible",
            "existing 42 mm keyed dies fit directly",
            "no screws, nuts, rods, bearings, springs, cap screws, or metal hardware",
            "female die is held directly by a keyed friction-fit pocket",
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
