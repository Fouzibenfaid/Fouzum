import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom
exec(open('gentex.py').read().split("def oak(")[0])
def aniso(h,w,sy,sx,seed):
    r=np.random.default_rng(seed); g=r.standard_normal((max(2,h//sy),max(2,w//sx)))
    return np.array(Image.fromarray(g.astype(np.float32),'F').resize((w,h),Image.BICUBIC))
def oak(name,base,dark,N=2048,plank_w=8,plank_l=2,seed=1):
    H=W=N; pw=W//plank_w
    col=np.zeros((H,W,3)); rough=np.zeros((H,W)); bump=np.zeros((H,W))
    r=np.random.default_rng(seed)
    for i in range(plank_w):
        x0=i*pw; sl=slice(x0,x0+pw)
        nseg=plank_l; off=r.integers(0,H//nseg)
        cuts=sorted([(off+k*H//nseg)%H for k in range(nseg)])
        segs=[(cuts[k],cuts[(k+1)%nseg] if k+1<nseg else cuts[0]+H) for k in range(nseg)]
        for (a,b) in segs:
            L=b-a
            ly,lx=np.mgrid[0:L,0:pw].astype(float)
            cx=r.uniform(-0.3,1.3)*pw
            d0=r.uniform(40,160); slope=r.uniform(-0.12,0.12)
            wl=aniso(L,pw,400,60,r.integers(1e9))*25
            R=np.sqrt((lx-cx)**2+(d0+slope*ly+wl)**2)
            ringn=aniso(L,pw,200,8,r.integers(1e9))*2.0
            f=r.uniform(0.09,0.14)
            ph=R*f+ringn
            g=(np.sin(ph)*0.5+0.5)**4
            streak=aniso(L,pw,90,1,r.integers(1e9)); streak=(streak-streak.min())/(np.ptp(streak)+1e-6)
            fleck=np.clip(aniso(L,pw,6,2,r.integers(1e9))-1.8,0,1)
            t=0.30*g+0.25*streak+0.10*aniso(L,pw,300,300,r.integers(1e9))
            t=np.clip(t+r.uniform(-0.08,0.08),0,1)
            c=base*(1-t[...,None])+dark*t[...,None]
            c=c*(1+0.12*fleck[...,None])*(1+r.uniform(-0.05,0.05))
            # end seam darkening
            m=np.exp(-(np.minimum(ly,L-1-ly)/1.2)**2)
            c*=(1-0.5*m[...,None])
            rows=(np.arange(a,b)%H)
            col[rows,sl]=c; rough[rows,sl]=0.42+0.12*t-0.05*fleck
            bump[rows,sl]=0.55+0.15*streak-0.5*m
        dx=np.arange(pw); m=np.exp(-(np.minimum(dx,pw-1-dx)/1.2)**2)
        col[:,sl]*=(1-0.5*m[None,:,None]); bump[:,sl]-=0.5*m[None,:]
    save(col,name+'_col.png'); save(rough,name+'_rough.png'); save(np.clip(bump,0,1),name+'_bump.png')
oak('oak',srgb('#D6BC98'),srgb('#A98863'),seed=3)
oak('smoked',srgb('#5A4535'),srgb('#33261C'),plank_l=1,seed=9)
s=Image.new('RGB',(1600,800))
for i,f in enumerate(['oak_col','smoked_col']):
    im=Image.open('assets/gen/'+f+'.png').convert('RGB'); s.paste(im.resize((800,800)),(i*800,0))
s.save('texsheet.jpg')
