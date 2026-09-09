from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ArtworkMode(str, Enum):
    """Geometry interpretation used by the die generator."""

    BINARY = "binary"
    RELIEF = "relief"


class SourceInterpretation(str, Enum):
    """Meaning assigned to uploaded pixels/vectors before geometry generation."""

    FLAT_ARTWORK = "flat-artwork"
    HEIGHT_MAP = "height-map"
    SHADED_REFERENCE = "shaded-reference"


class ReliefStyle(str, Enum):
    STEPPED = "stepped"
    CONTINUOUS = "continuous"


class ReliefPolarity(str, Enum):
    DARK_HIGH = "dark-high"
    LIGHT_HIGH = "light-high"


class ValidationSeverity(str, Enum):
    INFO = "info"
    CAUTION = "caution"
    HIGH = "high"
    ERROR = "error"


_SEVERITY_ORDER = {
    ValidationSeverity.INFO: 0,
    ValidationSeverity.CAUTION: 1,
    ValidationSeverity.HIGH: 2,
    ValidationSeverity.ERROR: 3,
}


@dataclass(frozen=True)
class ReliefSpec:
    """Shared variable-depth relief settings used by CLI, GUI, and API callers.

    ``min_relief_mm`` is an optional printable floor for any non-zero relief. The
    library default stays at zero for backwards compatibility and exact authored
    height-map work. The CLI applies a stronger FDM-oriented floor unless the user
    explicitly overrides it.
    """

    max_relief_mm: float = 1.20
    min_relief_mm: float = 0.0
    style: ReliefStyle = ReliefStyle.STEPPED
    levels: int = 4
    gamma: float = 1.0
    polarity: ReliefPolarity = ReliefPolarity.DARK_HIGH
    zero_threshold: float = 0.02
    smoothing_mm: float = 0.0
    sampling_quality: str = "balanced"
    auto_filter_subresolution: bool = True

    def validate(self) -> None:
        if self.max_relief_mm <= 0:
            raise ValueError("max_relief_mm must be > 0")
        if self.min_relief_mm < 0:
            raise ValueError("min_relief_mm must be >= 0")
        if self.min_relief_mm >= self.max_relief_mm:
            raise ValueError("min_relief_mm must be smaller than max_relief_mm")
        if self.style == ReliefStyle.STEPPED and self.levels < 2:
            raise ValueError("stepped relief requires at least 2 levels")
        if self.levels > 256:
            raise ValueError("relief levels must be <= 256")
        if self.gamma <= 0:
            raise ValueError("relief gamma must be > 0")
        if not 0.0 <= self.zero_threshold <= 1.0:
            raise ValueError("relief zero_threshold must be between 0 and 1")
        if self.smoothing_mm < 0:
            raise ValueError("relief smoothing_mm must be >= 0")
        if self.sampling_quality not in {"draft", "balanced", "fine"}:
            raise ValueError("sampling_quality must be draft, balanced, or fine")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["style"] = self.style.value
        data["polarity"] = self.polarity.value
        return data


@dataclass(frozen=True)
class ValidationFinding:
    code: str
    severity: ValidationSeverity
    message: str
    recommendation: str | None = None
    overridable: bool = True
    metric: float | int | str | None = None
    threshold: float | int | str | None = None
    units: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass(frozen=True)
class ValidationReport:
    findings: tuple[ValidationFinding, ...] = ()
    heuristic_version: int = 1
    override_used: bool = False
    verification_level: str = "geometry"

    @property
    def highest_severity(self) -> ValidationSeverity:
        if not self.findings:
            return ValidationSeverity.INFO
        return max((finding.severity for finding in self.findings), key=_SEVERITY_ORDER.__getitem__)

    @property
    def has_errors(self) -> bool:
        return any(f.severity == ValidationSeverity.ERROR for f in self.findings)

    @property
    def has_high_risk(self) -> bool:
        return any(f.severity == ValidationSeverity.HIGH for f in self.findings)

    @property
    def blocking_findings(self) -> tuple[ValidationFinding, ...]:
        return tuple(f for f in self.findings if not f.overridable or f.severity == ValidationSeverity.ERROR)

    def to_dict(self) -> dict[str, Any]:
        return {
            "highest_severity": self.highest_severity.value,
            "override_used": self.override_used,
            "heuristic_version": self.heuristic_version,
            "verification_level": self.verification_level,
            "findings": [f.to_dict() for f in self.findings],
        }


def coerce_artwork_mode(value: ArtworkMode | str) -> ArtworkMode:
    return value if isinstance(value, ArtworkMode) else ArtworkMode(value)


def coerce_source_interpretation(value: SourceInterpretation | str) -> SourceInterpretation:
    return value if isinstance(value, SourceInterpretation) else SourceInterpretation(value)


def default_source_interpretation(mode: ArtworkMode) -> SourceInterpretation:
    # Literal height semantics should always require an explicit choice.
    return SourceInterpretation.FLAT_ARTWORK if mode == ArtworkMode.BINARY else SourceInterpretation.HEIGHT_MAP
