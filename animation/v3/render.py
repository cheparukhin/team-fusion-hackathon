"""4K, depth-buffered molecular animation with atomic nucleotides and PDB ribosome.
Uses OpenGL sphere impostors with analytic surface depth, real ribbon meshes,
contact occlusion, multi-light shading, fog, bloom and selective depth of field.
"""
import sys, os
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
sys.path.insert(0,'/tmp/chimera_animation_libs')
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'v2'))
import render as old
import math, functools, time, json
import numpy as np
import gemmi, moderngl, imageio_ffmpeg
from scipy.interpolate import CubicSpline
from PIL import Image,ImageDraw,ImageFont

W,H,FPS=3840,2160,24
CYAN=np.array([84,193,227])/255
ORANGE=np.array([237,155,83])/255
PURPLE=np.array([146,132,203])/255
BACKBONE=np.array([230,241,239])/255
BASE={ 'A':np.array([124,196,141])/255, 'C':np.array([87,163,224])/255,
       'G':np.array([144,122,218])/255, 'T':np.array([216,114,107])/255,
       'U':np.array([216,114,107])/255 }
RAD={'C':1.70,'N':1.55,'O':1.52,'P':1.80,'S':1.80,'MG':1.45,'ZN':1.4}
def ease(x): return float(old.ease(x))
def norm(x): return old.norm(np.asarray(x))
def path(p,n=150): return old.path(p,n)
def rot(*args,**kwargs): return old.rot(*args,**kwargs)
def xyz(a): return old.pos(a)

