from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any

from ..config import DieSpec
from .cad import export_part


PLA_DENSITY_G_CM3 = 1.24


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            'CadQuery is required for lever-press generation. Install with: pip install -e ".[cad]"'
        ) from exc
    return cq


@dataclass(frozen=True)
class HandLeverSpec:
    """Compact hand embosser for the standard 42 mm keyed EmbossForge dies."""

    body_width_mm: float = 70.0
    body_rear_y_mm: float = -60.0
    body_front_y_mm: float = 60.0
    base_thickness_mm: float = 7.0

    die_center_y_mm: float = 30.0
    lower_jaw_width_mm: float = 58.0
    lower_jaw_depth_mm: float = 50.0
    lower_jaw_height_mm: float = 4.0
    die_pocket_clearance_mm: float = 0.15
    die_seat_extra_depth_mm: float = 0.05
    removal_notch_radius_mm: float = 4.0

    carriage_width_mm: float = 58.0
    carriage_depth_mm: float = 50.0
    carriage_thickness_mm: float = 7.0
    guide_clearance_mm: float = 0.35
    guide_wall_thickness_mm: float = 5.0
    guide_front_y_mm: float = 57.0
    guide_rear_y_mm: float = 5.0
    guide_height_mm: float = 35.0

    pivot_y_mm: float = -10.0
    pivot_z_mm: float = 43.0
    pivot_tower_rear_y_mm: float = -38.0
    pivot_tower_front_y_mm: float = 5.0
    pivot_tower_height_mm: float = 58.0
    main_pivot_diameter_mm: float = 6.4

    # The handle and drive pin are both behind the main pivot. Opening the
    # handle upward therefore lifts the carriage instead of driving it down.
    drive_y_offset_mm: float = -20.0
    drive_z_offset_mm: float = -7.0
    drive_pin_diameter_mm: float = 5.2
    drive_pin_clearance_mm: float = 0.50
    open_travel_mm: float = 14.0

    lever_width_mm: float = 25.0
    lever_thickness_mm: float = 10.0
    lever_fork_height_mm: float = 17.0
    lever_rear_length_mm: float = 150.0
    lever_fork_rear_mm: float = -34.0
    lever_fork_front_mm: float = 12.0
    lever_fork_slot_width_mm: float = 14.4

    stem_width_mm: float = 13.0
    stem_depth_mm: float = 18.0
    stem_top_margin_mm: float = 4.0
    neck_width_mm: float = 13.0

    cap_thickness_mm: float = 2.5
    cap_width_mm: float = 58.0
    cap_depth_mm: float = 46.0
    cap_boss_diameter_mm: float = 38.0
    cap_screw_clearance_mm: float = 3.3
    carriage_pilot_diameter_mm: float = 2.6
    cap_screw_x_mm: float = 25.0

    def validate(self, die: DieSpec | None = None) -> None:
        die = die or DieSpec()
        die.validate()
        signed = {
            "body_rear_y_mm",
            "pivot_y_mm",
            "pivot_tower_rear_y_mm",
            "drive_y_offset_mm",
            "drive_z_offset_mm",
            "lever_fork_rear_mm",
        }
        for name, value in self.__dict__.items():
            if name.endswith("_mm") and value <= 0 and name not in signed:
                raise ValueError(f"{name} must be positive")
        if self.body_rear_y_mm >= self.body_front_y_mm:
            raise ValueError("body rear must be behind body front")
        if self.drive_y_offset_mm >= 0:
            raise ValueError("handheld drive pin must be behind the pivot")
        if self.lower_jaw_width_mm <= die.diameter_mm + 2 * self.die_pocket_clearance_mm:
            raise ValueError("lower jaw is too narrow for the selected die")
        if self.carriage_width_mm <= die.diameter_mm + 2 * self.die_pocket_clearance_mm:
            raise ValueError("upper carriage is too narrow for the selected die")
        guide_inside = self.carriage_width_mm + 2 * self.guide_clearance_mm
        guide_outside = guide_inside + 2 * self.guide_wall_thickness_mm
        if guide_outside > self.body_width_mm:
            raise ValueError("guide walls do not fit within body width")
        if self.lever_fork_slot_width_mm <= self.stem_width_mm + 0.6:
            raise ValueError("lever fork slot does not clear the carriage stem")
        if self.open_angle_deg >= 58.0:
            raise ValueError("requested carriage opening requires excessive handle travel")
        if self.stem_pin_local_z_mm(die) <= self.carriage_thickness_mm:
            raise ValueError("carriage drive pin is below the stem")

    @property
    def body_depth_mm(self) -> float:
        return self.body_front_y_mm - self.body_rear_y_mm

    @property
    def drive_radius_mm(self) -> float:
        return math.hypot(self.drive_y_offset_mm, self.drive_z_offset_mm)

    @property
    def nominal_lever_ratio(self) -> float:
        return self.lever_rear_length_mm / self.drive_radius_mm

    def lower_die_face_z_mm(self, die: DieSpec) -> float:
        return self.base_thickness_mm + self.lower_jaw_height_mm - self.die_seat_extra_depth_mm

    def closed_carriage_bottom_z_mm(self, die: DieSpec) -> float:
        # Upper die face is flush with the carriage underside after the cap is fitted.
        return self.lower_die_face_z_mm(die) + die.paper_thickness_mm

    def drive_pin_closed_z_mm(self) -> float:
        return self.pivot_z_mm + self.drive_z_offset_mm

    def drive_pin_world_y_mm(self) -> float:
        return self.pivot_y_mm + self.drive_y_offset_mm

    def stem_pin_local_z_mm(self, die: DieSpec) -> float:
        return self.drive_pin_closed_z_mm() - self.closed_carriage_bottom_z_mm(die)

    def cap_boss_height_mm(self, die: DieSpec) -> float:
        return self.carriage_thickness_mm - die.base_thickness_mm + self.die_seat_extra_depth_mm

    def drive_lift_mm(self, opening_angle_deg: float) -> float:
        # Opening is a negative X rotation. Both the rear grip and rear drive pin rise.
        a = -math.radians(opening_angle_deg)
        y = self.drive_y_offset_mm
        z = self.drive_z_offset_mm
        z_rotated = y * math.sin(a) + z * math.cos(a)
        return z_rotated - z

    @property
    def open_angle_deg(self) -> float:
        lo, hi = 0.0, 57.0
        if self.drive_lift_mm(hi) < self.open_travel_mm:
            return 90.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if self.drive_lift_mm(mid) < self.open_travel_mm:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2


