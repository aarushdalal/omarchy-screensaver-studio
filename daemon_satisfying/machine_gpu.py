"""Static mesh stream with per-part GPU kinematics, depth buffer and material lighting."""
import ctypes as C
import numpy as np
from .gpu import P,AATarget
from .machine3d import PrecisionMachine
VERT='''#version 300 es
precision highp float;
layout(location=0) in vec3 pos;layout(location=1) in vec3 normal;
layout(location=2) in vec3 rgb;layout(location=3) in float part;
uniform sampler2D parts;uniform vec2 resolution;uniform float time;uniform float camera_angle;
out vec3 n;out vec3 c;
vec3 camera(vec3 p){
 float yaw=camera_angle+.10*sin(time*.009),pitch=.62+.035*sin(time*.007);
 p=vec3(p.x*cos(yaw)+p.z*sin(yaw),p.y,-p.x*sin(yaw)+p.z*cos(yaw));
 return vec3(p.x,p.y*cos(pitch)-p.z*sin(pitch),p.y*sin(pitch)+p.z*cos(pitch));
}
void main(){
 int i=int(part+.5);vec4 a=texelFetch(parts,ivec2(0,i),0);vec4 b=texelFetch(parts,ivec2(1,i),0);vec4 d=texelFetch(parts,ivec2(2,i),0);
 float t=mod(time,190.);float u=smoothstep(a.w,a.w+8.,t)*(1.-smoothstep(166.-a.w*.18,176.-a.w*.18,t));
 float run=clamp(t-72.,0.,70.);float angle=run*.17*(b.w>.5?-1.:1.)+(b.w>.5?3.14159265/32.:0.);
 vec3 p=pos;vec3 nn=normal;
 if(d.x>.5){mat2 rot=mat2(cos(angle),sin(angle),-sin(angle),cos(angle));p.xy=rot*p.xy;nn.xy=rot*nn.xy;}
 p=camera(p+a.xyz+b.xyz*(1.-u));n=camera(nn);c=rgb;
 float perspective=3.3/(3.3-p.z);p.xy*=perspective*1.35;
 gl_Position=vec4(p.x*resolution.y/resolution.x,p.y,-p.z*.25,1.);
}
'''
FRAG='''#version 300 es
precision highp float;
in vec3 n;in vec3 c;out vec4 color;uniform float intensity;uniform float time;uniform vec3 accent;uniform float finish;
void main(){vec3 nn=normalize(n);float light=max(0.,dot(nn,normalize(vec3(-.35,.65,1.))));
 float spec=pow(max(0.,dot(nn,normalize(vec3(-.15,.30,.942)))),mix(10.,64.,finish));
 vec3 col=c*(.30+.68*light+.55*spec)*(vec3(.88)+accent*.12);
 color=vec4(clamp(col*intensity*smoothstep(0.,3.,mod(time,190.))*(1.-smoothstep(184.,190.,mod(time,190.))),0.,.64),1.);}
'''
class MachineGPU:
 def __init__(self,gl,w,h,seed=1):
  self.g=gl;self.w=w;self.h=h;self.program,self.compile_ms=gl.program(VERT,FRAG)
  self.vao=gl.gen('VertexArrays');self.vbo=gl.gen('Buffers');self.texture=gl.gen('Textures')
  self.aa=AATarget(gl,w,h,4,depth=True);self.tex=self.aa.tex;self.fb=self.aa.fb
  self.seed=seed;self.cycle=0;self.build(seed)
 def build(self,seed):
  m=PrecisionMachine(seed);data=[];params=[]
  for i,((faces,col),pos,kind,stage,axis,offset) in enumerate(m.parts):
   normal=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
   vertices=faces.reshape(-1,3);n=np.repeat(normal,3,axis=0);c=np.repeat(col,3,axis=0)
   data.append(np.column_stack((vertices,n,c,np.full(len(vertices),i))))
   rotate=kind in ('gear','key','collar','locknut','washer')
   params.append([[*pos,stage],[*offset,axis],[int(rotate),0,0,0]])
  data=np.concatenate(data).astype('f4');self.count=len(data);self.part_count=m.part_count
  g=self.g;g.BindVertexArray(self.vao);g.BindBuffer(0x8892,self.vbo);g.BufferData(0x8892,data.nbytes,data.ctypes.data_as(P),0x88E4)
  for index,size,offset in [(0,3,0),(1,3,12),(2,3,24),(3,1,36)]:g.EnableVertexAttribArray(index);g.VertexAttribPointer(index,size,0x1406,0,40,P(offset))
  p=np.array(params,dtype='f4');g.BindTexture(0x0DE1,self.texture);g.TexImage2D(0x0DE1,0,0x8814,3,len(params),0,0x1908,0x1406,p.ctypes.data_as(P))
  for key,val in [(0x2800,0x2600),(0x2801,0x2600),(0x2802,0x812F),(0x2803,0x812F)]:g.TexParameteri(0x0DE1,key,val)
 def render(self,time,intensity,accent,params=None):
  params=params or {}
  cyc=int(time/190)
  if cyc!=self.cycle:self.cycle=cyc;self.build(self.seed+cyc)
  g=self.g;g.BindFramebuffer(0x8D40,self.fb);g.Viewport(0,0,self.w,self.h);g.Enable(0x0B71)
  g.ClearColor(0,0,0,1);g.Clear(0x4000|0x0100);g.UseProgram(self.program);g.BindVertexArray(self.vao)
  g.ActiveTexture(0x84C0);g.BindTexture(0x0DE1,self.texture)
  for k,v in {'parts':(0,),'time':(float(time),),'resolution':(self.w,self.h),'intensity':(float(intensity),),'accent':accent,'finish':(float(params.get('finish',.7)),),'camera_angle':(float(params.get('camera_angle',.28)),)}.items():g.uniform(self.program,k,*v)
  g.DrawArrays(4,0,self.count);g.Disable(0x0B71)
  return self.aa.resolve()
 def close(self):
  g=self.g;g.DeleteProgram(self.program);g.delete('Buffers',self.vbo);g.delete('VertexArrays',self.vao)
  g.delete('Textures',self.texture);self.aa.close()
