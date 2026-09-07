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

---

## Planned variable-depth relief API

Variable-depth grayscale relief is specified but not yet implemented. Agents must read [RELIEF_MODE_SPEC.md](RELIEF_MODE_SPEC.md) before implementing or consuming it.

The compatibility rule is strict: callers that use the current `DieGenerationRequest` without relief options must continue to get binary-mode behavior.

The planned additive API shape is conceptually:

```python
from pathlib import Path
from embossforge.generator import DieGenerationRequest, generate_die
from embossforge.relief import ReliefSpec

request = DieGenerationRequest(
    artwork=Path("input/grayscale-crest.png"),
    output_root=Path("build/agent"),
    name="grayscale-crest",
    diameter_mm=42.0,
    paper_preset="copy",
    printer_profile=profile,
    artwork_mode="relief",
    relief=ReliefSpec(
        max_relief_mm=0.80,
        style="stepped",
        levels=6,
        gamma=1.0,
        polarity="dark-high",
    ),
    allow_risky=False,
)

result = generate_die(request)
```

Exact class/field names may be refined during implementation, but the contract in `RELIEF_MODE_SPEC.md` takes precedence.

### Planned relief manifest behavior

- manifests gain `schema_version: 2`;
- manifests with no `schema_version` are interpreted as current v1;
- current top-level fields remain present;
- relief processing parameters and sampling metadata are recorded;
- validation findings are structured rather than only printed to stderr/UI;
- explicit risk override is recorded as provenance.

### Planned validation behavior for agents

Agents must distinguish:

- **hard geometry errors** — invalid model, cannot be bypassed;
- **printability/paper-risk findings** — heuristic advisories that may be overridden intentionally.

A future `allow_risky=True`/`--allow-risky` path may bypass only overrideable risk findings. It must never bypass base breakthrough, invalid dimensions, build-volume errors, NaN geometry, or failed solid generation.

An agent must not interpret an empty warning list as proof that a die cannot tear paper.

---

## What agents should not do

Do not:

- edit generated STL files to change dimensions
- guess the matching female geometry independently
- bypass paper/clearance settings
- implement GUI-only relief formulas that differ from CLI/API behavior
- silently enable grayscale relief because an image contains gray tones
- discard or hide relief-validation findings
- treat a Blender scene as the dimensional source of truth
- claim hardware strength from collision-free CAD
- claim paper safety or relief quality from software validation alone
- overwrite physical-validation records with inferred results

## Geometry changes

If an agent is asked to change die behavior, modify source modules and regenerate. If asked to change the press/cartridge mechanism, modify `embossforge/mechanics/` and preserve parametric source + validation.

For relief-mode work, preserve the parallel architecture: current binary processing stays stable while a deterministic height-map path is added behind the same generator service.

Expensive graphical/3D agents are most useful only after generated geometry exists and a visual inspection task remains.
