import os, math, time, json, argparse, subprocess
import numpy as np
import moderngl
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
TAU=math.tau
def clamp(v,a=0,b=1):return max(a,min(b,v))
def smooth(v):
    v=clamp(v);return v*v*(3-2*v)
def lerp(a,b,t):return a+(b-a)*t
def norm(a):
    a=np.asarray(a,dtype='f4');return a/max(np.linalg.norm(a),1e-8)
def T(x=0,y=0,z=0):
    m=np.eye(4,dtype='f4');m[:3,3]=[x,y,z];return m
def S(x=1,y=None,z=None):
    if y is None:y=z=x
    return np.diag([x,y,z,1]).astype('f4')
def Rx(a):
    c,s=math.cos(a),math.sin(a)
    return np.array([[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]],dtype='f4')
def Ry(a):
    c,s=math.cos(a),math.sin(a)
    return np.array([[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]],dtype='f4')
def Rz(a):
    c,s=math.cos(a),math.sin(a)
    return np.array([[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1]],dtype='f4')
def lookat(eye,target,up=(0,1,0)):
    f=norm(np.array(target)-eye);r=norm(np.cross(f,up));u=np.cross(r,f)
    m=np.eye(4,dtype='f4');m[0,:3]=r;m[1,:3]=u;m[2,:3]=-f
    m[:3,3]=-m[:3,:3]@np.array(eye);return m
def perspective(fov,aspect,near=.1,far=150):
    f=1/math.tan(math.radians(fov)/2)
    return np.array([[f/aspect,0,0,0],[0,f,0,0],[0,0,(far+near)/(near-far),2*far*near/(near-far)],[0,0,-1,0]],dtype='f4')
def ortho(r=24):
    return np.array([[1/r,0,0,0],[0,1/r,0,0],[0,0,-2/100,-1],[0,0,0,1]],dtype='f4')
def mesh_sphere(seg=24,rings=14):
    v=[];ix=[]
    for j in range(rings+1):
        th=j*math.pi/rings
        for i in range(seg+1):
            a=i*TAU/seg;p=(math.sin(th)*math.cos(a),math.cos(th),math.sin(th)*math.sin(a));v.append((*p,*p))
    for j in range(rings):
        for i in range(seg):
            a=j*(seg+1)+i;b=a+seg+1;ix.extend([a,b,a+1,a+1,b,b+1])
    return v,ix
def mesh_box(n=4,bevel=.20):
    v=[];ix=[]
    for axis in range(3):
        for side in [-1,1]:
            base=len(v);others=[k for k in range(3) if k!=axis]
            for j in range(n+1):
                for i in range(n+1):
                    p=np.zeros(3);p[axis]=side;p[others]=[i/n*2-1,j/n*2-1]
                    core=np.clip(p,-1+bevel,1-bevel);nn=norm(p-core);p=core+nn*bevel
                    v.append((*p,*nn))
            for j in range(n):
                for i in range(n):
                    a=base+j*(n+1)+i;b=a+n+1
                    ix.extend([a,a+1,b,a+1,b+1,b])
    return v,ix
def mesh_cylinder(seg=32):
    v=[];ix=[]
    for j in range(2):
        for i in range(seg+1):
            a=i*TAU/seg;c,s=math.cos(a),math.sin(a);v.append((c,j-.5,s,c,0,s))
    for i in range(seg):
        a=i;b=a+seg+1;ix.extend([a,a+1,b,a+1,b+1,b])
    for y,ny in [(-.5,-1),(.5,1)]:
        base=len(v);v.append((0,y,0,0,ny,0))
        for i in range(seg+1):
            a=i*TAU/seg;v.append((math.cos(a),y,math.sin(a),0,ny,0))
        for i in range(seg):ix.extend([base,base+i+1,base+i+2])
    return v,ix
def mesh_torus(seg=56,tube=8):
    v=[];ix=[]
    for j in range(seg+1):
        a=j*TAU/seg
        for i in range(tube+1):
            b=i*TAU/tube;c,s=math.cos(a),math.sin(a)
            v.append(((1+.065*math.cos(b))*c,(1+.065*math.cos(b))*s,.065*math.sin(b),math.cos(b)*c,math.cos(b)*s,math.sin(b)))
    for j in range(seg):
        for i in range(tube):
            a=j*(tube+1)+i;b=a+tube+1;ix.extend([a,a+1,b,a+1,b+1,b])
    return v,ix
