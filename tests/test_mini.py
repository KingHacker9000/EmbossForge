from embossforge.mechanics import mechanical_layout
from embossforge.mechanics.mini import mini_cartridge_spec, mini_die_spec, mini_press_spec
from embossforge.mechanics.spec import CartridgeSpec, PressSpec


def test_mini_specs_are_valid_and_materially_smaller():
    cartridge = mini_cartridge_spec()
    press = mini_press_spec()
    die = mini_die_spec()

    cartridge.validate()
    press.validate()
    die.validate()

    assert die.diameter_mm < 0.65 * CartridgeSpec().die_diameter_mm
    assert press.base_width_mm < 0.70 * PressSpec().base_width_mm
    assert press.base_depth_mm < 0.70 * PressSpec().base_depth_mm
    assert press.lever_length_mm < 0.65 * PressSpec().lever_length_mm


def test_mini_preserves_realistic_absolute_clearances():
    cartridge = mini_cartridge_spec()
    die = mini_die_spec()

    assert cartridge.receiver_slide_clearance_mm == 0.25
    assert cartridge.die_pocket_clearance_mm == 0.15
    assert die.female_xy_clearance_mm == 0.20


def test_mini_kinematics_have_valid_open_and_closed_states():
    cartridge = mini_cartridge_spec()
    press = mini_press_spec()
    layout = mechanical_layout(cartridge, press)

    assert layout["platen_open_bottom_z"] > layout["platen_closed_bottom_z"]
    assert layout["lever_open_angle_deg"] > 0
    assert layout["guide_rod_length"] > 0
    assert press.nominal_lever_ratio > 4
