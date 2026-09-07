import json
from pathlib import Path

import cv2
import numpy as np

from embossforge.config import adventurer_5m_profile
from embossforge.generator import DieGenerationRequest, generate_die
from embossforge.relief import ArtworkMode, ReliefSpec, ReliefStyle, SourceInterpretation


def test_generate_true_heightmap_scad_only(tmp_path: Path):
    image = np.full((96, 96), 255, dtype=np.uint8)
    cv2.circle(image, (48, 48), 24, 64, -1)
    source = tmp_path / "height.png"
    assert cv2.imwrite(str(source), image)

    result = generate_die(
        DieGenerationRequest(
            artwork=source,
            output_root=tmp_path / "out",
            printer_profile=adventurer_5m_profile(),
            artwork_mode=ArtworkMode.RELIEF,
            source_interpretation=SourceInterpretation.HEIGHT_MAP,
            relief=ReliefSpec(max_relief_mm=0.25, style=ReliefStyle.STEPPED, levels=4),
            allow_risky=True,
            render_stl=False,
        )
    )

    assert result.artwork_mode == ArtworkMode.RELIEF
    assert result.outputs["male_scad"].exists()
    assert result.outputs["female_scad"].exists()
    assert result.outputs["heightmap"].exists()
    assert result.male_stl is None

    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 2
    assert manifest["artwork_processing"]["geometry_mode"] == "relief"
    assert manifest["artwork_processing"]["source_interpretation"] == "height-map"
    assert manifest["relief"]["mode"] == "relief"
    assert "validation" in manifest


def test_binary_generation_stays_default(tmp_path: Path):
    svg = tmp_path / "mark.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><circle cx="10" cy="10" r="5" fill="black"/></svg>',
        encoding="utf-8",
    )
    result = generate_die(
        DieGenerationRequest(
            artwork=svg,
            output_root=tmp_path / "out",
            render_stl=False,
        )
    )
    assert result.artwork_mode == ArtworkMode.BINARY
    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 2
    assert manifest["relief"]["mode"] == "binary"
