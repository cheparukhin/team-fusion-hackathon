"""Procedural, perspective-rendered molecular explainer; 720 frames / 24 fps."""
import sys
sys.path.insert(0, '/tmp/chimera_animation_libs')
import math
import functools
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

OUT = Path(__file__).resolve().parent
W, H, FPS = 1280, 720, 24
A = (69, 205, 246)
B = (255, 153, 84)
V = (162, 129, 234)
G = (116, 210, 191)
GOLD = (228, 203, 139)
WHITE = (229, 242, 253)
MUTED = (155, 177, 204)
INTRON = (91, 115, 155)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def clamp(x): return max(0., min(1., x))
def smooth(x):
    x = clamp(x)
    return x*x*(3-2*x)
def mix(a,b,t): return np.asarray(a)*(1-t)+np.asarray(b)*t
def font(n,b=False): return ImageFont.truetype(BOLD if b else FONT,n)

yy,xx = np.mgrid[:H,:W]
light = np.exp(-((xx-690)**2/400000+(yy-330)**2/125000))
back = np.stack([5+8*light, 13+23*light, 31+36*light],axis=-1).astype('uint8')
BG = Image.fromarray(back)
del xx,yy,light,back

@functools.lru_cache(maxsize=12000)
def sphere(r,col):
    r=max(2,r)
    q=np.linspace(-1,1,2*r+1)
    x,y=np.meshgrid(q,q)
    d=x*x+y*y
    z=np.sqrt(np.maximum(0,1-d))
    shade=.30+.63*np.maximum(0,-.46*x-.55*y+.69*z)
    spec=.26*np.maximum(0,-.32*x-.41*y+.85*z)**24
    rim=.13*(1-z)**2
    rgb=np.clip(np.array(col)[None,None,:]*(shade+rim)[...,None]+255*spec[...,None],0,255)
    alpha=np.clip((1-d)*r,0,1)*255
    return Image.fromarray(np.dstack([rgb,alpha]).astype('uint8'))

class World:
    def __init__(self,t):
        self.t=t; self.balls=[]; self.labels=[]
        self.angle=.045*math.sin(t*.32)
    def project(self,p):
        x,y,z=p
        c,s=math.cos(self.angle),math.sin(self.angle)
        x,z=x*c+z*s,-x*s+z*c
        f=930/(18+z)
        return W/2+x*f, H/2-y*f, f,z
    def ball(self,p,r,c): self.balls.append((tuple(p),r,tuple(c)))
    def line(self,pts,c,r=.05):
        for p in pts: self.ball(p,r,c)
    def label(self,p,text,color=WHITE,size=20): self.labels.append((p,text,color,size))
    def render(self):
        im=BG.copy()
        # Defocused nuclear/cytoplasmic material provides depth without clutter.
        haze=Image.new('RGBA',(W,H))
        d=ImageDraw.Draw(haze)
        for k in range(18):
            x=(k*227+math.sin(k+self.t*.05)*25)%W
            y=175+(k*139)%440
            r=18+k%4*9
            d.ellipse((x-r,y-r,x+r,y+r),fill=(44,101,154,14))
        im.paste(haze.filter(ImageFilter.GaussianBlur(16)),(0,0),haze.filter(ImageFilter.GaussianBlur(16)))
        for p,r,c in sorted(self.balls,key=lambda b:self.project(b[0])[3],reverse=True):
            x,y,f,z=self.project(p)
            rr=int(max(2,min(90,r*f)))
            if x+rr<0 or y+rr<125 or x-rr>W or y-rr>600: continue
            spr=sphere(rr,c)
            im.paste(spr,(round(x)-rr,round(y)-rr),spr)
        d=ImageDraw.Draw(im)
        for p,txt,c,n in self.labels:
            x,y,_,_=self.project(p)
            box=d.textbbox((0,0),txt,font=font(n))
            width=box[2]
            d.rounded_rectangle((x-width/2-9,y-5,x+width/2+9,y+n+7),radius=7,fill=(8,20,42))
            d.text((x,y),txt,font=font(n),anchor='mt',fill=c)
        return im

def curve(a,b,n=90,bend=.0):
    ts=np.linspace(0,1,n)
    pts=np.array([mix(a,b,t) for t in ts])
    pts[:,1]+=bend*np.sin(ts*np.pi)
    return pts

def rna(w,start,end,c,progress=1,intron=False,phase=0,chimera=False):
    pts=curve(start,end,105)
    for i,p in enumerate(pts[:max(1,int(105*progress))]):
        u=i/104
        p=p.copy(); p[1]+=.13*math.sin(i*.32+phase); p[2]+=.14*math.cos(i*.32+phase)
        color=(A if u<.5 else B) if chimera else c
        if intron and .37<u<.63: color=INTRON
        w.ball(p,.078,color)
        if i%3==0:
            q=p+np.array([0,.17,.08])
            w.ball(q,.063,tuple(min(255,int(v*.8+45)) for v in color))
    return pts

