from __future__ import annotations

from dataclasses import asdict
import json
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
    """Kinematics shared with V2, with dimensions tuned for the sculpted V3 shell."""
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


def _xy_hull(points: list[tuple[float, float, float]], height: float):
    """Smooth 2D hull of circles in XY, then extrude +Z."""
    cq = _cq()
    wp = cq.Workplane("XY")
    for x, y, r in points:
        wp = wp.moveTo(x, y).circle(r)
    return wp.hull().extrude(height)


def _yz_hull(points: list[tuple[float, float, float]], width: float, *, x_center: float = 0.0):
    """Smooth side silhouette built from tangent circular stations."""
    cq = _cq()
    wp = cq.Workplane("YZ")
    for y, z, r in points:
        wp = wp.moveTo(y, z).circle(r)
    return wp.hull().extrude(width / 2.0, both=True).translate((x_center, 0, 0))


def _shallow_side_recess(
    points: list[tuple[float, float, float]],
    *,
    x_center: float,
    depth: float,
):
    return _yz_hull(points, depth, x_center=x_center)


def build_elegant_body(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    """Curved one-piece body with hidden straight guide faces for the upper platen."""
    spec = spec or elegant_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    # Rounded/tapered footprint. The wide front supports the 42 mm die while the
    # rear narrows visually like a commercial desk embosser.
    base = _xy_hull(
        [
            (0.0, -43.0, 23.0),
            (0.0, -16.0, 27.0),
            (0.0, 28.0, 31.0),
        ],
        spec.base_thickness_mm,
    )

    # A circular lower platen visually separates the replaceable die from the body.
    lower_outer_d = 56.0
    lower = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(lower_outer_d / 2)
        .extrude(spec.lower_jaw_height_mm)
        .translate((0, 0, spec.base_thickness_mm))
    )
    body = base.union(lower)

    # Side cheeks use an organic outer hull and a large inner aperture. They are
    # positioned so their inner faces remain the same precise guide surfaces used
    # by the mechanically validated V2 carriage.
    cheek_t = spec.guide_wall_thickness_mm
    guide_inner_x = spec.carriage_width_mm / 2 + spec.guide_clearance_mm
    cheek_x = guide_inner_x + cheek_t / 2
    outer_profile = [
        (-35.0, 14.0, 12.0),
        (-23.0, 31.0, 16.0),
        (-8.0, 43.0, 15.0),
        (17.0, 38.0, 17.0),
        (39.0, 27.0, 15.0),
        (48.0, 16.0, 10.0),
    ]
    inner_profile = [
        (-18.0, 18.0, 8.0),
        (2.0, 24.0, 12.0),
        (27.0, 23.0, 13.0),
        (42.0, 18.0, 7.0),
    ]

    for sign in (-1, 1):
        shell = _yz_hull(outer_profile, cheek_t, x_center=sign * cheek_x)
        opening = _yz_hull(inner_profile, cheek_t + 2.0, x_center=sign * cheek_x)
        shell = shell.cut(opening)

        # Precision rail hidden inside the sculpted cheek. This intentionally keeps
        # the printer-fit contract independent from the cosmetic outer silhouette.
        guide_d = spec.guide_front_y_mm - spec.guide_rear_y_mm
        guide_y = (spec.guide_front_y_mm + spec.guide_rear_y_mm) / 2
        guide = (
            cq.Workplane("XY")
            .center(sign * cheek_x, guide_y)
            .box(cheek_t, guide_d, spec.guide_height_mm, centered=(True, True, False))
            .translate((0, 0, spec.base_thickness_mm))
        )
        body = body.union(shell).union(guide)

        # Shallow flowing side accent. It is decorative only and never intersects
        # the precision guide face.
        accent_x = sign * (cheek_x + cheek_t / 2 - 0.45)
        accent = _shallow_side_recess(
            [(-21.0, 31.0, 2.2), (3.0, 37.0, 2.0), (24.0, 32.0, 1.8)],
            x_center=accent_x,
            depth=0.9,
        )
        body = body.cut(accent)

    # Closure pads are tucked into the body aperture and stop the upper platen at
    # nominal paper engagement rather than crushing the dies together.
    stop_h = spec.closed_carriage_bottom_z_mm(die) - spec.base_thickness_mm
    for sign in (-1, 1):
        stop = (
            cq.Workplane("XY")
            .center(sign * (spec.carriage_width_mm / 2 - 4.0), 8.5)
            .box(6.0, 7.0, stop_h, centered=(True, True, False))
            .translate((0, 0, spec.base_thickness_mm))
        )
        body = body.union(stop)

    # Exact standard keyed 42 mm lower-die socket.
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

    # Pivot bore through both side cheeks.
    pivot = (
        cq.Workplane("YZ")
        .center(spec.pivot_y_mm, spec.pivot_z_mm)
        .circle(spec.main_pivot_diameter_mm / 2)
        .extrude(spec.body_width_mm + 4, both=True)
    )
    return body.cut(pivot)


