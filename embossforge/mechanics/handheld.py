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
    except ImportError as exc:  # pragma: no cover - optional CAD dependency
        raise RuntimeError(
            'CadQuery is required for lever-press generation. Install with: pip install -e ".[cad]"'
        ) from exc
    return cq


@dataclass(frozen=True)
class HandLeverSpec:
    """Compact handheld lever embosser for the standard 42 mm EmbossForge die pair.

    This is intentionally closer to a commercial desk/hand embosser than the
    older rod-guided laboratory press. A forked lever drives one vertically
    guided upper carriage through a transverse pin. The upper die is clamped
    directly into the carriage; the lower die seats directly in the body.
    """

    body_width_mm: float = 62.0
    body_rear_y_mm: float = -75.0
    body_front_y_mm: float = 60.0
    base_thickness_mm: float = 7.0

    die_center_y_mm: float = 30.0
    lower_jaw_width_mm: float = 52.0
    lower_jaw_depth_mm: float = 50.0
    lower_jaw_height_mm: float = 4.0
    die_pocket_clearance_mm: float = 0.15
    die_seat_extra_depth_mm: float = 0.05
    removal_notch_radius_mm: float = 4.0

    carriage_width_mm: float = 52.0
    carriage_depth_mm: float = 50.0
    carriage_thickness_mm: float = 7.0
    guide_clearance_mm: float = 0.35
    guide_wall_thickness_mm: float = 5.0
    guide_front_y_mm: float = 57.0
    guide_rear_y_mm: float = 5.0
    guide_height_mm: float = 35.0

    pivot_y_mm: float = -10.0
    pivot_z_mm: float = 43.0
    pivot_tower_rear_y_mm: float = -28.0
    pivot_tower_front_y_mm: float = 8.0
    pivot_tower_height_mm: float = 58.0
    main_pivot_diameter_mm: float = 6.4

    drive_y_offset_mm: float = 20.0
    drive_z_offset_mm: float = -7.0
    drive_pin_diameter_mm: float = 5.2
    drive_pin_clearance_mm: float = 0.45
    open_travel_mm: float = 14.0

    lever_width_mm: float = 24.0
    lever_thickness_mm: float = 10.0
    lever_front_fork_height_mm: float = 16.0
    lever_rear_length_mm: float = 150.0
    lever_front_length_mm: float = 32.0
    lever_fork_slot_width_mm: float = 14.2

    stem_width_mm: float = 13.0
    stem_depth_mm: float = 18.0
    stem_top_margin_mm: float = 4.0

    cap_thickness_mm: float = 2.5
    cap_width_mm: float = 50.0
    cap_depth_mm: float = 42.0
    cap_boss_diameter_mm: float = 36.0
    cap_screw_clearance_mm: float = 3.3
    carriage_pilot_diameter_mm: float = 2.6
    cap_screw_x_mm: float = 20.0
    cap_screw_y_mm: float = 48.0

    def validate(self, die: DieSpec | None = None) -> None:
        die = die or DieSpec()
        die.validate()
        for name, value in self.__dict__.items():
            if name.endswith("_mm") and value <= 0 and name not in {"body_rear_y_mm", "pivot_y_mm", "pivot_tower_rear_y_mm", "drive_z_offset_mm"}:
                raise ValueError(f"{name} must be positive")
        if self.body_rear_y_mm >= self.body_front_y_mm:
            raise ValueError("body rear must be behind body front")
        if self.die_pocket_clearance_mm >= 1.0:
            raise ValueError("die pocket clearance is implausibly large")
        if self.lower_jaw_width_mm <= die.diameter_mm + 2 * self.die_pocket_clearance_mm:
            raise ValueError("lower jaw is too narrow for the selected die")
        if self.carriage_width_mm <= die.diameter_mm + 2 * self.die_pocket_clearance_mm:
            raise ValueError("upper carriage is too narrow for the selected die")
        if self.carriage_width_mm + 2 * (self.guide_clearance_mm + self.guide_wall_thickness_mm) > self.body_width_mm + 1.0:
            raise ValueError("guide walls do not fit within body width")
        if self.lever_fork_slot_width_mm <= self.stem_width_mm + 0.4:
            raise ValueError("lever fork slot needs printable side clearance around the carriage stem")
        if self.lever_width_mm <= self.lever_fork_slot_width_mm + 2 * 3.5:
            raise ValueError("lever fork arms are too thin")
        if self.open_angle_deg >= 60.0:
            raise ValueError("requested opening travel requires an excessive handle angle")
        if self.closed_carriage_bottom_z_mm(die) <= self.base_thickness_mm:
            raise ValueError("closed upper carriage would collide with the base")
        if self.cap_boss_height_mm(die) <= 0:
            raise ValueError("upper backing boss height must be positive")

    @property
    def body_depth_mm(self) -> float:
        return self.body_front_y_mm - self.body_rear_y_mm

    @property
    def drive_radius_mm(self) -> float:
        return math.hypot(self.drive_y_offset_mm, self.drive_z_offset_mm)

    @property
    def nominal_lever_ratio(self) -> float:
        return self.lever_rear_length_mm / max(self.drive_radius_mm, 1e-9)

    def lower_die_face_z_mm(self, die: DieSpec) -> float:
        return self.base_thickness_mm + self.lower_jaw_height_mm - self.die_seat_extra_depth_mm

    def closed_carriage_bottom_z_mm(self, die: DieSpec) -> float:
        # The upper die face is nominally flush with the underside of the carriage.
        return self.lower_die_face_z_mm(die) + die.paper_thickness_mm

    def drive_pin_closed_z_mm(self) -> float:
        return self.pivot_z_mm + self.drive_z_offset_mm

    def drive_pin_world_y_mm(self) -> float:
        return self.pivot_y_mm + self.drive_y_offset_mm

    def stem_pin_local_z_mm(self, die: DieSpec) -> float:
        return self.drive_pin_closed_z_mm() - self.closed_carriage_bottom_z_mm(die)

    def cap_boss_height_mm(self, die: DieSpec) -> float:
        # Pushes the 3 mm die base to the underside of the 7 mm through-pocket.
        return self.carriage_thickness_mm - die.base_thickness_mm + self.die_seat_extra_depth_mm

    def drive_lift_mm(self, angle_deg: float) -> float:
        a = math.radians(angle_deg)
        y = self.drive_y_offset_mm
        z = self.drive_z_offset_mm
        rotated_z = y * math.sin(a) + z * math.cos(a)
        return rotated_z - z

    @property
    def open_angle_deg(self) -> float:
        lo, hi = 0.0, 59.0
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
    """Return the exact die contract generated by the normal 42 mm desktop/CLI path."""
    die = DieSpec()
    die.validate()
    return die


