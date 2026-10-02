import bpy, bmesh, math, random, os, mathutils
from mathutils import Vector, Matrix, Euler

ROOT = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(ROOT, 'assets', 'gen')
ASSETS = os.path.join(ROOT, 'assets')

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def col(h, a=1.0):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, a)

def kelvin(k):
    # approximate blackbody -> linear rgb
    t = k / 100
    r = 255 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0, min(255, v)) / 255 for v in (r, g, b)]
    c = [0.62 * v + 0.38 for v in c]  # temper: warm, not orange
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

# ---------------------------------------------------------------- materials
_mats = {}

def _img(path, noncolor=False):
    name = os.path.basename(path)
    im = bpy.data.images.get(name) or bpy.data.images.load(path)
    if noncolor:
        im.colorspace_settings.name = 'Non-Color'
    return im

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    return m, nt, p

def box_mapping(nt, scale, rot=0.0):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / scale, 1 / scale, 1 / scale)
    mp.inputs['Rotation'].default_value = (0, 0, rot)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp

def tex(nt, path, vec, noncolor=False, proj='BOX', blend=0.25):
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = _img(path, noncolor)
    t.projection = proj
    t.projection_blend = blend
    nt.links.new(vec.outputs['Vector'], t.inputs['Vector'])
    return t

def textured(name, base, size, tint=None, rough=None, bump=0.3, rot=0.0, spec=0.5, coat=0.0, use_world=False):
    """image texture material with box projection in object (or world) space"""
    if name in _mats: return _mats[name]
    m, nt, p = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / size,) * 3
    mp.inputs['Rotation'].default_value = (0, 0, rot)
    if use_world:
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
    else:
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    c = tex(nt, os.path.join(GEN, base + '_col.png'), mp)
    out = c.outputs['Color']
    if tint is not None:
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        mix.inputs[7].default_value = tint
        nt.links.new(out, mix.inputs[6]); out = mix.outputs[2]
    nt.links.new(out, p.inputs['Base Color'])
    rp = os.path.join(GEN, base + '_rough.png')
    if os.path.exists(rp) and rough is None:
        r = tex(nt, rp, mp, True)
        nt.links.new(r.outputs['Color'], p.inputs['Roughness'])
    else:
        p.inputs['Roughness'].default_value = rough if rough is not None else 0.6
    bp = os.path.join(GEN, base + '_bump.png')
    if os.path.exists(bp) and bump:
        b = tex(nt, bp, mp, True)
        bn = nt.nodes.new('ShaderNodeBump'); bn.inputs['Strength'].default_value = bump
        bn.inputs['Distance'].default_value = 0.002
        nt.links.new(b.outputs['Color'], bn.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Specular IOR Level'].default_value = spec
    p.inputs['Coat Weight'].default_value = coat
    _mats[name] = m
    return m

def plain(name, color, rough=0.5, metal=0.0, sheen=0.0, spec=0.5, bumpimg=None, bumpscale=0.05, bumpstr=0.3,
          sss=0.0, transmission=0.0, coat=0.0, emission=None, estr=0.0, aniso=0.0, noise_var=0.0):
    if name in _mats: return _mats[name]
    m, nt, p = new_mat(name)
    p.inputs['Base Color'].default_value = col(color) if isinstance(color, str) else color
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Sheen Weight'].default_value = sheen
    p.inputs['Sheen Roughness'].default_value = 0.6
    p.inputs['Specular IOR Level'].default_value = spec
    p.inputs['Subsurface Weight'].default_value = sss
    p.inputs['Transmission Weight'].default_value = transmission
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Anisotropic'].default_value = aniso
    if emission:
        p.inputs['Emission Color'].default_value = emission
        p.inputs['Emission Strength'].default_value = estr
    if noise_var:
        # subtle colour variation so large surfaces don't look CG-flat
        mp = box_mapping(nt, 1.0)
        n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 1.5
        n.inputs['Detail'].default_value = 6
        nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
        hsv = nt.nodes.new('ShaderNodeHueSaturation')
        hsv.inputs['Color'].default_value = p.inputs['Base Color'].default_value
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['To Min'].default_value = 1 - noise_var; mr.inputs['To Max'].default_value = 1 + noise_var
        nt.links.new(n.outputs['Fac'], mr.inputs['Value'])
        nt.links.new(mr.outputs['Result'], hsv.inputs['Value'])
        nt.links.new(hsv.outputs['Color'], p.inputs['Base Color'])
    if bumpimg:
        mp = box_mapping(nt, bumpscale)
        b = tex(nt, os.path.join(GEN, bumpimg), mp, True)
        bn = nt.nodes.new('ShaderNodeBump'); bn.inputs['Strength'].default_value = bumpstr
        bn.inputs['Distance'].default_value = 0.003
        nt.links.new(b.outputs['Color'], bn.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], p.inputs['Normal'])
    _mats[name] = m
    return m

