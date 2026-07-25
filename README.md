# USB-C PD + Buck Converter + Capacitor Case

3D-printable enclosure (STL) for a small USB-C-powered adjustable DC supply
built from:

| Component | Part | Envelope used |
|---|---|---|
| DC-DC buck module 3–40 V in / 1.5–35 V out | [Altronics Z6334](https://www.altronics.com.au/p/z6334-dc-dc-buck-module-3-40v-input/) (LM2596) | 43 × 21 × 14 mm |
| 1000 uF 50 V low-ESR electrolytic capacitor | [Altronics R6187](https://www.altronics.com.au/p/r6187-lelon-1000uf-50v-pcb-low-esr-electrolytic-capacitor/) | 17 mm dia × 33 mm |
| USB-C PD trigger board, selectable voltage | [Core Electronics CE08536](https://core-electronics.com.au/usb-c-pd-trigger-board-selectable-voltage.html) | 42 × 18 mm |

A second **storage variant** additionally holds a BP-511 dummy battery
(DC coupler, 55 × 38 × 21 mm) and ~2 m of coiled cable.

## Files

Compact (electronics only), external **60.8 × 68.3 × 23.3 mm**:

- `case_base.stl` — the box. Print as-is (flat bottom on the bed).
- `case_lid.stl` — the lid, modeled in its assembled orientation.
- `case_lid_print_orientation.stl` — same lid pre-flipped flat-top-down, ready to print.
- `case_assembly_preview.stl` — base + lid together, for visual checking only.

With storage section, external **138.4 × 68.3 × 31.3 mm** (two-part lid):

- `case_base_with_storage.stl` — the box.
- `case_lid_with_storage_electronics.stl` — screwed lid over the electronics
  section (3 × M3).
- `case_lid_with_storage_hatch.stl` — tool-free snap-fit hatch over the
  battery/cable storage section.
- `case_lid_with_storage_electronics_print_orientation.stl`,
  `case_lid_with_storage_hatch_print_orientation.stl` — pre-flipped to print.
- `case_assembly_with_storage_preview.stl` — visual check only.

Shared:

- `generate_case.py` — parametric generator; edit dimensions and re-run to regenerate everything.

## Layout

The lane order and orientation follow how the unit is actually soldered: the
capacitor **and** the output cable go straight onto the buck module's
OUT+/OUT− pads with short leads, and flying leads run from the PD board's
screw terminal to the buck's IN pads. So the buck sits IN-end-first beside the
PD board's terminal — a ~24 mm hop for the input pair — which puts OUT at the
USB-C end with the capacitor's lead end right beside it.

Three parallel bays separated by 10 mm divider walls. **Each divider stops
short at the end where soldered wires have to cross lanes**, so nothing has to
arch over a wall:

1. **PD trigger bay** (front) — board slides in against the end wall; a
   14 × 9.6 mm cutout in that wall accepts the USB-C plug overmold. An end
   stop holds the board with 0.5 mm play. A 26 × 10 mm window in the lid
   exposes the voltage-select button and its LED row. The last 14 mm of the
   lane past the board is left open as a loop zone for the input pair, and
   the PD/buck divider is cut away there.
2. **Buck module bay** (middle) — low corner stops locate the 43 × 21 mm
   board with its **IN end toward the loop zone**. Lid vent slots (3 mm wide)
   sit above it for cooling and double as screwdriver access, but set the
   output voltage with the trimpot **before** final assembly. The output
   cable leaves through an 8 mm slot in the OUT-end wall (open to the top
   edge), one lane over from the USB-C opening.
3. **Capacitor cradle** (back) — the 1000 uF cap lies on its side in two
   saddle ribs (17.5 mm dia opening) with its **lead end toward the buck's
   OUT end**, about 16 mm of lead path away. The buck/cap divider is cut away
   for the first 16 mm so the leads cross straight over.

Because the input and output both terminate at the buck's OUT end, the USB-C
socket and the DC output slot share the same end wall, ~25 mm apart. That is
forced by the wiring: putting the PD terminal next to the buck's IN end
necessarily puts the USB-C and the output at the other.

### Storage variant

The storage version is 26.5 mm deep inside (vs 18.5 mm): the BP-511 dummy is
~21 mm thick lying flat, and its cable enters through a hole in the dummy's
**top face**, so there is ~5.5 mm of headroom for the cable to bend over the
battery. The section sits right of the electronics, behind a full-height
wall:

The bays follow the cable's own order — it arrives from the electronics, gets
coiled, and ends at the dummy — so the coil bay comes first and the BP-511
sits at the outer end beside the slot it deploys through:

4. **Cable bay** — open 34 × 63.5 × 26.5 mm compartment (~55 cm³) for ~2 m of
   coiled cable, first thing past the section wall. Because the output cable
   is soldered at the buck's OUT end (the USB-C end), it runs back over the
   top of the buck module and through a **high** notch in that wall — there
   is 12.5 mm of headroom above the module in this variant.
5. **BP-511 pocket** — 40 × 56 mm pocket at the outer end, behind a 12 mm
   retaining rib. The rib is well under the dummy's 21 mm thickness, so its
   top-face cable simply passes over into the bay; the rib's 26 mm gap is
   finger access to lift the dummy out.
6. **Deployment slot** — an 8 mm slot in the outer end wall beside the stored
   dummy, at the opposite end of the case from the USB-C inlet. It is open to
   the top edge: with the hatch off, lift the dummy out over the wall, drop
   its cable into the slot, and snap the hatch back on with the unused length
   still coiled inside.

The lid is split in two at the section wall:

- **Electronics lid** — screwed down with the same 3 × M3 self-tappers as the
  compact case. You only open this for wiring changes.
- **Storage hatch** — no screws. A half-round snap ridge on each long edge of
  its lip clicks into matching grooves in the case walls (~0.25 mm
  engagement). Thumb notches in both wall top edges, centered on the storage
  section, let you push the hatch edge up to pop it off. Snap tightness is
  tuned via `SNAP_RIDGE_R` / `SNAP_GROOVE_R` in the script.

## Assembly

1. Print in PETG or PLA, 0.2 mm layers, 3 walls, no supports needed
   (the USB-C opening bridges 14 mm — any printer handles that).
2. Set the buck module's output voltage first, then drop the boards in.
   A dab of hot glue or double-sided tape under each board stops rattle.
3. Orientation matters — the bays are cut for one way round:
   - PD board: USB-C against the end wall, screw terminal facing in.
   - Buck module: **IN end away from the USB-C wall**, OUT end toward it.
   - Capacitor: **lead end toward the USB-C wall**, beside the buck's OUT
     pads (mind polarity — the stripe is negative).
4. The input pair crosses the cut-away PD/buck divider at the IN end; the
   cap leads and the output cable cross the cut-away buck/cap divider at the
   OUT end. Nothing needs to route over a divider.
5. Lid screws: 3 × M3 self-tapping (8–10 mm long) into the corner posts
   (2.7 mm pilot holes), countersunk heads sit flush.

## Regenerating / tweaking

```bash
pip install trimesh manifold3d shapely numpy
python3 generate_case.py
```

All dimensions (wall thickness, clearances, bay sizes, slot positions) are
named parameters at the top of `generate_case.py`.
