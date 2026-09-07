# EmbossForge desktop app

The desktop app is the primary path for people who only want to turn a design into printable embossing dies.

## Downloadable Windows builds

Official tagged releases are intended to provide two Windows x64 downloads:

- `EmbossForge-Setup-Windows-x64.exe` — normal installer.
- `EmbossForge-Windows-x64-portable.zip` — unzip and run `EmbossForge.exe`.

The official Windows bundle includes the OpenSCAD runtime used to render current STL files, so release users should not need to install Python, CadQuery, or OpenSCAD themselves.

The release workflow is `.github/workflows/release-windows.yml`.

## Desktop workflow

1. Launch EmbossForge.
2. Drop an SVG/PNG/JPG onto the design card, or click the card to browse.
3. Confirm the preview.
4. Pick die diameter, paper type, and printer.
5. Leave advanced settings alone unless you know you need them.
6. Click **Generate matched die pair**.
7. Click **Open output folder**.

Each generated binary design folder contains at least:

```text
<name>_normalized.svg
<name>_male.scad
<name>_female.scad
<name>_male.stl
<name>_female.stl
<name>_manifest.json
```

The STL pair is what a normal user imports into a slicer. Source/manifest files are kept so every generated design is inspectable and reproducible.

## UI philosophy

The UI intentionally exposes only the decisions most users understand:

- design file
- die diameter
- paper type/thickness
- printer
- output location

Base thickness, binary relief, margin, clearance, and artwork inversion stay secondary.

The GUI must remain a thin layer over `embossforge.generator.generate_die()`. Geometry rules belong in the shared backend so desktop, CLI, and agent workflows cannot silently diverge.

---

## Planned variable-depth relief UX

Variable-depth grayscale relief is an accepted vNext design, not a current implemented desktop feature. The canonical behavior is specified in [RELIEF_MODE_SPEC.md](RELIEF_MODE_SPEC.md).

The desktop app must add it without turning the UI back into a dense CAD settings panel.

### Emboss style

After artwork is loaded, users should see a simple choice:

```text
Simple emboss      # current binary behavior, default
Variable depth     # grayscale controls physical relief height
```

Binary remains selected by default.

If the artwork contains meaningful grayscale variation, the app may suggest Variable depth, but it must not silently switch modes.

### Default variable-depth controls

Only the primary decisions should be visible:

- Maximum relief
- Depth style: Stepped / Continuous
- Levels (only for Stepped)
- Tone direction: Darker = deeper / Lighter = deeper

A secondary **More relief controls** disclosure may contain:

- gamma
- background/zero threshold
- smoothing
- sampling/quality controls
- future profile/texture composition controls

### Preview

Variable depth needs more than the existing flat artwork preview.

The first version should provide:

- the original artwork preview;
- a visual relief/depth preview;
- a clear legend from zero relief to maximum relief;
- obvious differentiation between background and shallow embossed areas.

A full interactive 3D viewer is useful later but is not a requirement for the first relief implementation.

### Warnings and intentional override

The desktop app should summarize printability and paper-risk findings close to the Generate action in plain language.

Example:

```text
2 cautions
• Fine texture may not resolve with this nozzle.
• One steep ridge may crease thin paper.
```

Caution-level findings do not need an extra confirmation.

For high but overrideable paper-risk findings, show a concise confirmation with two clear actions:

```text
Go back and adjust
Generate anyway
```

Do not describe an unwarned design as guaranteed "safe". The planned analysis is heuristic.

Impossible geometry remains a hard error and cannot be overridden from the desktop app.

---

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

A source checkout still needs OpenSCAD installed to render current STL output. The self-contained release bundle supplies its own copy.

## Release build notes

The Windows release uses PyInstaller in one-directory mode rather than one-file mode because the bundle includes Qt and an unmodified OpenSCAD runtime. The installer wraps that portable directory using Inno Setup.

When frozen, `embossforge.scad_backend.find_openscad()` checks `tools/openscad/openscad.exe` next to the application before looking for a system installation.

A future variable-depth relief backend may add packaged runtime components if OpenSCAD is not efficient enough for dense height-map surfaces. Any such change must preserve the no-developer-setup release goal.
