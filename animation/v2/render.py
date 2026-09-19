"""Slower 30 s molecular explainer with real PDB geometry and ribbon cartoons.

All macromolecular templates are attributed in SOURCES.md. The fusion is an
illustrative composite of retained reference fragments, NOT a predicted fold.
"""
import sys
sys.path.insert(0, '/tmp/chimera_animation_libs')
import math
import functools
import json
from pathlib import Path
import numpy as np
import gemmi
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
W,H,FPS=1600,900,24
CYAN=(14,139,184); ORANGE=(218,108,42); VIOLET=(122,91,159)
INK=(33,46,57); GREY=(110,120,131); PALE=(177,185,191)
TEAL=(67,141,130); GOLD=(184,157,100)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def ft(n,b=False): return ImageFont.truetype(BOLD if b else FONT,n)
def clamp(x): return np.clip(x,0.,1.)
def ease(x):
    x=clamp(x); return x*x*(3-2*x)
def norm(v): return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-8)
def pos(a): return np.array([a.pos.x,a.pos.y,a.pos.z])
def rot(y=0,x=0,z=0):
    cy,sy,cx,sx,cz,sz=math.cos(y),math.sin(y),math.cos(x),math.sin(x),math.cos(z),math.sin(z)
    return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]]) @ np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]) @ np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])

yy,xx=np.mgrid[:H,:W]
q=np.exp(-((xx-W*.5)**2/(W*.55)**2+(yy-H*.40)**2/(H*.7)**2))
BG=Image.fromarray(np.stack([232+21*q,235+19*q,237+17*q],axis=-1).astype('uint8'))
del xx,yy,q

@functools.lru_cache(maxsize=6000)
def sphere(r,c):
    r=max(2,int(r)); q=np.linspace(-1,1,r*2+1); x,y=np.meshgrid(q,q)
    d=x*x+y*y; z=np.sqrt(np.maximum(0,1-d))
    l=.43+.55*np.maximum(0,-.42*x-.55*y+.72*z)
    gl=.25*np.maximum(0,-.30*x-.40*y+.86*z)**32
    rgb=np.clip(np.array(c)[None,None,:]*l[...,None]+255*gl[...,None],0,255)
    return Image.fromarray(np.dstack([rgb,255*np.clip((1-d)*r,0,1)]).astype('uint8'))

class Scene:
    def __init__(self):
        self.spheres=[]; self.meshes=[]; self.labels=[]
    def points(self,p,r,c):
        p=np.asarray(p); n=len(p)
        rr=np.broadcast_to(np.asarray(r), (n,))
        cc=np.broadcast_to(np.asarray(c),(n,3))
        self.spheres.append((p,rr,cc))
    def tube(self,p,r,c): self.points(p,r,c)
    def mesh(self,v,f,c): self.meshes.append((np.asarray(v),np.asarray(f),np.asarray(c)))
    def label(self,x,y,text,size=36,color=INK): self.labels.append((x,y,text,size,color))
    @staticmethod
    def project(p):
        fac=1500/(1500+p[:,2])
        return np.column_stack([W/2+p[:,0]*fac,H/2-p[:,1]*fac]),fac
    def render(self):
        im=BG.copy()
        # A quiet soft shadow grounds the molecular view against the white studio.
        shadow=Image.new('RGBA',(W,H))
        d=ImageDraw.Draw(shadow)
        d.ellipse((330,655,1270,745),fill=(73,90,104,15))
        shadow=shadow.filter(ImageFilter.GaussianBlur(32)); im.paste(shadow,(0,0),shadow)
        if self.spheres:
            p=np.concatenate([a[0] for a in self.spheres]); r=np.concatenate([a[1] for a in self.spheres]); c=np.concatenate([a[2] for a in self.spheres])
            xy,fac=self.project(p)
            for i in np.argsort(p[:,2])[::-1]:
                radius=max(2,int(r[i]*fac[i])); x,y=xy[i]
                if x<-radius or x>W+radius or y<-radius or y>H+radius: continue
                spr=sphere(radius,tuple(map(int,c[i])))
                im.paste(spr,(round(x)-radius,round(y)-radius),spr)
        if self.meshes:
            polygons=[]; depths=[]; shades=[]
            light=norm(np.array([-.4,.6,-.8]))
            for v,f,c in self.meshes:
                pts=v[f]; n=norm(np.cross(pts[:,1]-pts[:,0],pts[:,2]-pts[:,0]))
                shade=.48+.48*np.abs(n@light)
                colors=np.broadcast_to(c,(len(f),3))*shade[:,None]
                xy,_=self.project(v)
                polygons.extend(xy[f]); depths.extend(pts[:,:,2].mean(axis=1)); shades.extend(colors)
            d=ImageDraw.Draw(im)
            for i in np.argsort(depths)[::-1]:
                d.polygon([tuple(p) for p in polygons[i]],fill=tuple(np.clip(shades[i],0,255).astype(int)))
        d=ImageDraw.Draw(im)
        for x,y,txt,size,color in self.labels:
            # Minimal opaque backing protects annotations without caption boxes.
            box=d.textbbox((x,y),txt,font=ft(size),anchor='mm')
            d.rounded_rectangle((box[0]-12,box[1]-8,box[2]+12,box[3]+8),radius=10,fill=(249,250,250))
            d.text((x,y),txt,font=ft(size),anchor='mm',fill=color)
        return im

