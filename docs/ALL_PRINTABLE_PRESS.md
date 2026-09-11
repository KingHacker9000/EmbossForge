# Fully printable 42 mm lever embosser

This is the primary V5 EmbossForge press architecture.

It replaces the earlier handheld prototypes after physical testing showed that tall structures, assumed metal fasteners, and screw-like printed parts were not appropriate for an actually self-contained FDM embosser. V5 is designed specifically around a **0.4 mm nozzle** and the existing standard **42 mm keyed EmbossForge die pair**.

## Design contract

- accepts the existing standard 42 mm male/female dies; no new dies are required;
- requires **no screws, nuts, threaded inserts, smooth rods, bearings, springs, or metal pins**;
- uses one body, one upper carriage, one lever, two printed linkage pins, and two identical printed retaining wedges;
- the female die presses directly into a keyed pocket in the upper carriage and is held by three one-nozzle-width friction ribs;
- there is no upper cap, no fake screw, and no threaded printed part;
- broad guide walls and an open ladder base replace the earlier tall decorative frame;
- the lever STL is exported already lying on its broad side;
- the upper-carriage STL is exported upside-down so its die pocket faces upward while printing rather than requiring a large bridge;
- CAD validation must pass in both open and closed states before a pack is exported.

## Generate

```powershell
embossforge lever-press --out build\lever-press
```

The complete functional STL set is:

```text
body.stl                 x1
upper_carriage.stl       x1
lever.stl                x1
main_pivot_pin.stl       x1
drive_pin.stl            x1
retaining_wedge.stl      x2
```

There are no omitted hardware items. `assembly_closed.step` and `assembly_open.step` are also exported so the mechanism can be inspected as a real assembled CAD model rather than inferred from a pile of print-bed parts.

## How the printed linkage works

The two round pins are **not screws**. Each has a rectangular transverse slot close to its free end. After a pin passes through its mating holes, a flat tapered `retaining_wedge` slides through that slot like a cotter key. Print the wedge twice.

This gives a mechanically understandable, replaceable printed hinge without pretending FDM cylinders are threaded fasteners.

## How the upper die is held

The female die is inserted from the underside of `upper_carriage`, emboss face pointing outward/down. Its rear face seats against the pocket roof. Three 0.4 mm-wide ribs locally reduce the side clearance and grip the cylindrical edge of the die.

The ribs touch the **side wall only**. No retaining lip sits below the female emboss face, so plastic from the carriage cannot become an early hard stop against the lower die.

The exported `upper_carriage.stl` is pre-flipped for printing: the solid roof goes on the bed and the die pocket grows upward. Do not manually flip it back before slicing.

## Assembly

1. Drop the existing male die face-up into the keyed lower pocket.
2. Turn the printed upper carriage over after printing. Align the female key and press the female die into its keyed pocket with the emboss face pointing down/outward.
3. Slide the carriage between the two broad guide walls with its stem toward the rear pivot.
4. Put the forked end of the lever around the carriage stem.
5. Align the large pivot holes. Insert `main_pivot_pin` and slide one `retaining_wedge` through the rectangular slot at its end.
6. Align the smaller drive holes through the lever fork and carriage stem. Insert `drive_pin` and lock it with the second wedge.
7. Move the handle through its full travel with no paper installed. The carriage must slide freely and remain approximately parallel to the lower die.
8. Only after the dry movement test passes, insert paper and apply light pressure first.

## First print settings — Adventurer 5M / 0.4 mm

For `body.stl`:

```text
Layer height: 0.24-0.28 mm
Walls:        3
Infill:       10-15%
Supports:     off
Outer wall:   60-80 mm/s
```

For `lever.stl` and `upper_carriage.stl`, use their exported orientation:

```text
Layer height: 0.20-0.24 mm carriage / 0.24-0.28 mm lever
Walls:        3
Infill:       15-20%
Supports:     off initially
Outer wall:   60-80 mm/s
```

For both printed pins and both retaining wedges:

```text
Layer height: 0.20 mm
Walls:        4
Infill:       100%
Speed:        40-60 mm/s
```

Do **not** use the earlier 300 mm/s prototype speed for the pins, guide surfaces, or friction-fit die pocket. Dimensional accuracy and layer bonding matter much more here.

## Why V5 should print more cleanly

The earlier prototype placed important geometry high above the bed and relied on narrow structures that became visibly untidy on the physical print. V5 lowers the pivot, keeps the sliding guides broad, removes the upper cap assembly entirely, lays the lever flat, and prints the carriage with its large cavity facing upward.

This does not guarantee that the first physical V5 will be the final strength revision, but it removes the known architectural mistakes from the previous print.

## Status

Software/CAD validation checks exact 42 mm die compatibility, real printed-part solids, open/closed collision clearance, and the complete no-external-hardware export pack. Physical force capacity, friction-rib fit, printed-pin wear, and long-term PLA creep still require real-world validation.
