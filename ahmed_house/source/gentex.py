import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
rng=np.random.default_rng(7)
OUT='assets/gen/'
def fbm(h,w,scales,amps,seed=0,wrap=True):
    r=np.random.default_rng(seed); acc=np.zeros((h,w))
    for s,a in zip(scales,amps):
        gh,gw=max(2,h//s),max(2,w//s)
        g=r.standard_normal((gh,gw))
        g=np.tile(g,(3,3))
        im=Image.fromarray(g.astype(np.float32),mode='F').resize((gw*3*s,gh*3*s),Image.BICUBIC)
        a_=np.array(im)[gh*s:gh*s+h, gw*s:gw*s+w]
        acc+=a*a_
    return acc
def save(a,name,mode='RGB'):
    a=np.clip(a,0,1)
    Image.fromarray((a*255).astype(np.uint8),mode if a.ndim==3 else 'L').save(OUT+name)
def srgb(h): h=h.lstrip('#'); return np.array([int(h[i:i+2],16)/255 for i in (0,2,4)])

def oak(name,base,dark,N=2048,plank_w=8,plank_l=1,seed=1,contrast=1.0):
    # texture covers planks: N px wide = plank_w planks across(x), length along y
    H=W=N; pw=W//plank_w
    col=np.zeros((H,W,3)); rough=np.zeros((H,W)); bump=np.zeros((H,W))
    yy,xx=np.mgrid[0:H,0:W].astype(float)
    r=np.random.default_rng(seed)
    warp=fbm(H,W,[256,64],[30,6],seed+1)
    for i in range(plank_w):
        x0=i*pw
        # plank split along length: offset seam
        off=r.integers(0,H)
        seams=[off%H]
        if plank_l>1: seams+= [ (off+H//plank_l*k)%H for k in range(1,plank_l)]
        sl=slice(x0,x0+pw)
        lx=xx[:,sl]-x0; ly=yy[:,sl]
        # grain: rings across width, stretched along length
        ring=(lx*0.9 + warp[:,sl]*1.0 + 18*np.sin(ly/H*2*np.pi*r.uniform(0.5,1.5)+r.uniform(0,6)))
        freq=r.uniform(0.18,0.30)
        g=0.5+0.5*np.sin(ring*freq)
        g=g**3
        fine=fbm(H,pw,[2,4],[1,0.6],seed+10+i)
        fine=gaussian_filter(fine,(6,0.6))  # streaks along length
        t=np.clip(0.35*g+0.25*(fine*0.5+0.5)+r.uniform(-0.12,0.12),0,1)*contrast
        tone=r.uniform(-0.06,0.06)
        c=base[None,None,:]*(1-t[...,None])+dark[None,None,:]*t[...,None]
        c*= (1+tone)
        col[:,sl]=c
        rough[:,sl]=0.45+0.15*t
        bump[:,sl]=0.5+0.2*fine
        # bevel gaps
        for s in seams:
            d=np.abs(((ly-s+H/2)%H)-H/2)
            m=np.exp(-(d/1.5)**2)
            col[:,sl]*=(1-0.45*m[...,None]); bump[:,sl]-=0.5*m
        dx=np.minimum(lx,pw-1-lx)
        m=np.exp(-(dx/1.5)**2)
        col[:,sl]*=(1-0.45*m[...,None]); bump[:,sl]-=0.5*m
    save(col,name+'_col.png'); save(rough,name+'_rough.png'); save(np.clip(bump,0,1),name+'_bump.png')

oak('oak',srgb('#D2B48E'),srgb('#9E7A55'),plank_w=8,plank_l=2,seed=3)
oak('smoked',srgb('#5E4838'),srgb('#2E2219'),plank_w=8,plank_l=1,seed=9)

def travertine(N=2048,seed=4):
    H=W=N
    yy,xx=np.mgrid[0:H,0:W].astype(float)
    warp=fbm(H,W,[512,128,32],[60,15,4],seed)
    bands=np.sin((yy+warp)/H*2*np.pi*9)*0.5+0.5
    bands2=np.sin((yy+warp*1.7)/H*2*np.pi*23)*0.5+0.5
    mott=fbm(H,W,[256,64,16,4],[1,0.5,0.25,0.12],seed+1)
    t=0.45*bands**2+0.25*bands2**4+0.15*mott
    base=srgb('#E4D6BE'); dark=srgb('#C4AD8A')
    col=base*(1-t[...,None])+dark*t[...,None]
    # pits (filled, slightly darker) elongated along bands
    pits=fbm(H,W,[8,3],[1,0.5],seed+5)
    pits=gaussian_filter(pits,(0.8,3))
    pm=np.clip((pits-1.6)*1.5,0,1)
    col*=(1-0.25*pm[...,None])
    bump=0.5+0.1*mott-0.3*pm
    rough=0.55+0.15*pm+0.05*mott
    save(col,'trav_col.png'); save(np.clip(bump,0,1),'trav_bump.png'); save(np.clip(rough,0,1),'trav_rough.png')
travertine()

def plaster(N=2048,seed=11):
    H=W=N
    m=fbm(H,W,[512,128,32,8,2],[1,0.6,0.35,0.2,0.1],seed)
    m=(m-m.min())/(m.max()-m.min())
    base=srgb('#EEE7DC'); dark=srgb('#DDD2C2')
    t=gaussian_filter(m,2)
    col=base*(1-t[...,None]*0.7)+dark*(t[...,None]*0.7)
    bump=fbm(H,W,[64,16,4,2],[0.3,0.4,0.3,0.2],seed+3)
    save(col,'plaster_col.png'); save(np.clip(0.5+bump*0.2,0,1),'plaster_bump.png')
plaster()

def boucle(N=1024,seed=21):
    b=fbm(N,N,[6,3,2],[1,0.7,0.5],seed); b=(b-b.min())/(b.max()-b.min())
    save(b,'boucle_bump.png')
    l=fbm(N,N,[2],[1],seed+1)
    # linen weave
    yy,xx=np.mgrid[0:N,0:N]
    w=0.5+0.25*np.sin(xx*np.pi/2.0)*np.sign(np.sin(yy*np.pi/8))+0.15*l
    save(np.clip(w,0,1),'linen_bump.png')
    r=fbm(N,N,[16,4,2],[1,0.6,0.4],seed+2); r=(r-r.min())/(r.max()-r.min())
    save(r,'wool_bump.png')
boucle()
print('ok')