def path(points,count=130):
    p=np.asarray(points,dtype=float)
    u=np.linspace(0,1,len(p)); v=np.linspace(0,1,count)
    return CubicSpline(u,p,axis=0)(v)

def strand(s,p,c,r=4.1,bases=True):
    p=np.asarray(p); s.tube(p,r,c)
    if bases and len(p)>3:
        tang=norm(np.gradient(p,axis=0)); offset=norm(np.cross(tang,np.array([0,0,1])))
        offset*=9
        cc=np.broadcast_to(c,(len(p),3))
        for f in [.4,.8,1.15]: s.points(p[::4]+offset[::4]*f,2.7,cc[::4])

def rna(s,left,right,c,wiggle=6,chimera=False):
    p=np.linspace(left,right,160)
    p[:,1]+=wiggle*np.sin(np.linspace(0,5*math.pi,160))
    p[:,2]+=wiggle*np.cos(np.linspace(0,5*math.pi,160))
    colors=np.array([CYAN if i<80 else ORANGE for i in range(160)]) if chimera else c
    strand(s,p,colors)
    return p

def prepare_complex(code):
    st=gemmi.read_structure(str(ROOT/'structures'/f'{code}.cif'))
    ps=[]; cs=[]; rs=[]; named={}
    for ci,ch in enumerate(st[0]):
        xyz=[]
        for res in ch:
            at=res.find_atom('CA','*')
            if at is not None:
                xyz.append(pos(at))
                ps.append(pos(at)); rs.append(2.65)
                base=np.array(VIOLET if code=='5XJC' else (136,150,155))
                base=np.clip(base+(ci%6-2)*7,0,255); cs.append(base)
            else:
                at=res.find_atom("C4'",'*') or res.find_atom('P','*')
                if at is not None:
                    xyz.append(pos(at)); ps.append(pos(at)); rs.append(2.55)
                    cs.append((182,150,207) if code=='5XJC' else (95,143,170))
        if xyz: named[ch.name]=np.array(xyz)
    ps=np.array(ps); center=np.median(ps,axis=0)
    # Principal axes give a reproducible view; choose RNA-bearing face for Pol II.
    _,_,vh=np.linalg.svd(ps-center,full_matrices=False)
    if np.linalg.det(vh)<0: vh[2]*=-1
    if code=='1Y1W':
        r=named['P']; exitv=norm(r[0]-r[2]); axis=norm(r[0]-center)
        y=norm(exitv+axis*.5); z=norm(np.cross(y, np.array([1.,0.,0.]))); x=norm(np.cross(y,z))
        vh=np.vstack([x,y,z])
    ps=(ps-center)@vh.T
    named={k:(v-center)@vh.T for k,v in named.items()}
    return {'p':ps,'c':np.array(cs),'r':np.array(rs),'chains':named,'structure':st}

