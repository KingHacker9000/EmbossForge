from __future__ import annotations

import numpy as np
import cv2

from .config import DieSpec, PrinterProfile
from .heightmap import HeightMapResult
from .relief import ReliefSpec, ValidationFinding, ValidationReport, ValidationSeverity


def validate_relief_field(
    result: HeightMapResult,
    spec: DieSpec,
    relief_spec: ReliefSpec,
    profile: PrinterProfile | None,
    *,
    override_used: bool = False,
) -> ValidationReport:
    findings: list[ValidationFinding] = []
    relief_mm = result.relief * relief_spec.max_relief_mm

    if result.filtered_pixels:
        area_mm2 = result.filtered_pixels * (result.mm_per_sample**2)
        findings.append(
            ValidationFinding(
                code="printability.subresolution_filtered",
                severity=ValidationSeverity.CAUTION,
                metric=round(area_mm2, 4),
                units="mm^2",
                message="Some sub-resolution positive relief was removed before both dies were derived.",
                recommendation="Use a finer nozzle/profile if those details are important.",
                details={"filtered_pixels": result.filtered_pixels},
            )
        )

    if profile is not None:
        _append_isolated_peak_findings(findings, result, relief_spec, profile)

    # Height change per horizontal millimetre. A normal emboss can contain sharp
    # walls, so slope alone is advisory. High severity is reserved for narrow
    # isolated peaks/ridges where steepness combines with small physical width.
    gy, gx = np.gradient(relief_mm, result.mm_per_sample, result.mm_per_sample)
    slope = np.sqrt(gx * gx + gy * gy)
    p99_slope = float(np.percentile(slope, 99.0)) if slope.size else 0.0
    caution_slope = 3.0
    if p99_slope >= caution_slope:
        findings.append(
            ValidationFinding(
                code="paper.steep_local_relief",
                severity=ValidationSeverity.CAUTION,
                metric=round(p99_slope, 3),
                threshold=caution_slope,
                units="mm/mm",
                message="Some relief transitions are steep. This is common in embossing but can be harsher on delicate paper.",
                recommendation="Test on scrap paper first, or smooth/reduce relief if the paper is fragile.",
            )
        )

    active_fraction = float(np.mean(result.relief > 0))
    if active_fraction > 0.70 and relief_spec.max_relief_mm >= 0.8:
        findings.append(
            ValidationFinding(
                code="paper.dense_deep_relief",
                severity=ValidationSeverity.CAUTION,
                metric=round(active_fraction, 3),
                threshold=0.70,
                units="fraction",
                message="A large portion of the die uses relief and the maximum depth is relatively high.",
                recommendation="Test on scrap paper first or reduce relief/texture density.",
            )
        )

    max_cavity = relief_spec.max_relief_mm + spec.paper_thickness_mm + spec.female_extra_depth_mm
    if max_cavity >= spec.base_thickness_mm:
        findings.append(
            ValidationFinding(
                code="geometry.female_base_breakthrough",
                severity=ValidationSeverity.ERROR,
                overridable=False,
                metric=round(max_cavity, 4),
                threshold=spec.base_thickness_mm,
                units="mm",
                message="The deepest female cavity would break through the die base.",
                recommendation="Increase base thickness or reduce relief/paper/extra depth.",
            )
        )

    return ValidationReport(
        findings=tuple(findings),
        override_used=override_used,
        verification_level="profile-heightfield" if profile is not None else "heightfield",
    )


def validate_heightfield_mating(
    male: HeightMapResult,
    female_surface_normalized: np.ndarray,
    max_cavity_mm: float,
    spec: DieSpec,
    relief_spec: ReliefSpec,
) -> ValidationReport:
    findings: list[ValidationFinding] = []
    female_unmirrored = np.fliplr(female_surface_normalized)
    female_cavity_mm = female_unmirrored * max_cavity_mm
    male_mm = male.relief * relief_spec.max_relief_mm
    active = male.relief > 0
    required = male_mm.copy()
    required[active] += spec.paper_thickness_mm + spec.female_extra_depth_mm

    shortfall = required - female_cavity_mm
    max_shortfall = float(np.max(shortfall[active])) if np.any(active) else 0.0
    tolerance = max(0.01, male.mm_per_sample * 0.05)
    if max_shortfall > tolerance:
        findings.append(
            ValidationFinding(
                code="mating.heightfield_interference",
                severity=ValidationSeverity.ERROR,
                overridable=False,
                metric=round(max_shortfall, 4),
                threshold=round(tolerance, 4),
                units="mm",
                message="The generated female depth field does not fully accommodate the canonical male relief.",
                recommendation="Do not print this pair; regenerate after fixing the matched-pair backend or settings.",
            )
        )

    return ValidationReport(findings=tuple(findings), verification_level="heightfield-closure")


def merge_validation_reports(*reports: ValidationReport, override_used: bool = False) -> ValidationReport:
    findings = tuple(f for report in reports for f in report.findings)
    levels = "+".join(report.verification_level for report in reports if report.verification_level)
    return ValidationReport(
        findings=findings,
        heuristic_version=max((r.heuristic_version for r in reports), default=1),
        override_used=override_used,
        verification_level=levels or "geometry",
    )


def _append_isolated_peak_findings(
    findings: list[ValidationFinding],
    result: HeightMapResult,
    relief_spec: ReliefSpec,
    profile: PrinterProfile,
) -> None:
    high = (result.relief >= 0.85).astype(np.uint8)
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(high, connectivity=8)
    min_area_mm2 = profile.min_feature_mm**2
    tiny = 0
    for idx in range(1, count):
        area_px = int(stats[idx, cv2.CC_STAT_AREA])
        area_mm2 = area_px * (result.mm_per_sample**2)
        if area_mm2 < min_area_mm2:
            tiny += 1
    if tiny:
        findings.append(
            ValidationFinding(
                code="paper.isolated_high_peaks",
                severity=ValidationSeverity.HIGH,
                metric=tiny,
                units="count",
                message=f"{tiny} tiny near-maximum relief island(s) may behave like puncture points.",
                recommendation="Widen/lower those peaks or let printer-aware filtering remove them.",
            )
        )
