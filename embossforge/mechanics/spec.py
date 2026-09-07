from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CartridgeSpec:
    """Shared dimensions for the interchangeable cartridge interface.

    All dimensions are millimetres. These are prototype defaults intended for
    a FlashForge Adventurer 5M with a 0.4 mm nozzle; calibration prints should
    be used before treating them as final manufacturing values.
    """

    die_diameter_mm: float = 42.0
    die_base_thickness_mm: float = 3.0
    outer_width_mm: float = 52.0
    outer_depth_mm: float = 58.0
    body_thickness_mm: float = 6.0
    die_pocket_clearance_mm: float = 0.25
    receiver_slide_clearance_mm: float = 0.25
    rail_width_mm: float = 4.0
    rail_height_mm: float = 2.5
    rail_inset_mm: float = 4.0
    insertion_stop_mm: float = 3.0
    front_finger_notch_radius_mm: float = 7.0
    key_width_mm: float = 5.0
    key_depth_mm: float = 2.5
    key_offset_mm: float = 8.0
    magnet_diameter_mm: float = 6.2
    magnet_depth_mm: float = 2.2
    magnet_edge_offset_mm: float = 8.0

    def validate(self) -> None:
        positive = {
            "die_diameter_mm": self.die_diameter_mm,
            "die_base_thickness_mm": self.die_base_thickness_mm,
            "outer_width_mm": self.outer_width_mm,
            "outer_depth_mm": self.outer_depth_mm,
            "body_thickness_mm": self.body_thickness_mm,
            "rail_width_mm": self.rail_width_mm,
            "rail_height_mm": self.rail_height_mm,
            "key_width_mm": self.key_width_mm,
            "key_depth_mm": self.key_depth_mm,
        }
        bad = [name for name, value in positive.items() if value <= 0]
        if bad:
            raise ValueError(f"Cartridge dimensions must be positive: {', '.join(bad)}")
        if self.die_pocket_clearance_mm < 0 or self.receiver_slide_clearance_mm < 0:
            raise ValueError("Clearances cannot be negative")
        if self.outer_width_mm <= self.die_diameter_mm + 2 * self.die_pocket_clearance_mm:
            raise ValueError("Cartridge outer width is too small for the die pocket")
        if self.outer_depth_mm <= self.die_diameter_mm + 2 * self.die_pocket_clearance_mm:
            raise ValueError("Cartridge outer depth is too small for the die pocket")
        if self.body_thickness_mm <= self.die_base_thickness_mm:
            raise ValueError("Cartridge body must be thicker than the die base")

    @property
    def die_pocket_diameter_mm(self) -> float:
        return self.die_diameter_mm + 2 * self.die_pocket_clearance_mm

    @property
    def receiver_width_mm(self) -> float:
        return self.outer_width_mm + 2 * self.receiver_slide_clearance_mm


@dataclass(frozen=True)
class PressSpec:
    """Prototype dimensions for the V0.2 lever press."""

    base_width_mm: float = 92.0
    base_depth_mm: float = 145.0
    base_thickness_mm: float = 12.0
    side_cheek_thickness_mm: float = 10.0
    side_cheek_height_mm: float = 105.0
    side_cheek_depth_mm: float = 28.0
    cheek_spacing_mm: float = 56.0
    pivot_diameter_mm: float = 6.4
    pivot_height_mm: float = 84.0
    throat_depth_mm: float = 62.0
    lever_width_mm: float = 28.0
    lever_thickness_mm: float = 12.0
    lever_length_mm: float = 245.0
    lever_pivot_to_ram_mm: float = 34.0
    ram_width_mm: float = 30.0
    ram_depth_mm: float = 30.0
    ram_height_mm: float = 62.0
    ram_slide_clearance_mm: float = 0.30
    guide_wall_mm: float = 7.0
    lower_receiver_height_mm: float = 8.0
    upper_receiver_height_mm: float = 8.0
    open_die_gap_mm: float = 18.0
    minimum_closed_gap_mm: float = 6.3
    hard_stop_adjustment_mm: float = 2.0
    mounting_hole_diameter_mm: float = 5.2
    mounting_hole_edge_offset_mm: float = 12.0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if name.endswith(("_mm",)) and value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.cheek_spacing_mm <= self.lever_width_mm:
            raise ValueError("Cheek spacing must exceed lever width")
        if self.lever_pivot_to_ram_mm >= self.lever_length_mm:
            raise ValueError("Ram contact must lie inside lever length")
        if self.minimum_closed_gap_mm >= self.open_die_gap_mm:
            raise ValueError("Closed gap must be smaller than open gap")

    @property
    def nominal_lever_ratio(self) -> float:
        return self.lever_length_mm / self.lever_pivot_to_ram_mm
