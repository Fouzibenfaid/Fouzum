"""Ahmed's House - Rev D. Architecture built from the plan sheet.
plan px -> metres: X = (px - 470) / 47.6  (north -> south),  Y = (935 - py) / 47.6  (west/street -> east)
first floor finished level Z = 0
"""
import bpy, math, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 47.6
def X(px): return (px - 470) / S
def Y(py): return (935 - py) / S
H = 3.2          # first floor clear height
ROOF = 3.62      # top of roof slab
GF = -3.70       # ground floor finished level
SLAB = -0.35

def R(px0, py0, px1, py1):
    """plan px rectangle -> (x0,y0,x1,y1) metres, ordered"""
    xs = sorted((X(px0), X(px1))); ys = sorted((Y(py0), Y(py1)))
    return xs[0], ys[0], xs[1], ys[1]

def wallpx(name, px0, py0, px1, py1, z0=0.0, z1=H, mat=None, coll=None):
    x0, y0, x1, y1 = R(px0, py0, px1, py1)
    return box(name, x0, y0, z0, x1, y1, z1, mat or MAT['plaster'], coll=coll)

def window_x_wall(name, xa, xb, y0, y1, gaps, z0=0.0, z1=H, sill=0.0, head=None, mat=None, skin=None, skin_side=-1, coll=None):
    """wall running along X between xa..xb (thickness y0..y1) with glazed gaps [(xa,xb)] (metres)"""
    mat = mat or MAT['plaster']
    head = H if head is None else head
    cur = xa
    for (ga, gb) in sorted(gaps):
        if ga > cur: box(name, cur, y0, z0, ga, y1, z1, mat, coll=coll)
        if sill > z0: box(name + '_sill', ga, y0, z0, gb, y1, sill, mat, coll=coll)
        if head < z1: box(name + '_head', ga, y0, head, gb, y1, z1, mat, coll=coll)
        ym = (y0 + y1) / 2
        box(name + '_glass', ga, ym - 0.012, sill, gb, ym + 0.012, head, MAT['glass'], coll=coll)
        # slim bronze frame at sill and head only (frameless look)
        box(name + '_fr', ga, ym - 0.03, sill, gb, ym + 0.03, sill + 0.025, MAT['bronze_dark'], coll=coll)
        box(name + '_fr', ga, ym - 0.03, head - 0.025, gb, ym + 0.03, head, MAT['bronze_dark'], coll=coll)
        cur = gb
    if xb > cur: box(name, cur, y0, z0, xb, y1, z1, mat, coll=coll)
    if skin:
        ys = (y0 - 0.02, y0) if skin_side < 0 else (y1, y1 + 0.02)
        cur = xa
        for (ga, gb) in sorted(gaps):
            if ga > cur: box(name + '_skin', cur, ys[0], z0 - 0.38, ga, ys[1], z1 + 0.42, skin, coll=coll)
            cur = gb
        if xb > cur: box(name + '_skin', cur, ys[0], z0 - 0.38, xb, ys[1], z1 + 0.42, skin, coll=coll)

def window_y_wall(name, ya, yb, x0, x1, gaps, z0=0.0, z1=H, sill=0.0, head=None, mat=None, skin=None, skin_side=-1, coll=None):
    mat = mat or MAT['plaster']
    head = H if head is None else head
    cur = ya
    for (ga, gb) in sorted(gaps):
        if ga > cur: box(name, x0, cur, z0, x1, ga, z1, mat, coll=coll)
        if sill > z0: box(name + '_sill', x0, ga, z0, x1, gb, sill, mat, coll=coll)
        if head < z1: box(name + '_head', x0, ga, head, x1, gb, z1, mat, coll=coll)
        xm = (x0 + x1) / 2
        box(name + '_glass', xm - 0.012, ga, sill, xm + 0.012, gb, head, MAT['glass'], coll=coll)
        box(name + '_fr', xm - 0.03, ga, sill, xm + 0.03, gb, sill + 0.025, MAT['bronze_dark'], coll=coll)
        box(name + '_fr', xm - 0.03, ga, head - 0.025, xm + 0.03, gb, head, MAT['bronze_dark'], coll=coll)
        cur = gb
    if yb > cur: box(name, x0, cur, z0, x1, yb, z1, mat, coll=coll)
    if skin:
        xs = (x0 - 0.02, x0) if skin_side < 0 else (x1, x1 + 0.02)
        cur = ya
        for (ga, gb) in sorted(gaps):
            if ga > cur: box(name + '_skin', xs[0], cur, z0 - 0.38, xs[1], ga, z1 + 0.42, skin, coll=coll)
            cur = gb
        if yb > cur: box(name + '_skin', xs[0], cur, z0 - 0.38, xs[1], yb, z1 + 0.42, skin, coll=coll)

