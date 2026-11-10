"""Batched 3D triangles with actual depth testing and conservative material lighting."""
import ctypes as C
import numpy as np
from .gpu import P,AATarget
VERT='''#version 300 es
precision highp float;layout(location=0) in vec3 pos;layout(location=1) in vec3 normal;layout(location=2) in vec3 rgb;
uniform vec2 resolution;uniform float time;out vec3 n;out vec3 c;
vec3 camera(vec3 p){float y=.32+.07*sin(time*.007),x=.65;
p=vec3(p.x*cos(y)+p.z*sin(y),p.y,-p.x*sin(y)+p.z*cos(y));return vec3(p.x,p.y*cos(x)-p.z*sin(x),p.y*sin(x)+p.z*cos(x));}
void main(){vec3 p=camera(pos);n=camera(normal);c=rgb;p.xy*=3.5/(3.5-p.z);gl_Position=vec4(p.x*resolution.y/resolution.x,p.y,-p.z*.23,1);}
'''
FRAG='''#version 300 es
precision highp float;in vec3 n;in vec3 c;out vec4 color;uniform float intensity;uniform vec3 accent;uniform vec3 secondary;
void main(){vec3 nn=normalize(n);float l=max(0.,dot(nn,normalize(vec3(-.4,.7,1.))));float s=pow(max(0.,dot(nn,normalize(vec3(-.1,.3,1.)))),25.);
vec3 matCol=mix(c,c*accent*2.4+accent*0.15,0.72);vec3 specCol=mix(vec3(1.),secondary*1.6,0.65);
vec3 lit=matCol*(0.28+0.72*l)+specCol*(s*0.50);color=vec4(clamp(lit*intensity,0.,0.88),1);}
'''
class World:
 def __init__(self):self.faces=[];self.colors=[]
 def add(self,mesh,pos=(0,0,0),rotation=None,color=None):
  faces,col=mesh;f=faces.copy()
  if rotation is not None:f=f@rotation.T
  f+=pos;self.faces.append(f);self.colors.append(np.broadcast_to(color,(len(f),3)).copy() if color is not None else col)
 def arrays(self):
  if not self.faces:return np.empty((0,9),dtype='f4')
  f=np.concatenate(self.faces);c=np.concatenate(self.colors)
  n=np.cross(f[:,1]-f[:,0],f[:,2]-f[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-9)
  return np.concatenate((f.reshape(-1,3),np.repeat(n,3,axis=0),np.repeat(c,3,axis=0)),axis=1).astype('f4')

def rotation(axis,angle):
 c,s=np.cos(angle),np.sin(angle)
 if axis=='x':return np.array([[1,0,0],[0,c,-s],[0,s,c]])
 if axis=='y':return np.array([[c,0,s],[0,1,0],[-s,0,c]])
 return np.array([[c,-s,0],[s,c,0],[0,0,1]])

class WorldGPU:
 def __init__(self,g,w,h):
  self.g=g;self.w=w;self.h=h;self.program,self.compile_ms=g.program(VERT,FRAG)
  self.vao=g.gen('VertexArrays');self.vbo=g.gen('Buffers');self.aa=AATarget(g,w,h,4,depth=True);self.tex=self.aa.tex;self.fb=self.aa.fb
 def render(self,world,time,intensity,accent,secondary=None):
  sec=secondary or accent
  g=self.g;data=world.arrays();g.BindFramebuffer(0x8D40,self.fb);g.Viewport(0,0,self.w,self.h);g.Enable(0x0B71);g.ClearColor(0,0,0,0);g.Clear(0x4000|0x100)
  g.UseProgram(self.program);g.BindVertexArray(self.vao);g.BindBuffer(0x8892,self.vbo);g.BufferData(0x8892,data.nbytes,data.ctypes.data_as(P),0x88E0)
  for i in range(3):g.EnableVertexAttribArray(i);g.VertexAttribPointer(i,3,0x1406,0,36,P(i*12))
  for k,v in {'time':(float(time),),'resolution':(self.w,self.h),'intensity':(float(intensity),),'accent':accent,'secondary':sec}.items():g.uniform(self.program,k,*v)
  g.DrawArrays(4,0,len(data));g.Disable(0x0B71);return self.aa.resolve()
 def close(self):
  g=self.g;g.DeleteProgram(self.program);g.delete('Buffers',self.vbo);g.delete('VertexArrays',self.vao);self.aa.close()
