# Pocket Cam 42 — printable prototype

An original five-part hand embosser for the existing 42mm EmbossForge dies. It uses an eccentric cam, a straight guided carrier, and a printed axle with a separate positive retaining fork. No previous EmbossForge press geometry is imported or reused.

**External hardware required: 0. Unique printed press parts: 5. Total press pieces: 5.**

Closed/contact storage envelope: **114 × 78.5 × 44.5mm**, including axle and clip. This meets the requested maximum envelope, but not the preferred110×70×35mm envelope. It is a thick pocket object; actual back-pocket fit depends on clothing. Do not sit on it.

Estimated press mass is **106.1g**, excluding the two existing dies and temporary supports. See BOM.csv for the per-part estimate. This misses the preferred75g and100g targets; it remains below the150g prototype ceiling. Exact solid CAD volume corresponds to144.87g of PLA, even before slicer infill removes material. The mass estimate is a conservative voxel shell/infill calculation, **not a slicer measurement**. Allow roughly±15% around the estimate. Supports/brim may add5–12g of filament.

This package contains complete CAD and inspected print meshes, but **no physical print, force test, fatigue test, or successful embossing test has been performed on this design**. Treat it as a first-print prototype, not a validated production tool.

## Files

- `source/model.py`: editable dimensional CadQuery source, with no dependency on the old press.
- `source/validate.py`: exported-mesh, paper-path and assembly checks.
- `stl/`: exactly five required print files, already oriented for printing. Print one of each.
- `step/`: individual parts plus named, colored closed, open and exploded assemblies.
- `views/`: assembled, open, exploded and actual-STL print-orientation images.
- `BOM.csv`, `validation/`: quantities, estimates and raw verification results.

Purple components in assemblies are the **42×3mm keyed die base envelopes**, not replacement dies or generated artwork. Keep your already-printed matched dies. Their relief must still be mutually compatible.

## Printing on the Adventurer 5M