def glass(name='glass', tint='#F4F8F6', rough=0.0):
    """architectural glass: lets shadow / diffuse rays straight through (no caustic blackout)"""
    if name in _mats: return _mats[name]
    m, nt, p = new_mat(name)
    nt.nodes.remove(p)
    out = nt.nodes['Material Output']
    g = nt.nodes.new('ShaderNodeBsdfGlass'); g.inputs['Color'].default_value = col(tint)
    g.inputs['Roughness'].default_value = rough; g.inputs['IOR'].default_value = 1.5
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = col(tint)
    lp = nt.nodes.new('ShaderNodeLightPath')
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
    nt.links.new(lp.outputs['Is Shadow Ray'], mx.inputs[0])
    nt.links.new(lp.outputs['Is Diffuse Ray'], mx.inputs[1])
    # thin glass: refraction looks wrong on a single plane -> mostly transparent + fresnel reflection
    fr = nt.nodes.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.5
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = rough
    thin = nt.nodes.new('ShaderNodeMixShader')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs['Backfacing'], inv.inputs[1])
    frm = nt.nodes.new('ShaderNodeMath'); frm.operation = 'MULTIPLY'
    nt.links.new(fr.outputs[0], frm.inputs[0]); nt.links.new(inv.outputs[0], frm.inputs[1])
    fr = frm
    nt.links.new(fr.outputs[0], thin.inputs[0]); nt.links.new(tr.outputs[0], thin.inputs[1]); nt.links.new(gl.outputs[0], thin.inputs[2])
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mx.outputs[0], mix.inputs[0]); nt.links.new(thin.outputs[0], mix.inputs[1]); nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    _mats[name] = m
    return m

def emissive(name, color, strength):
    if name in _mats: return _mats[name]
    m, nt, p = new_mat(name)
    nt.nodes.remove(p)
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1) if len(color) == 3 else color
    e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    _mats[name] = m
    return m

