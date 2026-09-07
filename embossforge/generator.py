from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import re

from .artwork import normalize_artwork
from .config import (
    PAPER_PRESETS_MM,
    DieSpec,
    PrinterProfile,
    adventurer_5m_profile,
    paper_thickness_for_preset,
)
from .heightmap import build_female_surface_map, build_height_map
from .mating import PrintablePairEstimate, validate_exported_stl_closure, validate_printable_pair
from .relief import (
    ArtworkMode,
    ReliefSpec,
    SourceInterpretation,
    ValidationReport,
    coerce_artwork_mode,
    coerce_source_interpretation,
    default_source_interpretation,
)
from .relief_backend import generate_relief_die_pair
from .scad_backend import generate_die_pair
from .validation import merge_validation_reports, validate_heightfield_mating, validate_relief_field


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
    artwork_mode: ArtworkMode | str = ArtworkMode.BINARY
    source_interpretation: SourceInterpretation | str | None = None
    relief: ReliefSpec | None = None
    allow_risky: bool = False
    enforce_mating: bool = True


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
    artwork_mode: ArtworkMode = ArtworkMode.BINARY
    source_interpretation: SourceInterpretation = SourceInterpretation.FLAT_ARTWORK
    validation: ValidationReport = ValidationReport()
    mating_estimate: PrintablePairEstimate | None = None

    @property
    def male_stl(self) -> Path | None:
        return self.outputs.get("male_stl")

    @property
    def female_stl(self) -> Path | None:
        return self.outputs.get("female_stl")

    @property
    def manifest(self) -> Path:
        return self.outputs["manifest"]


def safe_design_name(value: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value.strip())
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name:
        return "design"
    return name[:80].rstrip(" .") or "design"


def generate_die(request: DieGenerationRequest) -> DieGenerationResult:
    """Generate one matched die pair from a UI/CLI-neutral request object."""
    artwork = Path(request.artwork)
    if not artwork.exists():
        raise FileNotFoundError(artwork)

    mode = coerce_artwork_mode(request.artwork_mode)
    interpretation = (
        coerce_source_interpretation(request.source_interpretation)
        if request.source_interpretation is not None
        else default_source_interpretation(mode)
    )
    _validate_mode_interpretation(mode, interpretation)

    name = safe_design_name(request.name or artwork.stem)
    out = Path(request.output_root) / name
    out.mkdir(parents=True, exist_ok=True)

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

    effective_relief = request.relief.max_relief_mm if (mode == ArtworkMode.RELIEF and request.relief) else request.relief_height_mm
    spec = replace(
        base_spec,
        diameter_mm=request.diameter_mm,
        base_thickness_mm=request.base_thickness_mm,
        relief_height_mm=effective_relief,
        female_xy_clearance_mm=clearance,
        paper_thickness_mm=paper_thickness,
        female_extra_depth_mm=request.female_extra_depth_mm,
        margin_mm=request.margin_mm,
    )
    spec.validate()
    if profile is not None:
        profile.validate_die(spec)

    if mode == ArtworkMode.BINARY:
        return _generate_binary(
            request,
            artwork,
            out,
            name,
            spec,
            profile,
            paper_source,
            clearance_source,
            interpretation,
        )
    return _generate_relief(
        request,
        artwork,
        out,
        name,
        spec,
        profile,
        paper_source,
        clearance_source,
        interpretation,
    )


def _generate_binary(
    request: DieGenerationRequest,
    artwork: Path,
    out: Path,
    name: str,
    spec: DieSpec,
    profile: PrinterProfile | None,
    paper_source: str,
    clearance_source: str,
    interpretation: SourceInterpretation,
) -> DieGenerationResult:
    normalized = out / f"{name}_normalized.svg"
    normalize_artwork(
        artwork,
        normalized,
        threshold=request.threshold,
        invert=request.invert,
        physical_artwork_box_mm=spec.artwork_box_mm if profile is not None else None,
        min_feature_mm=profile.min_feature_mm if profile is not None else None,
        min_gap_mm=profile.effective_min_negative_feature_mm if profile is not None else None,
    )

    preflight, estimate = validate_printable_pair(normalized, spec, profile)
    if request.enforce_mating and preflight.blocking_findings:
        first = preflight.blocking_findings[0]
        raise ValueError(f"Matched-die closure validation failed: {first.message} {first.recommendation or ''}".strip())

    outputs = generate_die_pair(normalized, out, name, spec, render_stl=request.render_stl)
    closure = validate_exported_stl_closure(outputs.get("male_stl"), outputs.get("female_stl"), spec)
    validation = merge_validation_reports(preflight, closure)
    if request.enforce_mating and validation.blocking_findings:
        first = validation.blocking_findings[0]
        raise ValueError(f"Matched-die closure validation failed: {first.message} {first.recommendation or ''}".strip())

    _write_generation_context(
        outputs["manifest"],
        original_artwork=artwork,
        profile=profile,
        paper_source=paper_source,
        clearance_source=clearance_source,
        threshold=request.threshold,
        invert=request.invert,
        mode=ArtworkMode.BINARY,
        interpretation=interpretation,
        validation=validation,
        mating_estimate=estimate,
        relief_spec=None,
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
        artwork_mode=ArtworkMode.BINARY,
        source_interpretation=interpretation,
        validation=validation,
        mating_estimate=estimate,
    )