ATOM_VERTEX='''#version 330
in vec3 in_pos; in float in_rad; in vec3 in_color;
uniform vec2 resolution; uniform mat3 camera;
out vec3 color; out vec3 center; out float radius;
void main(){
 center=camera*in_pos; radius=in_rad; color=in_color;
 float f=1800.0/(1800.0+center.z);
 gl_Position=vec4(center.x*f/800.,center.y*f/450.,2.*(center.z+1000.)/4000.-1.,1.);
 gl_PointSize=2.*radius*f*resolution.x/1600.+2.;
}
'''
LIGHTING='''
vec3 illuminate(vec3 col,vec3 normal,vec3 p){
 vec3 key=normalize(vec3(-.55,.75,-.80));
 vec3 fill=normalize(vec3(.8,.15,-.35));
 vec3 rim=normalize(vec3(.15,.65,.75));
 float k=max(dot(normal,key),0.); float f=max(dot(normal,fill),0.);
 float r=max(dot(normal,rim),0.);
 vec3 v=vec3(0,0,-1);
 float spec=pow(max(dot(normal,normalize(key+v)),0.),40.);
 float spec2=pow(max(dot(normal,normalize(fill+v)),0.),55.);
 float edge=pow(1.-max(dot(normal,v),0.),3.);
 vec3 outc=col*(vec3(.13,.20,.17)+vec3(1.02,.96,.80)*k*1.10+vec3(.32,.52,.66)*f*.44);
 outc+=vec3(1.,.94,.81)*spec*.62+vec3(.53,.75,1.)*spec2*.22;
 outc+=vec3(.62,.85,.74)*r*.48*edge;
 float fog=clamp((p.z-120.)/1250.,0.,.82);
 return mix(outc,vec3(.21,.36,.29),fog);
}
'''
ATOM_FRAGMENT='''#version 330
in vec3 color; in vec3 center; in float radius;
out vec4 frag;
'''+LIGHTING+'''
void main(){
 vec2 q=gl_PointCoord*2.-1.; q.y=-q.y;
 float d=dot(q,q); if(d>1.) discard;
 float z=sqrt(1.-d); vec3 n=vec3(q,-z);
 vec3 p=center+vec3(q*radius,-z*radius);
 gl_FragDepth=(p.z+1000.)/4000.;
 frag=vec4(illuminate(color,n,p),1.);
}
'''
MESH_VERTEX='''#version 330
in vec3 in_pos; in vec3 in_normal; in vec3 in_color;
uniform mat3 camera;
out vec3 color; out vec3 normal; out vec3 position;
void main(){
 position=camera*in_pos; normal=normalize(camera*in_normal); color=in_color;
 float f=1800./(1800.+position.z);
 gl_Position=vec4(position.x*f/800.,position.y*f/450.,2.*(position.z+1000.)/4000.-1.,1.);
}
'''
MESH_FRAGMENT='''#version 330
in vec3 color; in vec3 normal; in vec3 position; out vec4 frag;
'''+LIGHTING+'''
void main(){vec3 n=normalize(normal); if(!gl_FrontFacing)n=-n; frag=vec4(illuminate(color,n,position),1.);}
'''
QUAD='''#version 330
in vec2 in_pos; out vec2 uv;
void main(){uv=in_pos*.5+.5;gl_Position=vec4(in_pos,0,1);}
'''
BACKGROUND='''#version 330
in vec2 uv; out vec4 frag; uniform float time;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f); return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.),f.x),f.y);}
void main(){
 vec2 p=uv; float cloud=noise(p*3.+time*.003)*.6+noise(p*7.-time*.002)*.3;
 float glow=exp(-dot((p-vec2(.3,.8))*vec2(1.3,1.),(p-vec2(.3,.8))*vec2(1.3,1.))*2.);
 vec3 col=mix(vec3(.055,.16,.14),vec3(.33,.52,.35),glow*.70+cloud*.3);
 float shaft=pow(max(0.,sin((p.x+p.y*.3)*10.+.7)),16.);
 col+=vec3(.22,.25,.14)*shaft*.28*p.y;
 float vign=smoothstep(.8,.12,length((p-.5)*vec2(1.,.8)));
 col*=.80+.20*vign;
 frag=vec4(col,1.);
}
'''
POST='''#version 330
in vec2 uv; out vec4 frag;
uniform sampler2D scene; uniform sampler2D depthmap; uniform vec2 resolution;
vec2 samplepos(int i){
 float a=float(i)*2.399963; float r=sqrt((float(i)+.5)/8.); return vec2(cos(a),sin(a))*r;
}
void main(){
 float depth=texture(depthmap,uv).r;
 float z=depth*4000.-1000.; vec3 col=texture(scene,uv).rgb;
 float ao=0.;
 if(depth<.95){
  for(int i=0;i<8;i++){
   vec2 q=uv+samplepos(i)*13.*resolution.x/1600./resolution;
   float d=depth-texture(depthmap,q).r;
   ao+=smoothstep(.00015,.0015,d)*(1.-smoothstep(.012,.035,d));
  }
  col*=1.-ao/8.*.38;
 }
 float blur=clamp((abs(z+65.)-110.)*.045,0.,42.);
 if(depth>.95)blur=0.;
 if(blur>1.){
  vec3 sum=col; float total=1.;
  for(int i=0;i<8;i++){
   vec2 q=uv+samplepos(i)*blur*resolution.x/1600./resolution;
   float qd=texture(depthmap,q).r;
   float weight=1.-smoothstep(.02,.10,abs(qd-depth));
   sum+=texture(scene,q).rgb*weight;total+=weight;
  }
  col=mix(col,sum/total,min(1.,blur/6.));
 }
 // Restrained bloom catches the pearly nucleotide backbone and rim light.
 vec3 bloom=vec3(0);
 for(int i=0;i<4;i++){
  vec2 q=uv+samplepos(i)*8.*resolution.x/1600./resolution;
  bloom+=max(texture(scene,q).rgb-.72,0.);
 }
 col+=bloom*.045;
 col=1.-exp(-col*1.27);
 col=pow(col,vec3(.82));
 frag=vec4(col,1.);
}
'''