COMPLEX={k:prepare_complex(k) for k in ['1Y1W','5XJC']}

def molecule(s,code,center=(0,0,0),scale=2.6,angle=0):
    m=COMPLEX[code]; R=rot(y=angle)
    p=m['p']@R.T*scale+center
    s.points(p,m['r']*scale,m['c'])
    return {k:v@R.T*scale+center for k,v in m['chains'].items()}

def get_ribbon(code):
    st=gemmi.read_structure(str(ROOT/'structures'/f'{code}.pdb'))
    ch=st[0][0]; residues=[]; ca=[]; co=[]; ids=[]
    for res in ch:
        a=res.find_atom('CA','*'); c=res.find_atom('C','*'); o=res.find_atom('O','*')
        if a is None: continue
        ca.append(pos(a)); co.append(pos(o)-pos(c) if c is not None and o is not None else np.array([0,0,1])); ids.append(res.seqid.num)
    ca=np.array(ca); co=np.array(co); ids=np.array(ids); ss=np.zeros(len(ca),int)
    for h in st.helices:
        if h.start.chain_name==ch.name: ss[(ids>=h.start.res_id.seqid.num)&(ids<=h.end.res_id.seqid.num)]=1
    for sheet in st.sheets:
        for h in sheet.strands:
            if h.start.chain_name==ch.name: ss[(ids>=h.start.res_id.seqid.num)&(ids<=h.end.res_id.seqid.num)]=2
    # Smooth beta-strand pleating for a conventional ribbon cartoon.
    for i in range(1,len(ca)-1):
        if ss[i]==2: ca[i]=.25*ca[i-1]+.5*ca[i]+.25*ca[i+1]
    for i in range(1,len(co)):
        if np.dot(co[i],co[i-1])<0: co[i]*=-1
    ca-=ca.mean(axis=0)
    _,_,R=np.linalg.svd(ca,full_matrices=False)
    if np.linalg.det(R)<0: R[2]*=-1
    return ca@R.T,co@R.T,ss,ids

RIBBON={k:get_ribbon(k) for k in ['1UBQ','1MBN']}

@functools.lru_cache(None)
def ribbon_mesh(code,start=0,stop=10000):
    ca,co,ss,ids=RIBBON[code]
    select=(ids>=start)&(ids<=stop)
    ca,co,ss=ca[select],co[select],ss[select]
    u=np.arange(len(ca)); v=np.linspace(0,len(ca)-1,(len(ca)-1)*5+1)
    center=CubicSpline(u,ca)(v); tangent=norm(np.gradient(center,axis=0))
    side=CubicSpline(u,co)(v); side-=np.sum(side*tangent,axis=1)[:,None]*tangent; side=norm(side)
    normal=norm(np.cross(tangent,side)); typ=ss[np.minimum(np.round(v).astype(int),len(ss)-1)]
    width=np.where(typ==1,1.30,np.where(typ==2,1.6,.19))
    depth=np.where(typ==0,.19,.18)
    # Arrowheads identify beta strands and their N-to-C direction.
    for i in range(1,len(ss)):
        if ss[i-1]==2 and ss[i]!=2:
            near=(v>=i-1.8)&(v<=i-.05)
            width[near]=np.maximum(.12,2.55*(i-.05-v[near])/1.75)
    width=gaussian_filter1d(width,.6)
    verts=[]
    for a,b in [(1,1),(-1,1),(-1,-1),(1,-1)]:
        verts.append(center+side*(a*width)[:,None]+normal*(b*depth)[:,None])
    verts=np.stack(verts,axis=1).reshape(-1,3)
    faces=[]
    for i in range(len(center)-1):
        for j in range(4): faces.append([i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j])
    return verts,np.array(faces),center[0],center[-1]

def ribbon(s,code,center,scale,color,angle=0,part=None,Rextra=None):
    v,f,start,end=ribbon_mesh(code,*(part or (0,10000)))
    R=rot(y=angle,x=.15,z=.12)
    if Rextra is not None: R=Rextra@R
    s.mesh(v@R.T*scale+center,f,color)
    return start@R.T*scale+center,end@R.T*scale+center

