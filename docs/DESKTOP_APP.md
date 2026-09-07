# EmbossForge desktop app

The desktop app is the primary path for turning artwork into printable matched embossing dies.

## Windows builds

Tagged releases are designed to provide:

- `EmbossForge-Setup-Windows-x64.exe` — normal installer;
- `EmbossForge-Windows-x64-portable.zip` — unzip and run `EmbossForge.exe`.

The Windows bundle includes OpenSCAD, so release users do not need Python, CadQuery, or a separate OpenSCAD install. The release workflow is `.github/workflows/release-windows.yml`.

## Desktop workflow

1. Launch EmbossForge and choose/drop artwork.
2. Choose **Simple emboss** or **Variable depth**. Simple emboss remains the default.
3. For Variable depth choose:
   - **True height map**, when grayscale was authored as geometry; or
   - **3D-looking / shaded reference**, when the image includes rendered lighting.
4. Choose die diameter, paper, and printer profile.
5. Adjust relief controls only when needed.
6. Generate and review the pair-fit/validation result.
7. Open the output folder and import the male/female STLs into the slicer.

## Variable-depth controls

Primary controls are intentionally small:

- maximum relief;
- stepped or continuous depth style;
- number of levels for stepped relief;
- tone direction / polarity.

Advanced controls include gamma, zero/dead-zone, smoothing, quality/sampling, printer-aware sub-resolution filtering, paper-risk override, base thickness, margin, and clearance.

## True height maps

True height maps go directly into the shared relief backend. By default, white means zero relief and black means maximum relief. Both dies are derived from one canonical sampled height field.

The desktop shows validation near the Generate action. Hard mating/geometry errors block generation. High experimental paper-risk findings can be intentionally accepted, but the UI never describes an unwarned design as guaranteed safe.

## Shaded-reference workflow

A shaded/rendered image cannot be treated as literal Z because highlights and shadows include illumination. The desktop therefore uses a two-stage flow:

```text
original shaded image
        ↓
deterministic interpretation
        ↓
derived machine height map + mask + preview
        ↓
matched-pair / paper-risk validation
        ↓
user reviews derived preview
        ↓
Accept preview & generate STLs
```

The converter suppresses broad lighting, isolates the motif, applies printer-aware cleanup, and synthesizes emboss-oriented relief from motif boundaries and stable local structure. This is explicitly an **interpretation for embossing, not reconstruction of true 3D geometry**.

The derived height map, relief preview, foreground mask, and converter provenance are saved in the design folder and manifest. Changing settings invalidates an accepted preview and causes it to be regenerated before final STL output.

The app may notice substantial continuous shading and recommend the shaded-reference mode, but it does not silently switch source semantics.

## Output and reproducibility

Binary jobs preserve normalized SVG + SCAD + STL + manifest. Relief jobs preserve the canonical machine height map and male/female surface maps in addition to SCAD/STL/manifest. Shaded-reference jobs preserve their derived preview/mask/height map too.

The GUI is intentionally a thin layer over `embossforge.generator.generate_die()`. Geometry and validation rules live in the shared backend so desktop, CLI, CI, and agent workflows cannot silently diverge.

## Run from source

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[cad,gui,dev]"
embossforge gui
```

or:

```powershell
embossforge-gui
```

A source checkout needs OpenSCAD installed for STL rendering. Packaged Windows builds bundle it.

## Release validation

CI constructs the completed desktop window offscreen on Windows. The release workflow additionally tests binary STL output, variable-depth STL output, matched closure validation, shaded-reference conversion tests, PyInstaller packaging, bundled OpenSCAD discovery, portable ZIP creation, and Inno Setup installer creation.

Variable-depth geometry is software/CAD validated but still awaits dedicated physical multi-height emboss calibration before being described as physically validated.