VERTEX='''#version 330
in vec3 in_pos;in vec3 in_normal;
in vec4 m0;in vec4 m1;in vec4 m2;in vec4 m3;
in vec3 in_color;in float in_metal;in float in_glow;
uniform mat4 vp;uniform mat4 light_vp;
out vec3 pos;out vec3 normal;out vec3 color;out float metal;out float glow;out vec4 shadowpos;
void main(){mat4 model=mat4(m0,m1,m2,m3);vec4 w=model*vec4(in_pos,1.);pos=w.xyz;normal=normalize(transpose(inverse(mat3(model)))*in_normal);color=in_color;metal=in_metal;glow=in_glow;shadowpos=light_vp*w;gl_Position=vp*w;}
'''
FRAGMENT='''#version 330
in vec3 pos;in vec3 normal;in vec3 color;in float metal;in float glow;in vec4 shadowpos;
uniform vec3 eye;uniform sampler2D shadowmap;uniform vec3 fog;uniform float mood;
out vec4 frag;
float shadow(vec3 n,vec3 l){
vec3 p=shadowpos.xyz/shadowpos.w*.5+.5;
if(p.x<0.||p.x>1.||p.y<0.||p.y>1.||p.z>1.)return 1.;
float b=max(.0015*(1.-dot(n,l)),.0005);float s=0.;
for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)s+=p.z-b<texture(shadowmap,p.xy+vec2(x,y)/1536.).r?1.:.20;
return s/9.;}
void main(){
vec3 n=normalize(normal);
vec3 l=normalize(vec3(-.5,1.,.55));vec3 v=normalize(eye-pos);vec3 h=normalize(v+l);
float nd=max(dot(n,l),0.);float sh=shadow(n,l);
vec3 base=pow(color,vec3(2.2));
vec3 ambient=mix(vec3(.14,.19,.22),vec3(.5,.57,.57),n.y*.5+.5);
vec3 diffuse=base*(ambient*.62+vec3(1.,.91,.73)*nd*sh*1.25);
vec3 rimlight=normalize(vec3(.8,.5,-.5));float rim=max(dot(n,rimlight),0.);
diffuse+=base*rim*vec3(.12,.42,.44)*(.6+mood*.45);
float sp=pow(max(dot(n,h),0.),mix(48.,105.,metal))*(.25+metal*1.5)*sh;
float fres=pow(1.-max(dot(v,n),0.),3.);
vec3 outc=diffuse+mix(vec3(1.,.94,.8),base,metal*.75)*sp;
outc+=vec3(.2,.46,.48)*fres*.2;outc+=base*glow*2.3;
float fogfac=1.-exp(-max(length(eye-pos)-18.,0.)*.018);
outc=mix(outc,pow(fog,vec3(2.2)),fogfac);frag=vec4(outc,1.);}
'''
SHADOW_V='''#version 330
in vec3 in_pos;in vec4 m0;in vec4 m1;in vec4 m2;in vec4 m3;uniform mat4 light_vp;
void main(){gl_Position=light_vp*mat4(m0,m1,m2,m3)*vec4(in_pos,1.);}
'''
QUAD_V='''#version 330
in vec2 in_pos;out vec2 uv;void main(){uv=in_pos*.5+.5;gl_Position=vec4(in_pos,0.,1.);}
'''
BLOOM_F='''#version 330
uniform sampler2D source;uniform vec2 direction;uniform int extract;in vec2 uv;out vec4 frag;
void main(){vec3 c=texture(source,uv).rgb*.227027;
c+=(texture(source,uv+direction*1.384615).rgb+texture(source,uv-direction*1.384615).rgb)*.316216;
c+=(texture(source,uv+direction*3.230769).rgb+texture(source,uv-direction*3.230769).rgb)*.070270;
if(extract==1)c=max(c-.72,0.);frag=vec4(c,1.);}
'''
POST_F='''#version 330
uniform sampler2D source;uniform sampler2D bloom;uniform sampler2D typography;
uniform float title_alpha;uniform float fade;uniform float t;
in vec2 uv;out vec4 frag;
vec3 aces(vec3 x){return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.);}
void main(){vec3 c=texture(source,uv).rgb+texture(bloom,uv).rgb*.16;
c=pow(aces(c*1.08),vec3(1./2.2));
float vig=1.-.20*pow(length((uv-.5)*vec2(1.2,1.)),1.5);c*=vig;
float grain=fract(sin(dot(uv+vec2(t*.001),vec2(12.9898,78.233)))*43758.5453)-.5;c+=grain*.004;
vec4 txt=texture(typography,vec2(uv.x,1.-uv.y));c=mix(c,txt.rgb,txt.a*title_alpha);
c=mix(vec3(.025,.06,.07),c,fade);frag=vec4(c,1.);}
'''
IVORY=(.91,.89,.79);CREAM=(.96,.94,.86);TEAL=(.08,.51,.53);NAVY=(.055,.15,.18);CORAL=(.96,.27,.18);GOLD=(.78,.57,.28);MINT=(.32,.86,.76);DARK=(.045,.09,.10)
PALETTE=[IVORY,TEAL,CORAL,GOLD,MINT,IVORY,TEAL]