def fusion(s,center,scale=5,angle=0):
    # Retained fragments arranged into a distinct elongated illustrative topology.
    R=rot(y=angle,x=-.20,z=-.26)
    a=np.array(center)+np.array([-15,10,0])@R.T*scale
    b=np.array(center)+np.array([15,-8,0])@R.T*scale
    a0,a1=ribbon(s,'1UBQ',a,scale,CYAN,part=(1,64),Rextra=R)
    b0,b1=ribbon(s,'1MBN',b,scale*.8,ORANGE,part=(30,130),Rextra=R@rot(z=1.15))
    mid=(a1+b0)/2+np.array([0,15,10])
    p=path([a1,mid,b0],70)
    strand(s,p,np.array([CYAN if i<35 else ORANGE for i in range(70)]),r=1.7,bases=False)

def helix(s,center,axis,length=400,color=CYAN):
    axis=norm(np.asarray(axis)); ref=np.array([0.,0.,1.])
    if abs(np.dot(axis,ref))>.9: ref=np.array([0.,1.,0.])
    u=norm(np.cross(axis,ref)); v=np.cross(axis,u)
    ts=np.linspace(-length/2,length/2,200)
    for phase in [0,math.pi]:
        p=np.array(center)+ts[:,None]*axis+13*(np.cos(ts[:,None]/11+phase)*u+np.sin(ts[:,None]/11+phase)*v)
        s.points(p,3.7,color)
    for a in ts[::8]:
        q=np.array(center)+a*axis; d=13*(math.cos(a/11)*u+math.sin(a/11)*v)
        s.tube(np.linspace(q-d,q+d,8),2.1,(153,171,179))

def ribosome(s,center):
    # Deliberately schematic two-subunit silhouette; splicing uses real coordinates.
    rng=np.random.default_rng(58)
    for off,scale,col in [(np.array([0,33,0]),np.array([66,50,47]),TEAL),(np.array([0,-25,0]),np.array([57,28,37]),GOLD)]:
        p=norm(rng.normal(size=(300,3)))*scale+off+center
        s.points(p,7.5,col)

def headers(im,section,sub=None):
    d=ImageDraw.Draw(im)
    d.text((75,57),section,font=ft(42,True),fill=INK)
    if sub: d.text((W-75,68),sub,font=ft(25),anchor='ra',fill=GREY)
    return im

def card(number,title,subtitle,t):
    im=BG.copy(); d=ImageDraw.Draw(im)
    d.text((W/2,280),number,font=ft(28,True),anchor='mm',fill=GREY)
    d.text((W/2,398),title,font=ft(80,True),anchor='mm',fill=INK)
    d.text((W/2,515),subtitle,font=ft(40),anchor='mm',fill=GREY)
    if number=='02':
        d.rounded_rectangle((624,586,796,594),radius=4,fill=CYAN); d.rounded_rectangle((803,586,975,594),radius=4,fill=ORANGE)
    else: d.rounded_rectangle((700,586,900,594),radius=4,fill=CYAN)
    return im

def transcription(t):
    s=Scene(); p=ease((t-1.8)/3.7)
    # Pol II is anchored; DNA advances through it. The nascent RNA is physically
    # continuous with the first modeled RNA residue and lengthens at its exit.
    cen=np.array([-70,-20,0]); scale=2.45
    chains=molecule(s,'1Y1W',cen,scale)
    template=chains['T']; n=chains['N']; nascent=chains['P']
    d=norm(template[-1]-template[0])
    for end,sign in [(template[0],-1),(template[-1],1)]:
        helix(s,end+sign*d*135,d,length=280,color=(69,130,158))
    strand(s,nascent,CYAN,r=4.9)
    exit=nascent[0]; direction=norm(nascent[0]-nascent[2])
    length=70+300*p
    end=exit+np.array([length*.82,length*.43,0])
    emitted=path([exit,exit+direction*32,exit+np.array([100,90,20]),end],int(55+110*p))
    strand(s,emitted,CYAN,r=4.8)
    s.label(440,720,'RNA polymerase',38)
    # A leader ties the label to the newly growing transcript.
    s.label(1110,250,'pre-mRNA A',42,CYAN)
    s.label(310,330,'DNA',36)
    im=s.render(); ddraw=ImageDraw.Draw(im)
    xy,_=s.project(np.array([emitted[-1]]))
    ddraw.line([(1090,285),tuple(xy[0]+[10,-10])],fill=CYAN,width=2)
    dna_xy,_=s.project(np.array([template[-1]+d*125]))
    ddraw.line([(355,335),tuple(dna_xy[0])],fill=(130,147,159),width=2)
    return headers(im,'Central dogma','Transcription')

