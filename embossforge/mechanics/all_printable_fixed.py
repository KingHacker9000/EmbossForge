from __future__ import annotations

from pathlib import Path

from .handheld_compact import HandLeverSpec, standard_handheld_die_spec
from . import all_printable as _base


def fully_printable_spec(*, die_pocket_clearance_mm: float = 0.20) -> HandLeverSpec:
    """Validated V4 spec for the hardware-free 42 mm press.

    The first V4 draft placed the front edge of the pivot ear at Y=-1 mm.
    HandLeverSpec intentionally treats that field as a positive distance-like
    coordinate, so the draft never reached CAD validation. Moving the ear edge
    to +1 mm keeps the same compact pivot envelope while satisfying the shared
    mechanical-spec contract.
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
        pivot_tower_front_y_mm=1.0,
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


def build_fully_printable_body(spec: HandLeverSpec | None = None):
    return _base.build_fully_printable_body(spec or fully_printable_spec())


def build_fully_printable_upper_carriage(spec: HandLeverSpec | None = None):
    return _base.build_fully_printable_upper_carriage(spec or fully_printable_spec())


def build_fully_printable_upper_cap(spec: HandLeverSpec | None = None):
    return _base.build_fully_printable_upper_cap(spec or fully_printable_spec())


def build_fully_printable_lever(spec: HandLeverSpec | None = None):
    return _base.build_fully_printable_lever(spec or fully_printable_spec())


def build_main_pivot_pin(spec: HandLeverSpec | None = None):
    return _base.build_main_pivot_pin(spec or fully_printable_spec())


def build_drive_pin(spec: HandLeverSpec | None = None):
    return _base.build_drive_pin(spec or fully_printable_spec())


def build_retaining_wedge():
    return _base.build_retaining_wedge()


def build_cap_peg():
    return _base.build_cap_peg()


def build_fully_printable_assembly(spec: HandLeverSpec | None = None, *, state: str = "closed"):
    return _base.build_fully_printable_assembly(spec or fully_printable_spec(), state=state)


def validate_fully_printable_clearance(spec: HandLeverSpec | None = None, *, tolerance_mm3: float = 1e-3):
    return _base.validate_fully_printable_clearance(
        spec or fully_printable_spec(), tolerance_mm3=tolerance_mm3
    )


def export_fully_printable_press_pack(
    out_dir: str | Path,
    *,
    die_pocket_clearance_mm: float = 0.20,
):
    # The base exporter is otherwise correct; temporarily point its internal
    # default factory at the validated V4 spec so every generated part and the
    # collision checker use the exact same dimensions.
    old_factory = _base.fully_printable_spec
    _base.fully_printable_spec = fully_printable_spec
    try:
        return _base.export_fully_printable_press_pack(
            out_dir,
            die_pocket_clearance_mm=die_pocket_clearance_mm,
        )
    finally:
        _base.fully_printable_spec = old_factory
