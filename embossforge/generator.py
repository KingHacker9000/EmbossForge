from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .artwork import normalize_artwork
from .config import (
    PAPER_PRESETS_MM,
    DieSpec,
    PrinterProfile,
    adventurer_5m_profile,
    paper_thickness_for_preset,
)
from .scad_backend import generate_die_pair


@dataclass(frozen=True)
class DieGenerationRequest:
    artwork: Path
    output_root: Path
    name: str | None = None
    diameter_mm: float = 42.0
    base_thickness_mm: float = 3.0
    relief_height_mm: float = 0.65
    clearance_mm: float | None = None
    paper_preset: str | None = "copy"
    paper_thickness_mm: float | None = None
    female_extra_depth_mm: float = 0.20
    margin_mm: float = 3.0
    threshold: int = 160
    invert: bool = False
    render_stl: bool = True
    printer_profile: PrinterProfile | None = None


@dataclass(frozen=True)
class DieGenerationResult:
    name: str
    output_dir: Path
    normalized_artwork: Path
    spec: DieSpec
    printer_profile: PrinterProfile | None
    paper_source: str
    clearance_source: str
    outputs: dict[str, Path]

    @property
    def male_stl(self) -> Path | None:
        return self.outputs.get("male_stl")

    @property
    def female_stl(self) -> Path | None:
        return self.outputs.get("female_stl")

    @property
    def manifest(self) -> Path:
        return self.outputs["manifest"]


def generate_die(request: DieGenerationRequest) -> DieGenerationResult:
    """Generate one matched die pair from a UI/CLI-neutral request object."""
    artwork = Path(request.artwork)
    if not artwork.exists():
        raise FileNotFoundError(artwork)

    name = request.name or artwork.stem
    if not name.strip():
        raise ValueError("Design name cannot be empty")

    out = Path(request.output_root) / name
    normalized = out / f"{name}_normalized.svg"
    normalize_artwork(
        artwork,
        normalized,
        threshold=request.threshold,
        invert=request.invert,
    )

    base_spec = DieSpec()
    profile = request.printer_profile

    if request.paper_thickness_mm is not None:
        paper_thickness = request.paper_thickness_mm
        paper_source = "explicit"
    elif request.paper_preset:
        paper_thickness = paper_thickness_for_preset(request.paper_preset)
        paper_source = f"preset:{request.paper_preset}"
    else:
        paper_thickness = base_spec.paper_thickness_mm
        paper_source = "default"

    if request.clearance_mm is not None:
        clearance = request.clearance_mm
        clearance_source = "explicit"
    elif profile is not None:
        clearance = profile.recommended_die_clearance_mm
        clearance_source = f"profile:{profile.name}"
    else:
        clearance = base_spec.female_xy_clearance_mm
        clearance_source = "default"

    spec = replace(
        base_spec,
        diameter_mm=request.diameter_mm,
        base_thickness_mm=request.base_thickness_mm,
        relief_height_mm=request.relief_height_mm,
        female_xy_clearance_mm=clearance,
        paper_thickness_mm=paper_thickness,
        female_extra_depth_mm=request.female_extra_depth_mm,
        margin_mm=request.margin_mm,
    )
    spec.validate()
    if profile is not None:
        profile.validate_die(spec)

    outputs = generate_die_pair(
        normalized,
        out,
        name,
        spec,
        render_stl=request.render_stl,
    )
    return DieGenerationResult(
        name=name,
        output_dir=out,
        normalized_artwork=normalized,
        spec=spec,
        printer_profile=profile,
        paper_source=paper_source,
        clearance_source=clearance_source,
        outputs=outputs,
    )


def default_gui_request(artwork: Path, output_root: Path) -> DieGenerationRequest:
    """Create the friendly desktop defaults used for the target printer."""
    return DieGenerationRequest(
        artwork=artwork,
        output_root=output_root,
        paper_preset="copy",
        printer_profile=adventurer_5m_profile(),
    )


def available_paper_presets() -> tuple[str, ...]:
    return tuple(sorted(PAPER_PRESETS_MM))