def _generate_relief(
    request: DieGenerationRequest,
    artwork: Path,
    out: Path,
    name: str,
    spec: DieSpec,
    profile: PrinterProfile | None,
    paper_source: str,
    clearance_source: str,
    interpretation: SourceInterpretation,
) -> DieGenerationResult:
    if interpretation == SourceInterpretation.SHADED_REFERENCE:
        raise ValueError(
            "Automatic shaded-reference conversion is not enabled in the deterministic desktop backend yet. "
            "Convert the reference to an unlit EmbossForge height map first (see skills/embossforge-design/SKILL.md), "
            "then choose source interpretation 'height-map'."
        )
    if interpretation != SourceInterpretation.HEIGHT_MAP:
        raise ValueError("Variable-depth relief currently requires source interpretation 'height-map'.")

    relief_spec = request.relief or ReliefSpec(max_relief_mm=request.relief_height_mm)
    relief_spec.validate()
    spec = replace(spec, relief_height_mm=relief_spec.max_relief_mm)
    spec.validate()

    heightmap = build_height_map(artwork, out, name, spec, relief_spec, profile)
    female_surface, max_cavity, female_field = build_female_surface_map(heightmap, out, name, spec, relief_spec)

    risk_report = validate_relief_field(
        heightmap,
        spec,
        relief_spec,
        profile,
        override_used=request.allow_risky,
    )
    field_mating = validate_heightfield_mating(heightmap, female_field, max_cavity, spec, relief_spec)
    validation = merge_validation_reports(risk_report, field_mating, override_used=request.allow_risky)

    if validation.blocking_findings:
        first = validation.blocking_findings[0]
        raise ValueError(f"Relief geometry validation failed: {first.message} {first.recommendation or ''}".strip())
    if validation.has_high_risk and not request.allow_risky:
        first = next(f for f in validation.findings if f.severity.value == "high")
        raise ValueError(
            f"Relief generation paused for a high experimental paper-risk finding: {first.message} "
            "Review the design or generate again with allow_risky/--allow-risky if intentional."
        )

    outputs = generate_relief_die_pair(
        heightmap,
        female_surface,
        max_cavity,
        out,
        name,
        spec,
        relief_spec,
        render_stl=request.render_stl,
    )
    closure = validate_exported_stl_closure(outputs.get("male_stl"), outputs.get("female_stl"), spec)
    validation = merge_validation_reports(validation, closure, override_used=request.allow_risky)
    if request.enforce_mating and validation.blocking_findings:
        first = validation.blocking_findings[0]
        raise ValueError(f"Matched-die closure validation failed: {first.message} {first.recommendation or ''}".strip())

    _write_generation_context(
        outputs["manifest"],
        original_artwork=artwork,
        profile=profile,
        paper_source=paper_source,
        clearance_source=clearance_source,
        threshold=request.threshold,
        invert=request.invert,
        mode=ArtworkMode.RELIEF,
        interpretation=interpretation,
        validation=validation,
        mating_estimate=None,
        relief_spec=relief_spec,
    )

    return DieGenerationResult(
        name=name,
        output_dir=out,
        normalized_artwork=heightmap.machine_heightmap,
        spec=spec,
        printer_profile=profile,
        paper_source=paper_source,
        clearance_source=clearance_source,
        outputs=outputs,
        artwork_mode=ArtworkMode.RELIEF,
        source_interpretation=interpretation,
        validation=validation,
        mating_estimate=None,
    )


def _validate_mode_interpretation(mode: ArtworkMode, interpretation: SourceInterpretation) -> None:
    if mode == ArtworkMode.BINARY and interpretation == SourceInterpretation.HEIGHT_MAP:
        raise ValueError("A literal height map requires --mode relief; choose flat-artwork for binary embossing.")


def _write_generation_context(
    manifest_path: Path,
    *,
    original_artwork: Path,
    profile: PrinterProfile | None,
    paper_source: str,
    clearance_source: str,
    threshold: int,
    invert: bool,
    mode: ArtworkMode,
    interpretation: SourceInterpretation,
    validation: ValidationReport,
    mating_estimate: PrintablePairEstimate | None,
    relief_spec: ReliefSpec | None,
) -> None:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["schema_version"] = 2
    data["generation_context"] = {
        "original_artwork": str(original_artwork.resolve()),
        "printer_profile": profile.name if profile else None,
        "paper_source": paper_source,
        "clearance_source": clearance_source,
        "raster_threshold": threshold,
        "raster_invert": invert,
    }
    data["artwork_processing"] = {
        "geometry_mode": mode.value,
        "source_interpretation": interpretation.value,
    }
    if mode == ArtworkMode.BINARY:
        data["relief"] = {"mode": "binary"}
    elif relief_spec is not None:
        existing_sampling = data.get("relief", {}).get("sampling")
        data["relief"] = {"mode": "relief", **relief_spec.to_dict()}
        if existing_sampling is not None:
            data["relief"]["sampling"] = existing_sampling
    data["validation"] = validation.to_dict()
    if mating_estimate is not None:
        data["validation"]["mating_preflight"] = {
            "checked_features": mating_estimate.checked_features,
            "unmeasured_features": mating_estimate.unmeasured_features,
            "coverage": mating_estimate.coverage,
            "source_kind": mating_estimate.source_kind,
        }
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def default_gui_request(artwork: Path, output_root: Path) -> DieGenerationRequest:
    return DieGenerationRequest(
        artwork=artwork,
        output_root=output_root,
        paper_preset="copy",
        printer_profile=adventurer_5m_profile(),
    )


def available_paper_presets() -> tuple[str, ...]:
    return tuple(sorted(PAPER_PRESETS_MM))
