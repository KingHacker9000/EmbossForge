from embossforge.mechanics.micro import build_micro_tongs, micro_tongs_spec
from embossforge.micro_die import micro_butterfly_spec


def test_micro_tongs_match_existing_butterfly_die_contract():
    die = micro_butterfly_spec()
    spec = micro_tongs_spec()

    assert die.diameter_mm == 16.0
    assert die.base_thickness_mm == 1.8
    assert die.key_width_mm == 3.5
    assert die.key_depth_mm == 1.5
    assert spec.jaw_outer_diameter_mm > die.diameter_mm
    assert spec.die_pocket_depth_mm < die.base_thickness_mm


def test_micro_tongs_need_only_small_elastic_closure():
    spec = micro_tongs_spec()

    assert spec.open_jaw_surface_gap_mm > spec.required_closed_surface_gap_mm
    assert 1.0 < spec.required_total_flex_mm < 4.0
    assert spec.required_flex_per_arm_mm < 2.0


def test_micro_tongs_are_single_printable_solid():
    part = build_micro_tongs(micro_tongs_spec())
    solid = part.val()

    assert solid.Volume() > 0
    assert len(part.solids().vals()) == 1


def test_micro_tongs_are_low_material_by_solid_upper_bound():
    part = build_micro_tongs(micro_tongs_spec())
    solid_mass_g = part.val().Volume() / 1000.0 * 1.24

    # This is a deliberately conservative all-solid upper bound. A normal sliced
    # print with sparse infill should be lower.
    assert solid_mass_g < 8.0
