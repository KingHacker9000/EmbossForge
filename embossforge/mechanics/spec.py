from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CartridgeSpec:
    """Dimensions for the interchangeable die cartridge and receiver.

    The same cartridge geometry is used for both halves. The lower cartridge is
    installed normally; the upper cartridge is rotated 180 degrees about Y so
    both cartridges still insert from the same +Y/front side of the press.

    All dimensions are millimetres. Defaults are prototype values for an AD5M
    with a 0.4 mm nozzle and must be calibrated before being treated as final.
    """

    die_diameter_mm: float = 42.0
    die_base_thickness_mm: float = 3.0
    die_key_width_mm: float = 6.0
    die_key_depth_mm: float = 2.5
    die_pocket_clearance_mm: float = 0.15
    die_seat_recess_mm: float = 0.05

    body_width_mm: float = 52.0
    body_depth_mm: float = 58.0
    body_thickness_mm: float = 6.0

    side_rail_extension_mm: float = 2.5
    side_rail_height_mm: float = 2.2
    side_rail_center_z_mm: float = 3.0
    side_rail_front_setback_mm: float = 3.0
    side_rail_rear_setback_mm: float = 2.0

    receiver_slide_clearance_mm: float = 0.25
    receiver_wall_mm: float = 3.0
    receiver_floor_mm: float = 1.5
    receiver_rear_wall_mm: float = 3.5
    receiver_height_mm: float = 8.0

    front_finger_notch_radius_mm: float = 7.0
    front_finger_notch_depth_mm: float = 3.0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if name.endswith("_mm") and value < 0:
                raise ValueError(f"{name} cannot be negative")

        required_positive = (
            "die_diameter_mm",
            "die_base_thickness_mm",
            "die_key_width_mm",
            "die_key_depth_mm",
            "body_width_mm",
            "body_depth_mm",
            "body_thickness_mm",
            "side_rail_extension_mm",
            "side_rail_height_mm",
            "receiver_wall_mm",
            "receiver_floor_mm",
            "receiver_rear_wall_mm",
            "receiver_height_mm",
        )
        bad = [name for name in required_positive if getattr(self, name) <= 0]
        if bad:
            raise ValueError(f"Cartridge dimensions must be positive: {', '.join(bad)}")

        if self.body_width_mm <= self.die_diameter_mm + 2 * self.die_pocket_clearance_mm:
            raise ValueError("Cartridge body is too narrow for the die insert")
        if self.body_depth_mm <= self.die_diameter_mm + self.die_key_depth_mm + 2 * self.die_pocket_clearance_mm:
            raise ValueError("Cartridge body is too shallow for the keyed die insert")
        if self.body_thickness_mm <= self.die_base_thickness_mm + self.die_seat_recess_mm:
            raise ValueError("Cartridge body must leave material below the die seat")
        if self.die_key_width_mm >= self.die_diameter_mm:
            raise ValueError("Die key must be narrower than the die")
        if self.side_rail_center_z_mm - self.side_rail_height_mm / 2 < 0:
            raise ValueError("Side rail extends below the cartridge body")
        if self.side_rail_center_z_mm + self.side_rail_height_mm / 2 > self.body_thickness_mm:
            raise ValueError("Side rail extends above the cartridge body")
        if self.receiver_floor_mm >= self.receiver_height_mm:
            raise ValueError("Receiver floor must be thinner than receiver height")
        if self.receiver_height_mm <= self.receiver_floor_mm + self.side_rail_center_z_mm + self.side_rail_height_mm / 2:
            raise ValueError("Receiver is too short to contain the cartridge rail")

    @property
    def die_pocket_diameter_mm(self) -> float:
        return self.die_diameter_mm + 2 * self.die_pocket_clearance_mm

    @property
    def rail_length_mm(self) -> float:
        return self.body_depth_mm - self.side_rail_front_setback_mm - self.side_rail_rear_setback_mm

    @property
    def receiver_outer_width_mm(self) -> float:
        return (
            self.body_width_mm
            + 2 * self.side_rail_extension_mm
            + 2 * self.receiver_wall_mm
        )

    @property
    def receiver_outer_depth_mm(self) -> float:
        return self.body_depth_mm + self.receiver_rear_wall_mm

    @property
    def inserted_cartridge_bottom_z_mm(self) -> float:
        return self.receiver_floor_mm

    @property
    def inserted_cartridge_top_z_mm(self) -> float:
        return self.receiver_floor_mm + self.body_thickness_mm


@dataclass(frozen=True)
class PressSpec:
    """Prototype dimensions for the V0.2 lever press."""

    base_width_mm: float = 100.0
    base_depth_mm: float = 155.0
    base_thickness_mm: float = 12.0

    side_cheek_thickness_mm: float = 10.0
    side_cheek_height_mm: float = 128.0
    side_cheek_depth_mm: float = 34.0
    cheek_spacing_mm: float = 58.0

    pivot_diameter_mm: float = 6.4
    pivot_axis_height_above_base_mm: float = 106.0
    throat_depth_mm: float = 67.0

    lever_width_mm: float = 28.0
    lever_thickness_mm: float = 12.0
    lever_length_mm: float = 250.0
    lever_rear_overhang_mm: float = 24.0
    lever_pivot_to_ram_mm: float = 36.0

    ram_width_mm: float = 34.0
    ram_depth_mm: float = 36.0
    ram_height_mm: float = 66.0
    ram_slide_clearance_mm: float = 0.30
    guide_wall_mm: float = 7.0
    guide_height_mm: float = 76.0
    guide_rear_wall_mm: float = 7.0

    open_face_gap_mm: float = 18.0
    closed_face_gap_mm: float = 0.20
    nominal_die_relief_mm: float = 0.65

    mounting_hole_diameter_mm: float = 5.2
    mounting_hole_edge_offset_mm: float = 12.0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if name.endswith("_mm") and value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.cheek_spacing_mm <= self.lever_width_mm:
            raise ValueError("Cheek spacing must exceed lever width")
        if self.lever_rear_overhang_mm >= self.lever_length_mm:
            raise ValueError("Lever rear overhang must be shorter than the lever")
        if self.lever_pivot_to_ram_mm >= self.lever_length_mm - self.lever_rear_overhang_mm:
            raise ValueError("Ram contact must lie on the forward lever arm")
        if self.closed_face_gap_mm >= self.open_face_gap_mm:
            raise ValueError("Closed face gap must be smaller than open face gap")
        if self.pivot_axis_height_above_base_mm >= self.side_cheek_height_mm:
            raise ValueError("Pivot must lie inside the side cheek")
        if self.guide_height_mm <= self.ram_height_mm / 2:
            raise ValueError("Ram guide is too short for useful guidance")

    @property
    def nominal_lever_ratio(self) -> float:
        return (self.lever_length_mm - self.lever_rear_overhang_mm) / self.lever_pivot_to_ram_mm

    @property
    def required_ram_travel_mm(self) -> float:
        return self.open_face_gap_mm - self.closed_face_gap_mm
