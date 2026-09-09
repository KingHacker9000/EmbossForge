import pytest

from embossforge.mechanics.elegant_test import (
    DEFAULT_TEST_SCALE,
    _test_die_base,
    build_elegant_test_parts,
    validate_elegant_test_clearance,
)


def test_default_elegant_test_scale_is_two_thirds():
    assert DEFAULT_TEST_SCALE == pytest.approx(2.0 / 3.0)
    assert DEFAULT_TEST_SCALE**3 == pytest.approx(8.0 / 27.0)


def test_test_press_parts_are_real_solids_and_small():
    parts = build_elegant_test_parts()
    assert set(parts) == {
        "body",
        "upper_carriage",
        "upper_backing_cap",
        "lever",
        "test_male_die",
        "test_female_die",
    }
    for name, part in parts.items():
        assert part.val().Volume() > 20.0, name


def test_scaled_motion_states_remain_collision_free():
    assert validate_elegant_test_clearance() == {"closed": [], "open": []}


def test_throwaway_die_is_about_28_mm_and_slightly_undersized():
    _carrier, dims = _test_die_base()
    assert dims["diameter_mm"] == pytest.approx(27.8)
    assert dims["base_thickness_mm"] == pytest.approx(2.0)
    assert dims["key_width_mm"] < 6.0 * DEFAULT_TEST_SCALE
    assert dims["key_depth_mm"] < 2.5 * DEFAULT_TEST_SCALE
