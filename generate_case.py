#!/usr/bin/env python3
"""
3D-printable enclosure for:
  1x Altronics Z6334  DC-DC buck module (LM2596, 43 x 21 x ~14 mm)
  1x Altronics R6187  Lelon 1000uF 50V low-ESR capacitor (17 mm dia x 33 mm)
  1x Core Electronics USB-C PD trigger board, selectable voltage (42 x 18 mm)

Two variants are exported (units: mm):
  case_base.stl / case_lid.stl
      compact electronics-only case, one screwed lid
  case_base_with_storage.stl
  case_lid_with_storage_electronics.stl / case_lid_with_storage_hatch.stl
      adds a storage section for a BP-511 dummy battery (55 x 38 x 21 mm)
      and ~2 m of coiled cable; the whole case is taller (22 mm interior)
      so the battery fits lying flat. The lid is split at the section
      wall: the electronics side is screwed shut, the storage side is a
      tool-free snap-fit hatch with thumb notches.

Lanes are ordered and oriented to match the assembled unit: the cap and the
output cable are soldered to the buck module's OUT pads, and flying leads run
from the PD board's screw terminal to the buck's IN pads.

        +--------------------------------------+
        |     [====== 1000uF cap ======]       |  cap lane
        |  ^leads   ----- divider -------------|
   out <-|  [====== buck module ======]  IN>   |  buck lane
        |  OUT      ------- divider ------     |
   USB-C|  [===== PD trigger =====] term>  ~~  |  PD lane
   <----|                              (loop)  |
        +--------------------------------------+
           ^ OUT end                  IN end ^

Storage variant (top view): the same electronics section, then a full-height
wall and the storage bays. Its output cable runs back over the top of the buck
module and through a high notch in that wall.

        +---------------- elec ----++----------+-------------+
        |    (as above)            ||  cable   | BP-511      |
        |                  [notch]->   bay     | dummy       |
        |                          ||          | pocket [exit]->
        +--------------------------++----------+-------------+
             ^ screwed lid               ^ snap hatch

Run:  python3 generate_case.py
"""

import numpy as np
import trimesh
from shapely.geometry import box as shp_box

# ---------------------------------------------------------------- parameters
WALL = 2.4          # wall thickness
FLOOR = 2.4         # floor thickness
LID_T = 2.4         # lid plate thickness
LIP_H = 2.5         # lid alignment lip height
LIP_T = 1.6         # lid lip thickness
LIP_CLR = 0.4       # lip-to-wall clearance per side
CORNER_R = 3.0      # outer corner radius

# component envelopes (incl. fitting clearance)
PD_LANE_W = 19.0    # PD board 18 wide
BUCK_LANE_W = 22.0  # buck board 21 wide
CAP_LANE_W = 18.5   # cap 17 dia
DIV_T = 2.0         # lane divider thickness
DIV_H = 10.0        # lane divider height above floor

# As-built layout. In the assembled unit the 1000uF cap and the output cable
# are soldered straight onto the buck module's OUT+/OUT- pads with short
# leads, and flying leads run from the PD board's screw terminal to the buck's
# IN pads. So the buck is placed IN-end-first next to the PD board's terminal
# (short hop for the input pair) which puts OUT at the USB-C end, with the
# cap's lead end right beside it. Both dividers are cut short so the soldered
# wires can cross lanes instead of arching over a 10 mm wall.
ELEC_LEN = 56.0     # electronics section interior length (X)
PD_LEN = 42.0       # PD trigger board length
BUCK_LEN = 43.0     # buck module length
BUCK_END_GAP = 4.0  # from the buck's IN end to the far wall (wire bend room)
CAP_LEAD_ZONE = 12.0   # from the cap's lead-end face to the OUT-end wall
WIRE_DIV_GAP = 16.0    # PD/buck divider stops short by this at the IN end
LEAD_DIV_GAP = 16.0    # buck/cap divider stops short by this at the OUT end
INT_H_COMPACT = 18.5   # buck ~14 tall, 17 dia cap top at ~17.5
INT_H_STORAGE = 26.5   # BP-511 dummy is ~21 thick lying flat, plus ~5.5 mm
                       # headroom: its cable enters through a hole in the
                       # dummy's TOP face and has to bend over the battery

# storage section (BP-511: 55.2 x 38.2 x 20.8 nominal)
BATT_POCKET_W = 40.0   # X, battery 38.2 wide
BATT_POCKET_L = 56.0   # Y, battery 55.2 long
BATT_RIB_T = 1.6       # retaining rib between battery and cable bay
BATT_RIB_H = 12.0
BATT_RIB_GAP = 26.0    # gap in the retaining rib: finger access to lift the
                       # dummy out (its top-face cable clears the rib anyway)
