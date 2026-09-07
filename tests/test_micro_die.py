from embossforge.micro_die import (
    _butterfly_2d_scad,
    _female_scad,
    _male_scad,
    _solid_pair_mass_upper_bound_g,
    micro_butterfly_spec,
)


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


def test_micro_butterfly_uses_direct_four_wing_geometry():
    shape = _butterfly_2d_scad()
    assert shape.count("scale([1.35, 1.00])") == 2
    assert shape.count("scale([1.10, 0.85])") == 2
    assert "hull()" in shape


def test_micro_scad_does_not_import_svg():
    spec = micro_butterfly_spec()
    male = _male_scad(spec)
    female = _female_scad(spec)
    assert "import(" not in male
    assert "import(" not in female
    assert "butterfly2d();" in male
    assert "offset(delta=0.2000) butterfly2d();" in female