def paper(name='paper', glow=0.0, k=2700):
    """rice paper lantern: translucent + optional self glow"""
    key = f'{name}_{glow}'
    if key in _mats: return _mats[key]
    m, nt, p = new_mat(key)
    p.inputs['Base Color'].default_value = col('#F3EEE4')
    p.inputs['Roughness'].default_value = 0.8
    nt.nodes.remove(p)
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent'); tl.inputs['Color'].default_value = col('#F6EBD8')
    df = nt.nodes.new('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = col('#F3EEE4')
    mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.45
    nt.links.new(df.outputs[0], mx.inputs[1]); nt.links.new(tl.outputs[0], mx.inputs[2])
    final = mx
    if glow:
        e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*kelvin(k), 1)
        e.inputs['Strength'].default_value = glow
        add = nt.nodes.new('ShaderNodeAddShader')
        nt.links.new(mx.outputs[0], add.inputs[0]); nt.links.new(e.outputs[0], add.inputs[1])
        final = add
    nt.links.new(final.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    _mats[key] = m
    return m

def water():
    if 'water' in _mats: return _mats['water']
    m, nt, p = new_mat('water')
    p.inputs['Base Color'].default_value = col('#9AA79E'); p.inputs['Roughness'].default_value = 0.02
    p.inputs['Transmission Weight'].default_value = 0.9; p.inputs['IOR'].default_value = 1.33
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 6
    bn = nt.nodes.new('ShaderNodeBump'); bn.inputs['Strength'].default_value = 0.05
    nt.links.new(n.outputs['Fac'], bn.inputs['Height']); nt.links.new(bn.outputs['Normal'], p.inputs['Normal'])
    _mats['water'] = m
    return m

def M():
    """the house palette"""
    return dict(
        plaster=textured('plaster', 'plaster', 2.4, bump=0.25, rough=0.9, spec=0.3),
        plaster_ext=textured('plaster_ext', 'plaster', 3.0, tint=col('#F4EEE6'), bump=0.6, rough=0.92, spec=0.25),
        ceiling=plain('ceiling', '#EDE6DB', rough=0.9, spec=0.3),
        oak=textured('oak', 'oak', 1.8, spec=0.45, coat=0.0),
        oak_v=textured('oak_v', 'oak', 1.8, rot=0, spec=0.45),
        oak_light=textured('oak_light', 'oak', 1.2, tint=col('#FFF8EE'), spec=0.4),
        smoked=textured('smoked', 'smoked', 1.6, spec=0.4),
        trav=textured('trav', 'trav', 1.6, bump=0.2, spec=0.4),
        travw=textured('travw', 'travw', 2.8, bump=0.15, spec=0.4),
        trav_rough=textured('trav_rough', 'trav', 1.6, bump=0.8, spec=0.3, rough=0.8),
        bronze=plain('bronze', '#8E6E4E', rough=0.32, metal=1.0, aniso=0.3),
        bronze_dark=plain('bronze_dark', '#5E4632', rough=0.4, metal=1.0),
        boucle=plain('boucle', '#CFC1AA', rough=0.95, sheen=0.6, spec=0.2, bumpimg='boucle_bump.png', bumpscale=0.15, bumpstr=0.8),
        linen=plain('linen', '#E6DED0', rough=0.9, sheen=0.4, spec=0.2, bumpimg='linen_bump.png', bumpscale=0.08, bumpstr=0.25),
        linen_sand=plain('linen_sand', '#CDB89A', rough=0.9, sheen=0.4, spec=0.2, bumpimg='linen_bump.png', bumpscale=0.08, bumpstr=0.25),
        linen_olive=plain('linen_olive', '#7C7A5A', rough=0.9, sheen=0.5, spec=0.2, bumpimg='linen_bump.png', bumpscale=0.08, bumpstr=0.25),
        terracotta=plain('terracotta', '#B66A48', rough=0.85, spec=0.3, noise_var=0.08),
        terracotta_fab=plain('terracotta_fab', '#A95F40', rough=0.95, sheen=0.5, spec=0.2, bumpimg='linen_bump.png', bumpscale=0.08, bumpstr=0.3),
        wool=plain('wool', '#D9CCB6', rough=1.0, sheen=0.7, spec=0.15, bumpimg='wool_bump.png', bumpscale=0.25, bumpstr=1.0),
        wool_sand=plain('wool_sand', '#CDBEA5', rough=1.0, sheen=0.7, spec=0.15, bumpimg='wool_bump.png', bumpscale=0.25, bumpstr=1.0),
        sheet=plain('sheet', '#F2EEE7', rough=0.85, sheen=0.4, spec=0.2, bumpimg='linen_bump.png', bumpscale=0.06, bumpstr=0.15),
        black=plain('black', '#1E1C1A', rough=0.35, spec=0.5),
        tv=plain('tv', '#0A0A0B', rough=0.08, spec=0.8),
        chrome=plain('chrome', '#D8D6D2', rough=0.12, metal=1.0),
        steel=plain('steel', '#B8B6B2', rough=0.3, metal=1.0),
        ceramic=plain('ceramic', '#F1EEE8', rough=0.15, spec=0.6, coat=0.5),
        stoneware=plain('stoneware', '#D6CDBE', rough=0.6, spec=0.4, noise_var=0.06),
        stoneware_dark=plain('stoneware_dark', '#5B5249', rough=0.55, spec=0.4, noise_var=0.06),
        gravel=plain('gravel', '#CFC4B2', rough=0.95, bumpimg='wool_bump.png', bumpscale=0.08, bumpstr=2.0, noise_var=0.1),
        soil=plain('soil', '#4A3B2E', rough=1.0, bumpimg='wool_bump.png', bumpscale=0.1, bumpstr=1.0),
        bark=plain('bark', '#76685A', rough=0.95, bumpimg='wool_bump.png', bumpscale=0.05, bumpstr=2.0, noise_var=0.15),
        leaf=plain('leaf', '#6E7A55', rough=0.55, sss=0.0, spec=0.4),
        leaf_olive=plain('leaf_olive', '#8E9878', rough=0.45, spec=0.5, sheen=0.6),
        asphalt=plain('asphalt', '#4A4641', rough=0.9, bumpimg='wool_bump.png', bumpscale=0.05, bumpstr=0.6, noise_var=0.08),
        paving=plain('paving', '#BDB3A3', rough=0.85, noise_var=0.06),
        neighbour=plain('neighbour', '#E4DCCF', rough=0.9, bumpimg='plaster_bump.png', bumpscale=3.0, bumpstr=0.5, noise_var=0.05),
        glass=glass(),
        frosted=glass('frosted', '#F3F5F2', 0.35),
        mirror=plain('mirror', '#F0F0F0', rough=0.02, metal=1.0),
        book_paper=plain('book_paper', '#EFE8DA', rough=0.9),
        paper=paper(),
        water=water(),
    )

# ---------------------------------------------------------------- geometry
def link(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o)
    return o

def box(name, x0, y0, z0, x1, y1, z1, mat=None, bevel=0.0, seg=3, coll=None):
    if x0 > x1: x0, x1 = x1, x0
    if y0 > y1: y0, y1 = y1, y0
    if z0 > z1: z0, z1 = z1, z0
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = (v.co.x + 0.5) * (x1 - x0)
        v.co.y = (v.co.y + 0.5) * (y1 - y0)
        v.co.z = (v.co.z + 0.5) * (z1 - z0)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = (x0, y0, z0)
    link(o, coll)
    if mat: me.materials.append(mat)
    if bevel:
        b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = seg; b.limit_method = 'ANGLE'
        b.harden_normals = False
        for f in me.polygons: f.use_smooth = True
        try:
            me.set_sharp_from_angle(angle=math.radians(35))
        except Exception:
            pass
    return o

def cushion(name, x0, y0, z0, x1, y1, z1, mat, soft=0.04, puff=0.0, coll=None):
    """soft upholstered block: bevel + subdivision + slight crown"""
    o = box(name, x0, y0, z0, x1, y1, z1, mat, coll=coll)
    me = o.data
    # subdivide geometry so we can puff the top
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    if puff:
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        for v in bm.verts:
            u = (v.co.x / sx - 0.5) * 2; w = (v.co.y / sy - 0.5) * 2; h = (v.co.z / sz - 0.5) * 2
            f = (1 - u * u) * (1 - w * w) * (1 - h * h * 0.0)
            # bulge outward on all faces a bit
            if abs(h) > 0.99: v.co.z += puff * f * (1 if h > 0 else -0.3)
            if abs(u) > 0.99: v.co.x += puff * 0.5 * (1 - w * w) * (1 - h * h) * (1 if u > 0 else -1)
            if abs(w) > 0.99: v.co.y += puff * 0.5 * (1 - u * u) * (1 - h * h) * (1 if w > 0 else -1)
    bm.to_mesh(me); bm.free()
    b = o.modifiers.new('bev', 'BEVEL'); b.width = soft; b.segments = 4; b.limit_method = 'ANGLE'
    s = o.modifiers.new('sub', 'SUBSURF'); s.levels = 1; s.render_levels = 2
    for f in me.polygons: f.use_smooth = True
    return o

def cyl(name, x, y, z0, z1, r, mat=None, verts=48, r2=None, coll=None, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r if r2 is None else r2, depth=z1 - z0)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = (x, y, (z0 + z1) / 2); link(o, coll)
    if mat: me.materials.append(mat)
    for f in me.polygons: f.use_smooth = True
    if bevel:
        b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    return o

def sphere(name, x, y, z, r, mat=None, coll=None, sx=1, sy=1, sz=1):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=r); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = (x, y, z); o.scale = (sx, sy, sz); link(o, coll)
    if mat: me.materials.append(mat)
    for f in me.polygons: f.use_smooth = True
    return o