CABLE_BAY_W = 34.0     # ~45 cm^3: 2 m of 4 mm cable coiled + plug
SEC_DIV_T = 2.0        # full-height wall between electronics and storage
LID_GAP = 0.4          # gap between the two lid plates at the split

# snap-fit hatch (storage lid)
SNAP_RIDGE_R = 0.65    # half-round ridge on the hatch lip, front + back
                       # (sized for ~0.25 mm engagement past the wall face)
SNAP_RIDGE_L = 16.0
SNAP_GROOVE_R = 0.8    # matching groove in the wall inner faces
SNAP_GROOVE_L = 20.0
SNAP_Z_BELOW = 1.5     # ridge/groove centerline below the lid seam
NOTCH_R = 5.0          # thumb notch in the wall top edges
NOTCH_DROP = 3.0       # notch depth below the lid seam

POST_D = 7.0        # lid screw posts
POST_LIP_CLR = 0.8  # lip cutout clearance around each post (per side);
                    # printed posts run oversize and lip cutouts undersize,
                    # so this is deliberately generous
PILOT_D = 2.7       # M3 self-tap pilot
PILOT_DEPTH = 11.0
SCREW_CLR_D = 3.6   # M3 clearance in lid (prints ~0.2-0.3 undersize)
CSK_D = 7.0         # countersink diameter (M3 csk head is 6.0 nominal)

CAP_D = 17.0
CAP_LEN = 33.0
CAP_SADDLE_R = CAP_D / 2 + 0.25
CAP_AXIS_H = CAP_SADDLE_R + 0.25   # saddle axis above floor; keeps the
                                   # saddle cut from gouging the floor
RIB_T = 2.5
RIB_H = CAP_AXIS_H + 2.0           # ribs reach 2 mm above the cap axis

USB_CUT_W = 14.0    # fits USB-C plug overmolds
USB_CUT_H = 9.6     # from floor up
WIRE_SLOT_W = 8.0   # cable slots/notches, open to the top edge

SEG = 64            # cylinder facets

# ------------------------------------------------ shared derived dimensions
INT_W = PD_LANE_W + DIV_T + BUCK_LANE_W + DIV_T + CAP_LANE_W   # 59.5
OUT_W = INT_W + 2 * WALL                                        # 64.3

IX0 = WALL
IY0 = WALL
PD_Y0, PD_Y1 = IY0, IY0 + PD_LANE_W
BUCK_Y0 = PD_Y1 + DIV_T
BUCK_Y1 = BUCK_Y0 + BUCK_LANE_W
CAP_Y0 = BUCK_Y1 + DIV_T
CAP_Y1 = CAP_Y0 + CAP_LANE_W       # == WALL + INT_W
IZ0 = FLOOR


def rounded_rect(x0, y0, x1, y1, r):
    return shp_box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(
        r, quad_segs=SEG // 4)


def extrude(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, height=z1 - z0)
    m.apply_translation([0, 0, z0])
    return m


def bx(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def cyl_z(cx, cy, z0, z1, d):
    m = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=SEG)
    m.apply_translation([cx, cy, (z0 + z1) / 2])
    return m


def cyl_x(x0, x1, cy, cz, r):
    m = trimesh.creation.cylinder(radius=r, height=x1 - x0, sections=SEG)
    m.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2, [0, 1, 0]))
    m.apply_translation([(x0 + x1) / 2, cy, cz])
    return m


def cyl_y(cx, y0, y1, cz, r):
    m = trimesh.creation.cylinder(radius=r, height=y1 - y0, sections=SEG)
    m.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2, [1, 0, 0]))
    m.apply_translation([cx, (y0 + y1) / 2, cz])
    return m


def cone_z(cx, cy, z_tip, z_top, d_top):
    m = trimesh.creation.cone(radius=d_top / 2, height=z_top - z_tip,
                              sections=SEG)
    m.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi, [1, 0, 0]))
    m.apply_translation([cx, cy, z_top])
    return m


def union(parts):
    return trimesh.boolean.union(parts, engine='manifold')


def diff(a, parts):
    return trimesh.boolean.difference([a] + parts, engine='manifold')


