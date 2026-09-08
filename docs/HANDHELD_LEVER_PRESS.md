# Handheld Lever Embosser

`embossforge lever-press` generates the primary full-size EmbossForge press: a compact hand-operated lever embosser built around the standard **42 mm keyed die pair**.

This design replaces the old rod-guided laboratory press as the recommended everyday mechanism. The older `embossforge mechanics` command remains available for engineering experiments.

## Architecture

The handheld press follows the layout of a conventional desk/hand embosser:

```text
                 long hand lever
        =================================
                    o  M6 pivot
                   / \
                  /   o M5 drive pin
                 /    │
             ┌───────────────┐
             │ upper carriage│
             │ female die ↓  │
             └───────┬───────┘
                     paper
             ┌───────┴───────┐
             │  male die ↑    │
        _____└───────────────┘____________ body/base
```

The lever is forked around a central carriage stem. A transverse M5-class pin connects the fork to the stem. Opening the handle lifts the carriage; closing it drives the carriage vertically so the two die faces stay parallel near engagement. Positive body stops set nominal closure rather than relying on the user to crush the printed dies together.

## Generate

```powershell
embossforge lever-press
```

Default files:

```text
build/lever-press/
  body.stl
  upper_carriage.stl
  upper_backing_cap.stl
  lever.stl
  body.step
  upper_carriage.step
  upper_backing_cap.step
  lever.step
  assembly_layout.json
  lever_press_manifest.json
```

## Compatible dies

The sockets are derived from the same standard `DieSpec` used by desktop/CLI die generation:

- diameter: **42.0 mm**
- base thickness: **3.0 mm**
- orientation key: **6.0 × 2.5 mm**
- default socket clearance: **0.15 mm per side**

Generate a compatible pair with either the desktop app or:

```powershell
embossforge die artwork.png --diameter 42 --paper copy --profile profiles/flashforge_adventurer_5m.toml
```

Do not scale either the press sockets or the die STLs to solve fit. Regenerate the press with an explicit clearance instead:

```powershell
embossforge lever-press --die-clearance 0.20
```

## Die loading

The lower male die drops into the keyed recess in the body with the artwork facing **up** and the orientation tab toward **+Y / the front paper-insertion nose**.

The female die is installed face **down** in the through-pocket of the upper carriage. Flip the printed female die **180° about Y** so its orientation tab still points toward the front. The removable backing cap clamps the die from above with a broad central boss.

The upper through-pocket deliberately avoids a 42 mm bridged ceiling, making the carriage practical to FDM print flat.

## Hardware

Prototype hardware:

- 1 × M6 bolt / ~6 mm smooth pin for the main pivot;
- 1 × M5 bolt / ~5 mm smooth pin for the carriage drive pin;
- 2 × M3 × ~10 mm screws for the upper die backing cap.

The M3 carriage holes are 2.6 mm prototype pilot holes intended for plastic self-tapping. Do not over-tighten them.

## Nominal mechanism

Current defaults are approximately:

- body footprint: **62 × 135 mm**;
- standard die: **42 mm**;
- upper-carriage travel: **14 mm**;
- open handle angle: about **40°**;
- nominal mechanical ratio: greater than **6.5:1**;
- no exposed guide rods or large top bridge.

The body uses two compact side guides around the die area plus rear pivot towers. The long lever provides mechanical advantage while remaining much closer to a commercial handheld embosser footprint than the original V0.2 laboratory press.

## Suggested first print

The design is CAD/software validated but has not yet been physically strength-qualified. For the first print:

1. generate the press at 100% scale;
2. slice the `body.stl` and `upper_carriage.stl` first and inspect material/time;
3. test a standard 42 mm die in the lower pocket before assembling the lever;
4. install the upper female die and backing cap;
5. use ordinary copy/notebook paper;
6. apply gradually increasing hand force only;
7. stop immediately if the body whitens, cracks, the pivot holes elongate, or the carriage binds.

Record the physical result in `docs/PHYSICAL_VALIDATION.md` before treating the press as strength validated.

## Old rod-guided prototype

`embossforge mechanics` still exports the much larger V0.2 rod-guided engineering press. It is retained for comparison and for future strength experiments, but it is no longer the recommended main EmbossForge form factor.
