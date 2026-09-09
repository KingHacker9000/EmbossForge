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

## 2026-09-08 — 42 mm Butterfly-M variable-depth failure

**Printer:** FlashForge Adventurer 5M  
**Nozzle:** 0.4 mm  
**Material:** PLA  
**Test article:** 42 mm Butterfly-M grayscale/variable-depth matched pair  
**Observed slicing:** shallow grayscale tiers collapsed to very few printed layers  
**Paper tested:** very thin paper as well as ordinary paper

### Result

This article is a **failed physical validation** and must not be used as evidence that the old variable-depth defaults work.

Observed problems from the printed pair and slicer preview:

- the male relief was far too shallow to produce useful paper deformation;
- lighter grayscale tiers were effectively only around one printed layer high;
- the female cavity looked broad/washed out rather than like a tight complementary accommodation;
- the two dies did not engage the artwork convincingly when brought together;
- even very thin paper showed essentially no useful emboss mark;
- the derived artwork also lost/smeared too much of the intended butterfly/rose/M hierarchy, making the physical design hard to read.

### Root causes identified

#### 1. Paper thickness was double-counted in Z

The old variable-depth backend used a female cavity equivalent to:

```text
male relief + paper thickness + female extra depth
```

while the nominal closure model already separated the flat die faces by paper thickness. The result was an unnecessary internal air gap. A pair could be collision-free yet still fail to drive paper into the female cavity.

The corrected model is:

```text
female cavity = male relief + female extra Z clearance
nominal local paper space = paper thickness + female extra Z clearance
```

Paper thickness therefore appears exactly once in the mechanical engagement model.

#### 2. Variable-depth tiers were too shallow for the FDM layer scale

Small grayscale values mapped to fractions of the old maximum depth. At a 0.20 mm print layer, useful tonal differences could collapse into roughly one printed layer.

The next 0.4 mm-nozzle physical-development recipe uses much stronger discrete tiers:

```text
0.00 mm  background
0.40 mm  shallow active detail
0.80 mm  medium detail
1.20 mm  strongest detail
```

This gives nominal 0/2/4/6-layer differences at a 0.20 mm slice height.

#### 3. The interpreted artwork was too intricate/noisy for this test

The failed print came from a derived height-map workflow with many tiny tonal/ornamental regions. The next test should use the clean authored `Butterfly-M.png` machine height map directly rather than reusing `Butterfly-M_derived_heightmap.png` from shaded-reference interpretation.

For reliable physical testing, the design hierarchy should favor broad tiers such as:

- flat background: 0 mm;
- secondary leaves/wing panels: ~0.4 mm;
- main butterfly/flowers/monogram: ~0.8 mm;
- outer ring and strongest structural accents: ~1.2 mm.

### Corrective software changes

After this failure, EmbossForge was changed so that:

- female relief depth no longer adds paper thickness a second time;
- explicit female extra Z clearance defaults are much smaller;
- the CLI can impose a physical minimum height on non-zero grayscale relief;
- current FDM CLI defaults use a deeper 1.20 mm maximum and fewer meaningful tiers;
- height-field validation checks **engagement** as well as non-interference;
- a historical double-paper-gap style field is now a hard validation error.

### Status

The failed pair should be retained only as a comparison article. Do not print another copy from its old STLs or old `*_derived_heightmap.png` source expecting a different result.

The corrected deeper 42 mm pair remains **not yet physically validated** until the next print is tested on real paper.

## Next queued physical article — 16 mm PLA flexure Micro Embosser

`embossforge micro-press` generates a **single-piece tong-style hand embosser** whose two long PLA arms flex elastically and whose opposing keyed sockets accept the already-proven 16 mm butterfly pair directly.

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
