from embossforge.config import DieSpec


def test_default_spec_is_valid():
    spec = DieSpec()
    spec.validate()
    assert spec.artwork_box_mm == 36.0
    assert spec.female_cavity_depth_mm == 0.95


def test_margin_cannot_consume_die():
    spec = DieSpec(diameter_mm=20, margin_mm=10)
    try:
        spec.validate()
    except ValueError as exc:
        assert "no printable artwork" in str(exc)
    else:
        raise AssertionError("expected validation failure")
