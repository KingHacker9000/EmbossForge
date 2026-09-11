# Fully printable 42 mm lever embosser

This is the primary V4 EmbossForge press architecture.

It exists because the earlier handheld prototypes still depended on metal fasteners and produced tall, awkward printed structures. V4 is designed specifically for a 0.4 mm FDM nozzle and for users who want every functional component to come off the printer.

## Design contract

- accepts the existing standard 42 mm EmbossForge keyed die pair;
- requires no new die pair if you already printed a standard 42 mm male/female set;
- requires no screws, nuts, threaded inserts, smooth rods, bearings, springs, or metal pins;
- uses one printed body, one printed upper carriage, one printed upper-die cap, one printed lever, two printed linkage pins, two identical retaining wedges, and two small cap pegs;
- uses broad guide walls and a ladder-style base instead of tall skinny towers;
- exports the lever already rotated onto its broad side for printing;
- is authored around 0.4 mm nozzle FDM constraints.

## Generate

```powershell
embossforge lever-press --out build\lever-press
```

The important STL files are:

```text
body.stl
upper_carriage.stl
upper_die_cap.stl
lever.stl
main_pivot_pin.stl
drive_pin.stl
retaining_wedge.stl      # print 2
cap_peg.stl              # print 2
```

`assembly_closed.step` and `assembly_open.step` are also exported so the mechanism can be inspected as an assembled CAD model before printing.

## Assembly

1. Drop the existing male die face-up into the keyed lower pocket.
2. Place the existing female die face-down into the keyed opening in `upper_carriage`.
3. Place `upper_die_cap` over the female die and push two `cap_peg` parts through the matching holes.
4. Slide the upper carriage between the guide walls with its rear stem pointing toward the pivot.
5. Put the forked nose of the lever around that stem.
6. Align the main pivot holes and insert `main_pivot_pin`.
7. Push one `retaining_wedge` through the rectangular slot near the end of that pin.
8. Align the smaller drive-pin holes through the lever fork and carriage stem, insert `drive_pin`, then retain it with the second wedge.
9. Cycle the press open and closed by hand before inserting paper. Nothing should bind.

The retaining wedges are cotter-style printed keys, not fake screws. They are supposed to slide through the rectangular cross-slots in the printed pins.

## First print settings — Adventurer 5M / 0.4 mm

For the large pieces:

```text
Layer height: 0.24-0.28 mm
Walls:        3
Infill:       10-15%
Supports:     off initially
Outer wall:   60-80 mm/s
```

For `main_pivot_pin`, `drive_pin`, both `cap_peg` parts and both retaining wedges:

```text
Layer height: 0.20 mm
Walls:        4
Infill:       100%
Speed:        40-60 mm/s
```

Do not print the small pins at the 300 mm/s prototype speed used for some earlier parts. Their dimensional accuracy and layer bonding matter more than saving a minute.

## Why the mechanism is different

The V4 body is an open frame rather than a thick decorative shell. The upper carriage is guided directly between two broad walls. A forked lever drives the carriage through a second printed pin. Both linkage pins are retained by printable wedges. The female die is held by a printable cap and two push-pegs.

This avoids the earlier failure mode where a part was represented as a screw even though the printed geometry had no usable thread, nut, or locking feature.

## Status

CAD collision checks are required in both the open and closed states before the exporter writes a validated pack. Physical strength and long-term wear still need to be established by actual prints; PLA pins should be treated as consumable test hardware until that validation exists.
