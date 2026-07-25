# USB-C PD + Buck Converter + Capacitor Case

3D-printable enclosure (STL) for a small USB-C-powered adjustable DC supply
built from:

| Component | Part | Envelope used |
|---|---|---|
| DC-DC buck module 3–40 V in / 1.5–35 V out | [Altronics Z6334](https://www.altronics.com.au/p/z6334-dc-dc-buck-module-3-40v-input/) (LM2596) | 43 × 21 × 14 mm |
| 1000 uF 50 V low-ESR electrolytic capacitor | [Altronics R6187](https://www.altronics.com.au/p/r6187-lelon-1000uf-50v-pcb-low-esr-electrolytic-capacitor/) | 17 mm dia × 25 mm |
| USB-C PD trigger board, selectable voltage | [Core Electronics CE08536](https://core-electronics.com.au/usb-c-pd-trigger-board-selectable-voltage.html) | 42 × 18 mm |

A second **storage variant** additionally holds a BP-511 dummy battery
(DC coupler, 55 × 38 × 21 mm) and ~2 m of coiled cable.

## Files

Compact (electronics only), external **54.8 × 68.3 × 23.3 mm**:

- `case_base.stl` — the box. Print as-is (flat bottom on the bed).
- `case_lid.stl` — the lid, modeled in its assembled orientation.
- `case_lid_print_orientation.stl` — same lid pre-flipped flat-top-down, ready to print.
- `case_assembly_preview.stl` — base + lid together, for visual checking only.

With storage section, external **132.4 × 68.3 × 26.8 mm** (two-part lid):

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

Three parallel bays separated by 10 mm divider walls:

1. **PD trigger bay** (front) — board slides in against the end wall; a
   14 × 9.6 mm cutout in that wall accepts the USB-C plug overmold. An end
   stop holds the board with 0.5 mm play. A slot in the lid above the board
   gives access to the voltage-select button and shows the LED.
2. **Buck module bay** (middle) — corner end-stops locate the 43 × 21 mm
   board. Lid vent slots (3 mm wide) sit above it for cooling and double as
   screwdriver access, but set the output voltage with the trimpot **before**
   final assembly. An 8 mm wire slot in the opposite end wall (open to the
   top edge) passes the output cable; closing the lid captures it.
3. **Capacitor cradle** (back) — the 1000 uF cap lies on its side in two
   saddle ribs (17.5 mm dia opening), leads facing the wire-slot end so they
   can bend down toward the buck output terminals.

### Storage variant

The storage version is 22 mm deep inside (vs 18.5 mm) so the BP-511 dummy fits
lying flat, and adds a section right of the electronics, behind a full-height
wall:

4. **BP-511 pocket** — 40 × 56 mm pocket boxed in by a 12 mm retaining rib.
   The rib has a 24 mm centered gap for finger access and for the dummy's
   attached cable to pass into the cable bay.
5. **Cable bay** — open 34 × 63.5 × 22 mm compartment (~45 cm³) for ~2 m of
   coiled cable. The buck output passes into the storage section through a
   notch in the dividing wall, and an 8 mm exit slot in the outer end wall
   lets the cable out with the lid closed.

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
3. Wire: PD trigger screw terminals → buck IN; buck OUT → capacitor
   (mind polarity — stripe = negative) and out through the wire slot.
4. Lid screws: 3 × M3 self-tapping (8–10 mm long) into the corner posts
   (2.7 mm pilot holes), countersunk heads sit flush.

## Regenerating / tweaking

```bash
pip install trimesh manifold3d shapely numpy
python3 generate_case.py
```

All dimensions (wall thickness, clearances, bay sizes, slot positions) are
named parameters at the top of `generate_case.py`.
