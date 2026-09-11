from embossforge.mechanics.all_printable_v5 import (
    build_drive_pin,
    build_fully_printable_body,
    build_fully_printable_lever,
    build_fully_printable_upper_carriage,
    build_main_pivot_pin,
    build_retaining_wedge,
    fully_printable_spec,
    validate_fully_printable_clearance,
)
from embossforge.mechanics.handheld_compact import standard_handheld_die_spec


def test_all_printable_press_keeps_existing_42mm_die_contract():
    die = standard_handheld_die_spec()
    spec = fully_printable_spec()
    assert die.diameter_mm == 42.0
    assert die.base_thickness_mm == 3.0
    assert die.key_width_mm == 6.0
    assert die.key_depth_mm == 2.5
    assert spec.nominal_lever_ratio > 7.0


def test_all_required_hardware_is_printed_geometry():
    spec = fully_printable_spec()
    parts = {
        "body": build_fully_printable_body(spec),
        "upper_carriage": build_fully_printable_upper_carriage(spec),
        "lever": build_fully_printable_lever(spec),
        "main_pivot_pin": build_main_pivot_pin(spec),
        "drive_pin": build_drive_pin(spec),
        "retaining_wedge": build_retaining_wedge(),
    }
    for name, part in parts.items():
        assert part.val().Volume() > 1.0, name


def test_all_printable_press_open_and_closed_states_are_collision_free():
    assert validate_fully_printable_clearance() == {"closed": [], "open": []}
