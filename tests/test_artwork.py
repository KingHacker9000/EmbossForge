from pathlib import Path
import xml.etree.ElementTree as ET

from embossforge.artwork import normalize_artwork


def test_negative_svg_viewbox_is_translated_to_zero_origin(tmp_path: Path):
    src = tmp_path / "negative.svg"
    dst = tmp_path / "normalized.svg"
    src.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -8 16 16">'
        '<circle cx="0" cy="0" r="4" fill="black"/>'
        '</svg>',
        encoding="utf-8",
    )

    normalize_artwork(src, dst)
    root = ET.parse(dst).getroot()
    assert root.attrib["viewBox"] == "0 0 16 16"

    groups = [child for child in list(root) if child.tag.endswith("}g") or child.tag == "g"]
    assert len(groups) == 1
    assert groups[0].attrib["transform"] == "translate(8 8)"


def test_zero_origin_svg_is_left_equivalent(tmp_path: Path):
    src = tmp_path / "zero.svg"
    dst = tmp_path / "normalized.svg"
    original = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'
    src.write_text(original, encoding="utf-8")
    normalize_artwork(src, dst)
    assert dst.read_text(encoding="utf-8") == original
