from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import tomllib


PAPER_PRESETS_MM: dict[str, float] = {
    "copy": 0.10,
    "premium": 0.13,
    "cardstock": 0.25,
}


def paper_thickness_for_preset(name: str) -> float:
    try:
        return PAPER_PRESETS_MM[name]
    except KeyError as exc:
        choices = ", ".join(sorted(PAPER_PRESETS_MM))
        raise ValueError(f"Unknown paper preset {name!r}; choose one of: {choices}") from exc


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
    key_width_mm: float = 6.0
    key_depth_mm: float = 2.5

    @property
    def artwork_box_mm(self) -> float:
        return self.diameter_mm - 2 * self.margin_mm

    @property
    def artwork_radius_mm(self) -> float:
        return self.diameter_mm / 2 - self.margin_mm

    @property
    def female_cavity_depth_mm(self) -> float:
        return self.relief_height_mm + self.paper_thickness_mm + self.female_extra_depth_mm

    @property
    def carrier_depth_mm(self) -> float:
        return self.diameter_mm + self.key_depth_mm

    def validate(self) -> None:
        positive = {
            "diameter_mm": self.diameter_mm,
            "base_thickness_mm": self.base_thickness_mm,
            "relief_height_mm": self.relief_height_mm,
            "paper_thickness_mm": self.paper_thickness_mm,
            "facets": float(self.facets),
            "key_width_mm": self.key_width_mm,
            "key_depth_mm": self.key_depth_mm,
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
        if self.key_width_mm >= self.diameter_mm:
            raise ValueError("key_width_mm must be smaller than die diameter")
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
    line_width_mm: float | None = None
    min_negative_feature_mm: float | None = None
    xy_compensation_mm: float = 0.0

    @property
    def effective_line_width_mm(self) -> float:
        return self.line_width_mm if self.line_width_mm is not None else self.nozzle_mm

    @property
    def effective_min_negative_feature_mm(self) -> float:
        return self.min_negative_feature_mm if self.min_negative_feature_mm is not None else self.min_gap_mm

    @classmethod
    def from_toml(cls, path: str | Path) -> "PrinterProfile":
        with Path(path).open("rb") as fh:
            data = tomllib.load(fh)
        profile = cls(**data["printer"])
        profile.validate()
        return profile

    def validate(self) -> None:
        required_positive = {
            "build_x_mm": self.build_x_mm,
            "build_y_mm": self.build_y_mm,
            "build_z_mm": self.build_z_mm,
            "nozzle_mm": self.nozzle_mm,
            "layer_height_mm": self.layer_height_mm,
            "min_feature_mm": self.min_feature_mm,
            "min_gap_mm": self.min_gap_mm,
            "recommended_die_clearance_mm": self.recommended_die_clearance_mm,
        }
        for name, value in required_positive.items():
            if float(value) <= 0:
                raise ValueError(f"Printer profile {name} must be > 0")
        for name, value in {
            "line_width_mm": self.line_width_mm,
            "min_negative_feature_mm": self.min_negative_feature_mm,
        }.items():
            if value is not None and float(value) <= 0:
                raise ValueError(f"Printer profile {name} must be > 0 when provided")
        if self.xy_compensation_mm < 0:
            raise ValueError("Printer profile xy_compensation_mm must be >= 0")

    def validate_die(self, spec: DieSpec) -> None:
        spec.validate()
        if spec.carrier_depth_mm > self.build_y_mm:
            raise ValueError(
                f"Die carrier depth {spec.carrier_depth_mm:.2f} mm exceeds printer Y build size {self.build_y_mm:.2f} mm"
            )
        if spec.diameter_mm > self.build_x_mm:
            raise ValueError(
                f"Die diameter {spec.diameter_mm:.2f} mm exceeds printer X build size {self.build_x_mm:.2f} mm"
            )


def adventurer_5m_profile() -> PrinterProfile:
    """Return the built-in profile used by the desktop app and quick-start CLI paths."""
    profile = PrinterProfile(
        name="FlashForge Adventurer 5M / 0.4 mm prototype",
        build_x_mm=220.0,
        build_y_mm=220.0,
        build_z_mm=220.0,
        nozzle_mm=0.4,
        layer_height_mm=0.12,
        min_feature_mm=0.50,
        min_gap_mm=0.45,
        recommended_die_clearance_mm=0.20,
        line_width_mm=0.45,
        min_negative_feature_mm=0.45,
        xy_compensation_mm=0.0,
    )
    profile.validate()
    return profile
