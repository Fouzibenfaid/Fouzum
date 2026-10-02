import sys, os, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import house as Hh
from house import X, Y, R, H
import furnish as F

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')

def portal_west(xa, xb):
    area('portal', ((xa + xb) / 2, -0.3, H / 2), xb - xa, 1.0, rot=(math.pi / 2, 0, 0), size_y=H, portal=True)

def portal_roof(r):
    area('portal_r', ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, Hh.ROOF + 0.3), r[2] - r[0], 1.0, size_y=r[3] - r[1], portal=True)

def build_common(rooms, eve):
    Hh.build_arch()
    cy, X2 = Hh.build_ground()
    Hh.build_street(cy)
    for r in rooms:
        getattr(F, r)(eve=eve)
    return cy

def day_sky(elev=26, az=255, strength=1.0, sun=4.5):
    return sky(strength, elev, az, sun=True, sun_strength=sun, sun_angle=0.8)

def dusk_sky():
    s, sun = sky(0.5, -1.5, 285, sun=False)
    return s

SHOTS = {}
def shot(f): SHOTS[f.__name__] = f; return f

@shot
def living_day(q):
    build_common(['living', 'library', 'courtyard', 'dining_kitchen', 'majlis'], False)
    day_sky(24, 252)
    portal_west(X(822), X(960)); portal_roof(Hh.LIB_SKY); portal_roof(Hh.COURT)
    camera((11.75, 3.55, 1.30), (7.4, 0.95, 1.30), lens=20, shift_y=-0.08)
    return -0.3

@shot
def living_eve(q):
    build_common(['living', 'library', 'courtyard', 'dining_kitchen', 'majlis'], True)
    dusk_sky()
    camera((11.75, 3.55, 1.30), (7.4, 0.95, 1.30), lens=20, shift_y=-0.08)
    return 0.2


ALL = ['living', 'library', 'courtyard', 'dining_kitchen', 'majlis', 'master', 'ensuite', 'hall', 'arrival', 'bedroom2', 'study']

@shot
def library_day(q):
    build_common(['living', 'library', 'courtyard', 'dining_kitchen'], False)
    day_sky(24, 252)
    portal_west(X(822), X(960)); portal_roof(Hh.LIB_SKY); portal_roof(Hh.COURT)
    camera((9.55, 4.75, 1.35), (4.4, 5.05, 1.35), lens=20, shift_y=0.02)
    return -0.3

@shot
def courtyard_day(q):
    build_common(['living', 'library', 'courtyard', 'dining_kitchen', 'arrival'], False)
    day_sky(58, 160, sun=5.0)
    portal_west(X(822), X(960)); portal_roof(Hh.LIB_SKY); portal_roof(Hh.COURT)
    for o in [o for o in bpy.data.objects if o.name.startswith('court_s_glass') or o.name.startswith('court_s_fr')]:
        bpy.data.objects.remove(o, do_unlink=True)
    camera((8.0, 4.6, 1.35), (9.0, 9.6, 1.6), lens=20, shift_y=0.06)
    return -0.4

@shot
def kitchen_day(q):
    build_common(['living', 'courtyard', 'dining_kitchen', 'arrival', 'majlis'], False)
    day_sky(40, 150, sun=5.0)
    portal_roof(Hh.COURT)
    area('portal_s', (X(1172) + 0.3, (Y(582) + Y(476)) / 2, H / 2), Y(476) - Y(582), 1.0, rot=(0, -math.pi / 2, 0), size_y=H, portal=True)
    for o in [o for o in bpy.data.objects if o.name.startswith('court_e_glass') or o.name.startswith('court_e_fr')]:
        bpy.data.objects.remove(o, do_unlink=True)
    camera((9.05, 7.3, 1.45), (14.4, 8.45, 1.35), lens=20, shift_y=-0.04)
    return -0.3

@shot
def majlis_eve(q):
    build_common(['living', 'majlis', 'arrival'], True)
    dusk_sky()
    camera((14.85, 2.8, 1.4), (10.8, 0.8, 0.95), lens=18)
    return 0.2

