from embossforge.mechanics.handheld_elegant import (
    build_elegant_body,
    build_elegant_lever,
    build_elegant_upper_cap,
    build_elegant_upper_carriage,
    elegant_lever_spec,
    validate_elegant_clearance,
)
from embossforge.mechanics.handheld_compact import standard_handheld_die_spec


def test_elegant_press_keeps_standard_die_contract():
    die = standard_handheld_die_spec()
    spec = elegant_lever_spec()
    assert die.diameter_mm == 42.0
    assert die.base_thickness_mm == 3.0
    assert die.key_width_mm == 6.0
    assert die.key_depth_mm == 2.5
    assert spec.nominal_lever_ratio > 6.5


def test_elegant_parts_are_real_solids():
    die = standard_handheld_die_spec()
    spec = elegant_lever_spec()
    parts = {
        "body": build_elegant_body(spec, die),
        "upper_carriage": build_elegant_upper_carriage(spec, die),
        "upper_cap": build_elegant_upper_cap(spec, die),
        "lever": build_elegant_lever(spec),
    }
    for name, part in parts.items():
        assert part.val().Volume() > 100.0, name


def test_elegant_open_and_closed_states_are_collision_free():
    assert validate_elegant_clearance() == {"closed": [], "open": []}