def dna(w,center,length=13,color=A,phase=0):
    n=int(length*15)
    for i in range(n):
        x=-length/2+length*i/(n-1)
        theta=x*3.1+phase
        for strand in [0,math.pi]:
            p=np.array(center)+[x,.32*math.cos(theta+strand),.32*math.sin(theta+strand)]
            w.ball(p,.083,color)
        if i%4==0:
            for u in np.linspace(-1,1,6):
                p=np.array(center)+[x,.32*math.cos(theta)*u,.32*math.sin(theta)*u]
                w.ball(p,.058,(180,207,214) if u<0 else (230,211,170))

@functools.lru_cache(None)
def cluster(seed,n):
    rng=np.random.default_rng(seed)
    pts=rng.normal(size=(n,3)); pts/=np.linalg.norm(pts,axis=1)[:,None]
    pts*=rng.uniform(.75,1.,n)[:,None]
    return pts

def protein(w,center,color,scale=1,seed=3,n=210,rotation=0,elong=(1,1,1),fraction=1):
    pts=cluster(seed,n)[:int(n*fraction)]
    ca,sa=math.cos(rotation),math.sin(rotation)
    for i,p in enumerate(pts):
        p=p.copy()*np.array(elong)*scale
        p=np.array([p[0]*ca+p[2]*sa,p[1],-p[0]*sa+p[2]*ca])
        col=tuple(max(0,min(255,int(v*(.90+(i%7)*.025)))) for v in color)
        w.ball(np.asarray(center)+p,.18*scale,col)

def polymerase(w,p):
    protein(w,p,GOLD,.62,17,180,elong=(1.2,1,.9))
    protein(w,np.asarray(p)+[.35,.2,.2],(169,181,204),.38,11,80)

def spliceosome(w,p,scale=1,opened=0):
    for k in range(5):
        th=k*math.tau/5
        center=np.asarray(p)+[(.66+opened)*math.cos(th),(.60+opened)*math.sin(th),.28*math.sin(th*2)]
        col=[V,(130,109,202),(188,159,241),(116,141,218),(149,103,205)][k]
        protein(w,center,col,.43*scale,k+40,95,rotation=w.t*.12)
    for k in range(55):
        a=k/54*math.tau
        w.ball(np.asarray(p)+[.57*math.cos(a),.50*math.sin(a),-.05],.052,(231,187,240))

def ribosome(w,p):
    protein(w,np.asarray(p)+[0,.65,.1],G,1,81,260,elong=(1.15,.8,.85))
    protein(w,np.asarray(p)+[0,-.47,.05],GOLD,.73,88,190,elong=(1.25,.56,.86))

def envelope(w,x=3.0):
    # Two layers with an open nuclear-pore channel at y=0.
    for off in [0,.17]:
        for y in np.linspace(-3.8,3.8,100):
            if abs(y)<.48: continue
            w.ball((x+off,y,1.5),.057,(71,103,154))
    for a in np.linspace(0,math.tau,55):
        w.ball((x+.08,.49*math.cos(a),1.5+.49*math.sin(a)),.10,(148,164,190))
    w.label((x-1.6,-3.3,0),'NUCLEUS',MUTED,15)
    w.label((x+2,-3.3,0),'CYTOPLASM',MUTED,15)

def fold(w,p,t,scale=1,both=True):
    rot=t*.42
    protein(w,np.asarray(p)+[-.67*scale,0,0],A,scale,32,250,rotation=rot,elong=(1,.8,.85))
    if both:
        protein(w,np.asarray(p)+[.84*scale,-.05,0],B,scale*.85,33,220,rotation=rot,elong=(1,.9,.8))
        for k in range(15):
            w.ball(np.asarray(p)+[-.1*scale+k*.043*scale,.09*math.sin(k*.5),.2],.12*scale,A if k<7 else B)

def chromatin(w,t):
    near=smooth((t-6)/3.8)
    for k,col in enumerate([A,B]):
        side=-1 if k==0 else 1
        cx=side*(4.0-2.1*near)
        cy=.45 if k==0 else -.45
        for i in range(250):
            a=i/249*math.tau
            p=np.array([cx+2.2*math.cos(a),cy+2.4*math.sin(a),.65*math.sin(a*2)])
            w.ball(p,.065,col)
            if i%21==0:
                protein(w,p,tuple(int(v*.65) for v in col),.22,9+i,35)
        w.label((side*5.2,3.15,0),'Gene A' if k==0 else 'Gene B',col,24)
    if near>.7:
        for k in range(7):
            w.ball((-.22+k*.075,0,.6),.045,(203,214,231))