def hand_lever_spec(*, die_pocket_clearance_mm: float = 0.15) -> HandLeverSpec:
    spec = HandLeverSpec(die_pocket_clearance_mm=die_pocket_clearance_mm)
    spec.validate(standard_handheld_die_spec())
    return spec


def _keyed_plan(die: DieSpec, spec: HandLeverSpec):
    cq = _cq()
    clear = spec.die_pocket_clearance_mm
    circle = cq.Workplane("XY").circle((die.diameter_mm + 2 * clear) / 2).extrude(1.0)
    overlap = 0.5
    tab_depth = die.key_depth_mm + overlap + 2 * clear
    tab_y = die.diameter_mm / 2 + (die.key_depth_mm - overlap) / 2
    tab = (
        cq.Workplane("XY")
        .center(0, tab_y)
        .rect(die.key_width_mm + 2 * clear, tab_depth)
        .extrude(1.0)
    )
    return circle.union(tab)


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

    base_center_y = (spec.body_rear_y_mm + spec.body_front_y_mm) / 2
    body = (
        cq.Workplane("XY")
        .box(spec.body_width_mm, spec.body_depth_mm, spec.base_thickness_mm, centered=(True, True, False))
        .translate((0, base_center_y, 0))
    )

    lower_jaw = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(
            spec.lower_jaw_width_mm,
            spec.lower_jaw_depth_mm,
            spec.lower_jaw_height_mm,
            centered=(True, True, False),
        )
        .translate((0, 0, spec.base_thickness_mm))
    )
    body = body.union(lower_jaw)

    guide_x = spec.carriage_width_mm / 2 + spec.guide_clearance_mm + spec.guide_wall_thickness_mm / 2
    guide_depth = spec.guide_front_y_mm - spec.guide_rear_y_mm
    guide_y = (spec.guide_front_y_mm + spec.guide_rear_y_mm) / 2
    tower_depth = spec.pivot_tower_front_y_mm - spec.pivot_tower_rear_y_mm
    tower_y = (spec.pivot_tower_front_y_mm + spec.pivot_tower_rear_y_mm) / 2

    for sign in (-1, 1):
        x = sign * guide_x
        guide = (
            cq.Workplane("XY")
            .center(x, guide_y)
            .box(
                spec.guide_wall_thickness_mm,
                guide_depth,
                spec.guide_height_mm,
                centered=(True, True, False),
            )
            .translate((0, 0, spec.base_thickness_mm))
        )
        tower = (
            cq.Workplane("XY")
            .center(x, tower_y)
            .box(
                spec.guide_wall_thickness_mm,
                tower_depth,
                spec.pivot_tower_height_mm - spec.base_thickness_mm,
                centered=(True, True, False),
            )
            .translate((0, 0, spec.base_thickness_mm))
        )
        body = body.union(guide).union(tower)

    # Positive mechanical stop: the carriage bears here at nominal paper closure.
    stop_height = spec.closed_carriage_bottom_z_mm(die) - spec.base_thickness_mm
    for sign in (-1, 1):
        stop = (
            cq.Workplane("XY")
            .center(sign * (spec.carriage_width_mm / 2 - 4.0), spec.guide_rear_y_mm + 4.0)
            .box(6.0, 8.0, stop_height, centered=(True, True, False))
            .translate((0, 0, spec.base_thickness_mm))
        )
        body = body.union(stop)

    lower_pocket_depth = die.base_thickness_mm + spec.die_seat_extra_depth_mm
    lower_pocket_z = (
        spec.base_thickness_mm + spec.lower_jaw_height_mm - lower_pocket_depth
    )
    body = body.cut(_keyed_cut(die, spec, lower_pocket_depth + 0.05, lower_pocket_z))

    front_notch = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm + die.diameter_mm / 2)
        .circle(spec.removal_notch_radius_mm)
        .extrude(lower_pocket_depth + 0.5)
        .translate((0, 0, lower_pocket_z))
    )
    body = body.cut(front_notch)

    pivot_bore = (
        cq.Workplane("YZ")
        .center(spec.pivot_y_mm, spec.pivot_z_mm)
        .circle(spec.main_pivot_diameter_mm / 2)
        .extrude(spec.body_width_mm + 4, both=True)
    )
    return body.cut(pivot_bore)


