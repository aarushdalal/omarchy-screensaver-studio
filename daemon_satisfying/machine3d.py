"""Exploded precision drive: explicit parts, rigid transforms and tooth-phase kinematics.

Prescribed assembly, not a rigid-body collision solver. Parts share z-aligned shafts.
"""
import math
import numpy as np
from .scenes import Geometry,smooth
TAU=math.tau

def extrude(poly,depth,color):
 p=np.asarray(poly);n=len(p);lo=np.column_stack((p,np.full(n,-depth/2)));hi=lo.copy();hi[:,2]=depth/2
 centerlo=np.mean(lo,axis=0);centerhi=np.mean(hi,axis=0);j=np.roll(np.arange(n),-1)
 faces=np.concatenate((np.stack((np.tile(centerhi,(n,1)),hi,hi[j]),axis=1),
  np.stack((np.tile(centerlo,(n,1)),lo[j],lo),axis=1),
  np.stack((lo,lo[j],hi),axis=1),np.stack((hi,lo[j],hi[j]),axis=1)),axis=0)
 return faces,np.broadcast_to(color,(len(faces),3)).copy()

def ring(ro,ri,depth,color,n=24):
 a=np.linspace(0,TAU,n,endpoint=False);v=[]
 for r,z in [(ro,-depth/2),(ro,depth/2),(ri,-depth/2),(ri,depth/2)]:v.append(np.column_stack((r*np.cos(a),r*np.sin(a),np.full(n,z))))
 j=np.roll(np.arange(n),-1);faces=[]
 for outer,inner in [(1,3),(2,0),(0,1),(3,2)]:
  faces.extend([np.stack((v[outer],v[outer][j],v[inner]),axis=1),np.stack((v[inner],v[outer][j],v[inner][j]),axis=1)])
 f=np.concatenate(faces);return f,np.broadcast_to(color,(len(f),3)).copy()

def cylinder(r,depth,color,n=16):
 a=np.linspace(0,TAU,n,endpoint=False);return extrude(np.column_stack((r*np.cos(a),r*np.sin(a))),depth,color)

def box(w,h,d,color):return extrude([[-w/2,-h/2],[w/2,-h/2],[w/2,h/2],[-w/2,h/2]],d,color)

def gear(n,module,depth):
 a=(np.arange(n*8)+.5)*TAU/(n*8)
 r=n*module/2+np.tile(np.array([-.72,-.72,-.3,.63,.63,.63,-.3,-.72]),n)*module
 # Use a true annular tooth rim, with independent spokes and a hub on its shaft.
 ro=np.column_stack((r*np.cos(a),r*np.sin(a)))
 ri=np.column_stack((n*module*.32*np.cos(a),n*module*.32*np.sin(a)))
 v=[]
 for p,z in [(ro,-depth/2),(ro,depth/2),(ri,-depth/2),(ri,depth/2)]:v.append(np.column_stack((p,np.full(len(p),z))))
 j=np.roll(np.arange(len(a)),-1);faces=[]
 for outer,inner in [(1,3),(2,0),(0,1),(3,2)]:faces.extend([np.stack((v[outer],v[outer][j],v[inner]),axis=1),np.stack((v[inner],v[outer][j],v[inner][j]),axis=1)])
 f=np.concatenate(faces);parts=[f];colors=[np.broadcast_to((.30,.33,.37),(len(f),3)).copy()]
 for k in range(5):
  sp,c=box(n*module*.28,.015,depth,(.26,.29,.33));a=k*TAU/5;sp[:,:,0]+=n*module*.18
  x=sp[:,:,0].copy();y=sp[:,:,1].copy();sp[:,:,0]=x*math.cos(a)-y*math.sin(a);sp[:,:,1]=x*math.sin(a)+y*math.cos(a)
  parts.append(sp);colors.append(c)
 hub,c=ring(n*module*.105,n*module*.045,depth*1.4,(.38,.41,.45),24);parts.append(hub);colors.append(c)
 return np.concatenate(parts),np.concatenate(colors)

