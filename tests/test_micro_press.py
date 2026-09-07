from embossforge.mechanics import mechanical_layout, validate_assembly_clearance
from embossforge.mechanics.micro import micro_press_cartridge_spec, micro_press_spec
from embossforge.mechanics.mini import mini_press_spec
from embossforge.micro_die import micro_butterfly_spec


def test_micro_press_matches_existing_butterfly_die_contract():
    die = micro_butterfly_spec()
    cartridge = micro_press_cartridge_spec()

    assert cartridge.die_diameter_mm == die.diameter_mm == 16.0
    assert cartridge.die_base_thickness_mm == die.base_thickness_mm == 1.8
    assert cartridge.die_key_width_mm == die.key_width_mm == 3.5
    assert cartridge.die_key_depth_mm == die.key_depth_mm == 1.5
    assert cartridge.die_pocket_diameter_mm > die.diameter_mm


def test_micro_press_is_smaller_than_existing_mini_press():
    micro = micro_press_spec()
    mini = mini_press_spec()

    assert micro.base_width_mm < mini.base_width_mm
    assert micro.base_depth_mm < mini.base_depth_mm
    assert micro.lever_length_mm < mini.lever_length_mm
    assert micro.guide_rod_diameter_mm < mini.guide_rod_diameter_mm
    assert micro.nominal_lever_ratio > 4.0


def test_micro_press_kinematics_are_valid():
    cartridge = micro_press_cartridge_spec()
    press = micro_press_spec()
    layout = mechanical_layout(cartridge, press)

    assert layout["platen_open_bottom_z"] > layout["platen_closed_bottom_z"]
    assert layout["lever_open_angle_deg"] > 0
    assert layout["guide_rod_length"] > 0
    assert layout["pivot_axis_height_above_base"] < press.side_cheek_height_mm


def test_micro_press_open_and_closed_assemblies_have_no_unintended_collisions():
    report = validate_assembly_clearance(micro_press_cartridge_spec(), micro_press_spec())
    assert report == {"open": [], "closed": []}