def standard_handheld_die_spec() -> DieSpec:
    die = DieSpec()
    die.validate()
    return die


def hand_lever_spec(*, die_pocket_clearance_mm: float = 0.15) -> HandLeverSpec:
    spec = HandLeverSpec(die_pocket_clearance_mm=die_pocket_clearance_mm)
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


def build_hand_lever_body(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    spec = spec or hand_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    body_y = (spec.body_rear_y_mm + spec.body_front_y_mm) / 2
    body = (
        cq.Workplane("XY")
        .box(spec.body_width_mm, spec.body_depth_mm, spec.base_thickness_mm, centered=(True, True, False))
        .translate((0, body_y, 0))
    )
    lower = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(spec.lower_jaw_width_mm, spec.lower_jaw_depth_mm, spec.lower_jaw_height_mm, centered=(True, True, False))
        .translate((0, 0, spec.base_thickness_mm))
    )
    body = body.union(lower)

    guide_x = spec.carriage_width_mm / 2 + spec.guide_clearance_mm + spec.guide_wall_thickness_mm / 2
    guide_d = spec.guide_front_y_mm - spec.guide_rear_y_mm
    guide_y = (spec.guide_front_y_mm + spec.guide_rear_y_mm) / 2
    tower_d = spec.pivot_tower_front_y_mm - spec.pivot_tower_rear_y_mm
    tower_y = (spec.pivot_tower_front_y_mm + spec.pivot_tower_rear_y_mm) / 2
    for sign in (-1, 1):
        x = sign * guide_x
        guide = (
            cq.Workplane("XY")
            .center(x, guide_y)
            .box(spec.guide_wall_thickness_mm, guide_d, spec.guide_height_mm, centered=(True, True, False))
            .translate((0, 0, spec.base_thickness_mm))
        )
        tower = (
            cq.Workplane("XY")
            .center(x, tower_y)
            .box(
                spec.guide_wall_thickness_mm,
                tower_d,
                spec.pivot_tower_height_mm - spec.base_thickness_mm,
                centered=(True, True, False),
            )
            .translate((0, 0, spec.base_thickness_mm))
        )
        body = body.union(guide).union(tower)

    # Closure pads stop the upper carriage at nominal paper engagement.
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