def build_elegant_upper_carriage(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    """Round upper platen with guide ears and a narrow rear drive stem."""
    spec = spec or elegant_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    plate_d = 56.0
    plate = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(plate_d / 2)
        .extrude(spec.carriage_thickness_mm)
    )

    # Short rectangular guide ears are mostly hidden between the body cheeks.
    ears = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(spec.carriage_width_mm, 18.0, spec.carriage_thickness_mm, centered=(True, True, False))
    )
    carriage = plate.union(ears)
    carriage = carriage.cut(_keyed_cut(die, spec, spec.carriage_thickness_mm + 0.4, -0.2))

    stem_y = spec.drive_pin_world_y_mm()
    plate_rear = spec.die_center_y_mm - plate_d / 2
    # A tapered-looking neck formed by a hull of two circles, then clipped to the
    # narrow stem width near the lever fork.
    neck = _xy_hull(
        [
            (0.0, plate_rear + 4.0, 7.0),
            (0.0, stem_y + 4.0, 6.0),
        ],
        spec.carriage_thickness_mm,
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
    """Round backing cap; print flat and install boss-down."""
    spec = spec or elegant_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    cap_d = 54.0
    cap = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .circle(cap_d / 2)
        .extrude(spec.cap_thickness_mm)
    )
    # Small screw ears preserve the two-screw retention without a rectangular cap.
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
    """Sweeping ergonomic forked lever with recessed side grip panels."""
    spec = spec or elegant_lever_spec()
    spec.validate(standard_handheld_die_spec())
    cq = _cq()

    # Circular stations create a continuously flowing side silhouette without the
    # slab-like appearance of V2. The rear rises gently into a broad palm grip.
    lever = _yz_hull(
        [
            (6.0, 0.0, 10.0),
            (-22.0, 1.5, 10.5),
            (-55.0, 6.0, 10.0),
            (-92.0, 12.0, 9.5),
            (-128.0, 17.0, 10.5),
            (-150.0, 19.0, 12.0),
        ],
        spec.lever_width_mm,
    )

    # Central fork slot clears the upper carriage stem while leaving strong side arms.
    slot_y0 = spec.lever_fork_rear_mm - 3.0
    slot_y1 = spec.lever_fork_front_mm + 2.0
    slot = (
        cq.Workplane("XY")
        .box(
            spec.lever_fork_slot_width_mm,
            slot_y1 - slot_y0,
            34.0,
            centered=(True, True, True),
        )
        .translate((0, (slot_y0 + slot_y1) / 2, -1.0))
    )
    lever = lever.cut(slot)

    pivot = (
        cq.Workplane("YZ")
        .circle(spec.main_pivot_diameter_mm / 2)
        .extrude(spec.lever_width_mm + 4, both=True)
    )
    lever = lever.cut(pivot)

    # A slightly elongated cam slot gives the M5 carriage pin room to follow the
    # lever's small fore/aft arc while the carriage itself remains vertically guided.
    slot_half = 1.6
    drive_r = spec.drive_pin_diameter_mm / 2
    drive = (
        cq.Workplane("YZ")
        .moveTo(spec.drive_y_offset_mm - slot_half, spec.drive_z_offset_mm)
        .circle(drive_r)
        .moveTo(spec.drive_y_offset_mm + slot_half, spec.drive_z_offset_mm)
        .circle(drive_r)
        .hull()
        .extrude(spec.lever_width_mm + 4, both=True)
    )
    lever = lever.cut(drive)

    # Recessed side panels echo the dark grip insert in the target concept. Users can
    # paint or filament-swap these recesses without needing another structural part.
    grip_profile = [
        (-72.0, 11.0, 4.0),
        (-103.0, 15.0, 4.5),
        (-133.0, 18.0, 5.0),
    ]
    side_x = spec.lever_width_mm / 2 - 0.55
    lever = lever.cut(_shallow_side_recess(grip_profile, x_center=side_x, depth=1.1))
    lever = lever.cut(_shallow_side_recess(grip_profile, x_center=-side_x, depth=1.1))
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
        "design_language": "curved premium desk embosser; sculpted C-cheeks; round platens; sweeping lever",
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
