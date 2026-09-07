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
    receiver_height_mm: float = 6.5

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
        return self.body_width_mm + 2 * self.side_rail_extension_mm + 2 * self.receiver_wall_mm

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
    """Dimensions for the V0.2 rod-guided lever press prototype.

    The upper platen slides on two 8 mm guide rods outside the cartridge. A
    small transverse roller under the lever contacts the platen so the lever
    itself never scrapes across the printed platen.
    """

    base_width_mm: float = 130.0
    base_depth_mm: float = 155.0
    base_thickness_mm: float = 12.0

    side_cheek_thickness_mm: float = 10.0
    side_cheek_height_mm: float = 82.0
    side_cheek_depth_mm: float = 70.0
    cheek_spacing_mm: float = 104.0

    pivot_diameter_mm: float = 6.4
    throat_depth_mm: float = 67.0

    lever_width_mm: float = 28.0
    lever_thickness_mm: float = 12.0
    lever_length_mm: float = 205.0
    lever_rear_overhang_mm: float = 24.0
    lever_pivot_to_platen_mm: float = 36.0

    contact_roller_diameter_mm: float = 12.0
    contact_roller_width_mm: float = 16.0
    contact_roller_pin_diameter_mm: float = 5.2
    contact_roller_drop_mm: float = 12.0
    contact_clearance_mm: float = 0.20
    lever_ear_thickness_mm: float = 5.0
    lever_ear_depth_mm: float = 18.0
    lever_ear_pin_margin_mm: float = 1.0
    lever_ear_overlap_mm: float = 1.0
    platen_ear_relief_depth_mm: float = 2.0

    platen_width_mm: float = 100.0
    platen_depth_mm: float = 46.0
    platen_thickness_mm: float = 12.0

    guide_rod_diameter_mm: float = 8.0
    guide_rod_spacing_mm: float = 78.0
    guide_rod_platen_clearance_mm: float = 0.50
    guide_rod_socket_clearance_mm: float = 0.20
    guide_rod_socket_depth_mm: float = 8.0

    top_bridge_depth_mm: float = 30.0
    top_bridge_thickness_mm: float = 12.0
    top_bridge_bottom_above_base_mm: float = 82.0

    stop_sleeve_outer_diameter_mm: float = 12.0
    stop_sleeve_rod_clearance_mm: float = 0.50

    open_face_gap_mm: float = 18.0
    closed_face_gap_mm: float = 0.20
    nominal_die_relief_mm: float = 0.65

    mounting_hole_diameter_mm: float = 5.2
    mounting_hole_edge_offset_mm: float = 12.0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if name.endswith("_mm") and value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.cheek_spacing_mm <= self.platen_width_mm:
            raise ValueError("Cheek spacing must exceed platen width")
        if self.cheek_spacing_mm <= self.lever_width_mm:
            raise ValueError("Cheek spacing must exceed lever width")
        if self.lever_rear_overhang_mm >= self.lever_length_mm:
            raise ValueError("Lever rear overhang must be shorter than the lever")
        if self.lever_pivot_to_platen_mm >= self.lever_length_mm - self.lever_rear_overhang_mm:
            raise ValueError("Platen contact must lie on the forward lever arm")
        if self.closed_face_gap_mm >= self.open_face_gap_mm:
            raise ValueError("Closed face gap must be smaller than open face gap")
        if self.top_bridge_bottom_above_base_mm < self.side_cheek_height_mm:
            raise ValueError("Top bridge overlaps the side cheeks; it must sit at or above their top")
        if self.guide_rod_spacing_mm >= self.platen_width_mm - self.guide_rod_diameter_mm:
            raise ValueError("Guide rods are too close to the platen edges")
        if self.stop_sleeve_outer_diameter_mm <= self.guide_rod_diameter_mm + self.stop_sleeve_rod_clearance_mm:
            raise ValueError("Stop sleeve needs positive wall thickness")
        if self.contact_roller_width_mm + 2 * self.lever_ear_thickness_mm > self.lever_width_mm:
            raise ValueError("Roller and ears do not fit within lever width")
        if self.contact_roller_drop_mm <= self.lever_thickness_mm / 2:
            raise ValueError("Roller pin must sit below the lever body")

    @property
    def nominal_lever_ratio(self) -> float:
        return (self.lever_length_mm - self.lever_rear_overhang_mm) / self.lever_pivot_to_platen_mm

    @property
    def required_platen_travel_mm(self) -> float:
        return self.open_face_gap_mm - self.closed_face_gap_mm

    @property
    def guide_rod_platen_hole_diameter_mm(self) -> float:
        return self.guide_rod_diameter_mm + self.guide_rod_platen_clearance_mm

    @property
    def guide_rod_socket_diameter_mm(self) -> float:
        return self.guide_rod_diameter_mm + self.guide_rod_socket_clearance_mm

    @property
    def top_bridge_width_mm(self) -> float:
        return self.cheek_spacing_mm + 2 * self.side_cheek_thickness_mm
