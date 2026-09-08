import pytest

from embossforge.mechanics.handheld import (
    build_hand_lever,
    build_hand_lever_body,
    build_upper_backing_cap,
    build_upper_carriage,
    hand_lever_spec,
    standard_handheld_die_spec,
    validate_hand_lever_clearance,
)


def test_handheld_press_matches_standard_42mm_die_contract():
    die = standard_handheld_die_spec()
    spec = hand_lever_spec()

    assert die.diameter_mm == 42.0
    assert die.base_thickness_mm == 3.0
    assert die.key_width_mm == 6.0
    assert die.key_depth_mm == 2.5
    assert spec.lower_jaw_width_mm > die.diameter_mm
    assert spec.carriage_width_mm > die.diameter_mm


def test_handheld_press_has_useful_leverage_and_opening():
    die = standard_handheld_die_spec()
    spec = hand_lever_spec()

    assert spec.nominal_lever_ratio > 6.5
    assert 25.0 < spec.open_angle_deg < 55.0
    assert spec.open_travel_mm >= 12.0
    assert spec.closed_carriage_bottom_z_mm(die) > spec.base_thickness_mm
    assert spec.stem_pin_local_z_mm(die) > spec.carriage_thickness_mm


def test_handheld_printed_parts_are_valid_solids():
    die = standard_handheld_die_spec()
    spec = hand_lever_spec()
    parts = [
        build_hand_lever_body(spec, die),
        build_upper_carriage(spec, die),
        build_upper_backing_cap(spec, die),
        build_hand_lever(spec),
    ]
    for part in parts:
        assert part.val().Volume() > 100.0


def test_handheld_open_and_closed_states_have_no_unintended_collisions():
    report = validate_hand_lever_clearance()
    assert report == {"closed": [], "open": []}


def test_upper_carriage_has_side_clearance_inside_guides():
    spec = hand_lever_spec()
    inside_gap = spec.body_width_mm - 2 * spec.guide_wall_thickness_mm
    assert inside_gap - spec.carriage_width_mm == pytest.approx(0.0, abs=2.0)
    assert spec.guide_clearance_mm >= 0.25