class Renderer:
    def __init__(self,w,h):
        self.w=w;self.h=h
        self.ctx=moderngl.create_standalone_context(require=330,backend='egl')
        print('GPU:',self.ctx.info['GL_RENDERER'],flush=True)
        self.p=self.ctx.program(vertex_shader=VERTEX,fragment_shader=FRAGMENT)
        self.sp=self.ctx.program(vertex_shader=SHADOW_V,fragment_shader='''#version 330\nvoid main(){}''')
        self.meshes={};self.batches={}
        for name,fn in [('sphere',mesh_sphere),('box',mesh_box),('cyl',mesh_cylinder),('torus',mesh_torus)]:
            v,ix=fn();vb=self.ctx.buffer(np.array(v,'f4').tobytes());ib=self.ctx.buffer(np.array(ix,'i4').tobytes());inst=self.ctx.buffer(reserve=84*12000)
            vao=self.ctx.vertex_array(self.p,[(vb,'3f 3f','in_pos','in_normal'),(inst,'4f 4f 4f 4f 3f 1f 1f /i','m0','m1','m2','m3','in_color','in_metal','in_glow')],ib)
            svao=self.ctx.vertex_array(self.sp,[(vb,'3f 12x','in_pos'),(inst,'4f 4f 4f 4f 20x /i','m0','m1','m2','m3')],ib)
            self.meshes[name]=(inst,vao,svao);self.batches[name]=[]
        self.depth=self.ctx.depth_texture((1536,1536));self.depth.compare_func='';self.depth.repeat_x=False;self.depth.repeat_y=False;self.depth.filter=(moderngl.NEAREST,moderngl.NEAREST)
        self.sfbo=self.ctx.framebuffer(depth_attachment=self.depth)
        self.color=self.ctx.texture((w,h),4,dtype='f2')
        self.fbo=self.ctx.framebuffer([self.color],self.ctx.depth_renderbuffer((w,h)))
        self.final=self.ctx.framebuffer([self.ctx.texture((w,h),4)])
        self.small=[]
        for j in range(2):
            tex=self.ctx.texture((w//4,h//4),4,dtype='f2');tex.filter=(moderngl.LINEAR,moderngl.LINEAR);tex.repeat_x=False;tex.repeat_y=False
            self.small.append((tex,self.ctx.framebuffer([tex])))
        qb=self.ctx.buffer(np.array([-1,-1,1,-1,-1,1,1,1],'f4').tobytes())
        self.bp=self.ctx.program(vertex_shader=QUAD_V,fragment_shader=BLOOM_F)
        self.pp=self.ctx.program(vertex_shader=QUAD_V,fragment_shader=POST_F)
        self.bvao=self.ctx.vertex_array(self.bp,[(qb,'2f','in_pos')]);self.pvao=self.ctx.vertex_array(self.pp,[(qb,'2f','in_pos')])
        self.p['shadowmap']=0;self.bp['source']=0;self.pp['source']=0;self.pp['bloom']=1;self.pp['typography']=2
        self.lv=ortho(27)@lookat((-18,32,20),(0,0,-2))
        self.sp['light_vp'].write(self.lv.T.tobytes());self.p['light_vp'].write(self.lv.T.tobytes())
        self.titles=[self.make_title(False),self.make_title(True)]
    def make_title(self,end):
        im=Image.new('RGBA',(self.w,self.h));d=ImageDraw.Draw(im);f=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');bold=f.with_name('DejaVuSans-Bold.ttf')
        def font(sz,b=False):return ImageFont.truetype(str(bold if b else f),int(sz*self.w/1920))
        def text(s,x,y,sz,fill,b=False):d.text((x*self.w/1920,y*self.h/1080),s,font=font(sz,b),fill=fill)
        navy=(17,43,47,255);red=(211,65,43,255)
        if not end:
            text('A  M E C H A N I C A L  D A Y D R E A M',115,212,18,navy)
            text('CLOCKWORK',108,267,91,navy,True);text('REBELLION',108,363,91,navy,True)
            d.rectangle((115*self.w/1920,495*self.h/1080,201*self.w/1920,502*self.h/1080),fill=red)
            text('IN THE HALL OF THE MOUNTAIN KING',115,535,23,navy)
            text('EDVARD GRIEG  /  ELECTRONIC REWORK',115,577,18,navy)
        else:
            text('E V E R Y T H I N G  H A S  A  R H Y T H M .',116,210,23,navy)
            text('CLOCKWORK',108,265,82,navy,True);text('REBELLION',108,353,82,navy,True)
            text('MUSIC: EDVARD GRIEG',116,502,20,navy)
            text('ORIGINAL ELECTRONIC ARRANGEMENT & 3D ANIMATION',116,539,17,navy)
        tex=self.ctx.texture((self.w,self.h),4,im.tobytes());tex.filter=(moderngl.LINEAR,moderngl.LINEAR);return tex
    def add(self,kind,m,c=IVORY,metal=0,glow=0):
        self.batches[kind].append(np.concatenate((m.T.ravel(),np.array([*c,metal,glow],dtype='f4'))))
    def draw(self,t,eye,target,fov=44,mood=0):
        ctx=self.ctx
        for name,(buf,_,_) in self.meshes.items():
            if self.batches[name]:buf.write(np.asarray(self.batches[name],dtype='f4').tobytes())
        ctx.enable(moderngl.DEPTH_TEST);ctx.disable(moderngl.CULL_FACE)
        self.sfbo.use();ctx.viewport=(0,0,1536,1536);self.sfbo.clear(depth=1)
        for name,(_,_,vao) in self.meshes.items():
            if self.batches[name]:vao.render(instances=len(self.batches[name]))
        self.fbo.use();ctx.viewport=(0,0,self.w,self.h)
        fog=(.88,.88,.79);linear=[v**2.2 for v in fog];self.fbo.clear(*linear,1,depth=1)
        self.p['vp'].write((perspective(fov,self.w/self.h)@lookat(eye,target)).T.tobytes());self.p['eye'].value=tuple(eye);self.p['fog'].value=fog;self.p['mood']=mood
        self.depth.use(0)
        for name,(_,vao,_) in self.meshes.items():
            if self.batches[name]:vao.render(instances=len(self.batches[name]))
        ctx.disable(moderngl.DEPTH_TEST);ctx.viewport=(0,0,self.w//4,self.h//4)
        self.small[0][1].use();self.color.use(0);self.bp['extract']=1;self.bp['direction'].value=(1/self.w,0);self.bvao.render(moderngl.TRIANGLE_STRIP)
        self.small[1][1].use();self.small[0][0].use(0);self.bp['extract']=0;self.bp['direction'].value=(0,4/self.h);self.bvao.render(moderngl.TRIANGLE_STRIP)
        self.final.use();ctx.viewport=(0,0,self.w,self.h);self.color.use(0);self.small[1][0].use(1)
        ending=t>=154;self.titles[1 if ending else 0].use(2)
        alpha=(smooth((t-.8)/1.2)*(1-smooth((t-6.1)/1.5))) if t<8 else (smooth((t-154)/1.4) if ending else 0)
        self.pp['title_alpha']=alpha;self.pp['fade']=smooth(t/.6)*(1-smooth((t-159.1)/.9));self.pp['t']=t
        self.pvao.render(moderngl.TRIANGLE_STRIP)
        return self.final.read(components=3,alignment=1)
    def clear(self):
        for v in self.batches.values():v.clear()
def sphere(r,m,c,scale,metal=0,glow=0):r.add('sphere',m@S(*scale) if isinstance(scale,tuple) else m@S(scale),c,metal,glow)
def box(r,m,c,scale,metal=0,glow=0):r.add('box',m@S(*scale),c,metal,glow)
def cyl(r,m,c,scale,metal=0,glow=0):r.add('cyl',m@S(*scale),c,metal,glow)
def torus(r,m,c,scale,metal=0,glow=0):r.add('torus',m@S(*scale) if isinstance(scale,tuple) else m@S(scale),c,metal,glow)
def bone(r,parent,a,b,radius,c,metal=0):
    a=np.array(a);b=np.array(b);v=b-a;y=norm(v);x=norm(np.cross([0,0,1],y))
    if np.linalg.norm(x)<.01:x=np.array([1,0,0])
    z=np.cross(x,y);m=np.eye(4,dtype='f4');m[:3,:3]=np.array([x,y,z]).T;m[:3,3]=(a+b)*.5
    cyl(r,parent@m,c,(radius,np.linalg.norm(v),radius),metal)
def limb(r,parent,a,b,cpt,color):
    for p in [a,b]:sphere(r,parent@T(*p),GOLD,.115,.7)
    bone(r,parent,a,b,.09,color,.2);bone(r,parent,b,cpt,.085,color,.2)

def robot(r,t,pos=(0,0,0),yaw=0,index=0,energy=1,mode='dance',scale=1):
    phase=t*TAU*2;p=phase+index*.42
    bounce=(.07+.07*math.sin(p*2))*energy;sway=math.sin(p*.5)*.16*energy;lift=0
    if mode=='float':lift=.8+.35*math.sin(t*1.4+index);bounce=0
    if mode=='sleep':bounce=0;sway=0
    base=T(*pos)@Ry(yaw)@S(scale);hipY=1.04+bounce;root=base@T(sway,lift,0)
    for side in [-1,1]:
        ph=p+(0 if side<0 else math.pi);up=max(0,math.sin(ph))*.32*energy
        fx=side*.24+math.sin(ph*.5)*.12*energy;fz=math.cos(ph)*.27*energy
        if mode=='float':fx=side*.53;up=.20+side*math.sin(p*.25)*.14;fz=.12
        if mode=='sleep':up=0;fz=0;fx=side*.22
        foot=(fx,.16+up,fz);hip=(side*.20,hipY,0);knee=(side*.27,.59+(up*.45),.19+fz*.55)
        limb(r,root,hip,knee,foot,IVORY)
        box(r,root@T(*foot)@Ry(-side*.12),NAVY if index==0 else TEAL,(.20,.13,.31),.1)
        box(r,root@T(foot[0],foot[1]-.09,foot[2]+.015),CORAL if index==0 else GOLD,(.205,.045,.305))
    body=root@T(0,hipY+.52,0)@Rz(math.sin(p*.5)*.10*energy)
    primary=CORAL if index==0 else PALETTE[index%len(PALETTE)]
    box(r,body,primary,(.38,.47,.24),.15);box(r,body@T(0,.02,.238),IVORY,(.19,.26,.038))
    sphere(r,body@T(0,.045,.29),MINT,.09,.25,.7)
    for k in range(3):box(r,body@T(-.075+k*.075,-.19,.286),NAVY,(.014,.045,.017))
    cyl(r,body@T(0,.52,0),GOLD,(.13,.21,.13),.75)
    htilt=.55 if mode=='sleep' else math.sin(p*.25)*.10*energy
    head=body@T(0,.87,0)@Rz(htilt)@Ry(math.sin(p*.25)*.16*energy)
    box(r,head,IVORY,(.48,.36,.35),.12);box(r,head@T(0,.025,.325),NAVY,(.405,.235,.062),.18)
    blink=.1 if (t+index*.7)%5.7>5.53 else 1
    if mode=='sleep':blink=.1
    for side in [-1,1]:
        box(r,head@T(side*.17,.05,.39),MINT,(.067,.067*blink,.02),.2,1.2)
        cyl(r,head@T(side*.51,0,0)@Rz(math.pi/2),GOLD,(.15,.09,.15),.8)
    box(r,head@T(0,-.105,.39),CORAL,(.073,.014,.012),0,.2)
    bone(r,head,(.24,.32,0),(.30,.64,0),.025,GOLD,.7)
    sphere(r,head@T(.30,.66,0),CORAL,.085,.2,.6 if mode!='sleep' else 0)
    for side in [-1,1]:
        a=(side*.45,.29,0);phrase=int(t//4)%4
        if mode=='sleep':el=(side*.53,-.12,0);hand=(side*.43,-.57,.05)
        elif mode=='reach':el=(side*(.56 if side<0 else .83),.13,.23);hand=(side*.75,.55 if side>0 else -.1,.57)
        elif mode=='float':el=(side*.76,.35,.07);hand=(side*1.01,.60+math.sin(p*.25)*.2,.1)
        elif phrase==0:
            el=(side*.73,.02+.28*math.sin(p*.5+side),.12)
            hand=(side*(.72+.15*math.cos(p*.5)),.47+.43*math.sin(p*.5+side),.33)
        elif phrase==1:el=(side*.74,.35,.10);hand=(side*(.48+.12*math.cos(p*.5)),.85+.18*math.sin(p+side),.05)
        elif phrase==2:el=(side*.65,-.10,.2);hand=(side*.32,.18+side*.27*math.sin(p*.5),.55)
        else:el=(side*.75,.20+side*.24*math.sin(p*.5),.05);hand=(side*1.02,.24+side*.62*math.sin(p*.5),.12)
        if energy<1 and mode=='dance':
            el=tuple(lerp(a,b,energy) for a,b in zip((side*.52,-.12,0),el))
            hand=tuple(lerp(a,b,energy) for a,b in zip((side*.43,-.57,.05),hand))
        limb(r,body,a,el,hand,primary);sphere(r,body@T(*hand),IVORY,(.13,.16,.12))
        sphere(r,body@T(hand[0]-side*.115,hand[1]-.02,hand[2]+.04),GOLD,.055,.6)
def gear(r,m,radius,color,rotation=0,teeth=20):
    p=m@Rz(rotation);torus(r,p,color,radius,.55);torus(r,p,NAVY,radius*.72,.3)
    cyl(r,p@Rx(math.pi/2),color,(radius*.29,.18,radius*.29),.5)
    for j in range(teeth):
        a=j*TAU/teeth;box(r,p@Rz(a)@T(0,radius*1.03,0),color,(radius*.055,radius*.105,.12),.45)
    for j in range(6):bone(r,p,(0,0,0),(math.sin(j*TAU/6)*radius*.9,math.cos(j*TAU/6)*radius*.9,0),.065,color,.5)
def world(r,t):
    energy=smooth((t-15)/20);final=smooth((t-120)/20)
    box(r,T(0,-.34,0),CREAM,(65,.20,65))
    cyl(r,T(0,-.05,0),IVORY,(7.3,.30,7.3));cyl(r,T(0,.12,0),GOLD,(6.65,.10,6.65),.5)
    cyl(r,T(0,.22,0),CREAM,(6.45,.12,6.45))
    torus(r,T(0,.29,0)@Rx(math.pi/2),TEAL,(5.9,5.9,.18),.2)
    for k in range(3):
        rad=2.2+k*1.15;torus(r,T(0,.30,0)@Rx(math.pi/2),GOLD if k%2 else TEAL,(rad,rad,.18),.3)
    for j in range(48):
        a=j*TAU/48;y=.3+energy*(.04+.15*max(0,math.sin(t*TAU*2-j*.32)))
        box(r,T(math.sin(a)*6.05,y,math.cos(a)*6.05)@Ry(a),CORAL if j%4==0 else TEAL,(.10,.035,.22),.1,.15*energy)
    for j in range(21):
        a=math.pi*.53+j*math.pi*.94/20;x=math.sin(a)*14;z=math.cos(a)*14-2
        height=2.8+((j*7)%9)*.55;tilt=math.sin(t*1.6+j*.8)*.035*energy;b=T(x,0,z)@Rz(tilt)
        box(r,b@T(0,height*.5,0),TEAL if j%3==0 else IVORY,(.54,height*.5,.64),.15)
        cyl(r,b@T(0,height+.12,0),GOLD,(.59,.24,.68),.6)
        sphere(r,b@T(0,height+.48,0),CORAL if j%3 else MINT,.27,.3,.15*energy)
        for k in range(min(5,int(height))):
            box(r,b@T(0,.65+k*.94,.65),NAVY,(.30,.18,.03),.1)
            for s in [-1,1]:box(r,b@T(s*.14,.65+k*.94,.69),MINT if energy>.3 else GOLD,(.052,.12,.015),0,energy*.8)
        if j%4==0:gear(r,b@T(0,height*.60,.95),.75,GOLD,t*.25*((j%2)*2-1),12)
    cl=T(0,5.5,-8);cyl(r,T(0,2,-8),TEAL,(1.3,4,1.3),.2);box(r,T(0,.8,-8),GOLD,(1.8,.8,1.4),.5)
    torus(r,cl,GOLD,3.3,.75);torus(r,cl,TEAL,2.95,.3);cyl(r,cl@Rx(math.pi/2),IVORY,(2.75,.20,2.75),.15)
    for j in range(12):
        a=j*TAU/12;ext=final*.85
        pet=cl@Rz(a+t*.04*final)@T(0,2.45+ext,.16+final*.35)@Rx(final*math.sin(t*.6+j)*.3)
        box(r,pet,CORAL if j%3==0 else GOLD,(.12+final*.18,.25+final*.48,.055+final*.12),.5)
    handspin=t*(.13+energy*.18)
    for length,angle,col in [(2.1,handspin,CORAL),(1.45,handspin/8,GOLD)]:
        bone(r,cl,(0,0,.32),(math.sin(angle)*length,math.cos(angle)*length,.32),.07,col,.5)
    sphere(r,cl@T(0,0,.40),TEAL,.28,.5,.35*final)
    for s in [-1,1]:
        g=T(s*4.3,3.2,-7);gear(r,g,1.25,GOLD,t*.42*s,18);torus(r,g@Ry(math.sin(t*.25)*.3),CORAL,1.45,.1)
    for j in range(18):
        a=j*2.399+t*.12;radius=5.3+(j%3)*1.0;h=6.5+math.sin(a*1.7+t*.6)*.9;vis=smooth((t-32-j*.7)/6)
        if vis>0:sphere(r,T(math.sin(a)*radius,h,math.cos(a)*radius-3),[GOLD,CORAL,MINT][j%3],(.11+.055*(j%3))*vis,.6,.18)
    if t>120:
        for j in range(55):
            a=j*2.399+t*.35;rad=3+(j*13%75)*.09;y=1.3+((j*.47+t*.54)%7)
            q=T(math.cos(a)*rad,y,math.sin(a)*rad-1)@Rx(t+j)@Ry(t*.6+j)
            box(r,q,[CORAL,TEAL,GOLD][j%3],(.045,.13,.035),.3)
def orbital_scene(r,t):
    for j in range(6):
        a=j*TAU/6+t*.18;m=T(math.cos(a)*3.6,2.2+math.sin(t*.8+j)*.4,math.sin(a)*3.6)@Ry(-a+math.pi/2)
        cyl(r,m,IVORY,(.95,.18,.95));torus(r,m@T(0,.12,0)@Rx(math.pi/2),GOLD,.87,.65)
        robot(r,t,(math.cos(a)*3.6,2.3+math.sin(t*.8+j)*.4,math.sin(a)*3.6),-a+math.pi/2,j+1,.7,'float',.63)
    robot(r,t,(0,1.8,0),math.sin(t*.3)*.6,0,1,'float')
    for j in range(3):torus(r,T(0,3.6,0)@Ry(j*1.05+t*.10)@Rx(j*.63+t*.08),[GOLD,TEAL,CORAL][j],5.5+j*.6,.5)
    for j in range(36):
        a=j*2.399+t*.4;sphere(r,T(math.cos(a)*5.2,1.8+math.sin(j+t*.7)*2.7,math.sin(a)*5.2),MINT if j%3 else CORAL,.07+(j%3)*.02,.3,.3)

SHOTS=[
(0,8,(9,4.8,12),(-2.4,1.8,0),44),
(8,12,(3.5,3.0,4.2),(.45,1.75,.1),44),
(12,16,(2.8,1.15,4.4),(.2,1.35,0),46),
(16,24,(8,4.4,10),(0,1.6,0),43),
(24,28,(2.8,2.7,4.8),(0,1.7,0),42),
(28,32,(-6,2.2,8),(0,1.4,0),44),
(32,40,(10,7.2,12),(0,1.6,0),48),
(40,44,(0,16,.01),(0,0,0),55),
(44,48,(-4.8,2.2,6.8),(0,1.8,0),46),
(48,56,(10,4.5,7),(0,1.9,-1),48),
(56,64,(0,3.1,11),(0,2.0,-1.0),48),
(64,68,(-2.8,2.3,5),(0,1.8,0),43),
(68,72,(6.5,1.5,7.5),(0,1.4,0),47),
(72,80,(10,10,10),(0,1.5,0),50),
(80,88,(-8,4,9),(0,2,0),45),
(88,96,(10,7.8,12),(0,3.7,0),48),
(96,104,(6,3.4,7),(0,4.0,0),50),
(104,108,(0,3.2,9),(0,2.1,-1),46),
(108,112,(-7,2.5,5),(0,2,-1),48),
(112,116,(0,4.3,1.5),(0,5.5,-8),50),
(116,120,(6,8,10),(0,3,-2),50),
(120,128,(0,4.5,13),(0,2.6,-2),52),
(128,132,(2.7,2.4,4.8),(0,1.9,0),43),
(132,136,(0,17,.01),(0,0,0),56),
(136,144,(11,6,11),(0,2.8,-1),50),
(144,152,(-10,4,10),(0,2,-1),50),
(152,160,(10,5.2,13),(-2.7,1.8,0),44)]
def animate(r,t):
    r.clear();shot=next((x for x in SHOTS if x[0]<=t<x[1]),SHOTS[-1])
    a,b,eye,target,fov=shot;u=(t-a)/(b-a);eye=np.array(eye,dtype=float);target=np.array(target,dtype=float)
    if a in [40,132]:
        ang=.18*(u-.5);eye=np.array([math.sin(ang)*4,16,math.cos(ang)*.12]);target=np.array([0,0,0])
    else:
        ang=(u-.5)*(.16 if a%3 else -.18)
        eye=(Ry(ang)@np.array([*eye,1]))[:3];eye=target+(eye-target)*(1-.055*smooth(u))
    world(r,t)
    if 88<=t<104:orbital_scene(r,t)
    else:
        energy=smooth((t-10)/8);mode='sleep' if t<7 else ('reach' if t<14 else 'dance')
        if t>=154:mode='reach';energy=.45
        robot(r,t,(0,.3,0),.10*math.sin(t*.4),0,energy,mode)
        if t<24:
            f=smooth((t-8)/5);px=1.3*(1-f)+math.sin(t)*.75*f;py=.9+f*(1.9+.3*math.sin(t*2));pz=.1+.4*f*math.cos(t)
            cyl(r,T(1.3,.6,.1),GOLD,(.24,.65,.24),.6);sphere(r,T(px,py,pz),MINT,.19,.25,.8)
            for j in range(2):torus(r,T(px,py,pz)@Ry(t+j*1.2)@Rx(j*.9),GOLD,.31,.6)
        count=0 if t<30 else (6 if t<48 else 10)
        if t>=120:count=12
        if t>=154:count=0
        for j in range(count):
            idx=j+1;emerge=smooth((t-30-j*.65)/4)*(1-smooth((t-152)/2))
            if t<56:
                ang=j*TAU/6;rad=3.7;x,z=math.sin(ang)*rad,math.cos(ang)*rad-1;yaw=0
            elif t<72:
                row=j//5;col=j%5;x=(col-2)*1.85;z=-2.4-row*2.1;yaw=.16*math.sin(t*.4)
            elif t<88:
                ang=j*TAU/count+t*.15;rad=3.5+(j%2)*.8;x,z=math.sin(ang)*rad,math.cos(ang)*rad-1;yaw=ang+math.pi
            elif t<120:
                row=j//5;col=j%5;x=(col-2)*1.9;z=-2.8-row*2.2;yaw=0
            else:
                ang=j*TAU/count;rad=4.4;x,z=math.sin(ang)*rad,math.cos(ang)*rad-.9;yaw=-.3*math.sin(ang)
            robot(r,t,(x,.3-2.5*(1-emerge),z),yaw,idx,energy,'dance',.72)
    return r.draw(t,eye,target,fov,smooth((t-24)/40))
def main():
    p=argparse.ArgumentParser();p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080);p.add_argument('--fps',type=int,default=24)
    p.add_argument('--preview',type=float,nargs='*');p.add_argument('--start',type=float,default=0);p.add_argument('--end',type=float,default=160);p.add_argument('--name',default='clockwork-rebellion-silent.mp4')
    args=p.parse_args();r=Renderer(args.width,args.height)
    if args.preview is not None:
        for t in args.preview:
            data=animate(r,t);im=Image.frombytes('RGB',(args.width,args.height),data).transpose(Image.Transpose.FLIP_TOP_BOTTOM);path=OUT/f'frame-{t:06.2f}.png';im.save(path);print(path,flush=True)
        return
    output=OUT/args.name
    proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{args.width}x{args.height}','-framerate',str(args.fps),'-i','-','-vf','vflip','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],stdin=subprocess.PIPE)
    total=round((args.end-args.start)*args.fps);begin=time.time()
    for frame in range(total):
        t=args.start+frame/args.fps;proc.stdin.write(animate(r,t))
        if frame%120==0:
            elapsed=time.time()-begin
            print(json.dumps({'frame':frame,'total':total,'seconds_done':round(t,2),'elapsed':round(elapsed,1),'fps':round((frame+1)/max(elapsed,.01),2)}),flush=True)
    proc.stdin.close();code=proc.wait()
    if code:raise RuntimeError(f'ffmpeg exited {code}')
    print('Finished '+str(output),flush=True)
if __name__=='__main__':main()