def build_upper_carriage(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    spec = spec or hand_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    plate = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(spec.carriage_width_mm, spec.carriage_depth_mm, spec.carriage_thickness_mm, centered=(True, True, False))
    )
    plate = plate.cut(_keyed_cut(die, spec, spec.carriage_thickness_mm + 0.4, -0.2))

    stem_y = spec.drive_pin_world_y_mm()
    plate_rear = spec.die_center_y_mm - spec.carriage_depth_mm / 2
    neck_y0 = stem_y - spec.stem_depth_mm / 2
    neck_y1 = plate_rear + 6.0
    neck = (
        cq.Workplane("XY")
        .center(0, (neck_y0 + neck_y1) / 2)
        .box(spec.neck_width_mm, neck_y1 - neck_y0, spec.carriage_thickness_mm, centered=(True, True, False))
    )

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
    carriage = plate.union(neck).union(stem)

    bore = (
        cq.Workplane("YZ")
        .center(stem_y, pin_z)
        .circle((spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2)
        .extrude(spec.stem_width_mm + 4, both=True)
    )
    carriage = carriage.cut(bore)

    # Two M3 pilot holes sit outside the 42 mm through-pocket.
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


def build_upper_backing_cap(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    """Print flat, then install boss-down to clamp the upper/female die."""
    spec = spec or hand_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    cap = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(spec.cap_width_mm, spec.cap_depth_mm, spec.cap_thickness_mm, centered=(True, True, False))
    )
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


def build_hand_lever(spec: HandLeverSpec | None = None):
    """Forked lever in local coordinates; main pivot is local (0,0,0)."""
    spec = spec or hand_lever_spec()
    spec.validate(standard_handheld_die_spec())
    cq = _cq()

    handle = (
        cq.Workplane("XY")
        .box(spec.lever_width_mm, spec.lever_rear_length_mm + 8.0, spec.lever_thickness_mm, centered=(True, True, True))
        .translate((0, -(spec.lever_rear_length_mm - 8.0) / 2, 0))
    )
    fork_center_y = (spec.lever_fork_rear_mm + spec.lever_fork_front_mm) / 2
    fork = (
        cq.Workplane("XY")
        .box(
            spec.lever_width_mm,
            spec.lever_fork_front_mm - spec.lever_fork_rear_mm,
            spec.lever_fork_height_mm,
            centered=(True, True, True),
        )
        .translate((0, fork_center_y, spec.drive_z_offset_mm / 2))
    )
    lever = handle.union(fork)

    slot_y0 = spec.lever_fork_rear_mm - 2.0
    slot_y1 = spec.lever_fork_front_mm + 1.0
    slot = (
        cq.Workplane("XY")
        .box(
            spec.lever_fork_slot_width_mm,
            slot_y1 - slot_y0,
            spec.lever_fork_height_mm + 10.0,
            centered=(True, True, True),
        )
        .translate((0, (slot_y0 + slot_y1) / 2, spec.drive_z_offset_mm / 2))
    )
    lever = lever.cut(slot)

    pivot = (
        cq.Workplane("YZ")
        .circle(spec.main_pivot_diameter_mm / 2)
        .extrude(spec.lever_width_mm + 4, both=True)
    )
    lever = lever.cut(pivot)
    drive = (
        cq.Workplane("YZ")
        .center(spec.drive_y_offset_mm, spec.drive_z_offset_mm)
        .circle(spec.drive_pin_diameter_mm / 2)
        .extrude(spec.lever_width_mm + 4, both=True)
    )
    return lever.cut(drive)


def build_hand_lever_assembly(
    spec: HandLeverSpec | None = None,
    die: DieSpec | None = None,
    *,
    state: str = "closed",
) -> dict[str, Any]:
    if state not in {"open", "closed"}:
        raise ValueError("state must be open or closed")
    spec = spec or hand_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)

    carriage_z = spec.closed_carriage_bottom_z_mm(die)
    angle = 0.0
    if state == "open":
        carriage_z += spec.open_travel_mm
        angle = -spec.open_angle_deg

    lever = build_hand_lever(spec).translate((0, spec.pivot_y_mm, spec.pivot_z_mm))
    if angle:
        lever = lever.rotate(
            (0, spec.pivot_y_mm, spec.pivot_z_mm),
            (1, spec.pivot_y_mm, spec.pivot_z_mm),
            angle,
        )
    return {
        "body": build_hand_lever_body(spec, die),
        "upper_carriage": build_upper_carriage(spec, die).translate((0, 0, carriage_z)),
        "lever": lever,
    }


def validate_hand_lever_clearance(
    spec: HandLeverSpec | None = None,
    die: DieSpec | None = None,
    *,
    tolerance_mm3: float = 1e-3,
) -> dict[str, list[tuple[str, str, float]]]:
    spec = spec or hand_lever_spec()
    die = die or standard_handheld_die_spec()
    report: dict[str, list[tuple[str, str, float]]] = {}
    for state in ("closed", "open"):
        parts = build_hand_lever_assembly(spec, die, state=state)
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


def export_hand_lever_press_pack(
    out_dir: str | Path,
    *,
    die_pocket_clearance_mm: float = 0.15,
) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    die = standard_handheld_die_spec()
    spec = hand_lever_spec(die_pocket_clearance_mm=die_pocket_clearance_mm)

    parts = {
        "body": build_hand_lever_body(spec, die),
        "upper_carriage": build_upper_carriage(spec, die),
        "upper_backing_cap": build_upper_backing_cap(spec, die),
        "lever": build_hand_lever(spec),
    }
    outputs: dict[str, str] = {}
    for name, part in parts.items():
        for ext in ("stl", "step"):
            outputs[f"{name}_{ext}"] = str(export_part(part, out / f"{name}.{ext}"))

    collisions = validate_hand_lever_clearance(spec, die)
    if collisions["closed"] or collisions["open"]:
        raise RuntimeError(
            "Handheld lever assembly contains unintended printed-part collisions:\n"
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
        "mode": "full-size-handheld-lever-embosser-v2",
        "status": "CAD/software validated prototype; physically validate before high force",
        "compatible_die_command": "embossforge die <artwork> --diameter 42",
        "exact_die_contract_mm": {
            "diameter": die.diameter_mm,
            "base_thickness": die.base_thickness_mm,
            "key_width": die.key_width_mm,
            "key_depth": die.key_depth_mm,
        },
        "press": asdict(spec),
        "derived": {
            "body_depth_mm": spec.body_depth_mm,
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