def lathe(name, profile, x, y, z, mat, seg=64, coll=None):
    """profile: list of (r, z) points -> revolved solid (vases, pots, bowls, lamps)"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), h)) for r, h in profile])
    for i in range(seg):
        A, B = rings[i], rings[(i + 1) % seg]
        for j in range(len(profile) - 1):
            bm.faces.new((A[j], B[j], B[j + 1], A[j + 1]))
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = (x, y, z); link(o, coll)
    me.materials.append(mat)
    for f in me.polygons: f.use_smooth = True
    sol = o.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.006
    return o

def poly_extrude(name, pts, z0, z1, mat, coll=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z0)) for x, y in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]:
        v.co.z = z1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o, coll)
    me.materials.append(mat)
    return o

def import_glb(name, loc=(0, 0, 0), rot=0.0, scale=1.0, tint=None, recolor=None, coll=None, remove=()):
    """import a real glTF model; tint multiplies base colour, recolor maps material name substring -> material"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, name + '.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    for o in list(new):
        if any(k.lower() in o.name.lower() for k in remove):
            new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    roots = [o for o in new if o.parent is None]
    holder = bpy.data.objects.new(name + '_root', None); link(holder, coll)
    for r in roots:
        r.parent = holder
    holder.location = loc; holder.rotation_euler = (0, 0, rot); holder.scale = (scale,) * 3
    for o in new:
        if coll and o.name in bpy.context.scene.collection.objects:
            pass
        if o.type == 'MESH':
            for i, ms in enumerate(o.material_slots):
                if not ms.material: continue
                if recolor:
                    for k, v in recolor.items():
                        if k.lower() in ms.material.name.lower():
                            ms.material = v
                if tint and ms.material.use_nodes:
                    _tint_material(ms.material, tint)
    return holder, new

def _tint_material(m, tint):
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            inp = n.inputs['Base Color']
            if inp.is_linked:
                src = inp.links[0].from_socket
                mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'COLOR'
                mix.inputs['Factor'].default_value = 1.0
                hsv = nt.nodes.new('ShaderNodeRGBToBW')
                nt.links.new(src, hsv.inputs[0])
                mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
                mul.inputs['Factor'].default_value = 1.0
                mul.inputs[7].default_value = tint
                # luminance * tint * 2 keeps texture detail but forces the colour
                sc = nt.nodes.new('ShaderNodeMath'); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 2.2
                nt.links.new(hsv.outputs[0], sc.inputs[0])
                cmb = nt.nodes.new('ShaderNodeCombineColor')
                for k in range(3): nt.links.new(sc.outputs[0], cmb.inputs[k])
                nt.links.new(cmb.outputs[0], mul.inputs[6])
                nt.links.new(mul.outputs[2], inp)
            else:
                inp.default_value = tint
            # sheen colour too
            if n.inputs['Sheen Weight'].default_value > 0 and not n.inputs['Sheen Tint'].is_linked:
                n.inputs['Sheen Tint'].default_value = (1, 1, 1, 1)

# ---------------------------------------------------------------- furniture
def books(x0, y, z, length, depth=0.22, rng=None, axis='x', facing=1, coll=None, lean_end=True):
    """a run of books along x (or y). spines face -y (facing=1) or +y"""
    rng = rng or random.Random(1)
    pal = ['#D9CDB8', '#B9A88C', '#8C7A62', '#5E5246', '#3E3A36', '#A7856A', '#7D7A68', '#9B6E52', '#4F5A55', '#6B4F3E', '#C4B08F', '#2F3A3A', '#8A8F7A', '#B07B5C']
    pos = 0.0
    while pos < length - 0.03:
        if rng.random() < 0.08 and pos > 0.1:
            pos += rng.uniform(0.05, 0.2); continue
        th = rng.uniform(0.018, 0.045)
        h = rng.uniform(0.19, 0.30)
        d = min(depth, rng.uniform(0.14, 0.22))
        c = rng.choice(pal)
        mat = plain('book_' + c, c, rough=rng.uniform(0.5, 0.85), sheen=0.2)
        if axis == 'x':
            b = box('book', x0 + pos, y, z, x0 + pos + th, y + d * facing, z + h, mat, bevel=0.002, seg=1, coll=coll)
        else:
            b = box('book', y, x0 + pos, z, y + d * facing, x0 + pos + th, z + h, mat, bevel=0.002, seg=1, coll=coll)
        pos += th + 0.001
    return pos

def stack_books(x, y, z, n=3, rng=None, rot=0.0, coll=None):
    rng = rng or random.Random(3)
    pal = ['#E8E0D0', '#BFAE92', '#6E655A', '#A27E62', '#D9CDB7', '#3F3B37']
    zz = z
    for i in range(n):
        w = rng.uniform(0.17, 0.26); d = rng.uniform(0.22, 0.30); t = rng.uniform(0.02, 0.04)
        c = rng.choice(pal)
        b = box('bk', -w / 2, -d / 2, 0, w / 2, d / 2, t, plain('book_' + c, c, rough=0.7, sheen=0.2), bevel=0.002, seg=1, coll=coll)
        b.location = (x, y, zz); b.rotation_euler = (0, 0, rot + rng.uniform(-0.15, 0.15))
        zz += t
    return zz

