# Pocket Cam 42 — Revision B split frame

Physical Revision A result: `carrier`, `cam_lever`, `axle`, and `axle_clip` printed cleanly. The one-piece `frame.stl` failed because its long horizontal arm/guide surfaces depended too heavily on supports.

Revision B changes **only the frame**. Reuse the four successful printed parts and your existing 42 mm dies.

Generate:

```powershell
cd C:\Dev\Random_Projects\EmbossForge
git pull --ff-only
python designs\pocket_cam_press\frame_rev_b.py
```

Print only:

```text
build\pocket_cam_press_rev_b\stl\frame_left.stl
build\pocket_cam_press_rev_b\stl\frame_right.stl
```

Starting settings for the Adventurer 5M / 0.4 mm nozzle:

```text
Layer height: 0.20 mm
Walls:        5
Infill:       15% grid or gyroid
Supports:     OFF
Brim:         off, or 4 mm only if bed adhesion needs it
Scale:        100%
```

Both halves are already exported in their intended print orientation: broad outer cheek face on the bed, center seam facing upward. Do not auto-orient them.

Assembly:

1. Start all three tapered pegs from `frame_left` into the matching sockets in `frame_right`.
2. Squeeze the seam together evenly by hand. Do not hammer the pegs.
3. Insert the existing lower 42 mm die into the joined lower pocket. Revision B uses three short friction ribs rather than the old cross-seam lower clamp.
4. Reuse the already-printed carrier, cam lever, axle and axle clip exactly as before. The axle passes through both frame halves and positively ties the upper cheeks together.

The split-frame generator exports watertight single-body STLs plus an assembled frame STEP. It preserves the original carrier guides, cam axis, axle seat, closing locators and die center. This is still a physical prototype: real peg fit, frame stiffness and embossing force are not certified until printed and tested.
