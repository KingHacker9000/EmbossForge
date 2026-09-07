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
- cartridge/receiver fit
- the Micro Embosser, miniature, or full press mechanism
- full-size press strength or durability
- optimal clearances for different paper stocks

## Next queued physical article — 16 mm Micro Embosser

The repository now includes `embossforge micro-press`, a dedicated low-force press whose cartridge dimensions are tied directly to the already-proven 16 mm `butterfly-test` die contract.

This article is **software/CAD validated only until printed**. Its first physical test should record, in order:

1. actual butterfly-die fit in one keyed cartridge;
2. cartridge sliding fit in the receiver;
3. open/closed platen and lever motion;
4. male/female alignment under paper;
5. whether the known-good butterfly pair embosses cleanly using lever force;
6. any observed flex, binding, cracking, or stop/alignment error.

See `docs/MICRO_PRESS.md` for the exact print/assembly sequence.

Future physical tests should append dated entries here rather than overwriting earlier results.