def vase(x, y, z, kind=0, mat=None, s=1.0, coll=None):
    profiles = [
        [(0.0, 0), (0.07, 0), (0.09, 0.05), (0.10, 0.12), (0.085, 0.2), (0.05, 0.26), (0.045, 0.30), (0.05, 0.31)],
        [(0.0, 0), (0.05, 0), (0.08, 0.04), (0.09, 0.08), (0.06, 0.13), (0.035, 0.18), (0.04, 0.40), (0.05, 0.42)],
        [(0.0, 0), (0.10, 0), (0.15, 0.04), (0.16, 0.08), (0.14, 0.12)],  # bowl
        [(0.0, 0), (0.06, 0), (0.12, 0.10), (0.13, 0.22), (0.10, 0.34), (0.06, 0.40), (0.065, 0.42)],
    ]
    pr = [(r * s, h * s) for r, h in profiles[kind]]
    return lathe('vase', pr, x, y, z, mat or M()['stoneware'], coll=coll)

def branch_sprig(x, y, z, h=0.7, seed=1, coll=None):
    """dried branches / olive sprig in a vase"""
    rng = random.Random(seed)
    leaf = M()['leaf_olive']
    stem = plain('stem', '#5A4A3A', rough=0.8)
    objs = []
    for i in range(5):
        ang = rng.uniform(0, 2 * math.pi); tilt = rng.uniform(0.05, 0.35)
        L = h * rng.uniform(0.7, 1.0)
        pts = []
        for k in range(8):
            t = k / 7
            pts.append((x + math.cos(ang) * math.sin(tilt) * L * t + 0.02 * math.sin(t * 6 + i),
                        y + math.sin(ang) * math.sin(tilt) * L * t, z + math.cos(tilt) * L * t))
        cu = bpy.data.curves.new('sprig', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.003
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for p, q in zip(sp.points, pts): p.co = (*q, 1)
        o = bpy.data.objects.new('sprig', cu); link(o, coll); cu.materials.append(stem)
        for k in range(2, 8):
            for side in (-1, 1):
                q = pts[k]
                lf = sphere('lf', q[0], q[1], q[2], 0.012, leaf, coll, sx=1, sy=3.2, sz=0.25)
                lf.rotation_euler = (rng.uniform(-1, 1), rng.uniform(-0.6, 0.6), ang + side * 1.0 + rng.uniform(-0.4, 0.4))
                lf.location.x += side * 0.015 * math.cos(ang + 1.57)
                lf.location.y += side * 0.015 * math.sin(ang + 1.57)

def throw_pillow(x, y, z, w=0.5, h=0.5, t=0.16, mat=None, rot=0.0, tilt=0.25, coll=None):
    o = cushion('pillow', -w / 2, -t / 2, -h / 2, w / 2, t / 2, h / 2, mat or M()['linen'], soft=0.05, puff=0.05, coll=coll)
    # pinch corners
    o.location = (x, y, z + h / 2 * math.cos(tilt)); o.rotation_euler = (tilt, 0, rot)
    return o

def sofa_run(x0, y0, length, depth=1.0, rot=0.0, mat=None, coll=None, seat_h=0.40, back_h=0.72, arms=(True, True), name='sofa'):
    """low modern sofa (along local +x, back at local +y). returns list of objects parented to an empty"""
    mat = mat or M()['boucle']
    e = bpy.data.objects.new(name, None); link(e, coll)
    parts = []
    plinth = box('plinth', 0.04, 0.04, 0.0, length - 0.04, depth - 0.04, 0.06, M()['black'], coll=coll)
    parts.append(plinth)
    base = cushion('base', 0, 0, 0.06, length, depth, 0.26, mat, soft=0.03, coll=coll); parts.append(base)
    armw = 0.20
    a0 = armw if arms[0] else 0; a1 = length - (armw if arms[1] else 0)
    n = max(1, round((a1 - a0) / 0.95))
    cw = (a1 - a0) / n
    for i in range(n):
        parts.append(cushion('seat', a0 + i * cw + 0.005, 0.02, 0.26, a0 + (i + 1) * cw - 0.005, depth - 0.22, seat_h + 0.02, mat, soft=0.05, puff=0.025, coll=coll))
        parts.append(cushion('backc', a0 + i * cw + 0.01, depth - 0.42, seat_h - 0.02, a0 + (i + 1) * cw - 0.01, depth - 0.12, back_h - 0.04, mat, soft=0.07, puff=0.04, coll=coll))
    parts.append(cushion('back', 0, depth - 0.16, 0.24, length, depth, back_h - 0.12, mat, soft=0.04, coll=coll))
    if arms[0]: parts.append(cushion('arm', 0, 0, 0.24, armw, depth, 0.56, mat, soft=0.06, puff=0.01, coll=coll))
    if arms[1]: parts.append(cushion('arm', length - armw, 0, 0.24, length, depth, 0.56, mat, soft=0.06, puff=0.01, coll=coll))
    for p in parts: p.parent = e
    e.location = (x0, y0, 0); e.rotation_euler = (0, 0, rot)
    return e

def rug(x0, y0, x1, y1, z=0.0, mat=None, coll=None):
    o = box('rug', x0, y0, z, x1, y1, z + 0.012, mat or M()['wool'], bevel=0.005, seg=2, coll=coll)
    return o

def paper_pendant(x, y, z, r=0.3, glow=6.0, light=40.0, k=2700, coll=None, shape='globe', wire_to=None):
    """Akari-style ribbed paper lantern with a warm bulb inside"""
    me = bpy.data.meshes.new('lantern')
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=40, radius=r)
    for v in bm.verts:
        lat = math.asin(max(-1, min(1, v.co.z / r)))
        rib = 1 + 0.018 * math.cos(lat * 40)
        if shape == 'oval': v.co.z *= 1.35
        v.co.x *= rib; v.co.y *= rib
    # open top / bottom
    for v in [v for v in bm.verts if abs(v.co.z) > r * (0.93 if shape == 'globe' else 1.25)]:
        bm.verts.remove(v)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('lantern', me); o.location = (x, y, z); link(o, coll)
    me.materials.append(paper('paper', glow, k))
    for f in me.polygons: f.use_smooth = True
    if light:
        L = bpy.data.lights.new('bulb', 'POINT'); L.energy = light; L.color = kelvin(k); L.shadow_soft_size = r * 0.4
        lo = bpy.data.objects.new('bulb', L); lo.location = (x, y, z); link(lo, coll)
    top = wire_to if wire_to is not None else z + 1.0
    cyl('cord', x, y, z + r * (0.9 if shape == 'globe' else 1.25), top, 0.003, M()['black'], 8, coll=coll)
    cyl('canopy', x, y, top - 0.02, top, 0.05, M()['ceiling'], coll=coll)
    return o