class PrecisionMachine:
 def __init__(self,seed=1,finish=.7):
  self.seed=seed;self.parts=[];self.finish=finish;self.cycle=0
  self.build(seed)
 def part(self,mesh,pos,kind,stage,axis=0):
  idx=len(self.parts);rng=np.random.default_rng(self.seed*997+idx)
  # Disassembly travels along each shaft, then outward into organized rows.
  offset=np.array([((idx%7)-3)*.07,((idx//7)%5-2)*.07,(-1 if idx%2 else 1)*(.35+idx%5*.06)])
  self.parts.append((mesh,np.array(pos,float),kind,float(stage),axis,offset))
 def build(self,seed):
  self.seed=seed;self.parts=[];nx,ny=(4,3) if seed%2 else (5,2);module=.0082;n=32;r=n*module/2
  dark=(.11,.13,.16);metal=(.27,.30,.34);bright=(.39,.43,.48)
  # Twin rails and four corner posts establish a rigid chassis before the shaft modules.
  width=(nx-1)*2*r+.28;height=(ny-1)*2*r+.28
  for y in [-height/2,height/2]:
   self.part(box(width,.055,.08,dark),(0,y,-.11),'rail',1)
   self.part(box(width,.016,.016,metal),(0,y+.021,-.055),'trim',4)
  for x in [-width/2,width/2]:
   self.part(box(.055,height,.08,dark),(x,0,-.11),'endframe',2)
  for x in [-width/2,width/2]:
   for y in [-height/2,height/2]:self.part(cylinder(.025,.35,metal),(x,y,.02),'post',7)
  for row in range(ny):
   for col in range(nx):
    x=(col-(nx-1)/2)*2*r;y=(row-(ny-1)/2)*2*r;axis=(row+col)%2;idx=row*nx+col
    self.part(cylinder(.010,.31,metal),(x,y,.015),'shaft',10+idx*.20,axis)
    for z,side in [(-.105,-1),(.105,1)]:
     self.part(box(.078,.068,.026,dark),(x,y,z),'bearing_block',19+idx*.25+side,axis)
     self.part(ring(.024,.012,.015,bright),(x,y,z+side*.021),'bearing_race',25+idx*.20,axis)
     self.part(ring(.028,.014,.009,metal),(x,y,z+side*.035),'washer',31+idx*.18,axis)
     self.part(cylinder(.019,.018,bright,6),(x,y,z+side*.050),'locknut',55+idx*.15,axis)
     for dx,dy in [(-.027,-.022),(-.027,.022),(.027,-.022),(.027,.022)]:
      self.part(cylinder(.0065,.014,metal,6),(x+dx,y+dy,z+side*.018),'fastener',58+idx*.10+side*.5,axis)
    self.part(gear(n,module,.027),(x,y,.028),'gear',37+idx*.70,axis)
    # Retaining collars and shaft key are individual assembled solids.
    self.part(ring(.018,.010,.011,metal),(x,y,-.025),'collar',33+idx*.2,axis)
    self.part(ring(.018,.010,.011,metal),(x,y,.063),'collar',49+idx*.2,axis)
    self.part(box(.006,.016,.04,bright),(x+.010,y,.03),'key',35+idx*.2,axis)
  self.part_count=len(self.parts)
 def geometry(self,time,speed=1.):
  time*=speed;cyc=int(time/190);t=time%190
  if cyc!=self.cycle:self.cycle=cyc;self.build(self.seed+1)
  # Assembly is completed before any gear motion; reverse transform hierarchy at end.
  runtime=max(0,min(t-72,70));omega=.17
  yaw=.28+.10*math.sin(time*.009);pitch=.62+.035*math.sin(time*.007)
  ry=np.array([[math.cos(yaw),0,math.sin(yaw)],[0,1,0],[-math.sin(yaw),0,math.cos(yaw)]])
  rx=np.array([[1,0,0],[0,math.cos(pitch),-math.sin(pitch)],[0,math.sin(pitch),math.cos(pitch)]])
  camera=rx@ry;all_tri=[];all_col=[]
  light=np.array([-.35,.65,1.]);light/=np.linalg.norm(light)
  for (faces,base),pos,kind,stage,axis,offset in self.parts:
   u=float(smooth((t-stage)/8)*(1-smooth((t-(166-stage*.18))/10)))
   f=faces.copy()
   if kind in ('gear','key','collar','locknut','washer'):
    angle=runtime*omega*(-1 if axis else 1)+(math.pi/32 if axis else 0)
    x=f[:,:,0].copy();y=f[:,:,1].copy();f[:,:,0]=x*math.cos(angle)-y*math.sin(angle);f[:,:,1]=x*math.sin(angle)+y*math.cos(angle)
   f+=pos+offset*(1-u)
   f=f@camera.T
   normal=np.cross(f[:,1]-f[:,0],f[:,2]-f[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
   diffuse=np.maximum(0,normal@light);spec=np.maximum(0,normal@np.array([-.15,.30,.942]))**24
   shade=.30+.68*diffuse+.55*spec
   all_tri.append(f);all_col.append(np.clip(base*shade[:,None],0,.64))
  f=np.concatenate(all_tri);c=np.concatenate(all_col);order=np.argsort(f[:,:,2].mean(axis=1))
  f=f[order];c=c[order]
  # Weak perspective gives legible depth while retaining calm architectural framing.
  f[:,:,:2]*=(3.3/(3.3-f[:,:,2:3]))*1.35
  f[:,:,2]=0
  g=Geometry();g.add(f.reshape(-1,3),np.repeat(c,3,axis=0))
  return g
