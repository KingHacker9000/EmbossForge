from embossforge.mechanics.handheld_compact import standard_handheld_die_spec
from embossforge.mechanics.handheld_lean_test import (
    build_lean_test_body,
    build_lean_test_lever,
    build_lean_test_upper_cap,
    build_lean_test_upper_carriage,
    build_printed_cap_peg,
    build_printed_drive_pin,
    build_printed_drive_retainer,
    build_printed_main_pivot,
    build_printed_main_pivot_retainer,
    lean_test_spec,
    validate_lean_test_clearance,
)


def test_lean_press_keeps_exact_existing_42mm_die_contract():
    die = standard_handheld_die_spec()
    spec = lean_test_spec()
    assert die.diameter_mm == 42.0
    assert die.base_thickness_mm == 3.0
    assert die.key_width_mm == 6.0
    assert die.key_depth_mm == 2.5
    assert spec.nominal_lever_ratio > 6.0


def test_lean_press_parts_and_printed_hardware_are_real_solids():
    spec = lean_test_spec()
    parts = {
        "body": build_lean_test_body(spec),
        "upper_carriage": build_lean_test_upper_carriage(spec),
        "upper_cap": build_lean_test_upper_cap(spec),
        "lever": build_lean_test_lever(spec),
        "main_pivot": build_printed_main_pivot(spec),
        "main_retainer": build_printed_main_pivot_retainer(),
        "drive_pin": build_printed_drive_pin(spec),
        "drive_retainer": build_printed_drive_retainer(),
        "cap_peg": build_printed_cap_peg(),
    }
    for name, part in parts.items():
        assert part.val().Volume() > 1.0, name


def test_lean_press_open_and_closed_states_are_collision_free():
    assert validate_lean_test_clearance() == {"closed": [], "open": []}