def lip_ring(x0, y0, x1, y1, base_h, extra_cuts):
    """Alignment lip descending from a lid: perimeter ring just inside the
    cavity rectangle (x0,y0)-(x1,y1)."""
    outer = bx(x0 + LIP_CLR, y0 + LIP_CLR, base_h - LIP_H,
               x1 - LIP_CLR, y1 - LIP_CLR, base_h)
    inner = bx(x0 + LIP_CLR + LIP_T, y0 + LIP_CLR + LIP_T,
               base_h - LIP_H - 1,
               x1 - LIP_CLR - LIP_T, y1 - LIP_CLR - LIP_T, base_h + 1)
    return diff(outer, [inner] + extra_cuts)


def build(with_storage):
    int_h = INT_H_STORAGE if with_storage else INT_H_COMPACT
    base_h = FLOOR + int_h
    iz1 = base_h

    ex1 = IX0 + ELEC_LEN                    # electronics section right edge
    if with_storage:
        # bays follow the cable: it arrives from the electronics section, so
        # the coil bay comes first and the dummy on the cable's far end sits
        # at the outer end, next to the exit slot it deploys through.
        bay_x0 = ex1 + SEC_DIV_T            # storage section left edge
        cable_x1 = bay_x0 + CABLE_BAY_W     # cable bay right edge
        rib_x1 = cable_x1 + BATT_RIB_T      # battery retaining rib
        ix1 = rib_x1 + BATT_POCKET_W        # interior right edge
    else:
        ix1 = ex1
    out_len = ix1 + WALL

    # lid screw posts, all in the electronics section. The left-front corner
    # is where the PD board meets the USB-C wall, so no post there; the lip
    # locates that corner. The storage hatch has no screws at all.
    posts = [
        (ex1 - POST_D / 2, PD_Y0 + POST_D / 2),
        (ex1 - POST_D / 2, CAP_Y1 - POST_D / 2),
        (IX0 + POST_D / 2, CAP_Y1 - POST_D / 2),
    ]

    # ------------------------------------------------------------- base
    shell = extrude(rounded_rect(0, 0, out_len, OUT_W, CORNER_R), 0, base_h)
    cavity = bx(IX0, PD_Y0, IZ0, ix1, CAP_Y1, iz1 + 1)
    base = diff(shell, [cavity])

    # component positions. OUT end of the chain is at IX0 (the USB-C wall),
    # IN end at ex1.
    buck_x1 = ex1 - BUCK_END_GAP          # buck IN end
    buck_x0 = buck_x1 - BUCK_LEN          # buck OUT end
    cap_x0 = IX0 + CAP_LEAD_ZONE          # cap lead-end face
    cap_x1 = cap_x0 + CAP_LEN

    adds = []
    # lane dividers, each stopping short at the end where soldered wires have
    # to cross: input pair at the IN end, cap leads + output cable at the OUT
    # end.
    adds.append(bx(IX0, PD_Y1, IZ0, ex1 - WIRE_DIV_GAP, BUCK_Y0,
                   IZ0 + DIV_H))
    adds.append(bx(IX0 + LEAD_DIV_GAP, BUCK_Y1, IZ0, ex1, CAP_Y0,
                   IZ0 + DIV_H))

    # buck module corner stops, kept low so the soldered leads clear them
    for x0, x1 in [(buck_x0 - 3.0, buck_x0), (buck_x1, buck_x1 + 3.0)]:
        adds.append(bx(x0, BUCK_Y0, IZ0, x1, BUCK_Y0 + 3.0, IZ0 + 5.0))
        adds.append(bx(x0, BUCK_Y1 - 3.0, IZ0, x1, BUCK_Y1, IZ0 + 5.0))

    # PD board end stop (board sits against USB-C wall; stop at its far end)
    adds.append(bx(IX0 + PD_LEN + 0.5, PD_Y1 - 3.0, IZ0,
                   IX0 + PD_LEN + 2.5, PD_Y1, IZ0 + 8.0))

    # capacitor saddle ribs at the quarter points of the cap body
    rib_solids = []
    for rcx in (cap_x0 + CAP_LEN * 0.25, cap_x0 + CAP_LEN * 0.75):
        rib_solids.append(bx(rcx - RIB_T / 2, CAP_Y0, IZ0, rcx + RIB_T / 2,
                             CAP_Y1, IZ0 + RIB_H))
    cap_cy = (CAP_Y0 + CAP_Y1) / 2
    saddle_cut = cyl_x(IX0 - 1, ex1 + 1, cap_cy, IZ0 + CAP_AXIS_H,
                       CAP_SADDLE_R)
    adds.append(diff(union(rib_solids), [saddle_cut]))

    if with_storage:
        # full-height wall between electronics and storage
        adds.append(bx(ex1, IY0, IZ0, bay_x0, CAP_Y1, iz1))
        # battery retaining rib, between the cable bay and the pocket. It is
        # only 12 mm tall against the dummy's 21 mm, so the top-face cable
        # passes over it into the bay; the gap is finger access to lift the
        # dummy out.
        batt_y1 = IY0 + BATT_POCKET_L
        adds.append(bx(cable_x1, IY0, IZ0, rib_x1, batt_y1 - BATT_RIB_GAP,
                       IZ0 + BATT_RIB_H))
        # cross rib boxing in the battery's far end
        adds.append(bx(rib_x1, batt_y1, IZ0, ix1, batt_y1 + BATT_RIB_T,
                       IZ0 + 8.0))

    for px, py in posts:
        adds.append(cyl_z(px, py, IZ0, iz1, POST_D))

    base = union([base] + adds)

    cuts = []
    for px, py in posts:
        cuts.append(cyl_z(px, py, iz1 - PILOT_DEPTH, iz1 + 1, PILOT_D))

    # USB-C cutout, left wall, centered on PD lane
    usb_cy = (PD_Y0 + PD_Y1) / 2
    cuts.append(bx(-1, usb_cy - USB_CUT_W / 2, IZ0,
                   IX0 + 0.1, usb_cy + USB_CUT_W / 2, IZ0 + USB_CUT_H))

    wire_cy = (BUCK_Y0 + BUCK_Y1) / 2
    if with_storage:
        # the output cable is soldered at the buck's OUT end (by the USB-C
        # wall), so it runs back over the top of the module and through a
        # high notch in the section wall into the storage bay
        cuts.append(bx(ex1 - 0.1, wire_cy - WIRE_SLOT_W / 2, IZ0 + 15.0,
                       bay_x0 + 0.1, wire_cy + WIRE_SLOT_W / 2, iz1 + 1))
        # deployment slot in the outer end wall, right beside the stored
        # dummy and at the opposite end of the case from the USB-C inlet.
        # Open to the top edge, so with the hatch off you lift the dummy out
        # over the wall and drop its cable into the slot.
        exit_cy = (IY0 + CAP_Y1) / 2
        cuts.append(bx(ix1 - 0.1, exit_cy - WIRE_SLOT_W / 2, IZ0 + 7.0,
                       out_len + 1, exit_cy + WIRE_SLOT_W / 2, base_h + 1))
        # snap grooves in the front/back wall inner faces (storage section)
        snap_cx = (bay_x0 + ix1) / 2
        snap_z = base_h - SNAP_Z_BELOW
        for wy in (IY0, CAP_Y1):
            cuts.append(cyl_x(snap_cx - SNAP_GROOVE_L / 2,
                              snap_cx + SNAP_GROOVE_L / 2, wy, snap_z,
                              SNAP_GROOVE_R))
        # thumb notches in the front/back wall top edges
        for ny0, ny1 in [(-1, IY0), (CAP_Y1, OUT_W + 1)]:
            cuts.append(cyl_y(snap_cx, ny0, ny1,
                              base_h + NOTCH_R - NOTCH_DROP, NOTCH_R))
    else:
        # output cable exits the same end wall it is soldered next to (the
        # buck's OUT end), one lane over from the USB-C opening
        exit_cy = wire_cy
        cuts.append(bx(-1, wire_cy - WIRE_SLOT_W / 2, IZ0 + 5.0,
                       IX0 + 0.1, wire_cy + WIRE_SLOT_W / 2, base_h + 1))

    base = diff(base, cuts)

    # -------------------------------------------------------------- lid(s)
    full_plate = extrude(rounded_rect(0, 0, out_len, OUT_W, CORNER_R),
                         base_h, base_h + LID_T)

    def screw_cuts():
        c = []
        for px, py in posts:
            c.append(cyl_z(px, py, base_h - LIP_H - 1, base_h + LID_T + 1,
                           SCREW_CLR_D))
            c.append(cone_z(px, py, base_h + LID_T - (CSK_D / 2),
                            base_h + LID_T + 0.01, CSK_D + 0.02))
        return c

    def vent_cuts():
        c = []
        n_slots = 5
        slot_len = 26.0
        slot_x0 = (buck_x0 + buck_x1 - slot_len) / 2
        for i in range(n_slots):
            sy = BUCK_Y0 + 2.5 + i * (BUCK_LANE_W - 5 - 3.0) / (n_slots - 1)
            c.append(bx(slot_x0, sy, base_h - 1,
                        slot_x0 + slot_len, sy + 3.0, base_h + LID_T + 1))
        # window over the PD board's voltage button and its LED row
        c.append(bx(IX0 + 7.0, usb_cy - 5.0, base_h - 1,
                    IX0 + 33.0, usb_cy + 5.0, base_h + LID_T + 1))
        return c

    post_lip_cuts = [cyl_z(px, py, base_h - LIP_H - 1, base_h + 1,
                           POST_D + 2 * POST_LIP_CLR) for px, py in posts]

    if not with_storage:
        exit_lip_cut = bx(IX0 - 1, exit_cy - WIRE_SLOT_W / 2 - 1,
                          base_h - LIP_H - 1, IX0 + LIP_T + LIP_CLR + 1,
                          exit_cy + WIRE_SLOT_W / 2 + 1, base_h + 1)
        lip = lip_ring(IX0, PD_Y0, ix1, CAP_Y1, base_h,
                       post_lip_cuts + [exit_lip_cut])
        lid = diff(union([full_plate, lip]), screw_cuts() + vent_cuts())
        return {'case_base': base, 'case_lid': lid}

    x_split = ex1 + SEC_DIV_T / 2   # both plates land on the section wall
    elec_plate = diff(full_plate, [bx(x_split - LID_GAP / 2, -1, base_h - 1,
                                      out_len + 1, OUT_W + 1,
                                      base_h + LID_T + 1)])
    hatch_plate = diff(full_plate, [bx(-1, -1, base_h - 1,
                                       x_split + LID_GAP / 2, OUT_W + 1,
                                       base_h + LID_T + 1)])

    # electronics lid: screwed, lip around the electronics cavity, cut where
    # the buck output cable passes through the section-wall notch
    wire_lip_cut = bx(ex1 - LIP_T - LIP_CLR - 1, wire_cy - WIRE_SLOT_W / 2
                      - 1, base_h - LIP_H - 1, ex1 + 1,
                      wire_cy + WIRE_SLOT_W / 2 + 1, base_h + 1)
    elec_lip = lip_ring(IX0, PD_Y0, ex1, CAP_Y1, base_h,
                        post_lip_cuts + [wire_lip_cut])
    elec_lid = diff(union([elec_plate, elec_lip]),
                    screw_cuts() + vent_cuts())

    # storage hatch: snap-fit, no screws. Lip cut at the section-wall notch
    # (left) and the cable exit slot (right); snap ridges on front/back.
    hatch_lip_cuts = [
        bx(bay_x0 - 1, wire_cy - WIRE_SLOT_W / 2 - 1, base_h - LIP_H - 1,
           bay_x0 + LIP_T + LIP_CLR + 1, wire_cy + WIRE_SLOT_W / 2 + 1,
           base_h + 1),
        bx(ix1 - LIP_T - LIP_CLR - 1, exit_cy - WIRE_SLOT_W / 2 - 1,
           base_h - LIP_H - 1, ix1 + 1, exit_cy + WIRE_SLOT_W / 2 + 1,
           base_h + 1),
    ]
    hatch_lip = lip_ring(bay_x0, IY0, ix1, CAP_Y1, base_h, hatch_lip_cuts)
    snap_z = base_h - SNAP_Z_BELOW
    ridges = [cyl_x(snap_cx - SNAP_RIDGE_L / 2, snap_cx + SNAP_RIDGE_L / 2,
                    ry, snap_z, SNAP_RIDGE_R)
              for ry in (IY0 + LIP_CLR, CAP_Y1 - LIP_CLR)]
    hatch = union([hatch_plate, hatch_lip] + ridges)

    return {'case_base_with_storage': base,
            'case_lid_with_storage_electronics': elec_lid,
            'case_lid_with_storage_hatch': hatch}


def export(name, mesh):
    assert mesh.is_watertight, f'{name} is not watertight'
    mesh.export(name)
    print(f'{name}: {len(mesh.faces)} faces, watertight, '
          f'bounds={np.round(mesh.bounds, 1).tolist()}')


for with_storage in (False, True):
    parts = build(with_storage)
    for name, mesh in parts.items():
        export(f'{name}.stl', mesh)
        if 'lid' in name or 'hatch' in name:
            flipped = mesh.copy()
            flipped.apply_transform(trimesh.transformations.rotation_matrix(
                np.pi, [1, 0, 0]))
            flipped.apply_translation([0, 0, -flipped.bounds[0][2]])
            flipped.export(f'{name}_print_orientation.stl')
            print(f'{name}_print_orientation.stl written (flipped to print)')
    suffix = '_with_storage' if with_storage else ''
    union(list(parts.values())).export(f'case_assembly{suffix}_preview.stl')
    print(f'case_assembly{suffix}_preview.stl written (visual check only)')
