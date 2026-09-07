from embossforge.mechanics.fit_coupon import build_fit_coupon_pair, build_fit_coupon_parts


def test_fit_coupon_contains_two_valid_parts():
    parts = build_fit_coupon_parts(slide_clearance_mm=0.25)
    assert set(parts) == {"slider", "receiver"}
    assert parts["slider"].val().Volume() > 0
    assert parts["receiver"].val().Volume() > 0


def test_fit_coupon_is_tiny_enough_for_scarce_filament():
    pair = build_fit_coupon_pair(slide_clearance_mm=0.25)
    # Solid PLA ceiling at 1.24 g/cm^3. Sliced mass should be lower still.
    solid_mass_g = pair.Volume() / 1000.0 * 1.24
    assert solid_mass_g < 4.0
