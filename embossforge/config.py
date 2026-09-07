from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class DieSpec:
    diameter_mm: float = 42.0
    base_thickness_mm: float = 3.0
    relief_height_mm: float = 0.65
    female_xy_clearance_mm: float = 0.20
    female_extra_depth_mm: float = 0.20
    paper_thickness_mm: float = 0.10
    margin_mm: float = 3.0
    facets: int = 160

    @property
    def artwork_box_mm(self) -> float:
        return self.diameter_mm - 2 * self.margin_mm

    @property
    def female_cavity_depth_mm(self) -> float:
        return self.relief_height_mm + self.paper_thickness_mm + self.female_extra_depth_mm

    def validate(self) -> None:
        positive = {
            "diameter_mm": self.diameter_mm,
            "base_thickness_mm": self.base_thickness_mm,
            "relief_height_mm": self.relief_height_mm,
            "paper_thickness_mm": self.paper_thickness_mm,
            "facets": float(self.facets),
        }
        for name, value in positive.items():
            if value <= 0:
                raise ValueError(f"{name} must be > 0 (got {value})")
        if self.female_xy_clearance_mm < 0:
            raise ValueError("female_xy_clearance_mm must be >= 0")
        if self.female_extra_depth_mm < 0:
            raise ValueError("female_extra_depth_mm must be >= 0")
        if self.margin_mm < 0:
            raise ValueError("margin_mm must be >= 0")
        if self.artwork_box_mm <= 0:
            raise ValueError("margin leaves no printable artwork area")
        if self.female_cavity_depth_mm >= self.base_thickness_mm:
            raise ValueError(
                "female cavity is deeper than the female die base; increase base thickness "
                "or reduce relief/paper/extra depth"
            )

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class PrinterProfile:
    name: str
    build_x_mm: float
    build_y_mm: float
    build_z_mm: float
    nozzle_mm: float
    layer_height_mm: float
    min_feature_mm: float
    min_gap_mm: float
    recommended_die_clearance_mm: float

    @classmethod
    def from_toml(cls, path: str | Path) -> "PrinterProfile":
        with Path(path).open("rb") as fh:
            data = tomllib.load(fh)
        return cls(**data["printer"])
