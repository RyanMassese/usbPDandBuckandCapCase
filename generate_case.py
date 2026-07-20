#!/usr/bin/env python3
"""
3D-printable enclosure for:
  1x Altronics Z6334  DC-DC buck module (LM2596, 43 x 21 x ~14 mm)
  1x Altronics R6187  Lelon 1000uF 50V low-ESR capacitor (13 mm dia x 25 mm)
  1x Core Electronics USB-C PD trigger board, selectable voltage (42 x 18 mm)

Outputs case_base.stl and case_lid.stl (units: mm).

Layout (top view, +X to the right, +Y to the back):

        +--------------------------------------------+
        |  cap cradle (saddle ribs, cap lies on side) |
        |--------------------------------------------|
        |  buck module bay             [wire slot] -> |
        |--------------------------------------------|
   USB-C|  PD trigger bay                             |
   <----|                                             |
        +--------------------------------------------+

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
DIV_T = 2.0         # divider wall thickness
DIV_H = 10.0        # divider height above floor

INT_LEN = 50.0      # interior length (X); buck board is 43, PD board 42
INT_H = 16.0        # interior height; buck ~14 tall, cap top at ~13.8

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
WIRE_SLOT_W = 8.0   # output cable slot, open to the top edge

SEG = 64            # cylinder facets

# ------------------------------------------------------------- derived dims
INT_W = PD_LANE_W + DIV_T + BUCK_LANE_W + DIV_T + CAP_LANE_W   # 59.5
OUT_LEN = INT_LEN + 2 * WALL      # 54.8
OUT_W = INT_W + 2 * WALL          # 64.3
BASE_H = FLOOR + INT_H            # 18.4

# interior extents
IX0, IX1 = WALL, WALL + INT_LEN
IY0 = WALL
PD_Y0, PD_Y1 = IY0, IY0 + PD_LANE_W
BUCK_Y0 = PD_Y1 + DIV_T
BUCK_Y1 = BUCK_Y0 + BUCK_LANE_W
CAP_Y0 = BUCK_Y1 + DIV_T
CAP_Y1 = CAP_Y0 + CAP_LANE_W       # == WALL + INT_W
IZ0, IZ1 = FLOOR, BASE_H

# lid screw posts: right-front (PD lane, past board), right-back and
# left-back (cap lane, past the cradle ribs). Left-front corner is where the
# PD board meets the USB-C wall, so no post there; the lip locates that corner.
POSTS = [
    (IX1 - POST_D / 2, PD_Y0 + POST_D / 2),
    (IX1 - POST_D / 2, CAP_Y1 - POST_D / 2),
    (IX0 + POST_D / 2, CAP_Y1 - POST_D / 2),
]


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


# ------------------------------------------------------------------- base
shell = extrude(rounded_rect(0, 0, OUT_LEN, OUT_W, CORNER_R), 0, BASE_H)
cavity = bx(IX0, PD_Y0, IZ0, IX1, CAP_Y1, IZ1 + 1)
base = diff(shell, [cavity])

adds = []
# lane dividers
adds.append(bx(IX0, PD_Y1, IZ0, IX1, BUCK_Y0, IZ0 + DIV_H))
adds.append(bx(IX0, BUCK_Y1, IZ0, IX1, CAP_Y0, IZ0 + DIV_H))

# buck module end stops (board 43 long, centered -> 3.5 mm inset each end)
for x0, x1 in [(IX0, IX0 + 3.0), (IX1 - 3.0, IX1)]:
    adds.append(bx(x0, BUCK_Y0, IZ0, x1, BUCK_Y0 + 3.0, IZ0 + 8.0))
    adds.append(bx(x0, BUCK_Y1 - 3.0, IZ0, x1, BUCK_Y1, IZ0 + 8.0))

# PD board end stop (board sits against USB-C wall; stop at its far end,
# 42 mm board + 0.5 mm clearance)
adds.append(bx(IX0 + 42.5, PD_Y1 - 3.0, IZ0, IX0 + 44.5, PD_Y1, IZ0 + 8.0))

# capacitor saddle ribs
rib_solids = []
for rx in (IX0 + 12.0, IX0 + 32.0):
    rib_solids.append(bx(rx, CAP_Y0, IZ0, rx + RIB_T, CAP_Y1, IZ0 + RIB_H))
cap_cy = (CAP_Y0 + CAP_Y1) / 2
saddle_cut = cyl_x(IX0 - 1, IX1 + 1, cap_cy, IZ0 + 7.0, CAP_SADDLE_R)
ribs = diff(union(rib_solids), [saddle_cut])
adds.append(ribs)

# lid screw posts
for px, py in POSTS:
    adds.append(cyl_z(px, py, IZ0, IZ1, POST_D))

base = union([base] + adds)

cuts = []
# pilot holes in posts
for px, py in POSTS:
    cuts.append(cyl_z(px, py, IZ1 - PILOT_DEPTH, IZ1 + 1, PILOT_D))

# USB-C cutout, left wall, centered on PD lane
usb_cy = (PD_Y0 + PD_Y1) / 2
cuts.append(bx(-1, usb_cy - USB_CUT_W / 2, IZ0,
               IX0 + 0.1, usb_cy + USB_CUT_W / 2, IZ0 + USB_CUT_H))

# output wire slot, right wall, centered on buck lane, open to the top edge
wire_cy = (BUCK_Y0 + BUCK_Y1) / 2
cuts.append(bx(IX1 - 0.1, wire_cy - WIRE_SLOT_W / 2, IZ0 + 7.0,
               OUT_LEN + 1, wire_cy + WIRE_SLOT_W / 2, BASE_H + 1))

base = diff(base, cuts)

# -------------------------------------------------------------------- lid
# modeled in place above the base: plate BASE_H..BASE_H+LID_T, lip below
plate = extrude(rounded_rect(0, 0, OUT_LEN, OUT_W, CORNER_R),
                BASE_H, BASE_H + LID_T)
lip_outer = bx(IX0 + LIP_CLR, PD_Y0 + LIP_CLR, BASE_H - LIP_H,
               IX1 - LIP_CLR, CAP_Y1 - LIP_CLR, BASE_H)
lip_inner = bx(IX0 + LIP_CLR + LIP_T, PD_Y0 + LIP_CLR + LIP_T,
               BASE_H - LIP_H - 1,
               IX1 - LIP_CLR - LIP_T, CAP_Y1 - LIP_CLR - LIP_T, BASE_H + 1)
lip_cuts = [lip_inner]
for px, py in POSTS:  # clear the screw posts
    lip_cuts.append(cyl_z(px, py, BASE_H - LIP_H - 1, BASE_H + 1,
                          POST_D + 2 * LIP_CLR))
# clear the wire slot so the cable can pass under the lid edge
lip_cuts.append(bx(IX1 - LIP_T - LIP_CLR - 1, wire_cy - WIRE_SLOT_W / 2 - 1,
                   BASE_H - LIP_H - 1, IX1 + 1,
                   wire_cy + WIRE_SLOT_W / 2 + 1, BASE_H + 1))
lip = diff(lip_outer, lip_cuts)
lid = union([plate, lip])

lid_cuts = []
# screw holes + countersinks
for px, py in POSTS:
    lid_cuts.append(cyl_z(px, py, BASE_H - LIP_H - 1, BASE_H + LID_T + 1,
                          SCREW_CLR_D))
    lid_cuts.append(cone_z(px, py, BASE_H + LID_T - (CSK_D / 2),
                           BASE_H + LID_T + 0.01, CSK_D + 0.02))

# vent slots over the buck module (3 mm wide: doubles as trimpot screwdriver
# access)
n_slots = 5
slot_len = 26.0
slot_x0 = IX0 + (INT_LEN - slot_len) / 2
for i in range(n_slots):
    sy = BUCK_Y0 + 2.5 + i * (BUCK_LANE_W - 5 - 3.0) / (n_slots - 1)
    lid_cuts.append(bx(slot_x0, sy, BASE_H - 1,
                       slot_x0 + slot_len, sy + 3.0, BASE_H + LID_T + 1))

# access slot over the PD board voltage button / LEDs (near the USB-C end)
lid_cuts.append(bx(IX0 + 6.0, usb_cy - 3.0, BASE_H - 1,
                   IX0 + 20.0, usb_cy + 3.0, BASE_H + LID_T + 1))

lid = diff(lid, lid_cuts)

# ------------------------------------------------------------------ export
for name, mesh in [('case_base.stl', base), ('case_lid.stl', lid)]:
    assert mesh.is_watertight, f'{name} is not watertight'
    mesh.export(name)
    print(f'{name}: {len(mesh.faces)} faces, watertight={mesh.is_watertight}, '
          f'bounds={np.round(mesh.bounds, 1).tolist()}')

# lid flipped upside down, ready to print (flat top face on the bed)
lid_print = lid.copy()
lid_print.apply_transform(trimesh.transformations.rotation_matrix(
    np.pi, [1, 0, 0]))
lid_print.apply_translation([0, 0, -lid_print.bounds[0][2]])
lid_print.export('case_lid_print_orientation.stl')
print('case_lid_print_orientation.stl written (lid flipped for printing)')

assembly = union([base, lid])
assembly.export('case_assembly_preview.stl')
print('case_assembly_preview.stl written (visual check only, do not print)')