def boolean_cut(obj, cutters):
    for c in cutters:
        m = obj.modifiers.new('cut', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = c; m.solver = 'EXACT'
        c.hide_render = True; c.hide_viewport = True
        c.display_type = 'WIRE'

# key plan rectangles (metres)
COURT = R(812, 468, 965, 603)
LIB_SKY = R(686, 668, 948, 738)
ENS_SKY = R(692, 486, 785, 535)
STAIR = R(1084, 663, 1222, 790)
KITCHEN = R(970, 336, 1158, 458)
DINING = R(970, 465, 1158, 595)
MAJLIS = R(978, 797, 1222, 918)
MASTER = R(487, 468, 668, 655)
BED2 = R(487, 752, 668, 918)
LIVING = R(812, 603, 962, 918)

def build_arch():
    m = MAT
    # ---------------- floor slab + finishes
    box('slab', X(470), Y(935), SLAB, X(1238), Y(452), 0 - 0.02, m['ceiling'])
    box('slab_k', X(955), Y(465), SLAB, X(1172), Y(322), -0.02, m['ceiling'])
    box('slab_s', X(1158), Y(935), SLAB, X(1238), Y(645), -0.02, m['ceiling'])
    # oak floor everywhere, travertine in wet rooms / courtyard (overlaid slightly above)
    fl = box('floor_oak', X(470), Y(935), -0.02, X(1238), Y(452), 0.0, m['oak'])
    flk = box('floor_oak_k', X(955), Y(465), -0.02, X(1172), Y(322), 0.0, m['oak'])
    for r in (COURT,):
        box('floor_trav_court', r[0], r[1], 0.0, r[2], r[3], 0.003, m['trav'])
    for name, r in (('ens', R(675, 468, 805, 555)), ('shw', R(487, 665, 590, 745)), ('wc', R(1088, 602, 1158, 655))):
        box('floor_trav_' + name, r[0], r[1], 0.0, r[2], r[3], 0.003, m['trav'])
    # stair void cut through slab + floor
    vc = box('void_cut', STAIR[0], STAIR[1], SLAB - 0.1, STAIR[2], STAIR[3], 0.1)
    for o in (fl, bpy.data.objects['slab'], bpy.data.objects['slab_s']):
        boolean_cut(o, [vc])

    # ---------------- exterior walls
    pl, ext = m['plaster'], m['plaster_ext']
    # WEST street facade, y 918..935 : piers + full height glass
    gaps = [(X(500), X(655)), (X(690), X(800)), (X(822), X(960)), (X(988), X(1210))]
    window_x_wall('w_west', X(470), X(1238), Y(935), Y(918), gaps, skin=ext, skin_side=-1)
    # NORTH end x 470..487
    window_y_wall('w_north', Y(935), Y(452), X(470), X(487), [(Y(905), Y(770)), (Y(630), Y(480))], skin=ext, skin_side=-1)
    # EAST main y 452..468 (x 470..970); courtyard back wall rises to parapet
    # master: high ribbon window above the headboard (morning light); ensuite: high window for privacy
    window_x_wall('w_east_m', X(470), X(675), Y(468), Y(452), [(X(500), X(655))], sill=2.2, head=2.9, skin=ext, skin_side=1)
    window_x_wall('w_east_e', X(675), X(812), Y(468), Y(452), [(X(692), X(790))], sill=1.55, head=3.0, skin=ext, skin_side=1)
    box('w_east_court', X(805), Y(468), 0, X(970), Y(452), ROOF + 0.2, pl)
    box('w_east_court_skin', X(805), Y(452), SLAB, X(970), Y(452) + 0.02, ROOF + 0.2, ext)
    # kitchen block
    window_y_wall('w_kn', Y(452), Y(322), X(955), X(970), [], skin=ext, skin_side=-1)
    window_x_wall('w_ke', X(955), X(1172), Y(336), Y(322), [(X(985), X(1145))], sill=0.95, head=2.45, skin=ext, skin_side=1)
    window_y_wall('w_ks', Y(600), Y(322), X(1158), X(1172), [(Y(440), Y(358)), (Y(582), Y(476))], skin=ext, skin_side=1)
    # fix kitchen part of that glazing: sill for the kitchen window over the counter
    # south block
    box('w_se', X(1158), Y(660), 0, X(1238), Y(645), H, pl)
    box('w_se_skin', X(1158), Y(645), SLAB, X(1238), Y(645) + 0.02, ROOF, ext)
    window_y_wall('w_south', Y(935), Y(645), X(1222), X(1238), [(Y(905), Y(810)), (Y(785), Y(668))], skin=ext, skin_side=1)

    # ---------------- interior walls (plaster)
    W = lambda *a, **k: wallpx('wi', *a, **k)
    W(487, 655, 668, 665)                       # master | shower/hall
    W(590, 665, 598, 745)                       # shower | bed2 entry
    W(487, 745, 505, 752); W(545, 745, 598, 752)  # shower | bed2 (door 505-545)
    # spine x 668..675
    W(668, 468, 675, 600); W(668, 650, 675, 675); W(668, 720, 675, 918)
    box('door_head', X(668), Y(650), 2.7, X(675), Y(600), H, pl); box('door_head', X(668), Y(720), 2.7, X(675), Y(675), H, pl)
    # ensuite/dressing block
    W(805, 468, 812, 660)
    W(675, 555, 760, 560); W(800, 555, 805, 560); box('dh', X(760), Y(560), 2.7, X(800), Y(555), H, pl)
    W(675, 655, 760, 665); W(800, 655, 805, 665); box('dh', X(760), Y(665), 2.7, X(800), Y(655), H, pl)
    # study
    W(675, 745, 745, 752); W(785, 745, 812, 752); box('dh', X(745), Y(752), 2.7, X(785), Y(745), H, pl)
    W(805, 752, 812, 918)
    # library back wall (the shelves sit on it) is the line y 660..665 between x 805 and 812 -> nothing extra
    # courtyard glazing (full height) on two sides
    window_x_wall('court_s', X(812), X(965), Y(603), Y(598), [(X(814), X(963))])
    window_y_wall('court_e', Y(603), Y(468), X(962), X(967), [(Y(600), Y(470))])
    # kitchen | dining wall with glass slider
    W(970, 458, 1045, 465); W(1120, 458, 1158, 465)
    box('slider_head', X(1045), Y(465), 2.7, X(1120), Y(458), H, pl)
    box('slider', X(1045), Y(462) - 0.01, 0, X(1120), Y(462) + 0.01, 2.7, m['glass'])
    box('slider_fr', X(1045), Y(462) - 0.02, 0, X(1047), Y(462) + 0.02, 2.7, m['bronze_dark'])
    box('slider_fr', X(1118), Y(462) - 0.02, 0, X(1120), Y(462) + 0.02, 2.7, m['bronze_dark'])
    # guest WC
    W(1080, 600, 1088, 610); W(1080, 645, 1088, 655); box('dh', X(1080), Y(645), 2.7, X(1088), Y(610), H, pl)
    W(1080, 595, 1158, 602)
    W(1080, 655, 1158, 660)
    # flush WC door (plaster coloured, hidden frame)
    box('wc_door', X(1082), Y(645), 0, X(1086), Y(610), 2.7, m['plaster'])
    # majlis | stair void : full-height glass
    box('majlis_glass', X(1084), Y(792) - 0.012, 0, X(1222), Y(792) + 0.012, H, m['glass'])
    box('majlis_glass_fr', X(1084), Y(792) - 0.03, 0, X(1222), Y(792) + 0.03, 0.03, m['bronze_dark'])
    # stair void west edge: glass balustrade
    box('void_glass', X(1082), Y(790), 0, X(1084), Y(663), 1.1, m['glass'])
    box('void_cap', X(1081.5), Y(790), 1.1, X(1084.5), Y(663), 1.12, m['bronze'])
    box('void_glass2', X(1084), Y(665), 0, X(1222), Y(663), 1.1, m['glass'])

    # ---------------- ceiling + roof with openings
    ceil = box('ceiling', X(470), Y(935), H, X(1238), Y(452), H + 0.02, m['ceiling'])
    ceil_k = box('ceiling_k', X(955), Y(465), H, X(1172), Y(322), H + 0.02, m['ceiling'])
    roof = box('roof', X(470) - 0.05, Y(935) - 0.05, H + 0.02, X(1238) + 0.05, Y(452) + 0.02, ROOF, m['plaster_ext'])
    roof_k = box('roof_k', X(955), Y(465), H + 0.02, X(1172) + 0.02, Y(322) - 0.02, ROOF, m['plaster_ext'])
    cutters = []
    for nm, r, z in (('c_court', COURT, 0), ('c_lib', LIB_SKY, 0), ('c_ens', ENS_SKY, 0), ('c_stair', STAIR, 0)):
        cutters.append(box(nm, r[0], r[1], H - 0.1, r[2], r[3], ROOF + 0.5))
    # skylight upstands + glass (solar-control)
    sky_glass = glass('skyglass', '#EDF2F0', 0.0)
    for nm, r in (('s_lib', LIB_SKY), ('s_ens', ENS_SKY), ('s_stair', STAIR)):
        box(nm + '_up1', r[0] - 0.1, r[1] - 0.1, ROOF, r[2] + 0.1, r[1], ROOF + 0.25, m['plaster_ext'])
        box(nm + '_up2', r[0] - 0.1, r[3], ROOF, r[2] + 0.1, r[3] + 0.1, ROOF + 0.25, m['plaster_ext'])
        box(nm + '_up3', r[0] - 0.1, r[1], ROOF, r[0], r[3], ROOF + 0.25, m['plaster_ext'])
        box(nm + '_up4', r[2], r[1], ROOF, r[2] + 0.1, r[3], ROOF + 0.25, m['plaster_ext'])
        box(nm + '_glass', r[0], r[1], ROOF + 0.22, r[2], r[3], ROOF + 0.245, sky_glass)
        # plaster reveal down to ceiling
        for (a, b, c, d) in ((r[0], r[1] + 0.001, r[2], r[1] + 0.02), (r[0], r[3] - 0.02, r[2], r[3] - 0.001), (r[0] + 0.001, r[1], r[0] + 0.02, r[3]), (r[2] - 0.02, r[1], r[2] - 0.001, r[3])):
            box(nm + '_rev', a, b, H, c, d, ROOF, m['ceiling'])
    for o in (ceil, roof):
        boolean_cut(o, cutters)
    # courtyard reveal
    r = COURT
    box('court_rev_w', r[0], r[1] + 0.001, H, r[2], r[1] + 0.02, ROOF, m['plaster_ext'])
    box('court_rev_n', r[0] + 0.001, r[1], H, r[0] + 0.02, r[3], ROOF, m['plaster_ext'])
    box('court_rev_s', r[2] - 0.02, r[1], H, r[2] - 0.001, r[3], ROOF, m['plaster_ext'])
    # parapet + slim bronze roof edge
    box('parapet_w', X(470) - 0.05, Y(935) - 0.05, ROOF, X(1238) + 0.05, Y(935) + 0.15, ROOF + 0.18, m['plaster_ext'])
    box('roof_edge_w', X(470) - 0.06, Y(935) - 0.40, ROOF - 0.10, X(1238) + 0.06, Y(935) - 0.05, ROOF + 0.02, m['bronze'])
    box('parapet_n', X(470) - 0.05, Y(935), ROOF, X(470) + 0.15, Y(452) + 0.02, ROOF + 0.18, m['plaster_ext'])
    box('parapet_s', X(1238) - 0.15, Y(935), ROOF, X(1238) + 0.05, Y(645), ROOF + 0.18, m['plaster_ext'])
    box('parapet_e', X(470), Y(452) - 0.13, ROOF, X(955), Y(452) + 0.02, ROOF + 0.18, m['plaster_ext'])

    # ---------------- vertical bronze fins over the whole west facade
    x = X(485)
    while x < X(1224):
        box('fin', x, Y(935) - 0.40, SLAB - 0.05, x + 0.06, Y(935) - 0.12, ROOF - 0.10, m['bronze'], bevel=0.004, seg=1)
        x += 0.35
    box('fin_bracket', X(485), Y(935) - 0.12, SLAB - 0.05, X(1224), Y(935) - 0.02, SLAB + 0.05, m['bronze_dark'])
    # travertine band at the floor line
    box('trav_band', X(470) - 0.05, Y(935) - 0.08, SLAB - 0.12, X(1238) + 0.05, Y(935) + 0.01, 0.02, m['trav'])

def build_ground():
    """the parents' house below, the entry court, hall shell, street"""
    m = MAT
    ext = m['plaster_ext']
    # parents' ground floor mass (under first floor + north wing)
    # (the new entrance hall X 12.52..16.0, Y 0..5.85 is carved out)
    box('gf_mass', X(470), Y(935), GF - 0.4, 12.52, Y(340), SLAB, ext)
    box('gf_mass2', 12.52, 5.85, GF - 0.4, X(1238) - 0.6, Y(340), SLAB, ext)
    box('gf_north', X(50), Y(720), GF - 0.4, X(470), Y(345), SLAB + 0.2, ext)
    box('gf_north_par', X(50), Y(720), SLAB + 0.2, X(470), Y(720) + 0.15, SLAB + 0.5, ext)
    # garage + store pavilion reaching to the street (north end)
    box('garage', X(50), Y(1120), GF - 0.4, X(470), Y(720), GF + 3.3, ext)
    box('garage_door', X(290), Y(1120) - 0.02, GF, X(450), Y(1120), GF + 2.5, m['bronze_dark'])
    # parents' ground floor windows on the west face (a few dark openings with glass)
    for (a, b) in ((X(500), X(640)), (X(700), X(830)), (X(880), X(1010))):
        box('gf_win', a, Y(935) - 0.01, GF + 0.9, b, Y(935) + 0.02, GF + 2.6, plain('gf_glass', '#2D2B28', rough=0.05, spec=0.9))
    # first floor roof parapet of parents north wing
    # ---- entry court (plan sheet 2)
    def X2(px): return 12.72 + (px - 657) / 89.6
    def Y2(py): return -(py - 780) / 89.6
    court_y0 = Y2(1165)  # street wall line
    box('court_wall_n', X2(640), court_y0, GF - 0.1, X2(658), -0.001, GF + 2.5, ext)
    box('court_wall_s', X2(972) - 0.0, court_y0, GF - 0.1, X2(972) + 0.2, -0.001, GF + 2.5, ext)
    box('gf_fill_s', 16.0, 0.0, GF - 0.4, 16.69, 4.4, SLAB, ext)
    box('gf_fill_s2', 16.0, 5.2, GF - 0.4, 16.69, 6.0, SLAB, ext)
    # street wall with own gate (bronze, flush)
    gate0, gate1 = X2(680), X2(790)
    box('street_wall_a', X(50), court_y0 - 0.2, GF - 0.1, gate0, court_y0, GF + 2.5, ext)
    box('street_wall_b', gate1, court_y0 - 0.2, GF - 0.1, X2(972) + 0.2, court_y0, GF + 2.5, ext)
    box('street_wall_c', X2(972) + 0.2, court_y0 - 0.2, GF - 0.1, 16.7, court_y0, GF + 2.5, ext)
    box('gate', gate0, court_y0 - 0.17, GF + 0.02, gate1, court_y0 - 0.03, GF + 2.45, m['bronze'])
    box('gate_pull', gate1 - 0.12, court_y0 - 0.20, GF + 0.7, gate1 - 0.10, court_y0 - 0.17, GF + 1.6, m['bronze_dark'])
    box('wall_cap', X(50), court_y0 - 0.22, GF + 2.5, 16.7, court_y0 + 0.02, GF + 2.53, m['trav'])
    # house number, backlit
    box('number_plate', gate1 + 0.25, court_y0 - 0.22, GF + 1.55, gate1 + 0.55, court_y0 - 0.20, GF + 1.9, m['bronze'])
    # court floor: gravel + travertine stepping stones
    box('court_gravel', X2(658), court_y0, GF - 0.05, X2(972), 0, GF + 0.0, m['gravel'])
    zz = GF + 0.012
    y = court_y0 + 0.35
    while y < -0.2:
        box('step_stone', X2(690), y, GF - 0.02, X2(765), y + 0.42, zz, m['trav'], bevel=0.008, seg=2)
        y += 0.58
    # canopy (first floor slab extended) with oak soffit + light strip
    box('canopy', X2(658), Y2(908), SLAB - 0.05, X2(972), 0.0, SLAB + 0.12, ext)
    box('canopy_soffit', X2(658) + 0.02, Y2(908) + 0.02, SLAB - 0.07, X2(972) - 0.02, 0.0, SLAB - 0.05, textured('oak_slat', 'oak', 4.0))
    # pivot door 1.1 x 2.7 smoked oak + long bronze pull
    d0, d1 = X2(690), X2(690) + 1.1
    box('door_jamb', d0 - 0.08, -0.04, GF, d0, 0.0, GF + 2.7, m['trav'])
    box('door_jamb', d1, -0.04, GF, d1 + 0.08, 0.0, GF + 2.7, m['trav'])
    box('door_headt', d0 - 0.08, -0.04, GF + 2.7, d1 + 0.08, 0.0, GF + 2.78, m['trav'])
    box('pivot_door', d0 + 0.005, -0.03, GF, d1 - 0.005, 0.03, GF + 2.7, m['smoked'], bevel=0.003, seg=1)
    box('door_pull', d1 - 0.16, -0.06, GF + 0.6, d1 - 0.13, -0.02, GF + 2.1, m['bronze'], bevel=0.005, seg=2)
    # water basin: travertine rim + water
    bx0, by0, bx1, by1 = X2(820), Y2(886), X2(945), Y2(806)
    box('basin_rim', bx0, by0, GF, bx1, by1, GF + 0.40, m['trav'], bevel=0.01, seg=2)
    box('basin_water', bx0 + 0.06, by0 + 0.06, GF + 0.30, bx1 - 0.06, by1 - 0.06, GF + 0.37, m['water'])
    # olive tree planter (gravel bed) + tree
    tree(X2(890), Y2(1015), GF, height=4.4, crown_r=1.05, trunk_r=0.13, seed=5, leaves=26000, crown_squash=0.7)
    return court_y0, X2

def build_street(court_y0):
    m = MAT
    box('sidewalk', -30, court_y0 - 2.2, GF - 0.25, 45, court_y0 - 0.2, GF - 0.1, m['paving'])
    box('kerb', -30, court_y0 - 2.35, GF - 0.3, 45, court_y0 - 2.2, GF - 0.1, m['trav'])
    box('road', -30, court_y0 - 14, GF - 0.45, 45, court_y0 - 2.35, GF - 0.25, m['asphalt'])
    box('sidewalk_far', -30, court_y0 - 16.0, GF - 0.25, 45, court_y0 - 14, GF - 0.1, m['paving'])
    # front garden (parents) between facade and street wall
    box('garden', X(470), court_y0, GF - 0.1, 12.53, 0, GF - 0.02, plain('lawn', '#7D8460', rough=0.95, bumpimg='wool_bump.png', bumpscale=0.05, bumpstr=1.5, noise_var=0.15))
    # neighbours (south + north + opposite) to give the street context
    box('nb_s', 16.7, court_y0, GF - 0.4, 30, 14, GF + 6.8, m['neighbour'])
    box('nb_s_wall', 16.7, court_y0 - 0.2, GF - 0.1, 30, court_y0 - 0.01, GF + 2.2, m['neighbour'])
    box('nb_n', -30, court_y0, GF - 0.4, X(50) - 0.2, 14, GF + 7.4, m['neighbour'])
    box('opp', -30, court_y0 - 26, GF - 0.4, 45, court_y0 - 16.2, GF + 7.0, m['neighbour'])
    # street trees on the sidewalk
    for i, xx in enumerate((-4.5, 1.5, 7.5, 18.5, 24.5)):
        tree(xx, court_y0 - 1.2, GF - 0.1, height=5.2, crown_r=1.9, trunk_r=0.13, seed=20 + i, kind='street', leaves=22000, crown_squash=0.75)
    # parents' garden shrubs peeking over the street wall
    for i, xx in enumerate((0.8, 3.2, 5.9, 8.4, 10.9)):
        tree(xx, court_y0 + 1.0, GF - 0.05, height=3.3, crown_r=1.0, trunk_r=0.05, seed=40 + i, kind='street', leaves=9000, crown_squash=0.9)
    # neighbour detail: dark window openings + parapet lines
    win = plain('nb_win', '#3A3733', rough=0.1, spec=0.8)
    for xx in (18.0, 21.5, 25.0):
        for zz in (GF + 3.8,):
            box('nb_s_win', xx, court_y0 - 0.02, zz, xx + 1.6, court_y0, zz + 1.8, win)
    box('nb_s_par', 16.7, court_y0 - 0.06, GF + 6.6, 30, court_y0, GF + 6.8, m['trav'])
    for xx in (-12.0, -16.0, -20.0):
        box('nb_n_win', xx, court_y0 - 0.02, GF + 4.0, xx + 1.4, court_y0, GF + 5.8, win)
        box('pit', xx - 0.6, court_y0 - 1.8, GF - 0.1, xx + 0.6, court_y0 - 0.6, GF - 0.09, m['gravel'])

MAT = None

def init():
    global MAT
    MAT = M()
    return MAT
