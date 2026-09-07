# Agent / automation interface

EmbossForge is structured so agents and automation operate on parametric requests rather than editing meshes directly. Read [`AGENTS.md`](../AGENTS.md) first.

## Python API

Use `embossforge.generator.generate_die()`.

### Binary / flat artwork

```python
from pathlib import Path
from embossforge.config import adventurer_5m_profile
from embossforge.generator import DieGenerationRequest, generate_die

result = generate_die(
    DieGenerationRequest(
        artwork=Path("input/logo.svg"),
        output_root=Path("build/agent"),
        name="library-seal",
        diameter_mm=42.0,
        paper_preset="copy",
        printer_profile=adventurer_5m_profile(),
    )
)
```

Binary behavior remains the backward-compatible default.

### True height-map relief

```python
from pathlib import Path
from embossforge.config import adventurer_5m_profile
from embossforge.generator import DieGenerationRequest, generate_die
from embossforge.relief import ArtworkMode, ReliefSpec, ReliefStyle, SourceInterpretation

result = generate_die(
    DieGenerationRequest(
        artwork=Path("input/grayscale-crest.png"),
        output_root=Path("build/agent"),
        name="grayscale-crest",
        paper_preset="copy",
        printer_profile=adventurer_5m_profile(),
        artwork_mode=ArtworkMode.RELIEF,
        source_interpretation=SourceInterpretation.HEIGHT_MAP,
        relief=ReliefSpec(
            max_relief_mm=0.35,
            style=ReliefStyle.STEPPED,
            levels=6,
            gamma=1.0,
        ),
        allow_risky=False,
    )
)
```

### Shaded/rendered reference

```python
result = generate_die(
    DieGenerationRequest(
        artwork=Path("input/rendered-medallion.png"),
        output_root=Path("build/agent"),
        paper_preset="copy",
        printer_profile=adventurer_5m_profile(),
        artwork_mode=ArtworkMode.RELIEF,
        source_interpretation=SourceInterpretation.SHADED_REFERENCE,
        relief=ReliefSpec(max_relief_mm=0.35),
    )
)
```

This invokes deterministic shaded-reference interpretation. It is not inverse rendering and does not claim to recover true 3D geometry. Agents should inspect `derived_relief_preview`, `derived_heightmap`, and the manifest's `source_derivation` before treating the result as approved artwork. Interactive desktop users receive an explicit preview/accept step; headless agents must implement their own review policy.

## Result object

`DieGenerationResult` exposes:

- `name`, `output_dir`, and `normalized_artwork`;
- resolved `spec` and `printer_profile`;
- `paper_source` and `clearance_source`;
- `artwork_mode` and `source_interpretation`;
- structured `validation`;
- `outputs` plus `male_stl`, `female_stl`, and `manifest` convenience properties.

Shaded-reference `outputs` additionally include the derived height map, relief preview, and foreground mask.

## Manifest provenance

Generated manifests use schema v2 for the shared generator path. They preserve the original artwork, resolved profile/settings, source semantics, relief parameters, sampling metadata, validation results, and whether a paper-risk override was used. Shaded-reference jobs also record the deterministic derivation method and the explicit statement that the result is interpreted emboss relief rather than reconstructed true depth.

Agents should inspect the manifest rather than reverse-engineering STL geometry.

## CLI

Binary:

```text
embossforge die logo.svg --out build/agent --paper copy --profile profiles/flashforge_adventurer_5m.toml
```

Height map:

```text
embossforge die relief.png --mode relief --source-interpretation height-map --relief-max 0.35 --paper copy --profile profiles/flashforge_adventurer_5m.toml
```

Shaded reference:

```text
embossforge die render.png --mode relief --source-interpretation shaded-reference --relief-max 0.35 --paper copy --profile profiles/flashforge_adventurer_5m.toml
```

Use Python when structured return values are important and CLI when shell orchestration is simpler.

## Validation contract

Agents must distinguish:

- **hard geometry/mating errors** — invalid dimensions, base breakthrough, build-volume errors, failed solids, or predicted die interference; these cannot be bypassed;
- **experimental paper-risk findings** — steep slopes, isolated peaks, dense/deep relief, and related heuristics; high findings may be intentionally accepted with `allow_risky=True` / `--allow-risky`.

`allow_risky` never bypasses die compatibility. An empty warning list is not proof that paper cannot tear.

When STLs are rendered, EmbossForge performs nominal exported-mesh closure collision validation in addition to source/height-field checks.

## Source semantics are explicit

Do not silently choose relief because an image contains grayscale. Use:

- `FLAT_ARTWORK` with `BINARY` for ordinary artwork;
- `HEIGHT_MAP` with `RELIEF` only when grayscale was authored as Z;
- `SHADED_REFERENCE` with `RELIEF` for rendered/photographic 3D-looking artwork.

Variable-depth SVG tone/gradient rendering is not a direct machine path; export a raster height map instead.

## What agents should not do

Do not edit generated STLs to change dimensions, derive the female independently, bypass paper/clearance rules, create GUI-only geometry formulas, hide validation findings, treat Blender as dimensional source of truth, claim press strength from collision-free CAD, or claim variable-depth physical quality from software validation alone.

Geometry changes belong in source modules followed by regeneration and tests. Press/cartridge changes belong in `embossforge/mechanics/`. Expensive graphical/3D agents are best reserved for visual QA after deterministic geometry exists.
