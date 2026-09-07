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
- the miniature or full press mechanism
- full-size press strength or durability
- optimal clearances for different paper stocks

Future physical tests should append dated entries here rather than overwriting this result.
