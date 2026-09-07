# Micro Embosser

The Micro Embosser is now an **ultra-light one-piece PLA flexure tong** made specifically for the existing **16 mm `butterfly-test` die pair**.

It deliberately does **not** reuse the full rod-guided press architecture. The goal is to spend as little filament as practical while still testing the important thing: can the already-proven butterfly male/female pair be held in alignment and squeezed together by a printed hand tool?

## Generate it

```powershell
embossforge micro-press
```

Default output:

```text
build/micro-press/
  micro_butterfly_tongs.stl
  micro_butterfly_tongs.step
  micro_press_manifest.json
```

That is the whole mechanism. There are no cartridges, receivers, guide rods, pivots, rollers, screws, or extra printed press parts.

## How it works

The body is shaped like a pair of spring tongs:

```text
rear flexure                                      jaws
┌──────────────────────────────────────────────────◉  female
│
│       long PLA spring arms
│
└──────────────────────────────────────────────────◉  male
```

The two long arms are joined at the rear. They are intentionally slender enough to flex elastically by a small amount when squeezed by hand. This uses the natural springiness of printed PLA over a long beam rather than relying on a very thin living hinge.

The 16 mm dies load **directly** into shallow keyed recesses in the opposing jaws.

## Exact butterfly compatibility

The socket geometry is derived from `micro_butterfly_spec()`:

- die diameter: **16.0 mm**
- die base thickness: **1.8 mm**
- orientation key width: **3.5 mm**
- orientation key depth: **1.5 mm**
- butterfly relief: **0.45 mm**

The default die-pocket clearance is **0.15 mm per side**.

If your already-printed pair is unusually tight or loose, regenerate explicitly instead of scaling the STL:

```powershell
embossforge micro-press --die-clearance 0.18
```

## Size and material goal

The important dimensions are approximately:

- arm length: **72 mm**
- arm width: **7 mm**
- arm thickness: **3 mm**
- jaw outside diameter: **20.5 mm**
- unloaded jaw-surface gap: **5.2 mm**
- required total elastic closure: about **2.9 mm**
- required flex per arm: about **1.45 mm**

The generated manifest records a conservative **all-solid PLA mass upper bound**. A normal sliced part with sparse infill should be lower. Always trust FlashPrint's actual material estimate before printing.

## Printing

The STL is pre-rotated onto its side so both spring arms are supported by the bed. The die sockets are shallow sideways recesses in that print orientation.

Starting point for the Adventurer 5M / 0.4 mm nozzle:

- 0.20 mm layers
- 3 walls
- 10% infill
- supports off initially

Inspect the socket layers in FlashPrint preview. If your slicer creates obviously unsupported material around the shallow recesses, enable only the minimum local support needed.

## Loading the dies

After printing and cooling:

1. Put the **male butterfly die** into the lower keyed socket.
2. Put the **female butterfly die** into the opposing upper keyed socket.
3. Make sure both rectangular tabs enter their key extensions. Do not rotate either die independently.
4. The die bases deliberately remain partly exposed so they can be removed again.
5. Small front scallops provide access for a fingernail or thin plastic pick.

The tool should not require glue for the first fit test. If a die is loose, stop and adjust `--die-clearance` rather than permanently bonding the known-good test pair.

## First use

1. Insert one sheet of notebook or copy paper between the butterfly faces.
2. Hold the long arms like tongs.
3. Squeeze gradually until the male and female begin to engage.
4. Stop as soon as the emboss is formed.
5. Release and inspect the paper.

Do **not** force the arms completely flat together. PLA can flex over a long beam, but repeated over-bending can cause whitening, cracking, or fatigue.

## What this test proves

A successful print validates:

- direct fit of the already-printed 16 mm butterfly pair;
- key orientation in a real hand tool;
- whether a very lightweight PLA flexure can provide enough closing force;
- whether the die faces remain aligned while the arms flex;
- whether this low-material architecture is worth carrying into future compact embosser designs.

It does **not** validate the full-size press strength, and the flexure tongs remain physically unvalidated until actually printed and tested.
