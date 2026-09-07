import json
from pathlib import Path

from embossforge.config import adventurer_5m_profile
from embossforge.generator import DieGenerationRequest, generate_die, safe_design_name


SIMPLE_SVG = """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 20 20\">
<circle cx=\"10\" cy=\"10\" r=\"6\" fill=\"black\"/>
</svg>
"""


def test_generate_die_service_can_run_scad_only(tmp_path: Path):
    artwork = tmp_path / "mark.svg"
    artwork.write_text(SIMPLE_SVG, encoding="utf-8")

    result = generate_die(
        DieGenerationRequest(
            artwork=artwork,
            output_root=tmp_path / "out",
            paper_preset="premium",
            printer_profile=adventurer_5m_profile(),
            render_stl=False,
        )
    )

    assert result.name == "mark"
    assert result.spec.paper_thickness_mm == 0.13
    assert result.spec.female_xy_clearance_mm == 0.20
    assert result.outputs["male_scad"].exists()
    assert result.outputs["female_scad"].exists()
    assert result.outputs["manifest"].exists()
    assert result.male_stl is None
    assert result.female_stl is None

    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
    assert manifest["generation_context"]["paper_source"] == "preset:premium"
    assert manifest["generation_context"]["printer_profile"].startswith("FlashForge Adventurer 5M")


def test_explicit_gui_values_override_presets(tmp_path: Path):
    artwork = tmp_path / "mark.svg"
    artwork.write_text(SIMPLE_SVG, encoding="utf-8")

    result = generate_die(
        DieGenerationRequest(
            artwork=artwork,
            output_root=tmp_path / "out",
            paper_preset="copy",
            paper_thickness_mm=0.18,
            clearance_mm=0.27,
            render_stl=False,
        )
    )

    assert result.spec.paper_thickness_mm == 0.18
    assert result.paper_source == "explicit"
    assert result.spec.female_xy_clearance_mm == 0.27
    assert result.clearance_source == "explicit"


def test_safe_design_name_removes_path_unsafe_characters():
    assert safe_design_name('  Wedding: "A/B"?  ') == "Wedding_ _A_B_"
    assert safe_design_name("   ") == "design"