class Renderer:
 def __init__(self,w=W,h=H):
  self.w,self.h=w,h; self.ctx=moderngl.create_standalone_context(backend='egl')
  self.atoms=self.ctx.program(vertex_shader=ATOM_VERTEX,fragment_shader=ATOM_FRAGMENT)
  self.mesh=self.ctx.program(vertex_shader=MESH_VERTEX,fragment_shader=MESH_FRAGMENT)
  self.bg=self.ctx.program(vertex_shader=QUAD,fragment_shader=BACKGROUND)
  self.post=self.ctx.program(vertex_shader=QUAD,fragment_shader=POST)
  self.quad=self.ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes())
  self.bgvao=self.ctx.simple_vertex_array(self.bg,self.quad,'in_pos')
  self.postvao=self.ctx.simple_vertex_array(self.post,self.quad,'in_pos')
  self.color=self.ctx.texture((w,h),4,dtype='f2'); self.color.filter=(moderngl.LINEAR,moderngl.LINEAR)
  self.depth=self.ctx.depth_texture((w,h)); self.depth.compare_func=''
  self.fbo=self.ctx.framebuffer([self.color],self.depth)
  self.final=self.ctx.simple_framebuffer((w,h),components=3)
  self.atoms['resolution'].value=(w,h); self.post['resolution'].value=(w,h)
  self.post['scene'].value=0; self.post['depthmap'].value=1
 def render(self,s,t):
  ctx=self.ctx; self.fbo.use();ctx.viewport=(0,0,self.w,self.h)
  self.fbo.clear(0,0,0,1,depth=1)
  ctx.disable(moderngl.DEPTH_TEST);self.bg['time'].value=t
  self.bgvao.render(moderngl.TRIANGLE_STRIP)
  ctx.enable(moderngl.DEPTH_TEST|moderngl.PROGRAM_POINT_SIZE)
  camera=rot(y=.025*math.sin(t*.24),x=.012*math.sin(t*.18))
  self.atoms['camera'].write(camera.T.astype('f4').tobytes()); self.mesh['camera'].write(camera.T.astype('f4').tobytes())
  if s.atoms:
   data=np.concatenate(s.atoms).astype('f4'); buf=ctx.buffer(data.tobytes())
   vao=ctx.vertex_array(self.atoms,[(buf,'3f 1f 3f','in_pos','in_rad','in_color')]);vao.render(moderngl.POINTS)
   vao.release();buf.release()
  for data in s.meshes:
   buf=ctx.buffer(data.astype('f4').tobytes());vao=ctx.vertex_array(self.mesh,[(buf,'3f 3f 3f','in_pos','in_normal','in_color')]);vao.render(moderngl.TRIANGLES);vao.release();buf.release()
  self.final.use();ctx.disable(moderngl.DEPTH_TEST);self.color.use(0);self.depth.use(1)
  self.postvao.render(moderngl.TRIANGLE_STRIP)
  image=Image.frombytes('RGB',(self.w,self.h),self.final.read(components=3,alignment=1)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  return image

class Scene:
 def __init__(self): self.atoms=[]; self.meshes=[]; self.labels=[]
 def points(self,p,r,c):
  p=np.asarray(p); n=len(p)
  self.atoms.append(np.column_stack([p,np.broadcast_to(r,(n,)),np.broadcast_to(c,(n,3))]))
 def label(self,x,y,text,size=38,color=(235,244,240),bold=False): self.labels.append((x,y,text,size,color,bold))
 def tube(self,p,r,c): self.points(p,r,c)

def frame_basis(st,code):
 p=np.array([xyz(a) for c in st[0] for res in c for a in res if a.name=='CA'])
 center=np.median(p,axis=0)
 if code=='1Y1W':
  rr=np.array([xyz(res.find_atom("C4'",'*')) for res in st[0]['P']])
  y=norm(norm(rr[0]-rr[2])+norm(rr[0]-center)*.5)
  z=norm(np.cross(y,[1,0,0]));x=norm(np.cross(y,z));R=np.vstack([x,y,z])
 elif code=='4UG0':
  large=np.array([xyz(a) for c in st[0] if c.name.startswith('L') for res in c for a in res if a.name in ['CA',"C4'"]])
  small=np.array([xyz(a) for c in st[0] if c.name.startswith('S') and c.name!='S6' for res in c for a in res if a.name in ['CA',"C4'"]])
  trna=np.array([xyz(a) for r in st[0]['S6'] for a in r]);center=(large.mean(0)+small.mean(0))/2
  y=norm(large.mean(0)-small.mean(0)); z=trna.mean(0)-center;z=-norm(z-y*np.dot(z,y));x=norm(np.cross(y,z));R=np.vstack([x,y,z])
 else:
  _,_,R=np.linalg.svd(p-center,full_matrices=False)
  if np.linalg.det(R)<0:R[2]*=-1
 return center,R

def load_complex(code):
 file=(ROOT/'structures'/f'{code}.cif') if code=='4UG0' else ROOT.parent/'v2'/'structures'/f'{code}.cif'
 st=gemmi.read_structure(str(file)); center,R=frame_basis(st,code)
 pp=[];rr=[];cc=[]; chains={}
 for ci,c in enumerate(st[0]):
  coords=[]
  for res in c:
   if res.name in ['HOH','WAT']:continue
   isrna=res.name in ['A','G','U','C']
   isdna=res.name in ['DA','DG','DC','DT']
   for a in res:
    if a.element.name=='H' or a.altloc not in ['\x00','A',' ']:continue
    p=(xyz(a)-center)@R.T; pp.append(p);rr.append(RAD.get(a.element.name,1.6))
    if isrna or isdna:
     base=res.name[-1];color=BACKBONE if "'" in a.name or a.name in ['P','OP1','OP2','O1P','O2P'] else BASE.get(base,BASE['A'])
     if code=='5XJC':color=color*.80+PURPLE*.20
    elif code=='1Y1W': color=np.array([.62,.68,.77]) if ci%3 else np.array([.77,.66,.55])
    elif code=='4UG0': color=np.array([.39,.70,.66]) if c.name.startswith('L') else np.array([.83,.72,.47])
    else: color=PURPLE*np.array([.93+(ci%3)*.07,.92+(ci%4)*.035,1.])
    cc.append(color)
    if a.name=="C4'":coords.append(p)
  if coords:chains[c.name]=np.array(coords)
 return dict(p=np.array(pp),r=np.array(rr),c=np.clip(cc,0,1),chains=chains,structure=st)

MODELS={k:load_complex(k) for k in ['1Y1W','5XJC','4UG0']}

def complex(s,code,center=(0,0,0),scale=2,orientation=None):
 m=MODELS[code]; R=np.eye(3) if orientation is None else orientation
 s.points(m['p']@R.T*scale+center,m['r']*scale,m['c'])
 return {k:v@R.T*scale+center for k,v in m['chains'].items()}

def templates():
 sources=[(gemmi.read_structure(str(ROOT/'structures'/'1BNA.pdb')),'D'),(MODELS['4UG0']['structure'],'R')]
 out={}
 for st,kind in sources:
  for ch in st[0]:
   for res in ch:
    base=res.name[-1]
    if (kind=='D' and res.name not in ['DA','DG','DC','DT']) or (kind=='R' and res.name not in ['A','C','G','U']):continue
    if (kind,base) in out:continue
    c4=res.find_atom("C4'",'*'); p=res.find_atom('P','*'); o=res.find_atom("O3'",'*'); c1=res.find_atom("C1'",'*')
    gly=res.find_atom('N9','*') if base in ['A','G'] else res.find_atom('N1','*')
    if any(x is None for x in [c4,p,o,c1,gly]):continue
    axis=norm(xyz(o)-xyz(p));side=xyz(gly)-xyz(c1);side=norm(side-axis*np.dot(side,axis));up=norm(np.cross(axis,side));R=np.vstack([axis,side,up])
    aa=[a for a in res if a.element.name!='H' and a.altloc in ['\x00','A',' ']]
    coords=np.array([(xyz(a)-xyz(c4))@R.T for a in aa]); radii=np.array([RAD.get(a.element.name,1.6) for a in aa]);back=np.array(["'" in a.name or a.name in ['P','OP1','OP2','O1P','O2P'] for a in aa])
    out[(kind,base)]=(coords,radii,back)
   if sum(k[0]==kind for k in out)==4:break
 return out
TEMPLATES=templates()

def atom_rna(s,p,origin='A',scale=2.4,sequence='ACGU',reveal=1):
 p=np.asarray(p); ds=np.linalg.norm(np.diff(p,axis=0),axis=1); cumulative=np.r_[0,np.cumsum(ds)]
 length=cumulative[-1]*max(.015,reveal); locs=np.arange(0,length,5.4*scale)
 centers=np.column_stack([np.interp(locs,cumulative,p[:,i]) for i in range(3)])
 if len(centers)<2:return
 tang=norm(np.gradient(centers,axis=0));side=norm(np.cross(np.tile([0.,0.,1.],(len(tang),1)),tang));up=norm(np.cross(tang,side))
 for i,center in enumerate(centers):
  base=sequence[i%len(sequence)]; v,r,back=TEMPLATES[('R',base)]
  twist=.20*math.sin(i*.45); ss=side[i]*math.cos(twist)+up[i]*math.sin(twist);uu=np.cross(tang[i],ss)
  R=np.column_stack([tang[i],ss,uu]);pos=v@R.T*scale+center
  parent='A' if origin=='AB' and i<len(centers)/2 else ('B' if origin=='AB' else origin)
  tint=CYAN if parent=='A' else ORANGE
  backbone=BACKBONE*.75+tint*.25 if parent in ['A','B'] else np.array([.58,.64,.64])
  colors=np.where(back[:,None],backbone,BASE[base])
  s.points(pos,r*scale*.94,colors)
 # Closely spaced backbone atoms keep the stylized polymer path continuous.
 dense=np.column_stack([np.interp(np.linspace(0,length,int(length/3)+2),cumulative,p[:,i]) for i in range(3)])
 colors=np.array([BACKBONE*.55+(CYAN if (origin=='A' or (origin=='AB' and i<len(dense)/2)) else ORANGE)*.45 for i in range(len(dense))])
 if origin=='grey':colors[:]=[.58,.64,.64]
 s.points(dense,2.2*scale/2.4,colors)

def atomic_dna(s,center,axis,length=440,scale=2.3,phase=0):
 axis=norm(axis);u=norm(np.cross(axis,[0,0,1.]));v=norm(np.cross(axis,u));seq='CGCGAATTCGCG'
 n=int(length/(3.4*scale))
 for strand in range(2):
  for i in range(n):
   z=(i-(n-1)/2)*3.4*scale;th=i*math.radians(34.3)+strand*math.pi+phase
   radial=math.cos(th)*u+math.sin(th)*v;circ=-math.sin(th)*u+math.cos(th)*v
   center_i=np.asarray(center)+axis*z+radial*9.2*scale
   tangent=norm(axis*3.4+circ*5.4)*(1 if strand==0 else -1)
   side=-radial;up=norm(np.cross(tangent,side));side=norm(np.cross(up,tangent))
   base=seq[i%len(seq)];base=({'A':'T','T':'A','C':'G','G':'C'}[base] if strand else base)
   pts,r,back=TEMPLATES[('D',base)]
   R=np.column_stack([tangent,side,up]);colors=np.where(back[:,None],BACKBONE,BASE[base])
   s.points(pts@R.T*scale+center_i,r*scale*.92,colors)

@functools.lru_cache(None)
def mesh_data(code,start=0,stop=10000):
 v,f,a,b=old.ribbon_mesh(code,start,stop)
 # Smooth shading over a genuine 3D ribbon, with opaque depth-tested geometry.
 tri=np.concatenate([f[:,[0,1,2]],f[:,[0,2,3]]]);tn=np.cross(v[tri[:,1]]-v[tri[:,0]],v[tri[:,2]]-v[tri[:,0]])
 normal=np.zeros_like(v)
 for j in range(3):np.add.at(normal,tri[:,j],tn)
 return v,tri,norm(normal),a,b

def ribbon(s,code,center,scale,color,angle=0,part=(0,10000),Rextra=None):
 v,f,n,a,b=mesh_data(code,*part);R=rot(y=angle,x=.1,z=.1)
 if Rextra is not None:R=Rextra@R
 verts=v@R.T*scale+center;normal=n@R.T
 s.meshes.append(np.column_stack([verts[f].reshape(-1,3),normal[f].reshape(-1,3),np.tile(color,(len(f)*3,1))]))
 return a@R.T*scale+center,b@R.T*scale+center

def fusion(s,center,scale=6,angle=0):
 R=rot(y=angle,x=-.2,z=-.26);a=np.array(center)+np.array([-15,10,0])@R.T*scale;b=np.array(center)+np.array([15,-8,0])@R.T*scale
 _,a1=ribbon(s,'1UBQ',a,scale,CYAN,part=(1,64),Rextra=R)
 b0,_=ribbon(s,'1MBN',b,scale*.8,ORANGE,part=(30,130),Rextra=R@rot(z=1.15))
 p=path([a1,(a1+b0)/2+[0,15,10],b0],100)
 s.points(p,2.1,np.array([CYAN if i<50 else ORANGE for i in range(100)]))

@functools.lru_cache(None)
def cell_context():
 s=Scene();rng=np.random.default_rng(73)
 ca=old.RIBBON['1UBQ'][0]
 for i in range(24):
  center=np.array([rng.uniform(-1750,1750),rng.uniform(-1100,1100),rng.uniform(650,1300)])
  R=rot(*rng.uniform(-3,3,3));p=ca@R.T*rng.uniform(3,7)+center
  s.points(p,rng.uniform(5,8),[.35,.53,.40] if i%3 else [.48,.59,.48])
 # Distant crowded macromolecules provide depth without a schematic cell outline.
 return np.concatenate(s.atoms)

def transcription(t):
 s=Scene();progress=ease((t-1.8)/3.7);R=rot(z=1.18,y=-.10);center=np.array([-245,-15,0]);scale=2.7
 ch=complex(s,'1Y1W',center,scale,R);template=ch['T'];nascent=ch['P'];axis=norm(template[-1]-template[0])
 for endpoint,sign in [(template[0],-1),(template[-1],1)]:atomic_dna(s,endpoint+axis*sign*155,axis,length=310,scale=2.45,phase=-t*.12)
 exit=nascent[0];direction=norm(nascent[0]-nascent[2])
 trajectory=path([exit,exit+direction*60,[-170,240,-70],[100,210,-130],[350,120,-120],[570,165,-100]],300)
 atom_rna(s,trajectory,'A',2.9,reveal=.12+.88*progress)
 s.label(420,780,'RNA polymerase',40)
 s.label(1310,445,'RNA A',49,tuple((CYAN*255).astype(int)),True)
 s.label(135,380,'DNA',34)
 return s,'Transcription','Central dogma'

def translation(t,start,end,fused=False):
 s=Scene();p=ease((t-start)/(end-start));x=-220+340*p;center=np.array([x,-90,100])
 ch=complex(s,'4UG0',center,1.32,rot(y=-.18))
 rnapath=path([[-650,-140,-70],[-450,-135,-90],[x-140,-125,-155],[x+110,-130,-155],[440,-130,-70],[660,-110,-30]],240)
 atom_rna(s,rnapath,'AB' if fused else 'A',2.55)
 # The schematic peptide exits the large subunit. Its N end is distal.
 exit=center+np.array([-35,150,-135]);tip=exit+np.array([130+125*p,100+50*p,-40])
 peptide=path([exit,exit+[20,90,-25],tip+[10,40,0],tip],100)
 colors=np.array([ORANGE if fused and i<45 and p>.5 else CYAN for i in range(100)])
 s.points(peptide,3.8,colors)
 if not fused and p>.87:ribbon(s,'1UBQ',[455,170,-80],6.3,CYAN,angle=-.35)
 s.label(360,760,'Chimeric mRNA' if fused else 'mRNA A',41,tuple((CYAN*255).astype(int)))
 s.label(1180,765,'Ribosome',41)
 return s,'Translation','Chimeric mRNA' if fused else 'Central dogma'

def splicing(t):
 s=Scene();p=ease((t-13.2)/4.6);joined=t>=18.1
 complex(s,'5XJC',[0,-50,80],1.78,rot(y=-.35))
 offset=120*(1-p);shift=120*ease((t-18.1)/2.4) if joined else 0
 left=path([[-640,140+shift,-50],[-350,135+shift,-100],[-140,offset+shift,-190],[-18,offset+shift,-210]],160)
 right=path([[18,-offset+shift,-210],[170,-offset+shift,-190],[380,-130+shift,-100],[640,-85+shift,-50]],160)
 atom_rna(s,left,'A',2.45);atom_rna(s,right,'B',2.45)
 if joined:
  s.points(path([left[-1],[0,shift,-210],right[0]],28),4,np.array([CYAN]*14+[ORANGE]*14))
  s.label(800,230,'Chimeric mRNA',47,bold=True)
 else:
  greyA=path([left[-1],[40,offset+90,-160],[120,offset+155,-90]],60)
  greyB=path([[-140,-offset-160,-90],[-50,-offset-80,-160],right[0]],60)
  atom_rna(s,greyA,'grey',1.8);atom_rna(s,greyB,'grey',1.8)
  s.label(205,240,'RNA A',47,tuple((CYAN*255).astype(int)),True)
  s.label(1350,660,'RNA B',47,tuple((ORANGE*255).astype(int)),True)
 s.label(800,815,'Spliceosome',40)
 return s,'Trans-splicing','Chimeric mRNA'

def comparison(t):
 s=Scene();angle=-.3+(t-24.5)*.085
 ribbon(s,'1UBQ',[-520,5,-20],9.0,CYAN,angle)
 ribbon(s,'1MBN',[-15,5,-20],7.0,ORANGE,angle+.3)
 fusion(s,[490,5,-20],6.0,angle*.7)
 s.label(280,740,'Protein A',48,tuple((CYAN*255).astype(int)),True)
 s.label(785,740,'Protein B',48,tuple((ORANGE*255).astype(int)),True)
 s.label(1300,740,'Fusion protein',46,bold=True)
 s.label(1300,802,'Illustrative fold',24)
 return s,'Different sequences. Different structures.',None

def compose(im,s,title,section):
 d=ImageDraw.Draw(im);scale=im.width/1600
 def text(x,y,txt,size,color,b=False,anchor='mm'):
  f=ImageFont.truetype(old.BOLD if b else old.FONT,int(size*scale))
  d.text((int(x*scale),int(y*scale)),txt,font=f,anchor=anchor,fill=tuple(map(int,color)),stroke_width=max(1,int(scale)),stroke_fill=(32,53,49))
 if title:
  text(78,85,title,68 if title=='Translation' else (53 if len(title)>30 else 63),(244,249,244),True,'lm')
 if section:text(1520,82,section,29,(192,218,207),False,'rm')
 for x,y,txt,size,col,b in s.labels:text(x,y,txt,size,col,b)
 return im

def raw(t,renderer):
 if t<1.8 or 9.5<=t<11.5:
  s=Scene();s.atoms.append(cell_context());im=renderer.render(s,t)
  second=t>=9.5
  s.label(800,280,'02' if second else '01',30)
  s.label(800,405,'Chimeric mRNA' if second else 'Central dogma',80,bold=True)
  s.label(800,525,'Two RNAs → one new message' if second else 'DNA → RNA → protein',41)
  return compose(im,s,None,None)
 if t<5.5:s,title,section=transcription(t)
 elif t<9.5:s,title,section=translation(t,5.5,9.5)
 elif t<20.5:s,title,section=splicing(t)
 elif t<24.5:s,title,section=translation(t,20.5,24.5,True)
 else:s,title,section=comparison(t)
 s.atoms.insert(0,cell_context());return compose(renderer.render(s,t),s,title,section)

def frame(t,renderer):
 for b in [1.8,5.5,9.5,11.5,20.5,24.5]:
  if b<=t<b+.24:return Image.blend(raw(b-.001,renderer),raw(t,renderer),ease((t-b)/.24))
 return raw(t,renderer)

def preview(renderer):
 samples=[.9,4.8,7.6,10.4,15.5,19.9,23.2,28]
 sheet=Image.new('RGB',(1920,2360),(20,38,35));d=ImageDraw.Draw(sheet)
 d.text((48,35),'CELLULAR EDITION  /  4K  /  30 SECONDS',font=old.ft(38,True),fill=(225,242,231))
 for i,t in enumerate(samples):
  im=frame(t,renderer);im.save(ROOT/f'frame_{i+1:02d}_4k.jpg',quality=96)
  small=im.resize((912,513),Image.Resampling.LANCZOS);x=32+(i%2)*960;y=115+(i//2)*555
  sheet.paste(small,(x,y));d.text((x+12,y+519),f'{t:.1f} s',font=old.ft(23),fill=(210,231,219))
 sheet.save(ROOT/'storyboard_v3.jpg',quality=95)
 print('Preview complete',flush=True)

def main():
 preview_only='--preview' in sys.argv
 width=1920 if '--draft' in sys.argv else W
 r=Renderer(width,int(width*9/16))
 print('Renderer:',r.ctx.info['GL_RENDERER'],'resolution:',r.w,r.h,flush=True)
 if '--one' in sys.argv:
  t=float(sys.argv[sys.argv.index('--one')+1]);frame(t,r).save(ROOT/'look_test.jpg',quality=97);print('Look test complete');return
 preview(r)
 if preview_only:return
 out=ROOT/'trans_splicing_v3_4k_30s.mp4'
 writer=imageio_ffmpeg.write_frames(str(out),(r.w,r.h),fps=FPS,codec='libx264',quality=9,macro_block_size=1,ffmpeg_log_level='error',output_params=['-preset','fast','-movflags','+faststart','-r','24','-threads','2'])
 writer.send(None);begin=time.time()
 for i in range(720):
  writer.send(np.asarray(frame(i/FPS,r)))
  if i%24==0:print(f'{i}/720 | {time.time()-begin:.1f}s elapsed',flush=True)
 writer.close(); print('Finished',flush=True)

if __name__=='__main__':main()