def area(name, loc, size, energy, color=(1, 1, 1), rot=(0, 0, 0), shape='RECTANGLE', size_y=None, portal=False, spread=180, coll=None):
    L = bpy.data.lights.new(name, 'AREA'); L.shape = shape; L.size = size
    if size_y: L.size_y = size_y
    L.energy = energy; L.color = color
    try: L.spread = math.radians(spread)
    except Exception: pass
    if portal:
        try: L.cycles.is_portal = True
        except Exception: pass
    o = bpy.data.objects.new(name, L); o.location = loc; o.rotation_euler = rot; link(o, coll)
    return o

def point(name, loc, energy, k=2700, r=0.05, coll=None):
    L = bpy.data.lights.new(name, 'POINT'); L.energy = energy; L.color = kelvin(k); L.shadow_soft_size = r
    o = bpy.data.objects.new(name, L); o.location = loc; link(o, coll)
    return o

def spot(name, loc, rot, energy, k=2700, angle=40, blend=0.6, r=0.03, coll=None):
    L = bpy.data.lights.new(name, 'SPOT'); L.energy = energy; L.color = kelvin(k)
    L.spot_size = math.radians(angle); L.spot_blend = blend; L.shadow_soft_size = r
    o = bpy.data.objects.new(name, L); o.location = loc; o.rotation_euler = rot; link(o, coll)
    return o

def led_strip(name, p0, p1, power_per_m=12.0, k=2700, rot=(0, 0, 0), width=0.02, coll=None):
    """linear LED as a thin area light (cove lighting)"""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    d = (p1 - p0).normalized()
    o = area(name, (p0 + p1) / 2, L, power_per_m * L, kelvin(k), shape='RECTANGLE', size_y=width, coll=coll)
    # orient: local x along strip, local -z is emission direction -> we pass rot as emission direction euler
    ang = math.atan2(d.y, d.x)
    o.rotation_euler = Euler((rot[0], rot[1], ang + rot[2]))
    return o

