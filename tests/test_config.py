import pytest

from embossforge.config import (
    DieSpec,
    PrinterProfile,
    paper_thickness_for_preset,
)


def test_default_spec_is_valid():
    spec = DieSpec()
    spec.validate()
    assert spec.artwork_box_mm == 36.0
    assert spec.female_cavity_depth_mm == pytest.approx(0.70)
    assert spec.nominal_feature_gap_mm == pytest.approx(0.15)


def test_female_cavity_does_not_double_count_paper_thickness():
    thin = DieSpec(relief_height_mm=1.2, paper_thickness_mm=0.10, female_extra_depth_mm=0.03)
    thick = DieSpec(relief_height_mm=1.2, paper_thickness_mm=0.25, female_extra_depth_mm=0.03)
    assert thin.female_cavity_depth_mm == pytest.approx(1.23)
    assert thick.female_cavity_depth_mm == pytest.approx(1.23)
    assert thin.nominal_feature_gap_mm == pytest.approx(0.13)
    assert thick.nominal_feature_gap_mm == pytest.approx(0.28)


def test_margin_cannot_consume_die():
    spec = DieSpec(diameter_mm=20, margin_mm=10)
    with pytest.raises(ValueError, match="no printable artwork"):
        spec.validate()


def test_paper_presets_are_available():
    assert paper_thickness_for_preset("copy") == 0.10
    assert paper_thickness_for_preset("premium") == 0.13
    assert paper_thickness_for_preset("cardstock") == 0.25


def test_unknown_paper_preset_is_rejected():
    with pytest.raises(ValueError, match="Unknown paper preset"):
        paper_thickness_for_preset("banana")


def test_printer_profile_validates_die_against_build_volume():
    profile = PrinterProfile(
        name="tiny test printer",
        build_x_mm=50,
        build_y_mm=50,
        build_z_mm=50,
        nozzle_mm=0.4,
        layer_height_mm=0.2,
        min_feature_mm=0.5,
        min_gap_mm=0.45,
        recommended_die_clearance_mm=0.2,
    )
    profile.validate_die(DieSpec(diameter_mm=42))

    with pytest.raises(ValueError, match="exceeds printer"):
        profile.validate_die(DieSpec(diameter_mm=60))
