from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from .config import DieSpec, PrinterProfile
from .relief import ValidationFinding, ValidationReport, ValidationSeverity


_LENGTH_RE = re.compile(r"^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([a-zA-Z%]*)\s*$")


@dataclass(frozen=True)
class PrintablePairEstimate:
    """Summary of how much of an artwork file could be inspected deterministically."""

    checked_features: int
    unmeasured_features: int
    source_kind: str

    @property
    def coverage(self) -> str:
        if self.checked_features and not self.unmeasured_features:
            return "complete-for-supported-primitives"
        if self.checked_features:
            return "partial"
        return "unknown"


def validate_printable_pair(
    artwork_svg: str | Path,
    spec: DieSpec,
    profile: PrinterProfile | None,
) -> tuple[ValidationReport, PrintablePairEstimate]:
    """Perform a fast nozzle/profile-aware matched-pair preflight.

    This is deliberately conservative. It catches explicit SVG strokes and simple
    primitives whose physical widths can be measured without a slicer. The female
    must accommodate the *effective printable male*, not merely the ideal source
    width. More complete slicer/toolpath validation can be layered on later.
    """
    if profile is None:
        estimate = PrintablePairEstimate(0, 0, "no-printer-profile")
        report = ValidationReport(
            findings=(
                ValidationFinding(
                    code="mating.profile_missing",
                    severity=ValidationSeverity.INFO,
                    overridable=True,
                    message="Matched-pair printability was not checked because no printer profile was selected.",
                    recommendation="Select a printer/nozzle profile for nozzle-aware closure validation.",
                ),
            ),
            verification_level="unverified",
        )
        return report, estimate

    path = Path(artwork_svg)
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except (OSError, ET.ParseError):
        estimate = PrintablePairEstimate(0, 0, "unparsed-svg")
        return (
            ValidationReport(
                findings=(
                    ValidationFinding(
                        code="mating.svg_unparsed",
                        severity=ValidationSeverity.CAUTION,
                        message="The normalized SVG could not be structurally inspected for tiny mating features.",
                        recommendation="Inspect the slicer preview or use a source format EmbossForge can fully analyze.",
                    ),
                ),
                verification_level="profile-preflight-partial",
            ),
            estimate,
        )

    viewbox = _viewbox(root)
    if viewbox is None:
        estimate = PrintablePairEstimate(0, 0, "svg-no-viewbox")
        return (
            ValidationReport(
                findings=(
                    ValidationFinding(
                        code="mating.viewbox_unknown",
                        severity=ValidationSeverity.CAUTION,
                        message="SVG physical feature scale could not be inferred for matched-pair preflight.",
                        recommendation="Use an SVG with a valid viewBox or inspect the slicer preview carefully.",
                    ),
                ),
                verification_level="profile-preflight-partial",
            ),
            estimate,
        )

    _, _, width, height = viewbox
    scale_mm_per_unit = spec.artwork_box_mm / max(width, height)
    findings: list[ValidationFinding] = []
    checked = 0
    unmeasured = 0

    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"svg", "g", "defs", "style", "metadata", "title", "desc", "clipPath", "mask"}:
            continue

        feature_widths = _measurable_feature_widths(element, tag, scale_mm_per_unit)
        if feature_widths:
            checked += len(feature_widths)
            for label, width_mm in feature_widths:
                findings.extend(_check_width(label, width_mm, spec, profile))
        elif tag in {"path", "polygon", "polyline", "text", "use"}:
            # These can contain narrow filled/counter geometry that cannot be
            # measured reliably without flattening/rasterizing the SVG.
            unmeasured += 1

    if unmeasured:
        findings.append(
            ValidationFinding(
                code="mating.partial_geometry_coverage",
                severity=ValidationSeverity.INFO,
                message=f"{unmeasured} complex SVG element(s) require later raster/slicer-level closure verification.",
                recommendation="EmbossForge will preserve this as partial verification in the manifest.",
                details={"unmeasured_elements": unmeasured},
            )
        )

    if checked == 0 and unmeasured == 0:
        findings.append(
            ValidationFinding(
                code="mating.no_measurable_features",
                severity=ValidationSeverity.INFO,
                message="No explicit thin SVG primitives required a width compatibility check.",
            )
        )

    estimate = PrintablePairEstimate(checked, unmeasured, "svg")
    level = "profile-preflight" if not unmeasured else "profile-preflight-partial"
    return ValidationReport(findings=tuple(findings), verification_level=level), estimate


