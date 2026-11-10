"""Explicit meshes and continuous kinematics for spatial motion concepts."""
import math
import numpy as np
from .world import World,rotation
from .scenes import smooth
from .machine3d import box,ring,cylinder,gear
TAU=math.tau

def sphere(r,color,n=18,m=10):
 u=np.linspace(0,TAU,n+1);v=np.linspace(-math.pi/2,math.pi/2,m+1)
 p=np.stack(np.meshgrid(u,v),axis=-1);a=p[:,:,0];b=p[:,:,1]
 q=np.stack((r*np.cos(b)*np.cos(a),r*np.sin(b),r*np.cos(b)*np.sin(a)),axis=-1)
 f=np.stack((q[:-1,:-1],q[1:,:-1],q[:-1,1:],q[:-1,1:],q[1:,:-1],q[1:,1:]),axis=2).reshape(-1,3,3)
 return f,np.broadcast_to(color,(len(f),3)).copy()

def tube(path,r,color):
 path=np.asarray(path);tangent=np.gradient(path,axis=0);side=np.cross(tangent,np.array([0,1,0]));side/=np.maximum(np.linalg.norm(side,axis=1,keepdims=True),1e-9)
 up=np.cross(side,tangent);up/=np.maximum(np.linalg.norm(up,axis=1,keepdims=True),1e-9)
 a=np.arange(8)*TAU/8;p=path[:,None,:]+r*(side[:,None,:]*np.cos(a)[None,:,None]+up[:,None,:]*np.sin(a)[None,:,None]);j=np.roll(np.arange(8),-1)
 f=np.stack((p[:-1],p[1:],p[:-1,j],p[:-1,j],p[1:],p[1:,j]),axis=2).reshape(-1,3,3)
 return f,np.broadcast_to(color,(len(f),3)).copy()

