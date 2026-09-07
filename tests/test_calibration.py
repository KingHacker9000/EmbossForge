from embossforge.calibration import (
    ClearanceCouponSpec,
    EmbossCouponSpec,
    render_emboss_matrix_scad,
    render_slide_clearance_scad,
)


def test_clearance_coupon_contains_requested_values():
    text = render_slide_clearance_scad(ClearanceCouponSpec(values_mm=(0.1, 0.25, 0.4)))
    assert '"0.10"' in text
    assert '"0.25"' in text
    assert '"0.40"' in text


def test_emboss_pair_uses_same_matrix_dimensions():
    spec = EmbossCouponSpec(relief_values_mm=(0.4, 0.7), xy_clearance_values_mm=(0.15, 0.25))
    male = render_emboss_matrix_scad(spec, female=False)
    female = render_emboss_matrix_scad(spec, female=True)
    assert "mark2d" in male
    assert "mark2d" in female
    assert "delta=0.1500" in female
    assert "delta=0.2500" in female