def translation(t,start,end,fused=False):
    s=Scene(); progress=ease((t-start)/(end-start))
    rna(s,(-580,-95,0),(580,-95,0),CYAN,chimera=fused)
    x=-360+640*progress; ribosome(s,np.array([x,-95,0]))
    # N terminus is distal; the C terminus remains at the ribosome exit.
    n=int(30+90*progress)
    chain=path([[x, -30,0],[x-30,65,15],[x-90,100+100*progress,15],[x-180,145+100*progress,0]],n)
    cols=np.array([ORANGE if fused and i<n*.48 and progress>.5 else CYAN for i in range(n)])
    if fused or progress<.84:
        strand(s,chain,cols,r=4,bases=False)
    else:
        ribbon(s,'1UBQ',(260,145,0),8.2,CYAN,angle=-.2)
    s.label(320,655,'Chimeric mRNA' if fused else 'mRNA A',38,CYAN)
    if not fused and progress>=.84: s.label(1120,170,'Protein A',38,CYAN)
    if fused: s.label(1050,170,'New polypeptide',38,INK)
    s.label(1350,570,'3′',31,GREY); s.label(215,570,'5′',31,GREY)
    return headers(s.render(),'Chimeric mRNA' if fused else 'Central dogma','Translation')

# The real complex is cached as a static structural reference. The schematic RNA
# substrate paths are animated around it; no invented protein subunit morphing.
@functools.lru_cache(None)
def splice_base():
    s=Scene(); molecule(s,'5XJC',(0,0,80),scale=1.95,angle=-.35)
    im=s.render()
    # Keep actual PDB geometry legible while foreground substrate paths stand out.
    return im

def splicing(t):
    s=Scene(); p=ease((t-13.2)/4.6); joined=t>=18.1
    # Recognizable separate molecules hold for 1.7 s before approaching.
    upper=110*(1-p); lower=-120*(1-p)
    left=path([[-630,165,0],[-400,150,0],[-170,upper, -140],[-18,upper,-190]],150)
    right=path([[18,lower,-190],[170,lower,-140],[400,-130,0],[630,-110,0]],150)
    strand(s,left,CYAN,4.6); strand(s,right,ORANGE,4.6)
    if not joined:
        # Intronic extensions retain splice substrates rather than joining mature ends.
        a=path([left[-1],[35,upper+85,-160],[120,upper+160,-90]],65)
        b=path([[-130,lower-165,-90],[-40,lower-80,-160],right[0]],65)
        strand(s,a,PALE,3.7); strand(s,b,PALE,3.7)
    else:
        shift=110*ease((t-18.1)/2.4)
        left[:,1]+=shift; right[:,1]+=shift
        s=Scene()
        strand(s,left,CYAN,4.6); strand(s,right,ORANGE,4.6)
        strand(s,path([left[-1],[0,shift,-190],right[0]],24),np.array([CYAN]*12+[ORANGE]*12),4.6)
    # Composite foreground RNA over a true-coordinate complex, as a cutaway schematic.
    base=splice_base().copy(); overlay=s.render()
    blank=Scene().render(); mask=Image.fromarray(np.any(np.asarray(overlay)!=np.asarray(blank),axis=2).astype('uint8')*255)
    base.paste(overlay,(0,0),mask)
    d=ImageDraw.Draw(base)
    if not joined:
        d.text((230,220),'RNA A',font=ft(43,True),anchor='mm',fill=CYAN)
        d.text((1240,650),'RNA B',font=ft(43,True),fill=ORANGE)
    else:
        d.text((800,210),'Chimeric mRNA',font=ft(45,True),anchor='mm',fill=INK)
    d.text((800,825),'Spliceosome',font=ft(37),anchor='mm',fill=VIOLET)
    return headers(base,'Chimeric mRNA','Trans-splicing')

