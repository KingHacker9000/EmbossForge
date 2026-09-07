from embossforge.micro_die import _solid_pair_mass_upper_bound_g, micro_butterfly_spec


def test_micro_butterfly_is_small_and_valid():
    spec = micro_butterfly_spec()
    spec.validate()
    assert spec.diameter_mm == 16.0
    assert spec.base_thickness_mm < 2.0
    assert spec.relief_height_mm <= 0.5


def test_micro_butterfly_pair_stays_near_one_gram_solid():
    spec = micro_butterfly_spec()
    assert _solid_pair_mass_upper_bound_g(spec) < 1.2


def test_micro_butterfly_female_cavity_fits_base():
    spec = micro_butterfly_spec()
    assert spec.female_cavity_depth_mm < spec.base_thickness_mm