# ---------------------------------------------------------------- plants
def leaf_mesh(name, length=0.07, width=0.012, mat=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    n = 6
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = width * math.sin(math.pi * t) ** 0.8
        bend = 0.15 * length * t * t
        left.append(bm.verts.new((t * length, -w, -bend)))
        right.append(bm.verts.new((t * length, w, -bend)))
    mid = []
    for i in range(n):
        bm.faces.new((left[i], left[i + 1], right[i + 1], right[i]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o)
    o.hide_render = False
    me.materials.append(mat)
    for f in me.polygons: f.use_smooth = True
    return o

_leaf_cache = {}

def invisible():
    if 'invisible' in _mats: return _mats['invisible']
    m, nt, p = new_mat('invisible')
    nt.nodes.remove(p)
    t = nt.nodes.new('ShaderNodeBsdfTransparent')
    nt.links.new(t.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    _mats['invisible'] = m
    return m

def tree(x, y, z, height=3.0, crown_r=1.1, trunk_r=0.09, seed=1, kind='olive', leaves=26000, coll=None, crown_squash=0.75):
    """procedural tree: gnarled multi-stem trunk + leaf-instanced crown (olive by default)"""
    rng = random.Random(seed)
    mats = M()
    lm = mats['leaf_olive'] if kind == 'olive' else mats['leaf']
    key = (kind,)
    if key not in _leaf_cache:
        lf = leaf_mesh('leaf_' + kind, 0.09 if kind == 'olive' else 0.10, 0.014 if kind == 'olive' else 0.035, lm)
        # olive leaves: silvery underside -> second material variant
        lf.location = (0, 0, -100)
        lf.hide_render = True
        _leaf_cache[key] = lf
    leafobj = _leaf_cache[key]
    # trunk: a few curved stems
    stems = 3 if kind == 'olive' else 1
    crown_c = Vector((x, y, z + height - crown_r * crown_squash))
    branch_tips = []
    branch_lines = []
    for s in range(stems):
        ang = 2 * math.pi * s / stems + rng.uniform(-0.4, 0.4)
        pts = []
        N = 10
        top = crown_c + Vector((math.cos(ang) * crown_r * 0.35, math.sin(ang) * crown_r * 0.35, rng.uniform(-0.2, 0.2)))
        base = Vector((x + math.cos(ang) * 0.03, y + math.sin(ang) * 0.03, z))
        for i in range(N + 1):
            t = i / N
            p = base.lerp(top, t)
            p.x += 0.12 * math.sin(t * 5 + s) * (1 - t) * (1 if kind == 'olive' else 0.2)
            p.y += 0.10 * math.cos(t * 4 + s * 2) * (1 - t) * (1 if kind == 'olive' else 0.2)
            pts.append(p)
        cu = bpy.data.curves.new('trunk', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = trunk_r * (0.75 if stems > 1 else 1)
        cu.bevel_resolution = 4
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
        for i, (bp, p) in enumerate(zip(sp.bezier_points, pts)):
            bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
            bp.radius = 1.0 - 0.75 * (i / N)
        o = bpy.data.objects.new('trunk', cu); link(o, coll); cu.materials.append(mats['bark'])
        # secondary branches
        for b in range(5):
            t0 = rng.uniform(0.55, 0.95)
            p0 = pts[int(t0 * N)]
            a2 = ang + rng.uniform(-1.6, 1.6)
            L = crown_r * rng.uniform(0.5, 0.95)
            p1 = p0 + Vector((math.cos(a2) * L, math.sin(a2) * L, rng.uniform(0.0, 0.6) * L))
            cu2 = bpy.data.curves.new('br', 'CURVE'); cu2.dimensions = '3D'; cu2.bevel_depth = trunk_r * 0.28; cu2.bevel_resolution = 2
            sp2 = cu2.splines.new('POLY'); sp2.points.add(1)
            sp2.points[0].co = (*p0, 1); sp2.points[1].co = (*p1, 1); sp2.points[1].radius = 0.3
            ob = bpy.data.objects.new('branch', cu2); link(ob, coll); cu2.materials.append(mats['bark'])
            branch_tips.append(p1); branch_lines.append((p0, p1))
    # crown: twigs off every branch, many small leaf clusters along them (reads as one airy canopy)
    me = bpy.data.meshes.new('crown')
    bm = bmesh.new()
    def clump(c, rr):
        mat = Matrix.Translation(c) @ Matrix.Diagonal((rr, rr, rr * 0.8, 1))
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0, matrix=mat)
    for (p0, p1) in branch_lines:
        d = (p1 - p0)
        for k in range(5):
            t = rng.uniform(0.35, 1.0)
            base = p0.lerp(p1, t)
            dirv = (d.normalized() + Vector((rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9), rng.uniform(-0.2, 0.7)))).normalized()
            L = crown_r * rng.uniform(0.25, 0.5)
            tip = base + dirv * L
            cu3 = bpy.data.curves.new('twig', 'CURVE'); cu3.dimensions = '3D'; cu3.bevel_depth = trunk_r * 0.09; cu3.bevel_resolution = 1
            sp3 = cu3.splines.new('POLY'); sp3.points.add(1)
            sp3.points[0].co = (*base, 1); sp3.points[1].co = (*tip, 1); sp3.points[1].radius = 0.3
            ot = bpy.data.objects.new('twig', cu3); link(ot, coll); cu3.materials.append(mats['bark'])
            for j in range(3):
                c = base.lerp(tip, 0.45 + 0.27 * j) + Vector((rng.uniform(-.05, .05), rng.uniform(-.05, .05), rng.uniform(-.02, .06)))
                clump(c, crown_r * rng.uniform(0.10, 0.17))
    # sparse inner fill so the canopy is not see-through
    for i in range(18):
        u = rng.uniform(0, 2 * math.pi); rf = crown_r * 0.6 * math.sqrt(rng.random())
        c = crown_c + Vector((math.cos(u) * rf, math.sin(u) * rf, rng.uniform(-0.2, 0.45) * crown_r * crown_squash))
        clump(c, crown_r * rng.uniform(0.12, 0.2))
    bm.to_mesh(me); bm.free()
    cr = bpy.data.objects.new('crown', me); link(cr, coll)
    cr.data.materials.append(invisible())
    ps = cr.modifiers.new('leaves', 'PARTICLE_SYSTEM').particle_system
    st = ps.settings
    st.type = 'HAIR'; st.count = int(leaves * 2.2); st.hair_length = 1.0
    st.render_type = 'OBJECT'; st.instance_object = leafobj
    st.particle_size = min(1.0, 0.4 + crown_r * 0.45); st.size_random = 0.5
    st.use_rotations = True; st.rotation_mode = 'NOR'; st.rotation_factor_random = 0.9; st.phase_factor_random = 2.0
    st.emit_from = 'VOLUME'; st.distribution = 'RAND'
    st.use_emit_random = True
    ps.seed = seed
    cr.show_instancer_for_render = False
    return cr

def potted_plant(x, y, z=0.0, scale=1.0, rot=0.0, coll=None):
    h, _ = import_glb('DiffuseTransmissionPlant', (x, y, z), rot, scale, coll=coll, remove=('firefly',))
    return h

def floor_lamp(x, y, rot=0.0, h=1.55, k=2700, on=False, coll=None):
    """bronze arc-free floor lamp with linen drum"""
    m = M()
    cyl('lamp_base', x, y, 0, 0.025, 0.16, m['bronze_dark'], bevel=0.005, coll=coll)
    cyl('lamp_rod', x, y, 0.025, h, 0.008, m['bronze'], 16, coll=coll)
    sh = lathe('lamp_shade', [(0.20, 0), (0.19, 0.30)], x, y, h - 0.25, plain('shade', '#EFE7D8', rough=0.9, sss=0.0, transmission=0.0), coll=coll)
    if on:
        sh.data.materials[0] = paper('shade_paper', 3.0, k)
        point('lamp_bulb', (x, y, h - 0.12), 35, k, 0.04, coll=coll)
    return sh

def wall_light(x, y, z, rot, on=False, coll=None):
    """plaster half-cylinder wall sconce washing up and down"""
    o = cyl('sconce', 0, 0, -0.15, 0.15, 0.07, plain('sconce', '#ECE5DA', rough=0.9), 32, coll=coll)
    o.location = (x, y, z); o.rotation_euler = (0, 0, rot)
    o.scale = (1, 0.6, 1)
    if on:
        point('sconce_l', (x + 0.08 * math.cos(rot - math.pi / 2) * -1, y + 0.08 * math.sin(rot - math.pi / 2) * -1, z), 12, 2700, 0.05, coll=coll)
    return o

# ---------------------------------------------------------------- world / render
def sky(strength=1.0, elev=35, azimuth_deg=250, sun=True, sun_strength=4.0, sun_angle=0.6, k_sun=None, air=1.0, dust=1.0, ozone=1.0, sun_disc=True):
    """physical sky. azimuth: compass bearing of the sun (0=N, 90=E, 180=S, 270=W).
    house axes: +Y = east, +X = south, -X = north."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    s = nt.nodes.new('ShaderNodeTexSky')
    s.sky_type = 'MULTIPLE_SCATTERING'
    s.sun_elevation = math.radians(elev)
    # Blender sky: sun_rotation 0 -> sun towards +Y, rotates counter-clockwise (towards -X)
    # compass bearing b -> direction vector in house coords:
    b = math.radians(azimuth_deg)
    # north = -X, east = +Y
    dx, dy = -math.cos(b), math.sin(b)
    ang = math.atan2(dy, dx)  # angle from +X
    s.sun_rotation = ang - math.pi / 2  # since 0 points to +Y
    s.air_density = air; s.aerosol_density = dust; s.ozone_density = ozone
    s.sun_disc = sun_disc
    s.sun_intensity = 1.0
    nt.links.new(s.outputs[0], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    sun_obj = None
    if sun:
        L = bpy.data.lights.new('sun', 'SUN'); L.energy = sun_strength; L.angle = math.radians(sun_angle)
        if k_sun: L.color = kelvin(k_sun)
        sun_obj = bpy.data.objects.new('sun', L); link(sun_obj)
        d = Vector((dx * math.cos(math.radians(elev)), dy * math.cos(math.radians(elev)), math.sin(math.radians(elev))))
        sun_obj.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        # the sky texture already contains the sun disc; disable the disc to avoid double sun lighting
        s.sun_disc = False
    return s, sun_obj

def hdri(path, strength=1.0, rot=0.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('hdri'); sc.world = w; w.use_nodes = True
    nt = w.node_tree
    e = nt.nodes.new('ShaderNodeTexEnvironment'); e.image = bpy.data.images.load(path)
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, rot)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], e.inputs['Vector'])
    nt.links.new(e.outputs[0], nt.nodes['Background'].inputs['Color'])
    nt.nodes['Background'].inputs['Strength'].default_value = strength
    return e

def camera(loc, look_at, lens=24, shift_x=0.0, shift_y=0.0, name='cam', clip_start=0.05, dof=None):
    sc = bpy.context.scene
    c = bpy.data.cameras.new(name); c.lens = lens; c.shift_x = shift_x; c.shift_y = shift_y; c.clip_start = clip_start
    c.sensor_width = 36
    o = bpy.data.objects.new(name, c); link(o)
    o.location = loc
    d = Vector(look_at) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if dof:
        c.dof.use_dof = True; c.dof.focus_distance = dof[0]; c.dof.aperture_fstop = dof[1]
    sc.camera = o
    return o

def render_settings(w=1600, h=1000, samples=256, exposure=0.0, look='Medium High Contrast', clamp=10.0, bounces=8, threads=0, gamma=1.0):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    try: sc.cycles.denoising_prefilter = 'ACCURATE'
    except Exception: pass
    sc.cycles.max_bounces = bounces
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 8
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.sample_clamp_indirect = clamp
    sc.cycles.blur_glossy = 1.0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = look
    except Exception: pass
    sc.view_settings.exposure = exposure
    sc.view_settings.gamma = gamma
    sc.render.image_settings.file_format = 'PNG'
    sc.render.film_transparent = False
    if threads:
        sc.render.threads_mode = 'FIXED'; sc.render.threads = threads
    sc.render.use_persistent_data = False

def render(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