def comparison(t):
    s=Scene(); angle=-.30+(t-24.5)*.085
    ribbon(s,'1UBQ',(-520,15,0),8.5,CYAN,angle)
    ribbon(s,'1MBN',(-15,15,0),6.5,ORANGE,angle+.30)
    fusion(s,(490,15,0),6.0,angle*.7)
    s.label(280,730,'Protein A',43,CYAN)
    s.label(785,730,'Protein B',43,ORANGE)
    s.label(1300,730,'Fusion protein',43)
    im=s.render(); d=ImageDraw.Draw(im)
    d.text((800,110),'Different sequences. Different structures.',font=ft(46,True),anchor='mm',fill=INK)
    d.text((1300,798),'Illustrative fold',font=ft(25),anchor='mm',fill=GREY)
    return im

def raw_frame(t):
    if t<1.8: return card('01','Central dogma','DNA → RNA → protein',t)
    if t<5.5: return transcription(t)
    if t<9.5: return translation(t,5.5,9.5)
    if t<11.5: return card('02','Chimeric mRNA','Two RNAs → one new message',t)
    if t<20.5: return splicing(t)
    if t<24.5: return translation(t,20.5,24.5,True)
    return comparison(t)

def frame(t):
    # Short editorial dissolves separate mechanisms without a rushed object morph.
    for boundary in [1.8,5.5,9.5,11.5,20.5,24.5]:
        if boundary<=t<boundary+.28:
            return Image.blend(raw_frame(boundary-.001),raw_frame(t),float(ease((t-boundary)/.28)))
    return raw_frame(t)

TIMELINE=[
 ('0–1.8 s','Title: central dogma',.9),
 ('1.8–5.5 s','RNA emerges from polymerase',4.6),
 ('5.5–9.5 s','Canonical translation',8.8),
 ('9.5–11.5 s','Title: chimeric mRNA',10.4),
 ('11.5–18.1 s','Two RNAs at the spliceosome',15.5),
 ('18.1–20.5 s','One joined RNA',19.8),
 ('20.5–24.5 s','Fusion-protein translation',23.8),
 ('24.5–30 s','Hold: three ribbon structures',28.0),
]

def preview():
    sheet=Image.new('RGB',(1600,2050),(233,236,239)); d=ImageDraw.Draw(sheet)
    d.text((45,35),'REVISED STORYBOARD  /  30 SECONDS',font=ft(32,True),fill=INK)
    for i,(timing,label,t) in enumerate(TIMELINE):
        im=frame(t); im.save(ROOT/f'frame_{i+1:02d}.png')
        small=im.resize((760,428),Image.Resampling.LANCZOS)
        x=30+(i%2)*800; y=110+(i//2)*480
        sheet.paste(small,(x,y)); d.text((x+10,y+442),timing+'  ·  '+label,font=ft(22),fill=INK)
    sheet.save(ROOT/'storyboard_v2.jpg',quality=95)
    comparison(28).save(ROOT/'poster_v2.jpg',quality=96)
    print('Storyboard ready',flush=True)

def main():
    preview()
    if '--preview' in sys.argv: return
    writer=imageio_ffmpeg.write_frames(str(ROOT/'trans_splicing_v2_30s.mp4'),(W,H),fps=FPS,codec='libx264',quality=8,macro_block_size=1,output_params=['-movflags','+faststart','-r','24'])
    writer.send(None)
    for i in range(720):
        writer.send(np.asarray(frame(i/FPS)))
        if i%48==0: print(f'{i}/720 frames',flush=True)
    writer.close(); print('Finished 720 frames',flush=True)

if __name__=='__main__': main()
