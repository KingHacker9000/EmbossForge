# Physical validation log

This file records real printed tests separately from CAD/unit-test validation.

## 2026-09-07 — first matched-die emboss success

**Printer:** FlashForge Adventurer 5M  
**Nozzle:** 0.4 mm  
**Material:** PLA  
**Test article:** `embossforge butterfly-test` micro matched die pair  
**Die diameter:** 16 mm  
**Base thickness:** 1.8 mm  
**Male relief:** 0.45 mm  
**Female XY clearance:** 0.20 mm  
**Nominal paper thickness:** 0.10 mm

FlashPrint settings used for the successful print:

- 0.20 mm layer height
- 2 shells
- 10% grid infill
- 225 °C nozzle
- 55 °C bed
- estimated model material: about 0.96 g for the pair
- estimated print time: about 2 minutes

### Result

The male and female pieces printed successfully and the butterfly geometry was visibly recognizable on both halves. The pair produced a visible embossed butterfly impression on ordinary notebook paper when manually pressed together.

### What this validates

- the basic matched male/female die concept
- the current female clearance/depth is capable of embossing ordinary paper at this tiny test scale
- the 0.4 mm nozzle can reproduce a deliberately chunky 16 mm butterfly relief
- the orientation-key concept is usable by hand
- the generated STL workflow works end to end on the target printer

### What this does *not* validate

- arbitrary intricate artwork quality
- fine text or thin-line limits
- the Micro Embosser, miniature, or full press mechanism
- full-size press strength or durability
- optimal clearances for different paper stocks

## Next queued physical article — 16 mm PLA flexure Micro Embosser

`embossforge micro-press` now generates a **single-piece tong-style hand embosser** whose two long PLA arms flex elastically and whose opposing keyed sockets accept the already-proven 16 mm butterfly pair directly.

There are no cartridges, guide rods, pivots, rollers, screws, or separate press parts in this micro article. It is intentionally a very low-material test.

This article is **software/CAD validated only until printed**. Its first physical test should record:

1. actual butterfly-die fit in both direct keyed sockets;
2. whether the dies stay seated while handling paper;
3. whether the unloaded jaw gap and alignment are sensible;
4. how much hand force is required to bring the pair into engagement;
5. whether the known-good butterfly pair embosses cleanly;
6. whether the spring arms return after release;
7. any whitening, cracking, permanent set, twisting, or loss of die alignment after repeated squeezes.

See `docs/MICRO_PRESS.md` for the exact print/use sequence.

Future physical tests should append dated entries here rather than overwriting earlier results.