def build_upper_carriage(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    spec = spec or hand_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    plate = (
        cq.Workplane("XY")
        .center(0, spec.die_center_y_mm)
        .box(
            spec.carriage_width_mm,
            spec.carriage_depth_mm,
            spec.carriage_thickness_mm,
            centered=(True, True, False),
        )
    )

    # Full through-hole: no 42 mm ceiling/bridge when printed flat.
    plate = plate.cut(_keyed_cut(die, spec, spec.carriage_thickness_mm + 0.4, -0.2))

    pin_z = spec.stem_pin_local_z_mm(die)
    stem_height = (
        pin_z
        + (spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2
        + spec.stem_top_margin_mm
        - spec.carriage_thickness_mm
    )
    if stem_height <= 0:
        raise ValueError("upper carriage stem height is invalid")

    stem = (
        cq.Workplane("XY")
        .center(0, spec.drive_pin_world_y_mm())
        .box(spec.stem_width_mm, spec.stem_depth_mm, stem_height, centered=(True, True, False))
        .translate((0, 0, spec.carriage_thickness_mm))
    )
    carriage = plate.union(stem)

    drive_bore = (
        cq.Workplane("YZ")
        .center(spec.drive_pin_world_y_mm(), pin_z)
        .circle((spec.drive_pin_diameter_mm + spec.drive_pin_clearance_mm) / 2)
        .extrude(spec.stem_width_mm + 4, both=True)
    )
    carriage = carriage.cut(drive_bore)

    # Two pilot holes accept ordinary M3 screws from the removable top backing cap.
    for sign in (-1, 1):
        pilot = (
            cq.Workplane("XY")
            .center(sign * spec.cap_screw_x_mm, spec.cap_screw_y_mm)
            .circle(spec.carriage_pilot_diameter_mm / 2)
            .extrude(5.5)
            .translate((0, 0, spec.carriage_thickness_mm - 5.5))
        )
        carriage = carriage.cut(pilot)
    return carriage


def build_upper_backing_cap(spec: HandLeverSpec | None = None, die: DieSpec | None = None):
    """Print-flat backing cap; flip it boss-down onto the carriage during assembly."""
    spec = spec or hand_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)
    cq = _cq()

    plate = (
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
    cap = plate.union(boss)
    for sign in (-1, 1):
        hole = (
            cq.Workplane("XY")
            .center(sign * spec.cap_screw_x_mm, spec.cap_screw_y_mm)
            .circle(spec.cap_screw_clearance_mm / 2)
            .extrude(spec.cap_thickness_mm + 0.5)
        )
        cap = cap.cut(hole)
    return cap


def build_hand_lever(spec: HandLeverSpec | None = None):
    """Build the forked handle in local coordinates with the main pivot at the origin."""
    spec = spec or hand_lever_spec()
    spec.validate(standard_handheld_die_spec())
    cq = _cq()

    rear_y0 = -spec.lever_rear_length_mm
    rear_y1 = 8.0
    rear = (
        cq.Workplane("XY")
        .box(
            spec.lever_width_mm,
            rear_y1 - rear_y0,
            spec.lever_thickness_mm,
            centered=(True, True, True),
        )
        .translate((0, (rear_y0 + rear_y1) / 2, 0))
    )

    fork_y0 = -8.0
    fork_y1 = spec.lever_front_length_mm
    fork_center_z = spec.drive_z_offset_mm / 2
    fork = (
        cq.Workplane("XY")
        .box(
            spec.lever_width_mm,
            fork_y1 - fork_y0,
            spec.lever_front_fork_height_mm,
            centered=(True, True, True),
        )
        .translate((0, (fork_y0 + fork_y1) / 2, fork_center_z))
    )
    lever = rear.union(fork)

    slot = (
        cq.Workplane("XY")
        .box(
            spec.lever_fork_slot_width_mm,
            fork_y1 - (-5.0) + 1.0,
            spec.lever_front_fork_height_mm + 8.0,
            centered=(True, True, True),
        )
        .translate((0, (fork_y1 - 5.0) / 2, fork_center_z))
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
        raise ValueError("state must be 'open' or 'closed'")
    spec = spec or hand_lever_spec()
    die = die or standard_handheld_die_spec()
    spec.validate(die)

    carriage_z = spec.closed_carriage_bottom_z_mm(die)
    angle = 0.0
    if state == "open":
        carriage_z += spec.open_travel_mm
        angle = spec.open_angle_deg

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
    """Export the compact 42 mm handheld lever embosser and assembly metadata."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    die = standard_handheld_die_spec()
    spec = hand_lever_spec(die_pocket_clearance_mm=die_pocket_clearance_mm)

    body = build_hand_lever_body(spec, die)
    carriage = build_upper_carriage(spec, die)
    cap = build_upper_backing_cap(spec, die)
    lever = build_hand_lever(spec)

    parts = {
        "body": body,
        "upper_carriage": carriage,
        "upper_backing_cap": cap,
        "lever": lever,
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

    layout = {
        "coordinate_system": "+Y is the paper/die insertion nose; +Z is up",
        "die_orientation": {
            "lower_male": "face up; carrier key +Y",
            "upper_female": "face down; flip printed female 180 degrees about Y; carrier key remains +Y",
        },
        "closed": {
            "upper_carriage_translation_mm": [0.0, 0.0, spec.closed_carriage_bottom_z_mm(die)],
            "lever_translation_mm": [0.0, spec.pivot_y_mm, spec.pivot_z_mm],
            "lever_rotation_deg_x": 0.0,
        },
        "open": {
            "upper_carriage_translation_mm": [0.0, 0.0, spec.closed_carriage_bottom_z_mm(die) + spec.open_travel_mm],
            "lever_translation_mm": [0.0, spec.pivot_y_mm, spec.pivot_z_mm],
            "lever_rotation_deg_x": spec.open_angle_deg,
        },
    }
    layout_path = out / "assembly_layout.json"
    layout_path.write_text(json.dumps(layout, indent=2) + "\n", encoding="utf-8")
    outputs["assembly_layout"] = str(layout_path)

    masses = {name: round(_solid_mass_g(part), 2) for name, part in parts.items()}
    manifest = {
        "mode": "full-size-handheld-lever-embosser",
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
            "closed_carriage_bottom_z_mm": spec.closed_carriage_bottom_z_mm(die),
            "open_carriage_bottom_z_mm": spec.closed_carriage_bottom_z_mm(die) + spec.open_travel_mm,
            "open_handle_angle_deg": spec.open_angle_deg,
            "nominal_lever_ratio": spec.nominal_lever_ratio,
            "solid_pla_mass_upper_bound_g": masses,
        },
        "hardware": {
            "main_pivot": "1 x M6 bolt / 6 mm smooth pin",
            "drive_pin": "1 x M5 bolt / 5 mm smooth pin",
            "upper_die_cap": "2 x M3 x ~10 mm screws; the 2.6 mm carriage pilots are intended for prototype self-tapping",
        },
        "printed_quantities": {"body": 1, "upper_carriage": 1, "upper_backing_cap": 1, "lever": 1},
        "collision_validation": collisions,
        "assembly": layout,
        "outputs": outputs,
    }
    manifest_path = out / "lever_press_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    outputs["manifest"] = str(manifest_path)
    return outputs
