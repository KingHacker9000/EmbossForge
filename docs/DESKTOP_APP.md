# EmbossForge desktop app

The desktop app is the primary path for people who only want to turn a design into printable embossing dies.

## Downloadable Windows builds

Official tagged releases are intended to provide two Windows x64 downloads:

- `EmbossForge-Setup-Windows-x64.exe` — normal installer.
- `EmbossForge-Windows-x64-portable.zip` — unzip and run `EmbossForge.exe`.

The official Windows bundle includes the OpenSCAD runtime used to render STL files, so release users should not need to install Python, CadQuery, or OpenSCAD themselves.

The release workflow is `.github/workflows/release-windows.yml`.

## Desktop workflow

1. Launch EmbossForge.
2. Drop an SVG/PNG/JPG onto the design card, or click the card to browse.
3. Confirm the preview.
4. Pick die diameter, paper type, and printer.
5. Leave advanced settings alone unless you know you need them.
6. Click **Generate die files**.
7. Click **Open output folder**.

Each generated design folder contains at least:

```text
<name>_normalized.svg
<name>_male.scad
<name>_female.scad
<name>_male.stl
<name>_female.stl
<name>_manifest.json
```

The STL pair is what a normal user imports into a slicer. SCAD and manifest files are kept so every generated design is inspectable and reproducible.

## UI philosophy

The UI intentionally exposes only the decisions most users understand:

- design file
- die diameter
- paper type/thickness
- printer
- output location

Base thickness, relief, margin, clearance, and artwork inversion live under **Advanced settings**.

The GUI must remain a thin layer over `embossforge.generator.generate_die()`. Geometry rules belong in the shared backend so desktop, CLI, and agent workflows cannot silently diverge.

## Run from source

For contributors:

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

A source checkout still needs OpenSCAD installed to render STL output. The self-contained release bundle supplies its own copy.

## Release build notes

The Windows release uses PyInstaller in one-directory mode rather than one-file mode because the bundle includes Qt and an unmodified OpenSCAD runtime. The installer wraps that portable directory using Inno Setup.

When frozen, `embossforge.scad_backend.find_openscad()` checks `tools/openscad/openscad.exe` next to the application before looking for a system installation.
