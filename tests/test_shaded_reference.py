import json
from pathlib import Path

import cv2
import numpy as np

from embossforge.config import DieSpec, adventurer_5m_profile
from embossforge.generator import DieGenerationRequest, generate_die
from embossforge.relief import ArtworkMode, ReliefSpec, ReliefStyle, SourceInterpretation
from embossforge.shaded_reference import convert_shaded_reference, looks_continuously_shaded


def _shaded_medallion(path: Path) -> Path:
    image = np.full((180, 180, 3), 248, dtype=np.uint8)
    yy, xx = np.ogrid[:180, :180]
    circle = (xx - 90) ** 2 + (yy - 90) ** 2 <= 62**2
    gradient = np.clip(95 + (xx.astype(np.float32) / 179.0) * 95, 0, 255).astype(np.uint8)
    for channel in range(3):
        plane = image[:, :, channel]
        plane[circle] = gradient.repeat(180, axis=0)[circle]
    cv2.circle(image, (90, 90), 62, (70, 70, 70), 3)
    cv2.line(image, (55, 90), (125, 90), (85, 85, 85), 4)
    cv2.line(image, (90, 55), (90, 125), (200, 200, 200), 4)
    assert cv2.imwrite(str(path), image)
    return path


def test_shaded_reference_converter_is_deterministic_and_background_safe(tmp_path: Path):
    source = _shaded_medallion(tmp_path / "render.png")
    spec = DieSpec(relief_height_mm=0.35)
    relief = ReliefSpec(max_relief_mm=0.35, style=ReliefStyle.STEPPED, levels=6)
    profile = adventurer_5m_profile()

    first = convert_shaded_reference(source, tmp_path, "first", spec, relief, profile)
    second = convert_shaded_reference(source, tmp_path, "second", spec, relief, profile)

    a = cv2.imread(str(first.height_map), cv2.IMREAD_GRAYSCALE)
    b = cv2.imread(str(second.height_map), cv2.IMREAD_GRAYSCALE)
    assert a is not None and b is not None
    assert np.array_equal(a, b)
    assert int(a[0, 0]) >= 250
    assert int(a[a.shape[0] // 2, a.shape[1] // 2]) < 250
    assert 0.05 < first.foreground_fraction < 0.80
    assert first.background_method in {"alpha", "border-color-distance", "border-luminance-otsu"}
    assert first.relief_preview.exists()
    assert first.foreground_mask.exists()


def test_shaded_reference_generation_preserves_derivation_provenance(tmp_path: Path):
    source = _shaded_medallion(tmp_path / "render.png")
    result = generate_die(
        DieGenerationRequest(
            artwork=source,
            output_root=tmp_path / "out",
            paper_preset="copy",
            printer_profile=adventurer_5m_profile(),
            artwork_mode=ArtworkMode.RELIEF,
            source_interpretation=SourceInterpretation.SHADED_REFERENCE,
            relief=ReliefSpec(max_relief_mm=0.30, style=ReliefStyle.STEPPED, levels=5),
            render_stl=False,
            allow_risky=True,
        )
    )

    assert result.artwork_mode == ArtworkMode.RELIEF
    assert result.source_interpretation == SourceInterpretation.SHADED_REFERENCE
    assert result.outputs["derived_heightmap"].exists()
    assert result.outputs["derived_relief_preview"].exists()
    assert result.outputs["derived_foreground_mask"].exists()
    assert result.outputs["male_scad"].exists()
    assert result.outputs["female_scad"].exists()

    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
    processing = manifest["artwork_processing"]
    assert processing["source_interpretation"] == "shaded-reference"
    assert processing["source_derivation"]["method"] == "deterministic-shaded-reference-v1"
    assert "not reconstructed true 3D depth" in processing["source_derivation"]["claim"]


def test_continuous_shading_hint_is_advisory(tmp_path: Path):
    source = _shaded_medallion(tmp_path / "render.png")
    assert looks_continuously_shaded(source)