def _check_width(
    label: str,
    source_width_mm: float,
    spec: DieSpec,
    profile: PrinterProfile,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    positive_min = profile.min_feature_mm
    negative_min = profile.min_gap_mm

    # A slicer may inflate a narrow positive to one line. The corresponding
    # female groove must accommodate that effective positive plus deliberate XY
    # clearance, not merely the ideal source line.
    predicted_male_width = max(source_width_mm, positive_min)
    nominal_female_width = source_width_mm + 2.0 * spec.female_xy_clearance_mm
    required_female_width = max(
        negative_min,
        predicted_male_width + 2.0 * spec.female_xy_clearance_mm,
    )

    if source_width_mm < positive_min:
        findings.append(
            ValidationFinding(
                code="mating.thin_positive_feature",
                severity=ValidationSeverity.ERROR,
                overridable=False,
                metric=round(source_width_mm, 4),
                threshold=positive_min,
                units="mm",
                message=(
                    f"{label} is about {source_width_mm:.3f} mm wide, below the selected printer's "
                    f"{positive_min:.3f} mm positive-feature limit. It may survive on the male as a single "
                    "extrusion while its ideal female groove remains too narrow."
                ),
                recommendation="Thicken/remove the feature on the shared master artwork or choose a finer nozzle/profile.",
            )
        )

    if nominal_female_width + 1e-9 < required_female_width:
        findings.append(
            ValidationFinding(
                code="mating.female_accommodation_too_narrow",
                severity=ValidationSeverity.ERROR,
                overridable=False,
                metric=round(nominal_female_width, 4),
                threshold=round(required_female_width, 4),
                units="mm",
                message=(
                    f"The matching female accommodation for {label} is predicted at {nominal_female_width:.3f} mm, "
                    f"but at least {required_female_width:.3f} mm is needed for the effective printed male and clearance."
                ),
                recommendation="Canonicalize the feature to printer resolution before deriving both dies.",
            )
        )

    return findings


def _viewbox(root: ET.Element) -> tuple[float, float, float, float] | None:
    value = root.attrib.get("viewBox")
    if not value:
        return None
    parts = [p for p in re.split(r"[\s,]+", value.strip()) if p]
    if len(parts) != 4:
        return None
    try:
        x, y, width, height = (float(p) for p in parts)
    except ValueError:
        return None
    if width <= 0 or height <= 0:
        return None
    return x, y, width, height


def _style_value(element: ET.Element, name: str) -> str | None:
    if name in element.attrib:
        return element.attrib[name]
    style = element.attrib.get("style", "")
    for item in style.split(";"):
        key, sep, value = item.partition(":")
        if sep and key.strip() == name:
            return value.strip()
    return None


def _length_to_units(value: str | None) -> float | None:
    if not value:
        return None
    match = _LENGTH_RE.match(value)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2).lower()
    if unit in {"", "px"}:
        return number
    if unit == "mm":
        return number * 96.0 / 25.4
    if unit == "cm":
        return number * 96.0 / 2.54
    if unit == "in":
        return number * 96.0
    if unit == "pt":
        return number * 96.0 / 72.0
    if unit == "pc":
        return number * 16.0
    return None


def _measurable_feature_widths(
    element: ET.Element,
    tag: str,
    scale_mm_per_unit: float,
) -> list[tuple[str, float]]:
    results: list[tuple[str, float]] = []

    stroke = _style_value(element, "stroke")
    stroke_width = _length_to_units(_style_value(element, "stroke-width"))
    if stroke and stroke.lower() != "none" and stroke_width and stroke_width > 0:
        results.append((f"{tag} stroke", stroke_width * scale_mm_per_unit))

    if tag == "rect":
        width = _length_to_units(element.attrib.get("width"))
        height = _length_to_units(element.attrib.get("height"))
        if width and height and width > 0 and height > 0:
            results.append(("rectangle narrow dimension", min(width, height) * scale_mm_per_unit))
    elif tag == "circle":
        radius = _length_to_units(element.attrib.get("r"))
        if radius and radius > 0:
            results.append(("circle diameter", 2.0 * radius * scale_mm_per_unit))
    elif tag == "ellipse":
        rx = _length_to_units(element.attrib.get("rx"))
        ry = _length_to_units(element.attrib.get("ry"))
        if rx and ry and rx > 0 and ry > 0:
            results.append(("ellipse narrow diameter", 2.0 * min(rx, ry) * scale_mm_per_unit))

    return results
