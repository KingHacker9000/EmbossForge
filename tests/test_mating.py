from pathlib import Path

from embossforge.config import DieSpec, adventurer_5m_profile
from embossforge.mating import validate_printable_pair


def _svg(stroke_width: float) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
<line x1="2" y1="10" x2="18" y2="10" stroke="black" stroke-width="{stroke_width}"/>
</svg>
'''


def test_thin_svg_stroke_blocks_predicted_mating(tmp_path: Path):
    artwork = tmp_path / "thin.svg"
    artwork.write_text(_svg(0.10), encoding="utf-8")

    report, estimate = validate_printable_pair(artwork, DieSpec(), adventurer_5m_profile())

    assert estimate.checked_features >= 1
    assert report.has_errors
    assert any(f.code == "mating.thin_positive_feature" for f in report.findings)
    assert any(f.code == "mating.female_accommodation_too_narrow" for f in report.findings)


def test_wide_svg_stroke_passes_supported_primitive_preflight(tmp_path: Path):
    artwork = tmp_path / "wide.svg"
    artwork.write_text(_svg(1.0), encoding="utf-8")

    report, estimate = validate_printable_pair(artwork, DieSpec(), adventurer_5m_profile())

    assert estimate.checked_features >= 1
    assert not report.has_errors
