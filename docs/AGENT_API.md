# Agent / automation interface

EmbossForge is intentionally structured so coding agents and external automation do not need to manipulate CAD meshes directly.

Read the repository-level [`AGENTS.md`](../AGENTS.md) first. This document focuses on invoking the die generator as a tool.

## Preferred integration: Python API

Use `embossforge.generator.generate_die()`.

```python
from pathlib import Path
from embossforge.config import adventurer_5m_profile
from embossforge.generator import DieGenerationRequest, generate_die

request = DieGenerationRequest(
    artwork=Path("input/logo.svg"),
    output_root=Path("build/agent"),
    name="library-seal",
    diameter_mm=42.0,
    paper_preset="copy",
    printer_profile=adventurer_5m_profile(),
)

result = generate_die(request)

print(result.male_stl)
print(result.female_stl)
print(result.manifest)
```

`DieGenerationResult` exposes:

- `name`
- `output_dir`
- `normalized_artwork`
- resolved `spec`
- resolved `printer_profile`
- `paper_source`
- `clearance_source`
- `outputs`
- convenience properties `male_stl`, `female_stl`, and `manifest`

## Manifest as machine-readable provenance

Every normal generation writes `<name>_manifest.json`. The shared generator adds a `generation_context` block containing the original artwork path, resolved printer profile, where paper/clearance values came from, and raster preprocessing settings.

An agent should inspect the manifest instead of reverse-engineering settings from STL geometry.

## CLI integration

The same backend is available through:

```text
embossforge die logo.svg --out build/agent --paper copy --profile profiles/flashforge_adventurer_5m.toml
```

Use the Python API when you need structured return values. Use the CLI when shell-level orchestration is simpler.

## What agents should not do

Do not:

- edit generated STL files to change dimensions
- guess the matching female geometry independently
- bypass paper/clearance settings
- treat a Blender scene as the dimensional source of truth
- claim hardware strength from collision-free CAD
- overwrite physical-validation records with inferred results

## Geometry changes

If an agent is asked to change die behavior, modify source modules and regenerate. If asked to change the press/cartridge mechanism, modify `embossforge/mechanics/` and preserve parametric source + validation.

Expensive graphical/3D agents are most useful only after generated geometry exists and a visual inspection task remains.