def frame(t):
    w=World(t)
    if t<6:
        chapter='01 / THE CANONICAL PATHWAY'
        title='From a gene to a protein'
        if t<2:
            p=smooth(t/1.75)
            dna(w,(0,1.1,0),14,A)
            x=-5.5+11*p
            polymerase(w,(x,1.1,0))
            rna(w,(-5.5,-1.0,0),(x,-1.0,0),A,intron=True)
            w.line(curve((x,-1,0),(x,1.05,0),25),A,.065)
            w.label((-6,2.2,0),'Gene A',A,24)
            w.label((0,-2,0),'pre-mRNA: exons + intron',WHITE,23)
            caption='Transcription copies DNA into a precursor RNA.'
        elif t<4:
            p=smooth((t-2)/1.6)
            rna(w,(-6,0,0),(-.35,0,0),A)
            rna(w,(.35,0,0),(6,0,0),A)
            spliceosome(w,(0,0,.2),opened=.45*p)
            if p<.85:
                for k in range(65):
                    a=k/64*math.tau
                    w.ball((.65*math.cos(a),1+p+.50*math.sin(a),.1),.067,INTRON)
                w.line(curve((.65,1+p,.1),(1.2,1.6+p,.1),22),INTRON,.067)
                w.label((0,2.9,0),'Intron removed',MUTED,21)
            else: rna(w,(-.4,0,0),(.4,0,0),A)
            w.label((-4,-1,0),'Exon',A,22); w.label((4,-1,0),'Exon',A,22)
            caption='Cis-splicing joins exons from the same RNA.'
        else:
            p=smooth((t-4)/1.7)
            envelope(w,-4.3)
            rna(w,(-3.5,0,0),(6,0,0),A)
            x=-2.5+6*p; ribosome(w,(x,0,0))
            for i in range(int(70*p)):
                a=i*.3
                w.ball((x+.20*math.sin(a),1.3+i*.028,.2*math.cos(a)),.092,A)
            w.label((0,-1.6,0),'mRNA → protein',A,25)
            caption='After nuclear export, a ribosome translates the mRNA.'
        note='One canonical example • genes can also produce multiple isoforms'
    elif t<13:
        chapter='02 / A SHARED NUCLEAR NEIGHBORHOOD'
        title='Two genes. Two separate transcripts.'
        if t<9.8:
            chromatin(w,t)
            caption='Chromatin contacts can bring separate genes close together.'
        else:
            p=smooth((t-9.8)/2.7)
            for y,col,name in [(1.7,A,'A'),(-1.7,B,'B')]:
                dna(w,(-3,y,0),7,col,phase=.3)
                x=-5.7+5.2*p; polymerase(w,(x,y,0))
                dest=(5.4,y*.50,0)
                rna(w,(x,y-.55,0),dest,col,progress=p,intron=True)
                w.label((-7.4,y+.4,0),'Gene '+name,col,22)
                w.label((5.4,y*1.2,0),'pre-mRNA '+name,col,22)
            caption='Each gene is transcribed independently.'
        note='Mechanistic model • CTCF-dependent proximity supported by Venezia et al., 2026'
    elif t<21:
        chapter='03 / TRANS-SPLICING'
        title='Joining RNA from different genes'
        p=smooth((t-13)/3)
        yy=1.25*(1-p)
        # 5′ exon A approaches the donor; B's 3′ exon approaches its acceptor.
        rna(w,(-7,yy,0),(-.25,yy,0),A)
        rna(w,(.25,-yy,0),(7,-yy,0),B)
        cut=smooth((t-16.5)/2)
        if t<19:
            shift=1.8*smooth((cut-.3)/.7)
            rna(w,(-.25,yy+shift,0),(1.6,2+shift,0),INTRON)
            rna(w,(-1.6,-2-shift,0),(.25,-yy-shift,0),INTRON)
            if cut>.65: rna(w,(-.3,0,0),(.3,0,0),A,chimera=True)
            spliceosome(w,(0,0,.4),opened=.65*cut)
            w.label((-3,1.9,0),'5′ donor · A',A,23)
            w.label((3,-2.1,0),'3′ acceptor · B',B,23)
            caption='The spliceosome recognizes sites on two precursor RNAs.' if t<16.5 else 'Selected exons join; intervening RNA is released.'
        else:
            rna(w,(-.3,0,0),(.3,0,0),A,chimera=True)
            w.label((0,1.3,0),'A–B junction',WHITE,23)
            w.label((0,-1.8,0),'Chimeric mRNA',WHITE,29)
            caption='One continuous RNA now contains sequence from both genes.'
        w.label((-7.3,-.9,0),'5′',A,24); w.label((7.3,.8,0),'3′',B,24)
        note='Selective RNA joining • DNA remains separate • molecular choreography is schematic'
    elif t<28:
        chapter='04 / TRANSLATION'
        title='A chimeric RNA can encode a fusion protein'
        if t<22.5:
            envelope(w,0)
            p=smooth((t-21)/1.5)
            start=-8+9*p
            rna(w,(start,0,0),(start+6,0,0),A,chimera=True)
            w.label((0,2.0,0),'Nuclear export',WHITE,24)
            caption='The processed chimeric mRNA enters the cytoplasm.'
        elif t<26.4:
            p=clamp((t-22.5)/3.7)
            rna(w,(-7,-.8,0),(7,-.8,0),A,chimera=True)
            x=-5.3+10.6*p
            ribosome(w,(x,-.8,0))
            for i in range(max(1,int(100*p))):
                # N terminus is the oldest, distal portion; C terminus grows at ribosome.
                u=i/max(1,int(100*p)-1)
                color=A if i<50 else B
                w.ball((x+.34*math.sin(u*13),.4+(1-u)*2.6,.28*math.cos(u*13)),.095,color)
            w.label((-7,-1.7,0),'5′',A,23); w.label((7,-1.7,0),'3′',B,23)
            w.label((0,-2.4,0),'Ribosome reads 5′ → 3′',WHITE,23)
            caption='A translatable reading frame produces one connected polypeptide.'
        else:
            fold(w,(0,.1,0),t,1.65)
            w.label((-4.0,-2.1,0),'A-derived region',A,24)
            w.label((4.0,-2.1,0),'B-derived region',B,24)
            caption='The combined sequence can confer different protein properties.'
        note='Protein production depends on the resulting open reading frame • generic A/B example'
    else:
        chapter='FROM TWO TRANSCRIPTS TO ONE PRODUCT'
        title='New sequence. New protein possibilities.'
        fold(w,(-5,1.05,0),t,.72,False)
        protein(w,(-5,-1.25,0),B,.70,33,200,rotation=t*.3)
        fold(w,(4,0,0),t,1.5)
        w.label((-2.3,1.45,0),'A → protein A',A,22)
        w.label((-2.3,-.85,0),'B → protein B',B,22)
        w.label((4,-2.2,0),'A + B RNA → fusion protein',WHITE,23)
        caption='Trans-splicing combines RNA sequences without joining the DNA.'
        note='Illustrative molecular models • time and scale compressed • Venezia et al., Nature (2026)'
    im=w.render(); d=ImageDraw.Draw(im)
    d.text((48,28),chapter,font=font(17,True),fill=A)
    d.text((48,62),title,font=font(32,True),fill=WHITE)
    d.text((1230,33),f'{min(30,int(t)):02d} / 30 s',font=font(16),anchor='ra',fill=MUTED)
    d.line((48,117,1232,117),fill=(45,64,87),width=1)
    # Footer has its own opaque field, maintaining consistent caption contrast.
    d.rectangle((0,608,W,H),fill=(6,16,34))
    d.text((W//2,626),caption,font=font(23),anchor='mt',fill=WHITE)
    d.text((W//2,671),note,font=font(15),anchor='mt',fill=MUTED)
    for i,(a,b) in enumerate([(0,6),(6,13),(13,21),(21,30)]):
        x=48+i*300
        d.rounded_rectangle((x,707,x+281,711),radius=2,fill=(36,53,74))
        progress=clamp((t-a)/(b-a))
        if progress>0: d.rounded_rectangle((x,707,x+max(2,281*progress),711),radius=2,fill=A if i<2 else B)
    return im

def main():
    samples=[1.3,3,5.3,8.7,11.8,15,17.5,20,21.8,24.3,27,29]
    sheet=Image.new('RGB',(1280,1080),(4,12,26))
    for i,t in enumerate(samples):
        pic=frame(t).resize((426,240),Image.Resampling.LANCZOS)
        sheet.paste(pic,((i%3)*426,(i//3)*270))
        ImageDraw.Draw(sheet).text(((i%3)*426+12,(i//3)*270+243),f'{t:.1f} seconds',font=font(16),fill=WHITE)
    sheet.save(OUT/'storyboard.jpg',quality=93)
    frame(27).save(OUT/'poster.jpg',quality=95)
    if '--preview' in sys.argv: return
    writer=imageio_ffmpeg.write_frames(str(OUT/'trans_splicing_30s.mp4'),(W,H),fps=FPS,codec='libx264',quality=8,macro_block_size=1,output_params=['-pix_fmt','yuv420p','-movflags','+faststart'])
    writer.send(None)
    for i in range(FPS*30):
        writer.send(np.asarray(frame(i/FPS)))
        if i%72==0: print(f'Rendered {i}/{FPS*30} frames',flush=True)
    writer.close()
    print('Complete: 720 frames, 30.000 seconds',flush=True)

if __name__=='__main__': main()
