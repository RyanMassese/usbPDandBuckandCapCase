#!/usr/bin/env python3
"""
3D-printable enclosure for:
  1x Altronics Z6334  DC-DC buck module (LM2596, 43 x 21 x ~14 mm)
  1x Altronics R6187  Lelon 1000uF 50V low-ESR capacitor (13 mm dia x 25 mm)
  1x Core Electronics USB-C PD trigger board, selectable voltage (42 x 18 mm)

Two variants are exported (units: mm):
  case_base.stl / case_lid.stl
      compact electronics-only case
  case_base_with_storage.stl / case_lid_with_storage.stl
      adds a storage section for a BP-511 dummy battery (55 x 38 x 21 mm)
      and ~2 m of coiled cable; the whole case is taller (22 mm interior)
      so the battery fits lying flat.

Layout of the storage variant (top view, +X right, +Y back):

        +---------------------------++------------+----------+
        | cap cradle (saddle ribs)  ||            |          |
        |---------------------------|| BP-511     |  cable   |
        | buck module bay   [notch]->  dummy      |  bay     |
        |---------------------------|| pocket     | [exit]-> |
   USB-C| PD trigger bay            ||            |          |
   <----|                           ||            |          |
        +---------------------------++------------+----------+

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
LIP_CLR = 0.3       # lip-to-wall clearance per side
CORNER_R = 3.0      # outer corner radius

# component envelopes (incl. fitting clearance)
PD_LANE_W = 19.0    # PD board 18 wide
BUCK_LANE_W = 22.0  # buck board 21 wide
CAP_LANE_W = 14.5   # cap 13 dia
DIV_T = 2.0         # lane divider thickness
DIV_H = 10.0        # lane divider height above floor

ELEC_LEN = 50.0     # electronics section interior length (X)
INT_H_COMPACT = 16.0   # buck ~14 tall, cap top at ~13.8
INT_H_STORAGE = 22.0   # BP-511 dummy is ~21 thick, lying flat

# storage section (BP-511: 55.2 x 38.2 x 20.8 nominal)
BATT_POCKET_W = 40.0   # X, battery 38.2 wide
BATT_POCKET_L = 56.0   # Y, battery 55.2 long
BATT_RIB_T = 1.6       # retaining rib between battery and cable bay
BATT_RIB_H = 12.0
BATT_RIB_GAP = 24.0    # centered gap: finger access + attached-cable pass
CABLE_BAY_W = 34.0     # ~45 cm^3: 2 m of 4 mm cable coiled + plug
SEC_DIV_T = 2.0        # full-height wall between electronics and storage

POST_D = 7.0        # lid screw posts
PILOT_D = 2.7       # M3 self-tap pilot
PILOT_DEPTH = 11.0
SCREW_CLR_D = 3.4   # M3 clearance in lid
CSK_D = 6.4         # countersink diameter

CAP_D = 13.0
CAP_SADDLE_R = CAP_D / 2 + 0.25
RIB_T = 2.5
RIB_H = 9.0         # rib height above floor; saddle axis at 7.0

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


def build(with_storage):
    int_h = INT_H_STORAGE if with_storage else INT_H_COMPACT
    base_h = FLOOR + int_h
    iz1 = base_h

    ex1 = IX0 + ELEC_LEN                    # electronics section right edge
    if with_storage:
        bay_x0 = ex1 + SEC_DIV_T            # storage bay left edge
        batt_x1 = bay_x0 + BATT_POCKET_W    # battery pocket right edge
        rib_x1 = batt_x1 + BATT_RIB_T
        ix1 = rib_x1 + CABLE_BAY_W          # interior right edge
    else:
        ix1 = ex1
    out_len = ix1 + WALL

    # lid screw posts. The left-front corner is where the PD board meets the
    # USB-C wall, so no post there; the lip locates that corner.
    posts = [
        (ex1 - POST_D / 2, PD_Y0 + POST_D / 2),
        (ex1 - POST_D / 2, CAP_Y1 - POST_D / 2),
        (IX0 + POST_D / 2, CAP_Y1 - POST_D / 2),
    ]
    if with_storage:                        # cable-bay corners
        posts += [
            (ix1 - POST_D / 2, PD_Y0 + POST_D / 2),
            (ix1 - POST_D / 2, CAP_Y1 - POST_D / 2),
        ]

    # ------------------------------------------------------------- base
    shell = extrude(rounded_rect(0, 0, out_len, OUT_W, CORNER_R), 0, base_h)
    cavity = bx(IX0, PD_Y0, IZ0, ix1, CAP_Y1, iz1 + 1)
    base = diff(shell, [cavity])

    adds = []
    # lane dividers (electronics section)
    adds.append(bx(IX0, PD_Y1, IZ0, ex1, BUCK_Y0, IZ0 + DIV_H))
    adds.append(bx(IX0, BUCK_Y1, IZ0, ex1, CAP_Y0, IZ0 + DIV_H))

    # buck module end stops (board 43 long, centered -> 3.5 mm inset each end)
    for x0, x1 in [(IX0, IX0 + 3.0), (ex1 - 3.0, ex1)]:
        adds.append(bx(x0, BUCK_Y0, IZ0, x1, BUCK_Y0 + 3.0, IZ0 + 8.0))
        adds.append(bx(x0, BUCK_Y1 - 3.0, IZ0, x1, BUCK_Y1, IZ0 + 8.0))

    # PD board end stop (board sits against USB-C wall; stop at its far end,
    # 42 mm board + 0.5 mm clearance)
    adds.append(bx(IX0 + 42.5, PD_Y1 - 3.0, IZ0, IX0 + 44.5, PD_Y1, IZ0 + 8.0))

    # capacitor saddle ribs
    rib_solids = []
    for rx in (IX0 + 12.0, IX0 + 32.0):
        rib_solids.append(bx(rx, CAP_Y0, IZ0, rx + RIB_T, CAP_Y1,
                             IZ0 + RIB_H))
    cap_cy = (CAP_Y0 + CAP_Y1) / 2
    saddle_cut = cyl_x(IX0 - 1, ex1 + 1, cap_cy, IZ0 + 7.0, CAP_SADDLE_R)
    adds.append(diff(union(rib_solids), [saddle_cut]))

    if with_storage:
        # full-height wall between electronics and storage
        adds.append(bx(ex1, IY0, IZ0, bay_x0, CAP_Y1, iz1))
        # battery retaining rib with a centered gap (finger access and
        # pass-through for the dummy's attached cable)
        batt_y1 = IY0 + BATT_POCKET_L
        gap_c = (IY0 + batt_y1) / 2
        adds.append(bx(batt_x1, IY0, IZ0, rib_x1, gap_c - BATT_RIB_GAP / 2,
                       IZ0 + BATT_RIB_H))
        adds.append(bx(batt_x1, gap_c + BATT_RIB_GAP / 2, IZ0, rib_x1,
                       batt_y1, IZ0 + BATT_RIB_H))
        # cross rib boxing in the battery's far end
        adds.append(bx(bay_x0, batt_y1, IZ0, rib_x1, batt_y1 + BATT_RIB_T,
                       IZ0 + 8.0))

    # lid screw posts
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
        # notch in the section wall: buck output feeds the storage bay
        cuts.append(bx(ex1 - 0.1, wire_cy - WIRE_SLOT_W / 2, IZ0 + 7.0,
                       bay_x0 + 0.1, wire_cy + WIRE_SLOT_W / 2, iz1 + 1))
        # cable exit slot in the outer right wall, centered
        exit_cy = (IY0 + CAP_Y1) / 2
        cuts.append(bx(ix1 - 0.1, exit_cy - WIRE_SLOT_W / 2, IZ0 + 7.0,
                       out_len + 1, exit_cy + WIRE_SLOT_W / 2, base_h + 1))
    else:
        # output wire slot straight through the right wall
        exit_cy = wire_cy
        cuts.append(bx(ix1 - 0.1, wire_cy - WIRE_SLOT_W / 2, IZ0 + 7.0,
                       out_len + 1, wire_cy + WIRE_SLOT_W / 2, base_h + 1))

    base = diff(base, cuts)

    # -------------------------------------------------------------- lid
    plate = extrude(rounded_rect(0, 0, out_len, OUT_W, CORNER_R),
                    base_h, base_h + LID_T)
    lip_outer = bx(IX0 + LIP_CLR, PD_Y0 + LIP_CLR, base_h - LIP_H,
                   ix1 - LIP_CLR, CAP_Y1 - LIP_CLR, base_h)
    lip_inner = bx(IX0 + LIP_CLR + LIP_T, PD_Y0 + LIP_CLR + LIP_T,
                   base_h - LIP_H - 1,
                   ix1 - LIP_CLR - LIP_T, CAP_Y1 - LIP_CLR - LIP_T,
                   base_h + 1)
    lip_cuts = [lip_inner]
    for px, py in posts:
        lip_cuts.append(cyl_z(px, py, base_h - LIP_H - 1, base_h + 1,
                              POST_D + 2 * LIP_CLR))
    # clear the exit slot so the cable can pass under the lid edge
    lip_cuts.append(bx(ix1 - LIP_T - LIP_CLR - 1, exit_cy - WIRE_SLOT_W / 2
                       - 1, base_h - LIP_H - 1, ix1 + 1,
                       exit_cy + WIRE_SLOT_W / 2 + 1, base_h + 1))
    lid = union([plate, diff(lip_outer, lip_cuts)])

    lid_cuts = []
    for px, py in posts:
        lid_cuts.append(cyl_z(px, py, base_h - LIP_H - 1, base_h + LID_T + 1,
                              SCREW_CLR_D))
        lid_cuts.append(cone_z(px, py, base_h + LID_T - (CSK_D / 2),
                               base_h + LID_T + 0.01, CSK_D + 0.02))

    # vent slots over the buck module (3 mm wide: doubles as trimpot
    # screwdriver access)
    n_slots = 5
    slot_len = 26.0
    slot_x0 = IX0 + (ELEC_LEN - slot_len) / 2
    for i in range(n_slots):
        sy = BUCK_Y0 + 2.5 + i * (BUCK_LANE_W - 5 - 3.0) / (n_slots - 1)
        lid_cuts.append(bx(slot_x0, sy, base_h - 1,
                           slot_x0 + slot_len, sy + 3.0, base_h + LID_T + 1))

    # access slot over the PD board voltage button / LEDs
    lid_cuts.append(bx(IX0 + 6.0, usb_cy - 3.0, base_h - 1,
                       IX0 + 20.0, usb_cy + 3.0, base_h + LID_T + 1))

    lid = diff(lid, lid_cuts)
    return base, lid


def export(name, mesh):
    assert mesh.is_watertight, f'{name} is not watertight'
    mesh.export(name)
    print(f'{name}: {len(mesh.faces)} faces, watertight, '
          f'bounds={np.round(mesh.bounds, 1).tolist()}')


for suffix, with_storage in [('', False), ('_with_storage', True)]:
    base, lid = build(with_storage)
    export(f'case_base{suffix}.stl', base)
    export(f'case_lid{suffix}.stl', lid)

    lid_print = lid.copy()
    lid_print.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi, [1, 0, 0]))
    lid_print.apply_translation([0, 0, -lid_print.bounds[0][2]])
    lid_print.export(f'case_lid{suffix}_print_orientation.stl')
    print(f'case_lid{suffix}_print_orientation.stl written (flipped to print)')

    union([base, lid]).export(f'case_assembly{suffix}_preview.stl')
    print(f'case_assembly{suffix}_preview.stl written (visual check only)')