The manufacturer specifies a220×220×220mm build volume. Every part fits with ample room. The supplied orientations intentionally differ between parts. Do not auto-orient the whole set as though they were identical. [FlashForge specification](https://www.flashforge.com/products/adventurer-5m-3d-printer?country=US)

Use the printer's normal0.4mm PLA profile, with these mechanical-part settings:

| Part | Orientation supplied in STL | Layers | Walls | Top/bottom | Infill | Supports |
|---|---|---|---|---|---|---|
| frame | broad underside on bed; die pocket up |0.20mm|5|6 layers|15% gyroid|**Required** under arm/guide ledges and horizontal axle-hole ceilings |
| carrier | broad back on bed; pocket and cones up |0.20mm|5|6 layers|15% gyroid|Off |
| cam_lever | side face on bed; axle hole vertical |0.20mm|5|6 layers|15% gyroid|Off; use a4mm brim |
| axle | long D flat on bed; shaft horizontal |0.20mm|7|6 layers|15%|Off;6mm internal bore and3mm groove are short bridges |
| axle_clip | broad flat face on bed |0.15mm|4|5 layers|15%|Off |

Small load-bearing sections will become nearly solid through perimeters; this is intentional. **Do not select100% infill for the whole machine.** Start near210°C nozzle/55°C bed, within your filament maker's limits. Use30–40mm/s outer walls,60–80mm/s other structural walls,1200–2000mm/s² acceleration and20–25mm/s bridges. Use ordinary PLA cooling after the first layers. Do not use the printer's advertised top speed for these fits.

For the frame, enable normal/organic supports from all necessary surfaces, including support starting on its own base. Build-plate-only support can miss the ledges. Suggested starting support contact gap0.20mm, XY separation0.35mm and two interface layers. Keep supports out of the through-cut die clamp and the small ejection hole. The under-arm support is accessible from the sides/front after printing. Smooth its remnants so paper cannot snag. The horizontal bearing roofs must be clean before inserting the axle.

The cam has a1.2mm central grip web and tapered lobe transitions: these eliminate the long bridge that an open handle and abrupt second flange would create. Inspect the slicer preview for continuous web lines and supported taper layers. The cam is50mm tall in this orientation, with a roughly78×23mm footprint; the brim improves stability.

No reliable slicer time was obtained. Plan from the slicer's preview, not an invented hour estimate. Load the five STLs at100% scale, in millimetres.

## Assembly and die changes

1. Remove supports/brims, particularly beneath the frame arms. The clamp beam behind each die pocket must flex freely in its through slot. Do not lever hard against a layer seam.
2. Place the lower die in the frame, working face up, tab toward the rear clamp. Gently deflect the clamp toward the back and seat the die flat. Release it so the die bears against the two small fixed circular datums. The clamp grips the tab by friction; no lip covers the working face.
3. Install the upper die in the carrier's upward-facing pocket while the carrier is outside the press. Then turn the carrier over about its front-to-back axis: the female working face points down and both keys point to the back. Do not mirror or rotate the artwork independently.
4. Lower the carrier vertically into the frame. Its two rear side notches engage the small keys on the cheeks. The finger lip faces forward. Its two conical sockets face the matching rear locators. These are behind the paper path.
5. Lower the cam between the cheeks, above the carrier, with its handle pointing forward in the closed position. Align the axle hole. Slide the axle from the left through both frame cheeks and the cam. Its D flat faces toward the rear. Finger pressure should suffice; do not hammer it.
6. Hold the U-shaped clip **below** the exposed groove at the right end of the axle, arms pointing upward. Push it **upward** onto the neck. Its two small internal bumps must pass the neck and return inward. The fork bottom sits below the neck, and its arms remain upward. Pull gently on the axle head to confirm positive retention.

To change dies, unload and open the press, spread the clip's arms slightly and slide it **downward** off the neck, withdraw the axle, and lift out the cam and carrier. Release each tab clamp and gently push the die out through its6.4mm ejection hole using one arm of the removed printed clip, or a short blunt piece of scrap filament. Do not twist the clip while using it this way. No additional tool is structurally required. Replace the matched pair and reassemble. This is a simple disassembly, rather than a one-motion cartridge swap.

## Operation

Lift the lever, then lift the carrier's front finger lip until it touches the cam. **Reopening is manual; there is no hidden return spring.** The open base-face gap is2.35mm. With the repository's nominal0.65mm male relief there is useful insertion room; conservatively, two0.65mm opposing relief envelopes would leave1.05mm. Relief whose combined protrusion exceeds about2.2mm is outside this opening allowance.

Insert ordinary single-sheet paper horizontally from the front, over the lower die. Broad paper passes underneath the cheeks. The nominal center-to-rear-obstruction distance is25mm; the locator pads begin behind25.5mm. A full42mm imprint can therefore lie near a sheet edge. For predictable placement, stop the leading paper edge aroundY=24mm; the die center is marked by the center of the circular holder. This is an edge-access embosser, not a deep-reach device for arbitrary page locations.

Hold the rear/base of the frame and squeeze the lever at its front end, keeping fingers outside the die gap and away from the moving carrier. Make the first impressions with light force on scrap paper. The lever is approximately horizontal at nominal contact; elastic loading moves it somewhat below horizontal. Release pressure as soon as the impression is adequate. Raise the lever and manually lift the carrier to remove the sheet.

Use about15–25N hand force initially. A target of roughly200–300N die force is an engineering estimate, not a tested rating. Do not use two hands to force the lever, add extensions, or hold it clamped. A desktop can restrict the handle's extra travel; the intended operation is handheld. There is no force limiter or automatic storage latch. For carrying, relax the lever near horizontal; the carrier is geometrically captured by the axle/cam and rear guides. The press must not be carried under embossing preload.

## Fits and alignment

| Interface | Nominal allowance | Practical check |
|---|---|---|
|42mm die/circular clearance pocket|42.60mm pocket, plus two21.05mm radial datum faces|Clamp must seat die against both datums; don't sand the datums casually |
|6mm orientation tab|6.30mm slot|Deburr tab elephant foot; seat both keys consistently against the same world-side wall |
|Tab clamp|about0.48mm deflection after seating|Die should resist falling out or light paper peel; no structural adhesive |
|Carrier side guides|0.30mm each side|Free manual slide, no rocking under final pressure |
|Rear guide keys|3.00mm key/3.60mm notch|0.30mm each end; no preload adjustment |
|Closing conical locators|0.20mm radial clearance at0.10mm paper gap|They must enter without stopping die closure; no blind press fit |
|Axle/cam bearing|14.00/14.50mm diameters|0.25mm radial; rotates without forcing |
|Frame D bearing|0.25mm radial/flat allowance|D shape prevents axle rotation |
|Axle clip|2.70mm fork/3.00mm groove|0.15mm axial clearance each side; bumps retain fork |

The CAD die centers are concentric throughout straight carrier travel. The conical locators improve final registration beyond the loose running guides. Nominal die seating shifts both centers about0.07mm toward the front, equally. Real printing error, locator clearance, key backlash and wear remain: do not assume better than roughly0.2–0.4mm relative registration without measuring the print. Very fine existing dies with tighter clearances may need better fit or die-specific adjustment. Their actual relief meshes were not supplied or tested here.

If a fit binds, first remove support scars and elephant foot. The editable source exposes pocket diameter and locator clearance. Change only the relevant allowance in0.05–0.10mm steps; do not scale individual parts or force an assembly that rocks. PLA fit is printer-specific; Prusa recommends beginning around0.3mm for movable interfaces and checking orientation and real prints. [Prusa FDM guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)

## Wear and safety

Likely wear parts are the axle, cam bearing/lobes, clip and integrated die-clamp beams. A worn clamp requires reprinting its frame or carrier. Guide looseness and frame cracking are rejection signs. Check them after the first few impressions. The split fork carries retention loads only; the axle and broad cheeks carry the embossing reaction.

Keep fingers clear, release immediately if PLA whitens/cracks, and keep away from heat and hot cars. PLA has limited creep and heat resistance; an example manufacturer reports roughly55°C heat-deflection temperature. Material properties vary by brand and print orientation. [Prusament PLA data](https://prusament.com/wp-content/uploads/2022/10/PLA_Prusament_TDS_2021_10_EN.pdf)

## Rebuild

Use Python3.11 with `cadquery==2.8.0`, `trimesh`, `manifold3d`, `scipy`, `numpy`, `vtk` and `Pillow`. From the repository root run `python designs/pocket_cam_press/model.py`, then `python designs/pocket_cam_press/validate.py`. In the ZIP, run `python source/model.py` and `python source/validate.py`; generated outputs go under `build/pocket_cam_press` in the current directory. No existing die generation backend is changed.

See ENGINEERING.md for research, assumptions, strength screening and the limits of the digital validation.