@shot
def master_day(q):
    build_common(['master', 'ensuite', 'library'], False)
    day_sky(30, 75, sun=4.0)
    camera((3.85, 6.08, 1.4), (1.3, 9.4, 1.2), lens=19)
    return -0.2

@shot
def master_eve(q):
    build_common(['master', 'ensuite', 'library'], True)
    dusk_sky()
    camera((3.85, 6.08, 1.4), (1.3, 9.4, 1.2), lens=19)
    return 0.3

@shot
def ensuite_day(q):
    build_common(['master', 'ensuite'], False)
    day_sky(60, 120, sun=5.0)
    portal_roof(Hh.ENS_SKY)
    camera((6.85, 8.12, 1.5), (4.4, 9.55, 1.35), lens=16)
    return -0.2

@shot
def hall_day(q):
    build_common(['hall', 'majlis', 'arrival'], False)
    day_sky(62, 200, sun=5.0)
    portal_roof(Hh.STAIR)
    camera((13.35, 0.55, Hh.GF + 1.55), (14.3, 5.6, Hh.GF + 1.55), lens=15, shift_y=0.2)
    return 1.3

def street_cam():
    camera((2.6, -17.5, Hh.GF + 1.65), (10.4, 0, Hh.GF + 1.65), lens=24, shift_y=0.12)

@shot
def street_day(q):
    build_common(ALL, False)
    day_sky(22, 205, strength=0.7, sun=7.0)
    street_cam()
    return -1.35

@shot
def street_dusk(q):
    build_common(ALL, True)
    dusk_sky()
    street_cam()
    exterior_night_lights()
    return 0.6

def exterior_night_lights():
    GF = Hh.GF
    X2 = lambda px: 12.72 + (px - 657) / 89.6
    # wall washers on the entry court walls + uplight on the olive + canopy strip + backlit number
    for xx in (13.0, 14.0, 15.0, 16.0):
        spot('washer', (xx, -4.0, GF + 2.45), (math.radians(30), 0, 0), 25, 2700, 70)
    spot('olive_up', (X2(890) + 0.4, -2.2, GF + 0.05), (math.radians(-165), math.radians(-15), 0), 160, 2700, 45)
    led_strip('canopy_strip', (X2(660), Y2c() + 0.05, Hh.SLAB - 0.09), (X2(970), Y2c() + 0.05, Hh.SLAB - 0.09), 18, 2700)
    point('number_glow', (X2(790) + 0.4, -4.55, GF + 1.72), 3, 2700, 0.05)
    point('gate_glow', (X2(735), -4.0, GF + 2.0), 6, 2700, 0.2)
    # soft grazers either side of the gate on the street face
    for xx in (X2(680) - 0.5, X2(790) + 0.9):
        spot('graze', (xx, -4.75, GF + 0.02), (math.radians(172), 0, 0), 30, 2700, 35, 0.8)

def Y2c():
    return -(908 - 780) / 89.6

@shot
def entry_eve(q):
    build_common(['hall'], True)
    dusk_sky()
    exterior_night_lights()
    camera((12.95, -4.1, Hh.GF + 1.6), (14.05, 0, Hh.GF + 1.6), lens=19, shift_y=0.14)
    return 0.6

if __name__ == '__main__':
    name = sys.argv[1]; q = sys.argv[2] if len(sys.argv) > 2 else 'preview'
    reset(); Hh.init()
    t = time.time()
    exp = SHOTS[name](q)
    if q == 'preview':
        render_settings(800, 500, 48, exposure=exp)
    elif q == 'mid':
        render_settings(1280, 800, 160, exposure=exp)
    else:
        render_settings(1600, 1000, 144, exposure=exp)
    print('build', round(time.time() - t, 1))
    render(os.path.join(OUT, f'{name}_{q}.png'))
    print('done', round(time.time() - t, 1))