class Physical:
 def __init__(self,key,seed,params,palette=None):
  self.key=key;self.seed=seed;self.p=params;self.palette=palette or {};self.cycle=-1;self.build(seed)
 def update_theme(self,palette):
  self.palette=palette or {}
 def build(self,seed):
  self.seed=seed;rng=np.random.default_rng(seed)
  if self.key=='monolithic_construction':
   cells=[]
   for y in range(10):
    for x in range(-8,9):
     radius=(x/6)**2+((y-3)/6)**2
     if (y<4 and 4<=abs(x)<=6) or (y>=3 and .62<radius<1.15):cells.append((x,y,0))
   self.target=np.array(cells)*.082;self.target[:,1]-=.35
   self.initial=rng.uniform([-1.,-.1,-.65],[1.,.65,.65],(len(cells),3));self.block=box(.078*self.p.get('block_scale',1.),.078*self.p.get('block_scale',1.),.13*self.p.get('block_scale',1.),(.24,.27,.31))
  elif self.key=='infinite_marble_machine':
   a=np.linspace(0,TAU,1001);route=int(self.p.get('route',seed%3));self.path=np.column_stack((.73*np.sin(a),.16*np.cos(a)+.10*np.cos(2*a),(.34+.035*route)*np.sin(2*a)))
   if route==0:self.path=np.column_stack((.73*np.cos(a),.12*np.sin(2*a),.42*np.sin(a)))
   elif route==2:self.path=np.column_stack(((.58+.12*np.cos(3*a))*np.cos(a),.16*np.sin(3*a),(.36+.07*np.cos(3*a))*np.sin(a)))
   tangent=np.gradient(self.path,axis=0);side=np.cross(tangent,np.array([0,1,0]));side/=np.maximum(np.linalg.norm(side,axis=1,keepdims=True),1e-9)
   self.rails=[tube(self.path+side*s*.026,.008,(.29,.32,.36)) for s in [-1,1]]
   ds=np.linalg.norm(np.diff(self.path,axis=0),axis=1);velocity=np.sqrt(np.maximum(.12,1.2-1.4*self.path[:-1,1]));weights=ds/velocity
   self.travel=np.concatenate(([0],np.cumsum(weights)));self.ball=sphere(.029,(.43,.47,.52))
  elif self.key=='domino_architect':
   branches=int(self.p.get('branch_count',6));positions=[];dist=[];yaw=[]
   for k in range(branches):
    a=k*TAU/branches;u=np.linspace(.04,.67,27);theta=a+.36*np.sin(u*math.pi/.67)
    path=np.column_stack((u*np.cos(theta),np.zeros(len(u)),u*np.sin(theta)));d=np.concatenate(([0],np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))))+.04
    tangent=np.gradient(path,axis=0)
    positions.extend(path);dist.extend(d);yaw.extend(np.arctan2(tangent[:,0],tangent[:,2]))
   self.positions=np.array(positions);self.dist=np.array(dist);self.yaw=np.array(yaw);self.domino=box(.021,.085,.014,(.29,.32,.36))
  elif self.key=='mechanical_eternity':
   self.sun=gear(72,.008,.035);self.planet=gear(24,.008,.025)
  elif self.key=='wave_field':
   n=int(self.p.get('pin_density',36));x,z=np.meshgrid(np.linspace(-.65,.65,n),np.linspace(-.45,.45,n));self.pins=np.column_stack((x.ravel(),np.zeros(n*n),z.ravel()));self.pin=box(1,1,1,(.30,.33,.37));self.n=n
  elif self.key=='orbital_synchronization':
   self.rings=[ring(.15+i*.047,.141+i*.047,.013,(.31,.34,.38),96) for i in range(int(self.p.get('ring_count',10)))]
 def world(self,time):
  time*=float(self.p.get('rotation_speed',self.p.get('marble_speed',self.p.get('fold_speed',self.p.get('assembly_speed',1.)))))
  cyc=int(time/190);t=time%190
  if cyc!=self.cycle:
   if self.cycle>=0:self.build(self.seed+1)
   self.cycle=cyc
  w=World();p=self.p
  if self.key=='silk_continuum':
   phase=float(smooth((t-15)/100)*(1-smooth((t-155)/30)));coils=3-2*phase
   u=np.linspace(0,TAU*.94,260);a=u*coils+time*.045
   for k in range(int(p.get('ribbon_count',2))):
    center=np.column_stack((.43*np.cos(a),.38*np.sin(a),.07*u*coils-.45+k*.17))
    tangent=np.gradient(center,axis=0);side=np.column_stack((np.cos(a)*np.cos(u*(.3+.4*(1-float(p.get('stiffness',.6))))+time*.015),np.sin(a)*np.cos(u*(.3+.4*(1-float(p.get('stiffness',.6))))+time*.015),np.sin(u*(.3+.4*(1-float(p.get('stiffness',.6))))+time*.015)))
    side-=tangent*(np.sum(side*tangent,axis=1)/np.maximum(np.sum(tangent*tangent,axis=1),1e-9))[:,None];side/=np.maximum(np.linalg.norm(side,axis=1,keepdims=True),1e-9)
    width=float(p.get('ribbon_width',.045));left=center-side*width;right=center+side*width
    f=np.stack((left[:-1],right[:-1],left[1:],left[1:],right[:-1],right[1:]),axis=1).reshape(-1,3,3)
    w.add((f,np.broadcast_to((.31,.34,.39),(len(f),3)).copy()))
  elif self.key=='mechanical_eternity':
   angle=time*.10;w.add(self.sun,rotation=rotation('z',angle))
   for k in range(10):
    theta=k*TAU/10;pos=(.384*math.cos(theta),.384*math.sin(theta),0)
    a=theta+math.pi-(math.pi-72*(theta-angle))/24
    w.add(self.planet,pos,rotation('z',a));w.add(cylinder(.013,.10,(.24,.27,.31)),pos)
   # Stationary skeletal frame and a restrained balance mechanism outside the sun.
   w.add(ring(.505,.493,.025,(.14,.16,.19),120),pos=(0,0,-.05))
   w.add(ring(.10,.094,.015,(.32,.35,.40),48),pos=(0,-.66,0),rotation=rotation('y',math.sin(angle*3)*.5))
  elif self.key=='infinite_marble_machine':
   for mesh in self.rails:w.add(mesh)
   # Arc-length integration with height-dependent speed, closed route and continuous velocity.
   travel=(time*.16)%self.travel[-1];i=min(len(self.path)-2,int(np.searchsorted(self.travel,travel)-1));u=(travel-self.travel[i])/max(self.travel[i+1]-self.travel[i],1e-9)
   pos=self.path[i]*(1-u)+self.path[i+1]*u;pos[1]+=.025;w.add(self.ball,pos)
   for idx in [80,300,550,800]:
    at=self.path[idx];w.add(cylinder(.012,.30,(.13,.15,.18)),(at[0],at[1]-.16,at[2]),rotation('x',math.pi/2))
    proximity=math.exp(-np.linalg.norm(pos-at)**2/.018);w.add(ring(.075,.069,.012,(.22,.25,.29),48),at,rotation('x',math.pi/2+proximity*.7))
  elif self.key=='domino_architect':
   for i,(pos,d,yaw) in enumerate(zip(self.positions,self.dist,self.yaw)):
    assembled=float(smooth((t-i*.30)/6))
    fall=float(smooth((t-(76+d*7))/float(p.get('fall_speed',.5))))*math.pi/2
    rot=rotation('y',yaw)@rotation('x',fall)
    center=pos+rot@np.array([0,.0425,0])+np.array([0,.45*(1-assembled),0])
    w.add(self.domino,center,rot)
  elif self.key=='wave_field':
   envelope=float(smooth(t/30)*(1-smooth((t-125)/35)));q=self.pins
   amp=float(p.get('wave_amplitude',.13));height=.15+amp*envelope*(np.sin(q[:,0]*8/float(p.get('wavelength',1.))-time*.40)+.45*np.sin(q[:,2]*11/float(p.get('wavelength',1.))-time*.31))
   f,c=self.pin;f=np.broadcast_to(f,(len(q),*f.shape)).copy();f[:,:,:,0]*=.011;f[:,:,:,2]*=.011;f[:,:,:,1]*=height[:,None,None]
   f+=q[:,None,None,:];f[:,:,:,1]+=height[:,None,None]/2-.20
   w.faces.append(f.reshape(-1,3,3));w.colors.append(np.broadcast_to((.29,.32,.36),(len(q)*len(c),3)).copy())
  elif self.key=='orbital_synchronization':
   period=140.;a=TAU*(time%period)/period
   for i,mesh in enumerate(self.rings):
    # Integer rates return all rings to the same plane at the exact period.
    rot=rotation('y',a*(i+1))@rotation('x',a*(i+2));w.add(mesh,rotation=rot)
  elif self.key=='infinite_origami':
   panels=int(p.get('fold_count',10));u=float(smooth((t-12)/70)*(1-smooth((t-125)/50)))
   angle=u*math.radians(72);length=1.3/panels;vertices=[np.array([0.,0.,0.])]
   for i in range(panels):vertices.append(vertices[-1]+np.array([length*math.cos(angle),length*math.sin(angle)*(1 if i%2 else -1),0]))
   vertices=np.array(vertices);vertices-=vertices.mean(axis=0)
   for i in range(panels):
    a,b=vertices[i],vertices[i+1];corner=np.array([a+[0,0,-.42],b+[0,0,-.42],a+[0,0,.42],b+[0,0,.42]])
    f=np.array([corner[[0,1,2]],corner[[2,1,3]]]);w.add((f,np.broadcast_to((.24,.27,.31),(2,3)).copy()))
  elif self.key=='monolithic_construction':
   for i,(target,start) in enumerate(zip(self.target,self.initial)):
    u=float(smooth((t-5-i*.58)/18));lift=np.array([0,.45*math.sin(u*math.pi),0]);pos=start*(1-u)+target*u+lift
    w.add(self.block,pos)
  if self.key=='mechanical_eternity':w.colors=[c*(.5+.5*float(p.get('finish',.7))) for c in w.colors]
  return w
