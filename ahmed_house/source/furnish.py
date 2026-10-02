import bpy, math, random, bmesh
from mathutils import Vector
from lib import *
import house as Hh
from house import X, Y, R, H

def curtain(xa, xb, y, z0=0.02, z1=None, folds=None, mat=None, axis='x', amp=0.05, gather=1.0, name='curtain'):
    """ceiling hung sheer linen curtain as a wavy sheet. axis='x' runs along X at constant y"""
    z1 = (H - 0.02) if z1 is None else z1
    L = abs(xb - xa)
    folds = folds or max(3, int(L / 0.14))
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    nu, nv = folds * 8, 12
    grid = []
    rng = random.Random(int(xa * 100))
    for i in range(nu + 1):
        t = i / nu
        row = []
        for j in range(nv + 1):
            v = j / nv
            off = amp * math.sin(t * folds * 2 * math.pi) * (0.85 + 0.3 * v)
            s = min(xa, xb) + t * L
            z = z0 + v * (z1 - z0)
            row.append(bm.verts.new((s, y + off, z) if axis == 'x' else (y + off, s, z)))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o)
    me.materials.append(mat or sheer())
    for f in me.polygons: f.use_smooth = True
    return o

def sheer():
    from lib import _mats
    if 'sheer' in _mats: return _mats['sheer']
    m, nt, p = new_mat('sheer')
    nt.nodes.remove(p)
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent'); tl.inputs['Color'].default_value = col('#F2ECE2')
    df = nt.nodes.new('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = col('#EFE8DD')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    a = nt.nodes.new('ShaderNodeMixShader'); a.inputs[0].default_value = 0.5
    nt.links.new(df.outputs[0], a.inputs[1]); nt.links.new(tl.outputs[0], a.inputs[2])
    b = nt.nodes.new('ShaderNodeMixShader'); b.inputs[0].default_value = 0.45
    nt.links.new(a.outputs[0], b.inputs[1]); nt.links.new(tr.outputs[0], b.inputs[2])
    nt.links.new(b.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    m.surface_render_method = 'BLENDED' if hasattr(m, 'surface_render_method') else None
    _mats['sheer'] = m
    return m

def woven():
    from lib import _mats
    if 'woven' in _mats: return _mats['woven']
    m, nt, p = new_mat('woven')
    p.inputs['Base Color'].default_value = col('#C8AE84'); p.inputs['Roughness'].default_value = 0.8
    mp = box_mapping(nt, 0.03, rot=math.radians(45))
    w = nt.nodes.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'; w.inputs['Scale'].default_value = 1.0
    w2 = nt.nodes.new('ShaderNodeTexWave'); w2.wave_type = 'BANDS'; w2.bands_direction = 'Y'; w2.inputs['Scale'].default_value = 1.0
    nt.links.new(mp.outputs[0], w.inputs['Vector']); nt.links.new(mp.outputs[0], w2.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
    nt.links.new(w.outputs['Fac'], mx.inputs[0]); nt.links.new(w2.outputs['Fac'], mx.inputs[1])
    bn = nt.nodes.new('ShaderNodeBump'); bn.inputs['Strength'].default_value = 0.6
    nt.links.new(mx.outputs[0], bn.inputs['Height']); nt.links.new(bn.outputs['Normal'], p.inputs['Normal'])
    _mats['woven'] = m
    return m

def dining_chair(x, y, rot):
    """oak frame chair with woven paper-cord seat"""
    m = Hh.MAT
    e = bpy.data.objects.new('chair', None); link(e)
    parts = []
    lw = 0.035
    for (a, b) in ((-0.21, -0.20), (0.21, -0.20), (-0.21, 0.20), (0.21, 0.20)):
        top = 0.45 if b < 0 else 0.80
        parts.append(box('leg', a - lw / 2, b - lw / 2, 0, a + lw / 2, b + lw / 2, top, m['oak_light'], bevel=0.008, seg=2))
    parts.append(box('seatfr', -0.23, -0.22, 0.42, 0.23, 0.22, 0.46, m['oak_light'], bevel=0.008, seg=2))
    parts.append(cushion('seat', -0.21, -0.20, 0.44, 0.21, 0.20, 0.47, woven(), soft=0.01))
    parts.append(box('backrail', -0.23, 0.17, 0.66, 0.23, 0.22, 0.79, m['oak_light'], bevel=0.015, seg=3))
    for p in parts: p.parent = e
    e.location = (x, y, 0); e.rotation_euler = (0, 0, rot)
    return e

def side_table_round(x, y, r=0.24, h=0.5, mat=None):
    m = Hh.MAT
    cyl('st_top', x, y, h - 0.03, h, r, mat or m['trav'], bevel=0.004)
    cyl('st_stem', x, y, 0.02, h - 0.03, 0.10, mat or m['trav'])
    cyl('st_base', x, y, 0, 0.02, r * 0.7, mat or m['trav'], bevel=0.004)

def tray_set(x, y, z, rot=0.0):
    """bronze tray with a dallah-like coffee pot and cups (majlis)"""
    m = Hh.MAT
    cyl('tray', x, y, z, z + 0.015, 0.22, m['bronze'], bevel=0.004)
    lathe('dallah', [(0.0, 0), (0.07, 0), (0.08, 0.04), (0.05, 0.12), (0.035, 0.16), (0.06, 0.20), (0.03, 0.27), (0.012, 0.30)], x - 0.08, y, z + 0.015, m['bronze'])
    for i in range(3):
        a = i * 2.1 + rot
        lathe('cup', [(0.0, 0), (0.018, 0), (0.025, 0.012), (0.03, 0.045)], x + 0.10 + 0.05 * math.cos(a), y + 0.05 * math.sin(a), z + 0.015, m['ceramic'])

def tv_wall_living():
    m = Hh.MAT
    x0, x1 = 10.02, 10.34
    ya, yb = Y(762) + 0.5, Y(625)
    # fluted smoked oak wall: slats
    box('tvw_back', x0 + 0.04, ya, 0, x1, yb, H, m['smoked'])
    yy = ya
    while yy < yb - 0.03:
        box('tvw_slat', x0, yy, 0.0, x0 + 0.04, yy + 0.035, H, m['smoked'], bevel=0.006, seg=2)
        yy += 0.05
    # niche + tv
    ty0, ty1 = ya + 0.45, ya + 1.95
    box('tv_niche', x0 - 0.01, ty0 - 0.08, 0.98, x0 + 0.03, ty1 + 0.08, 1.98, m['black'])
    box('tv', x0 - 0.03, ty0, 1.04, x0 - 0.005, ty1, 1.89, m['tv'])
    # long low travertine shelf with bio-ethanol fire
    box('tv_shelf', x0 - 0.45, ya + 0.05, 0.0, x0, yb - 0.05, 0.38, m['trav'], bevel=0.006, seg=2)
    fy0, fy1 = yb - 1.25, yb - 0.35
    box('fire_slot', x0 - 0.33, fy0, 0.36, x0 - 0.12, fy1, 0.385, m['black'])
    return (x0, ya, yb, fy0, fy1)

def fire(x0, fy0, fy1, on=True):
    if not on: return
    # flame: emissive wavy sheet
    flame = emissive('flame', (1.0, 0.45, 0.12), 25.0)
    me = bpy.data.meshes.new('flame'); bm = bmesh.new()
    n = 24
    for i in range(n):
        t = i / n
        yy = fy0 + 0.04 + t * (fy1 - fy0 - 0.08)
        h = 0.12 + 0.07 * abs(math.sin(t * 17)) + 0.04 * math.sin(t * 41)
        w = (fy1 - fy0 - 0.08) / n * 0.9
        v = [bm.verts.new((x0 - 0.225, yy, 0.385)), bm.verts.new((x0 - 0.225, yy + w, 0.385)), bm.verts.new((x0 - 0.225, yy + w * 0.5, 0.385 + h))]
        bm.faces.new(v)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('flame', me); link(o); me.materials.append(flame)
    point('fire_l', (x0 - 0.35, (fy0 + fy1) / 2, 0.55), 60, 1900, 0.2)

def living(eve=False):
    m = Hh.MAT
    # L sofa in oatmeal boucle (long leg along the street glass, short leg along the study wall)
    sofa_run(9.6, 1.42, 2.35, 1.0, math.pi, m['boucle'], arms=(True, False), name='sofa_long')
    sofa_run(8.32, 1.42, 1.95, 1.0, math.pi / 2, m['boucle'], arms=(False, True), name='sofa_short')
    rug(7.45, 0.62, 10.0, 3.75, 0, m['wool'])
    # pillows
    throw_pillow(9.15, 0.62, 0.42, 0.5, 0.5, mat=m['linen_sand'], rot=math.radians(4), tilt=-0.3)
    throw_pillow(8.65, 0.62, 0.42, 0.45, 0.45, mat=m['terracotta_fab'], rot=math.radians(-6), tilt=-0.28)
    throw_pillow(7.62, 1.70, 0.42, 0.5, 0.5, mat=m['linen_olive'], rot=math.radians(90 + 5), tilt=-0.3)
    throw_pillow(7.62, 2.25, 0.42, 0.45, 0.45, mat=m['linen'], rot=math.radians(90 - 4), tilt=-0.28)
    # boucle throw over the arm
    cushion('throw', 7.75, 3.15, 0.40, 8.2, 3.35, 0.60, m['linen_sand'], soft=0.03, puff=0.01)
    # travertine block coffee tables (two staggered blocks)
    box('ct1', 8.55, 1.95, 0.0, 9.55, 2.75, 0.32, m['trav'], bevel=0.01, seg=3)
    box('ct2', 9.25, 2.55, 0.0, 9.85, 3.15, 0.26, m['trav'], bevel=0.01, seg=3)
    stack_books(8.85, 2.25, 0.32, 3, random.Random(11), rot=0.2)
    vase(9.25, 2.45, 0.32, 2, m['stoneware_dark'], s=0.8)
    for i in range(5):
        sphere('olive_fruit', 9.25 + 0.04 * math.cos(i * 1.3), 2.45 + 0.04 * math.sin(i * 1.3), 0.36, 0.022, m['linen_olive'], sx=1, sy=0.8, sz=0.7)
    vase(9.6, 2.85, 0.26, 1, m['stoneware'], s=0.9)
    branch_sprig(9.6, 2.85, 0.6, 0.55, seed=4)
    # lounge chair (real model, retinted to boucle) + pouf
    import_glb('SheenChair', (7.75, 6.35, 0), math.radians(200), 1.12, recolor={'fabric': m['boucle'], 'wood': m['oak'], 'metal': m['bronze'], 'label': m['boucle']})
    import_glb('SpecularSilkPouf', (8.15, 3.95, 0), 0, 0.9, recolor={'silk': m['wool_sand']})
    floor_lamp(7.55, 3.75, on=eve)
    # indoor olive tree in terracotta pot by the glass
    lathe('pot_big', [(0.0, 0), (0.20, 0), (0.27, 0.10), (0.29, 0.55), (0.27, 0.58)], 9.98, 0.72, 0, m['terracotta'])
    cyl('pot_soil', 9.98, 0.72, 0.50, 0.55, 0.26, m['soil'])
    # (placed next to the sofa end, by the pier)
    tree(9.98, 0.72, 0.55, height=1.75, crown_r=0.55, trunk_r=0.03, seed=12, leaves=9000, crown_squash=0.9)
    # curtains: sheer linen, ceiling hung, on the living glass
    curtain(X(822) + 0.02, X(845), Y(918) + 0.10, amp=0.04)
    curtain(X(935), X(960) - 0.02, Y(918) + 0.10, amp=0.04)
    # TV wall
    x0, ya, yb, fy0, fy1 = tv_wall_living()
    fire(x0, fy0, fy1, on=eve)
    vase(9.75, ya + 2.45, 0.38, 3, m['stoneware'], s=0.9)
    vase(9.78, ya + 2.75, 0.38, 0, m['stoneware_dark'], s=0.75)
    stack_books(9.8, yb - 0.1 - 0.3, 0.38, 2, random.Random(5))
    # cove ceiling over the sitting area: dropped plaster panel with LED up-light
    cove(7.18, 0.36, 10.34, 3.95, eve)
    box('cove_beam', 7.18, 3.95 - 0.135, H - 0.215, 10.34, 3.95 - 0.003, H, m['ceiling'])
    # plant on library side
    potted_plant(7.4, 4.25, 0, 1.3, 0.5)
    # large textured linen artwork above the sofa (on the study wall)
    box('lv_art_frame', 7.18, 1.45, 1.05, 7.215, 3.15, 2.25, m['oak_light'], bevel=0.004, seg=1)
    box('lv_art', 7.215, 1.5, 1.10, 7.22, 3.10, 2.20, plain('lv_canvas', '#DDD1BE', rough=0.95, bumpimg='linen_bump.png', bumpscale=0.06, bumpstr=0.4))
    box('lv_art_m1', 7.22, 1.75, 1.30, 7.223, 2.45, 1.95, plain('lv_m1', '#A8714F', rough=0.95, bumpimg='wool_bump.png', bumpscale=0.1, bumpstr=0.5))
    box('lv_art_m2', 7.22, 2.35, 1.55, 7.224, 2.85, 2.05, plain('lv_m2', '#7C7A5A', rough=0.95, bumpimg='wool_bump.png', bumpscale=0.1, bumpstr=0.5))

def cove(x0, y0, x1, y1, on, drop=0.22):
    """perimeter cove: slim plaster ledge along the top of the walls, LED on top washing the ceiling"""
    m = Hh.MAT
    d = 0.14   # ledge depth
    z0 = H - drop
    box('cove_ledge', x0, y0, z0, x1, y0 + d, z0 + 0.05, m['ceiling'])
    box('cove_ledge', x0, y1 - d, z0, x1, y1, z0 + 0.05, m['ceiling'])
    box('cove_ledge', x0, y0 + d, z0, x0 + d, y1 - d, z0 + 0.05, m['ceiling'])
    box('cove_ledge', x1 - d, y0 + d, z0, x1, y1 - d, z0 + 0.05, m['ceiling'])
    # upstand lip hides the strip
    box('cove_lip', x0 + d - 0.012, y0 + d - 0.012, z0 + 0.05, x1 - d + 0.012, y0 + d, z0 + 0.09, m['ceiling'])
    box('cove_lip', x0 + d - 0.012, y1 - d, z0 + 0.05, x1 - d + 0.012, y1 - d + 0.012, z0 + 0.09, m['ceiling'])
    box('cove_lip', x0 + d - 0.012, y0 + d, z0 + 0.05, x0 + d, y1 - d, z0 + 0.09, m['ceiling'])
    box('cove_lip', x1 - d, y0 + d, z0 + 0.05, x1 - d + 0.012, y1 - d, z0 + 0.09, m['ceiling'])
    if on:
        z = z0 + 0.055
        k = 2700
        pw = 10.0
        for (a, b) in (((x0 + 0.1, y0 + 0.07), (x1 - 0.1, y0 + 0.07)), ((x0 + 0.1, y1 - 0.07), (x1 - 0.1, y1 - 0.07))):
            led_strip('cove', (*a, z), (*b, z), pw, k, rot=(math.pi, 0, 0))
        for (a, b) in (((x0 + 0.07, y0 + 0.1), (x0 + 0.07, y1 - 0.1)), ((x1 - 0.07, y0 + 0.1), (x1 - 0.07, y1 - 0.1))):
            led_strip('cove', (*a, z), (*b, z), pw, k, rot=(math.pi, 0, 0))

def library(eve=False):
    m = Hh.MAT
    # oak shelving wall on the dressing wall side (faces -Y)
    xa, xb = X(678) + 0.05, X(805) - 0.02
    yb = Y(665)   # wall face
    ya = yb - 0.36
    box('shelf_back', xa, yb - 0.02, 0, xb, yb, H, m['oak'])
    nsec = 4
    secw = (xb - xa) / nsec
    for i in range(nsec + 1):
        xx = xa + i * secw
        box('shelf_side', xx - 0.015, ya, 0, xx + 0.015, yb, H - 0.0, m['oak'], bevel=0.003, seg=1)
    levels = [0.0, 0.45, 0.85, 1.25, 1.65, 2.05, 2.45, 2.85, H - 0.03]
    rng = random.Random(42)
    for z in levels:
        box('shelf', xa, ya, z, xb, yb, z + 0.03, m['oak'], bevel=0.003, seg=1)
    box('shelf_plinth', xa, ya + 0.02, 0, xb, yb, 0.45, m['oak'])
    for i in range(nsec):
        for z in levels[1:-1]:
            sx0 = xa + i * secw + 0.02
            if rng.random() < 0.25:
                # an object instead of a full run
                vase(sx0 + secw / 2, yb - 0.18, z + 0.03, rng.choice([0, 1, 3]), rng.choice([m['stoneware'], m['stoneware_dark'], m['terracotta']]), s=0.6)
                books(sx0, ya + 0.025, z + 0.03, secw * 0.35, rng=rng, facing=1)
            else:
                books(sx0, ya + 0.025, z + 0.03, secw * rng.uniform(0.55, 0.95), rng=rng, facing=1)
    # window seat on the opposite (study wall) side with cushions
    ys = Y(745) - 0.0
    box('seat_base', xa + 0.2, ys - 0.0, 0, xa + 2.4, ys + 0.55, 0.42, m['oak'], bevel=0.004, seg=2)
    cushion('seat_cush', xa + 0.22, ys + 0.02, 0.42, xa + 2.38, ys + 0.53, 0.52, m['linen_sand'], soft=0.03, puff=0.01)
    throw_pillow(xa + 0.55, ys + 0.10, 0.52, 0.45, 0.42, mat=m['linen'], rot=0, tilt=0.35)
    throw_pillow(xa + 1.05, ys + 0.10, 0.52, 0.42, 0.40, mat=m['terracotta_fab'], rot=0.08, tilt=0.35)
    stack_books(xa + 1.9, ys + 0.3, 0.52, 3, random.Random(9))
    # reading pendant (paper) over the seat
    paper_pendant(xa + 1.3, ys + 0.45, 2.15, 0.18, glow=(4.0 if eve else 0.0), light=(25 if eve else 0), wire_to=H)

def courtyard(eve=False):
    m = Hh.MAT
    x0, y0, x1, y1 = Hh.COURT
    cx, cy = X(885), Y(528)
    # planter: travertine square with gravel top
    box('planter', cx - 0.75, cy - 0.75, 0, cx + 0.75, cy + 0.75, 0.45, m['trav'], bevel=0.01, seg=2)
    box('planter_soil', cx - 0.65, cy - 0.65, 0.40, cx + 0.65, cy + 0.65, 0.44, m['gravel'])
    tree(cx, cy, 0.44, height=4.3, crown_r=1.35, trunk_r=0.15, seed=7, leaves=36000, crown_squash=0.7)
    # built-in travertine bench along the back wall
    box('court_bench', x0 + 0.1, y1 - 0.48, 0, x1 - 0.1, y1, 0.42, m['trav'], bevel=0.008, seg=2)
    cushion('court_cush', x0 + 0.4, y1 - 0.46, 0.42, x0 + 1.4, y1 - 0.04, 0.48, m['linen_sand'], soft=0.02)
    # gravel drainage strip
    box('court_gravel', x0, y0 + 0.05, 0.0, x1, y0 + 0.30, 0.008, m['gravel'])
    vase(x1 - 0.5, y1 - 0.25, 0.42, 3, m['terracotta'], s=1.1)
    if eve:
        spot('tree_up', (cx + 0.5, cy - 0.5, 0.46), (math.radians(160), math.radians(-20), 0), 80, 2700, 50)

def dining_kitchen(eve=False):
    m = Hh.MAT
    # island: travertine with waterfall ends
    ix0, iy0, ix1, iy1 = X(988), Y(528), X(1097), Y(485)
    box('island_top', ix0, iy0, 0.88, ix1, iy1, 0.92, m['trav'], bevel=0.004, seg=2)
    box('island_wf1', ix0, iy0, 0, ix0 + 0.04, iy1, 0.88, m['trav'], bevel=0.003, seg=1)
    box('island_wf2', ix1 - 0.04, iy0, 0, ix1, iy1, 0.88, m['trav'], bevel=0.003, seg=1)
    box('island_body', ix0 + 0.04, iy0 + 0.05, 0.08, ix1 - 0.04, iy1, 0.88, m['smoked'])
    box('island_kick', ix0 + 0.04, iy0 + 0.1, 0, ix1 - 0.04, iy1, 0.08, m['black'])
    # stools-free clean island; bowl of fruit + vase
    vase((ix0 + ix1) / 2 - 0.4, (iy0 + iy1) / 2, 0.92, 2, m['ceramic'], s=1.0)
    for i in range(6):
        sphere('lemon', (ix0 + ix1) / 2 - 0.4 + 0.06 * math.cos(i), (iy0 + iy1) / 2 + 0.06 * math.sin(i), 0.97, 0.035, plain('lemon', '#D9B33D', rough=0.4), sx=1.2, sy=1, sz=1)
    vase((ix0 + ix1) / 2 + 0.5, (iy0 + iy1) / 2 + 0.1, 0.92, 1, m['stoneware'], s=0.8)
    branch_sprig((ix0 + ix1) / 2 + 0.5, (iy0 + iy1) / 2 + 0.1, 1.25, 0.6, seed=8)
    # dining table oak 2.4 x 1.0, chairs
    tx0, ty0, tx1, ty1 = X(1000), Y(580), X(1113), Y(535)
    box('table_top', tx0, ty0, 0.72, tx1, ty1, 0.76, textured('oak_table', 'oak', 3.6, rot=1.5708), bevel=0.006, seg=3)
    for (a, b) in ((tx0 + 0.25, ty0 + 0.1), (tx1 - 0.25, ty0 + 0.1)):
        box('table_leg', a - 0.05, b, 0, a + 0.05, ty1 - 0.1, 0.72, m['oak'], bevel=0.006, seg=2)
    tcx, tcy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    for i in range(3):
        xx = tx0 + 0.45 + i * (tx1 - tx0 - 0.9) / 2
        dining_chair(xx, ty0 - 0.12, math.pi)
        dining_chair(xx, ty1 + 0.12, 0)
    dining_chair(tx0 - 0.15, tcy, math.pi / 2)
    dining_chair(tx1 + 0.15, tcy, -math.pi / 2)
    vase(tcx, tcy, 0.76, 0, m['stoneware'], s=0.9)
    branch_sprig(tcx, tcy, 1.02, 0.5, seed=3)
    import_glb('GlassHurricaneCandleHolder', (tcx - 0.55, tcy + 0.05, 0.76), 0, 1.0, recolor={'-glass': m['glass']})
    import_glb('GlassHurricaneCandleHolder', (tcx + 0.55, tcy - 0.05, 0.76), 0, 0.8, recolor={'-glass': m['glass']})
    # three paper globe pendants
    gl = 5.0 if eve else 0.0; li = 45 if eve else 0
    paper_pendant(ix0 + 0.65, (iy0 + iy1) / 2, 1.95, 0.19, glow=gl, light=li, wire_to=H)
    paper_pendant(ix1 - 0.65, (iy0 + iy1) / 2, 1.95, 0.19, glow=gl, light=li, wire_to=H)
    paper_pendant(tcx, tcy, 1.82, 0.30, glow=gl, light=li * 1.6, wire_to=H)
    # kitchen behind glass: smoked oak runs, travertine worktop, tall wall
    kx0, ky0, kx1, ky1 = KITCHEN = Hh.KITCHEN
    box('k_run', kx0 + 0.05, ky1 - 0.62, 0.1, kx1 - 0.05, ky1, 0.88, m['smoked'])
    box('k_top', kx0 + 0.05, ky1 - 0.64, 0.88, kx1 - 0.05, ky1, 0.92, m['trav'])
    box('k_kick', kx0 + 0.05, ky1 - 0.55, 0, kx1 - 0.05, ky1, 0.1, m['black'])
    box('k_tall', kx1 - 0.75, ky0 + 0.05, 0, kx1 - 0.05, ky1 - 0.64, 2.6, m['smoked'])
    box('k_shelf', kx0 + 0.3, ky1 - 0.28, 1.55, kx1 - 1.0, ky1, 1.59, m['oak'])
    for i in range(4):
        vase(kx0 + 0.6 + i * 0.35, ky1 - 0.15, 1.59, [0, 3, 1, 0][i], [m['ceramic'], m['stoneware'], m['stoneware_dark'], m['ceramic']][i], s=0.55)
    box('k_hob', kx0 + 1.2, ky1 - 0.55, 0.92, kx0 + 1.9, ky1 - 0.05, 0.925, m['black'])
    box('k_sink', kx0 + 2.4, ky1 - 0.5, 0.905, kx0 + 3.1, ky1 - 0.1, 0.921, m['steel'])
    if eve:
        led_strip('kled', (kx0 + 0.3, ky1 - 0.2, 1.545), (kx1 - 1.0, ky1 - 0.2, 1.545), 10, 2700, rot=(0, 0, 0))

def majlis(eve=False, walls_open=1.0):
    m = Hh.MAT
    x0, y0, x1, y1 = Hh.MAJLIS
    # low deep L seating in sand linen (along the street glass + the south wall)
    def seat(xa, ya, xb, yb, back_side):
        box('mj_base', xa, ya, 0, xb, yb, 0.10, m['oak'], bevel=0.004, seg=2)
        cushion('mj_seat', xa + 0.01, ya + 0.01, 0.10, xb - 0.01, yb - 0.01, 0.30, m['linen_sand'], soft=0.04, puff=0.02)
    seat(x0 + 0.05, y0 + 0.05, x1 - 0.05, y0 + 0.85, 'y')
    seat(x1 - 0.85, y0 + 0.85, x1 - 0.05, y1 - 0.25, 'x')
    # back cushions
    nx = int((x1 - x0 - 0.9) / 0.75)
    for i in range(nx):
        xa = x0 + 0.1 + i * 0.75
        cushion('mj_back', xa, y0 + 0.06, 0.30, xa + 0.72, y0 + 0.28, 0.80, m['linen'], soft=0.06, puff=0.03)
    ny = int((y1 - y0 - 1.1) / 0.75)
    for i in range(ny):
        ya = y0 + 0.9 + i * 0.75
        cushion('mj_back', x1 - 0.28, ya, 0.30, x1 - 0.06, ya + 0.72, 0.80, m['linen'], soft=0.06, puff=0.03)
    throw_pillow(x0 + 1.2, y0 + 0.35, 0.33, 0.45, 0.45, mat=m['terracotta_fab'], tilt=-0.35)
    throw_pillow(x1 - 0.4, y0 + 1.3, 0.33, 0.45, 0.45, mat=m['linen_olive'], rot=math.pi / 2, tilt=-0.35)
    rug(x0 + 0.9, y0 + 0.9, x1 - 0.9, y1 - 0.1, 0, m['wool_sand'])
    tcx, tcy = (x0 + x1) / 2 + 0.3, (y0 + y1) / 2 + 0.15
    box('mj_table', tcx - 0.6, tcy - 0.45, 0, tcx + 0.6, tcy + 0.45, 0.30, m['trav'], bevel=0.01, seg=3)
    tray_set(tcx, tcy, 0.30)
    import_glb('IridescentDishWithOlives', (tcx + 0.35, tcy - 0.2, 0.30), 0, 0.55, remove=('glassCover',))
    # sliding oak walls (to living at x~970 and to arrival at y~792)
    sx = X(972)
    if walls_open >= 1.0:
        sx = None
    if sx is not None:
      box('mj_slide1', sx - 0.03, y0, 0, sx + 0.03, y0 + (y1 - y0) * (1 - walls_open), 2.9, m['oak'], bevel=0.003, seg=1)
      box('mj_slide1b', sx - 0.09, y1 - 0.2, 0, sx - 0.03, y1 + 0.0, 2.9, m['oak'], bevel=0.003, seg=1)
    # curtains on the street glass
    curtain(X(990), X(1020), Y(918) + 0.10, amp=0.04)
    potted_plant(x1 - 0.5, y1 - 0.0 - 0.25, 0, 1.2, 1.0)
    cove(x0, y0, x1, y1, eve)
    if eve:
        wall_light(x1 - 0.02, y0 + 1.6, 1.9, math.pi / 2, on=True)

def bed(x0, y0, x1, y1, m):
    """platform bed: oak base on recessed plinth, mattress, linen bedding, pillows, folded throw. head at y1"""
    box('bed_plinth', x0 + 0.15, y0 + 0.15, 0, x1 - 0.15, y1 - 0.1, 0.10, m['black'])
    box('bed_base', x0, y0, 0.10, x1, y1, 0.32, m['oak'], bevel=0.008, seg=2)
    cushion('mattress', x0 + 0.05, y0 + 0.05, 0.32, x1 - 0.05, y1 - 0.05, 0.56, m['sheet'], soft=0.05, puff=0.01)
    # duvet covering most of the bed, turned down at the top
    cushion('duvet', x0 + 0.02, y0 + 0.02, 0.50, x1 - 0.02, y1 - 0.55, 0.62, m['linen'], soft=0.06, puff=0.03)
    cushion('duvet_fold', x0 + 0.03, y1 - 0.75, 0.58, x1 - 0.03, y1 - 0.55, 0.66, m['sheet'], soft=0.05, puff=0.02)
    # throw across the foot
    cushion('bed_throw', x0 - 0.04, y0 + 0.05, 0.56, x1 + 0.04, y0 + 0.65, 0.645, m['linen_sand'], soft=0.03, puff=0.01)
    w = x1 - x0
    for i, (mat, dz) in enumerate(((m['sheet'], 0.0), (m['sheet'], 0.0))):
        cx = x0 + w * (0.27 + 0.46 * i)
        throw_pillow(cx, y1 - 0.30, 0.50, 0.68, 0.48, 0.18, m['sheet'], rot=0, tilt=-0.30)
        throw_pillow(cx, y1 - 0.45, 0.52, 0.58, 0.40, 0.16, m['linen'], rot=0, tilt=-0.22)
    throw_pillow(x0 + w / 2, y1 - 0.55, 0.58, 0.55, 0.30, 0.14, m['terracotta_fab'], rot=0, tilt=-0.15)

def master(eve=False):
    m = Hh.MAT
    x0, y0, x1, y1 = X(487), Y(655), X(668), Y(468)   # 0.36..4.12 , 5.88..9.80
    bx0, bx1 = 1.12, 2.97
    # tall upholstered linen headboard wall panel spanning bed + side tables
    box('headboard_back', 0.52, y1 - 0.04, 0.0, 3.57, y1 - 0.01, 1.35, m['linen'])
    nch = 9; cw = (3.57 - 0.52) / nch
    for i in range(nch):
        cushion('headboard_ch', 0.52 + i * cw + 0.004, y1 - 0.13, 0.02, 0.52 + (i + 1) * cw - 0.004, y1 - 0.03, 1.33, m['linen'], soft=0.04, puff=0.015)
    bed(bx0, y1 - 2.30, bx1, y1 - 0.12, m)
    # floating oak side tables + plaster wall lights
    for sx in (0.62, 3.07):
        box('side_t', sx, y1 - 0.55, 0.42, sx + 0.42, y1 - 0.12, 0.54, m['oak'], bevel=0.006, seg=2)
        wall_light(sx + 0.21, y1 - 0.16, 1.62, math.pi, on=eve)
    stack_books(0.85, y1 - 0.35, 0.54, 2, random.Random(4))
    vase(3.25, y1 - 0.33, 0.54, 0, m['stoneware'], s=0.6)
    import_glb('DiffuseTransmissionTeacup', (0.95, y1 - 0.30, 0.58), 0.4, 0.9)
    # boucle bench at the foot of the bed
    cushion('bench', bx0 + 0.25, y1 - 2.95, 0.0, bx1 - 0.25, y1 - 2.50, 0.44, m['boucle'], soft=0.05, puff=0.01)
    rug(0.75, 6.35, 3.4, y1 - 0.9, 0, m['wool'])
    # lounge chair by the north window + floor lamp
    import_glb('SheenChair', (1.05, 6.55, 0), math.radians(-60), 1.12, recolor={'fabric': m['linen_sand'], 'wood': m['oak'], 'metal': m['bronze'], 'label': m['linen_sand']})
    floor_lamp(0.62, 6.15, on=eve)
    side_table_round(1.55, 6.25, 0.2, 0.45, m['trav'])
    import_glb('GlassVaseFlowers', (1.55, 6.25, 0.45), 0, 1.4)
    # full height linen curtains on the north window
    curtain(Y(905) if False else Y(630) + 0.02, Y(480) - 0.02, X(487) + 0.10, axis='y', amp=0.05, mat=m['linen'] if False else None)
    # art: large linen canvas on the south wall
    box('art_frame', 1.4, y0 + 0.0, 1.05, 2.9, y0 + 0.04, 2.15, m['oak_light'], bevel=0.004, seg=1)
    box('art_canvas', 1.45, y0 + 0.04, 1.10, 2.85, y0 + 0.045, 2.10, plain('canvas', '#D8CCB8', rough=0.9, bumpimg='linen_bump.png', bumpscale=0.06, bumpstr=0.3))
    box('art_mark', 1.85, y0 + 0.045, 1.35, 2.35, y0 + 0.048, 1.85, plain('art_mark', '#9C6A4C', rough=0.9))
    potted_plant(3.75, 6.25, 0, 1.4, 2.0)
    cove(x0, y0, x1, y1, eve)

def ensuite(eve=False):
    m = Hh.MAT
    x0, y0, x1, y1 = X(675), Y(555), X(805), Y(468)   # 4.37..7.04 , 7.98..9.80
    # travertine walls in the wet room
    box('ens_wall_e', x0, y1 - 0.02, 0, x1, y1, H, m['travw'])
    box('ens_wall_n', x0, y0, 0, x0 + 0.02, y1, H, m['travw'])
    box('ens_wall_s', x1 - 0.02, y0, 0, x1, y1, H, m['travw'])
    # walk-in rain shower (south end) with glass screen
    box('shower_screen', x1 - 1.25, y0 + 0.05, 0, x1 - 1.24, y1 - 0.75, 2.2, m['glass'])
    cyl('rain_head', x1 - 0.62, (y0 + y1) / 2, 2.95, 2.96, 0.15, m['bronze'])
    cyl('rain_arm', x1 - 0.62, (y0 + y1) / 2, 2.96, H, 0.01, m['bronze'])
    box('shower_niche', x1 - 0.9, y1 - 0.021, 1.0, x1 - 0.35, y1 - 0.019, 1.3, m['stoneware_dark'])
    # floating vanity in smoked oak with travertine top, round bronze mirror
    box('vanity', x0 + 0.05, y1 - 0.55, 0.45, x0 + 1.35, y1 - 0.02, 0.80, m['smoked'], bevel=0.004, seg=1)
    box('vanity_top', x0 + 0.05, y1 - 0.56, 0.80, x0 + 1.35, y1 - 0.02, 0.84, m['trav'])
    lathe('basin', [(0.0, 0.0), (0.12, 0.0), (0.20, 0.03), (0.21, 0.13)], x0 + 0.7, y1 - 0.28, 0.84, m['stoneware'])
    cyl('tap', x0 + 0.7, y1 - 0.05, 1.05, 1.07, 0.015, m['bronze'])
    m_r = cyl('mirror', 0, 0, -0.01, 0.01, 0.38, m['mirror'], 64)
    m_r.location = (x0 + 0.7, y1 - 0.025, 1.55); m_r.rotation_euler = (math.pi / 2, 0, 0)
    ring = cyl('mirror_ring', 0, 0, -0.012, 0.012, 0.395, m['bronze'], 64)
    ring.location = (x0 + 0.7, y1 - 0.02, 1.55); ring.rotation_euler = (math.pi / 2, 0, 0)
    # bronze towel ladder leaning on the wall + draped towels
    for yy in (y0 + 0.35, y0 + 0.85):
        r = cyl('ladder', 0, 0, 0, 1.7, 0.012, m['bronze'], 12); r.location = (x0 + 0.17, yy, 0.85); r.rotation_euler = (0, math.radians(-6), 0)
    for zz in (0.55, 0.95, 1.35):
        r = cyl('rung', 0, 0, -0.25, 0.25, 0.008, m['bronze'], 10); r.location = (x0 + 0.20 - zz * 0.1, y0 + 0.6, zz); r.rotation_euler = (math.radians(90), 0, 0)
    cushion('towel1', x0 + 0.10, y0 + 0.40, 0.75, x0 + 0.17, y0 + 0.80, 1.38, m['linen_sand'], soft=0.02, puff=0.01)
    cushion('towel2', x0 + 0.15, y0 + 0.42, 0.40, x0 + 0.21, y0 + 0.78, 0.97, m['sheet'], soft=0.02, puff=0.01)
    # teak stool in the shower, toiletries in the niche, tray on the vanity
    box('niche_ledge', x1 - 0.9, y1 - 0.12, 0.97, x1 - 0.35, y1 - 0.02, 1.0, m['trav'])
    cyl('stool', x1 - 0.45, y0 + 0.4, 0, 0.45, 0.17, plain('teak', '#8A6243', rough=0.6), bevel=0.01)
    for i, c in enumerate(('#E8E1D5', '#6E5A48', '#D3C7B5')):
        lathe('bottle', [(0.0, 0), (0.03, 0), (0.032, 0.14), (0.012, 0.17), (0.012, 0.2)], x1 - 0.8 + i * 0.1, y1 - 0.05, 1.0, plain('bot' + c, c, rough=0.3, coat=0.4))
    box('vtray', x0 + 0.15, y1 - 0.45, 0.84, x0 + 0.45, y1 - 0.25, 0.852, m['trav'], bevel=0.003, seg=2)
    import_glb('DiffuseTransmissionPlant', (x0 + 1.15, y1 - 0.3, 0.84), 0, 0.45, remove=('firefly',))
    lathe('vessel', [(0.0, 0), (0.03, 0), (0.035, 0.08), (0.02, 0.12)], x0 + 0.2, y1 - 0.25, 0.84, m['stoneware_dark'])
    if eve:
        led_strip('vanity_led', (x0 + 0.1, y1 - 0.3, 0.44), (x0 + 1.3, y1 - 0.3, 0.44), 8, 2700, rot=(math.pi, 0, 0))

def hall(eve=False):
    m = Hh.MAT
    GF = Hh.GF
    hx0, hx1 = 12.72, 15.80
    hy0, hy1 = 0.30, 5.65
    # shell (inside the parents' mass we carve the hall with its own walls)
    box('hall_floor', hx0, hy0 - 0.3, GF - 0.02, hx1, hy1, GF, trav_tiles())
    box('hall_wall_n', hx0 - 0.2, hy0 - 0.29, GF, hx0, hy1 + 0.2, 0, m['plaster'])
    # south wall with a tall glass slot (continues the first floor stair glass)
    box('hall_wall_s', hx1, hy0 - 0.29, GF, hx1 + 0.2, 4.45, 0.0, m['plaster'])
    box('hall_wall_s', hx1, 5.15, GF, hx1 + 0.2, hy1 + 0.2, 0.0, m['plaster'])
    box('hall_slot', hx1 + 0.09, 4.45, GF, hx1 + 0.11, 5.15, 0.0, m['glass'])
    box('hall_wall_back', hx0 - 0.2, hy1, GF, hx1 + 0.2, hy1 + 0.2, Hh.ROOF, m['travw'])
    d0, d1 = 12.72 + (690 - 657) / 89.6, 12.72 + (690 - 657) / 89.6 + 1.1
    box('hall_front', hx0 - 0.2, 0.0, GF, d0 - 0.06, hy0, GF + 3.35, m['plaster'])
    box('hall_front', d1 + 0.06, 0.0, GF, hx1 + 0.2, hy0, GF + 3.35, m['plaster'])
    box('hall_front', d0 - 0.06, 0.0, GF + 2.76, d1 + 0.06, hy0, GF + 3.35, m['plaster'])
    # door opening in front wall (door leaf is built with the court); cut by re-building pieces
    # low ceiling at the door, then the void
    box('hall_ceiling', hx0, hy0, GF + 3.32, hx1, 3.05, GF + 3.34, m['ceiling'])
    # north wall above the low ceiling up to FF (void side)
    # built-in smoked oak wall: coats / shoes / keys with oak bench niche
    box('hall_joinery', hx0, 0.9, GF, hx0 + 0.42, 4.6, GF + 2.7, m['smoked'], bevel=0.003, seg=1)
    box('hall_niche', hx0 + 0.30, 1.6, GF + 0.45, hx0 + 0.43, 3.6, GF + 1.65, m['black'])
    box('hall_bench', hx0 + 0.0, 1.6, GF + 0.40, hx0 + 0.55, 3.6, GF + 0.46, m['oak'], bevel=0.004, seg=2)
    cushion('hall_bench_cush', hx0 + 0.05, 2.4, GF + 0.46, hx0 + 0.52, 3.5, GF + 0.52, m['linen_sand'], soft=0.02)
    for k in range(5):
        box('hook', hx0 + 0.40, 1.8 + k * 0.4, GF + 1.85, hx0 + 0.48, 1.82 + k * 0.4, GF + 1.87, m['bronze'])
    # floating oak treads cantilevered from the south wall, glass on the open side
    n = 20
    rise = (0 - GF) / n
    go = (hy1 - 0.45 - (hy0 + 0.6)) / (n - 1)
    sx0, sx1 = hx1 - 1.2, hx1
    for i in range(n - 1):
        yy = hy0 + 0.6 + i * go
        z = GF + rise * (i + 1)
        box('tread', sx0, yy, z - 0.06, sx1, yy + go + 0.02, z, m['oak'], bevel=0.004, seg=2)
        if eve:
            led_strip('tread_led', (sx0 + 0.05, yy + 0.03, z - 0.065), (sx1 - 0.05, yy + 0.03, z - 0.065), 2.5, 2700, rot=(0, 0, 0))
    box('landing', hx0 + 0.15, hy1 - 0.45, -0.06, hx1, hy1, 0.0, m['oak'])
    # frameless glass balustrade following the stair pitch, slim bronze cap
    from mathutils import Matrix
    ya_, yb_ = hy0 + 0.6, hy1 - 0.45
    for (z0, z1, mat, nm) in ((0.0, 1.0, m['glass'], 'stair_glass'), (1.0, 1.02, m['bronze'], 'stair_cap')):
        pts = [(ya_, GF + rise + z0), (yb_, 0.0 + z0), (yb_, 0.0 + z1), (ya_, GF + rise + z1)]
        o = poly_extrude(nm, pts, 0, 0.02 if nm == 'stair_glass' else 0.04, mat)
        o.matrix_world = Matrix(((0, 0, 1, sx0 - 0.03), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    # art on the travertine feature wall, washed by the skylight
    box('hall_art', 13.3, hy1 - 0.03, GF + 1.2, 14.3, hy1, GF + 2.6, plain('hall_art', '#B8A588', rough=0.9, bumpimg='linen_bump.png', bumpscale=0.08, bumpstr=0.4))
    # large paper pendant hanging in the void
    paper_pendant(13.9, 4.3, GF + 3.6, 0.45, glow=(5.0 if eve else 0.6), light=(80 if eve else 0), shape='oval', wire_to=H)
    potted_plant(hx0 + 0.45, hy1 - 0.4, GF, 1.5, 0.3)
    vase(hx0 + 0.25, 1.15, GF + 0.0, 1, m['terracotta'], s=1.6)

def trav_tiles():
    from lib import _mats
    if 'trav_tiles' in _mats: return _mats['trav_tiles']
    m = textured('trav_tiles_base', 'trav', 1.6, bump=0.2)
    m = m.copy(); m.name = 'trav_tiles'
    nt = m.node_tree
    p = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    # 1.2 x 0.6 joints
    tc = nt.nodes.new('ShaderNodeTexCoord')
    brick = nt.nodes.new('ShaderNodeTexBrick')
    brick.inputs['Scale'].default_value = 1.0
    brick.inputs['Mortar Size'].default_value = 0.003
    brick.inputs['Brick Width'].default_value = 1.2
    brick.inputs['Row Height'].default_value = 0.6
    brick.offset = 0.5
    brick.inputs['Color1'].default_value = (1, 1, 1, 1); brick.inputs['Color2'].default_value = (0.96, 0.95, 0.93, 1)
    brick.inputs['Mortar'].default_value = (0.55, 0.5, 0.45, 1)
    nt.links.new(tc.outputs['Object'], brick.inputs['Vector'])
    src = p.inputs['Base Color'].links[0].from_socket
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    nt.links.new(src, mul.inputs[6]); nt.links.new(brick.outputs['Color'], mul.inputs[7])
    nt.links.new(mul.outputs[2], p.inputs['Base Color'])
    _mats['trav_tiles'] = m
    return m

def arrival(eve=False):
    """pivoting oak fins between living and arrival + console"""
    m = Hh.MAT
    for i in range(6):
        yy = Y(775) + 0.15 + i * 0.5
        f = box('pivot_fin', -0.04, -0.20, 0, 0.04, 0.20, H - 0.02, m['oak'], bevel=0.004, seg=2)
        f.location = (X(968), yy, 0); f.rotation_euler = (0, 0, math.radians(35))


def bedroom2(eve=False):
    m = Hh.MAT
    x0, y0, x1, y1 = Hh.BED2
    # bed with head on the north side wall? head against the shower wall (y1 side)
    bed(X(520), Y(885), X(590), Y(752) - 0.05, m)
    box('b2_side', X(592), Y(752) - 0.45, 0.42, X(592) + 0.4, Y(752) - 0.05, 0.52, m['oak'], bevel=0.005, seg=2)
    rug(X(505), Y(910), X(660), Y(790), 0, m['wool_sand'])
    curtain(X(500) + 0.02, X(655) - 0.02, Y(918) + 0.10, amp=0.04)
    potted_plant(X(650), Y(905), 0, 1.2, 0.7)
    cove(x0, y0, x1, y1, eve)
    if eve:
        floor_lamp(X(500) + 0.3, Y(905) + 0.2, on=True)

def study(eve=False):
    m = Hh.MAT
    x0, y0, x1, y1 = R(675, 752, 805, 918)
    box('desk', x0 + 0.1, y0 + 0.15, 0.72, x1 - 0.1, y0 + 0.85, 0.75, m['oak'], bevel=0.004, seg=2)
    box('desk_leg', x0 + 0.12, y0 + 0.2, 0, x0 + 0.16, y0 + 0.8, 0.72, m['bronze_dark'])
    box('desk_leg', x1 - 0.16, y0 + 0.2, 0, x1 - 0.12, y0 + 0.8, 0.72, m['bronze_dark'])
    dining_chair((x0 + x1) / 2, y0 + 1.15, 0)
    stack_books(x0 + 0.5, y0 + 0.5, 0.75, 3, random.Random(2))
    curtain(X(690) + 0.02, X(800) - 0.02, Y(918) + 0.10, amp=0.04)
    cove(x0, y0, x1, y1, eve)
    if eve:
        point('desk_lamp', (x1 - 0.4, y0 + 0.5, 1.1), 20, 2700, 0.05)
