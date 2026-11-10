"""State and geometry for precision scenes. Coordinates are height-normalized."""
import math
import numpy as np
TAU=math.tau

def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)

def harmonograph(t,seed=0,ratio=3,damping=.006):
 # Integer ratios guarantee a closed undamped core; slow envelope draws inward.
 a=TAU*t;b=a*(-ratio-.125)+seed*.17
 # Rotary-table harmonograph: two damped coupled oscillations form a rosette.
 return np.stack(((.47*np.cos(a)+.22*np.cos(b))*np.exp(-damping*t),
 (.47*np.sin(a)+.22*np.sin(b))*np.exp(-damping*t)),axis=-1)

def gear_graph(count=7):
 """Tangent pitch circles. Each child has the same module; no random placement."""
 teeth=[40,24,32,20,28,24,20][:count]
 centers=[np.array([-.36,0.])]; module=.009
 for i in range(1,len(teeth)):
  # Extend away from the root in an alternating shallow zigzag.
  angle=.35 if i%2 else -.35
  r=(teeth[i-1]+teeth[i])*module/2
  centers.append(centers[-1]+np.array([math.cos(angle),math.sin(angle)])*r)
 centers=np.array(centers);centers-=centers.mean(axis=0)
 return centers,np.array(teeth),module

def gear_angles(time,centers,teeth,module):
 angles=[time*.17]
 for i in range(1,len(teeth)):
  d=centers[i]-centers[i-1];theta=math.atan2(d[1],d[0])
  # Tooth at contact on parent maps to gap on child.
  phase=teeth[i-1]*(theta-angles[i-1])
  angles.append(theta+math.pi-(math.pi-phase)/teeth[i])
 return angles

class Geometry:
 def __init__(self):self.lines=[];self.tris=[]
 def line(self,points,color=(.28,.31,.34),width=1.):
  # Stroke as triangles: consistent antialias-independent width across GLES drivers.
  p=np.asarray(points,dtype=float)
  if p.shape[1]==2:p=np.column_stack((p,np.zeros(len(p))))
  if len(p)<2:return
  a,b=p[:-1],p[1:];d=b[:,:2]-a[:,:2];n=np.stack((-d[:,1],d[:,0]),axis=-1)
  n*=width*.0012/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-9)
  off=np.column_stack((n,np.zeros(len(n))))
  q=np.stack((a+off,a-off,b+off,b+off,a-off,b-off),axis=1).reshape(-1,3)
  self.add(q,color)
 def add(self,vertices,color):
  v=np.asarray(vertices); c=np.broadcast_to(color,(len(v),3)); self.tris.append(np.concatenate((v,c),axis=1))
 def circle(self,x,y,r,color,width=1,n=72):
  a=np.linspace(0,TAU,n+1);self.line(np.column_stack((x+r*np.cos(a),y+r*np.sin(a))),color,width)
 def disk(self,x,y,r,color,n=40,z=0):
  a=np.linspace(0,TAU,n+1);c=np.tile([x,y,z],(n,1));p=np.column_stack((x+r*np.cos(a),y+r*np.sin(a),np.full(n+1,z)))
  self.add(np.stack((c,p[:-1],p[1:]),axis=1).reshape(-1,3),color)
 def gear(self,center,teeth,module,angle,finish=.6):
  x,y=center;r=teeth*module/2
  # Flat top teeth with tip/root relief rather than colliding circular polygons.
  aa=(np.arange(teeth*8)+.5)/(teeth*8)*TAU+angle
  rr=r+np.tile(np.array([-.75,-.75,-.35,.65,.65,.65,-.35,-.75]),teeth)*module
  outer=np.column_stack((x+rr*np.cos(aa),y+rr*np.sin(aa)))
  inner=np.column_stack((x+r*.68*np.cos(aa),y+r*.68*np.sin(aa)))
  nxt=np.roll(np.arange(len(aa)),-1)
  q=np.stack((outer,inner,outer[nxt],outer[nxt],inner,inner[nxt]),axis=1).reshape(-1,2)
  shade=np.repeat((.24+.10*np.sin(aa+1))*finish,6)
  rgb=shade[:,None]*np.array([1,1.08,1.15])
  self.add(np.column_stack((q,np.zeros(len(q)))),rgb)
  self.line(np.vstack((outer,outer[0])),(.31,.34,.37),.7)
  self.circle(x,y,r*.68,(.12,.14,.16),.8)
  self.disk(x,y,r*.19,(.10,.12,.14));self.circle(x,y,r*.19,(.35,.38,.42),.7)
  for k in range(5):
   a=angle+k*TAU/5;b=a+.07
   pts=np.array([[x+r*.22*math.cos(a),y+r*.22*math.sin(a)],
    [x+r*.65*math.cos(a),y+r*.65*math.sin(a)],
    [x+r*.65*math.cos(b),y+r*.65*math.sin(b)],
    [x+r*.22*math.cos(b),y+r*.22*math.sin(b)]])
   self.add([[*pts[0],0],[*pts[1],0],[*pts[2],0],[*pts[0],0],[*pts[2],0],[*pts[3],0]],(.16,.18,.20))
 def array(self):return np.concatenate(self.tris).astype('f4') if self.tris else np.empty((0,6),dtype='f4')

class Machine:
 def __init__(self,seed=0,count=7):
  self.seed=seed;self.centers,self.teeth,self.module=gear_graph(count)
 def geometry(self,time,assembly=True,speed=1.):
  t=time*speed;cycle=140.;p=(t%cycle)/cycle;g=Geometry()
  assembled=float(smooth((p-.06)/.36)*(1-smooth((p-.82)/.16))) if assembly else 1.
  # A train only operates once every gear has fully seated.
  run=max(0.,min(t%cycle-60.,52.)) if assembly else t
  angles=gear_angles(run,self.centers,self.teeth,self.module)
  # Chassis rails, bearing pedestals and end caps assemble before the gear train.
  support=float(smooth((p-.015)/.12)*(1-smooth((p-.94)/.06))) if assembly else 1.
  for side in [-1,1]:
   y=side*(.30+.40*(1-support))
   g.line([[-.82,y],[.82,y]],(.16,.18,.21),5.0)
   g.line([[-.82,y+side*.008],[.82,y+side*.008]],(.31,.34,.38),.75)
   for k,x in enumerate(np.linspace(-.77,.77,13)):
    u=float(smooth((p-.02-k*.006)/.10)) if assembly else 1.
    by=y+side*.20*(1-u)
    g.disk(x,by,.012,(.24,.27,.30));g.circle(x,by,.006,(.08,.10,.12),.7)
  for i,center in enumerate(self.centers):
   x,y=center
   g.line([[x,-.30],[x,y]],(.095,.11,.13),6.)
   g.circle(x,y,.045,(.20,.23,.26),2)
  for i,(center,n,a) in enumerate(zip(self.centers,self.teeth,angles)):
   delay=i*.035;u=float(smooth((p-.05-delay)/.18)*(1-smooth((p-.82+delay*.2)/.15))) if assembly else 1.
   offset=np.array([0.,(-1 if i%2 else 1)*.67*(1-u)])
   c=center+offset
   if assembly and u<1:g.line([center,c],(.035,.045,.052),.5)
   g.gear(c,int(n),self.module,a)
   g.disk(c[0],c[1],.009,(.36,.39,.42))
  # Separate mounting posts/plates settle before gears and recede after them.
  for x in np.linspace(-.78,.78,7):
   y=-.33-.25*(1-assembled);g.circle(x,y,.012,(.13,.15,.17),.8)
  if assembled>.999:
   # Completion latch and slow reciprocating linkage, tied to the input gear.
   a=angles[0];root=self.centers[0];pin=root+np.array([math.cos(a),math.sin(a)])*.065
   slider=np.array([pin[0]+math.sqrt(.42**2-(pin[1]+.29)**2),-.29])
   g.line([pin,slider],(.24,.27,.30),2.3);g.disk(*pin,.012,(.40,.43,.46))
  return g

class InkFilaments:
 """Connected material lines transported together through the velocity field."""
 def __init__(self,seed=1,density=4,palette=None):
  self.seed=seed;self.palette=palette or {};self.n=int(np.clip(density,2,6))*5;self.length=220
  self.angles=np.repeat(np.arange(self.n//5)*TAU/(self.n//5),5)+np.tile(np.linspace(-.025,.025,5),self.n//5)
  self.points=np.zeros((self.n,self.length,2));self.valid=0;self.emit=0.;self.last_cycle=0
 def update_theme(self,palette):
  self.palette=palette or {}
 def sources(self,time,converge):
  a=self.angles+math.sin(time*.07)*.3+self.seed*.31
  radius=.27-.16*converge+np.tile(np.linspace(-.006,.006,5),self.n//5)
  return np.column_stack((np.cos(a)*radius,np.sin(a)*radius))
 def update(self,time,dt,vortex=.6):
  phase=time%120/120;converge=float(smooth((phase-.4)/.25)*(1-smooth((phase-.76)/.16)))
  if int(time/120)!=self.last_cycle:
   self.valid=0;self.last_cycle=int(time/120)
  q=self.points;radius=np.linalg.norm(q,axis=-1,keepdims=True)
  v=np.stack((-q[:,:,1],q[:,:,0]),axis=-1)*(.025+vortex*.055)/(radius+.18)
  v+=np.stack((np.sin(q[:,:,1]*9+time*.13),np.cos(q[:,:,0]*8-time*.11)),axis=-1)*.021
  v-=q*converge*.22;self.points+=v*dt
  self.emit+=dt
  if self.emit>=.15:
   self.emit%=.15;self.points[:,1:]=self.points[:,:-1];self.points[:,0]=self.sources(time,converge)
   self.valid=min(self.length,self.valid+1)
 def geometry(self,time,intensity=.65):
  g=Geometry();phase=time%120/120;fade=float(smooth(time/3)*(1-smooth((phase-.79)/.19)))
  if self.valid<2:return g
  accent=np.array(self.palette.get('accent',(.59,.45,.48)))
  secondary=np.array(self.palette.get('secondary',(.79,.61,.61)))
  for i,points in enumerate(self.points[:,:self.valid]):
   # Restrained individual filaments; density buffer underneath supplies the soft body.
   c=(accent if i%2==0 else secondary)*(.85+.35*math.sin(i*2.1)**2)*intensity*fade
   g.line(points*2,c,.85)
  return g

class Choreography(InkFilaments):
 def sources(self,time,converge=0):
  group=np.arange(self.n)//5;side=np.where(group%2,-1.,1.)
  radius=.22+.015*(group//2)+np.tile(np.linspace(-.004,.004,5),self.n//5)
  return np.column_stack((side*radius,np.full(self.n,-.19+.025*math.sin(time*.05))))
 def update(self,time,dt,vortex=.6):
  phase=time%120/120;align=float(smooth((phase-.16)/.48));q=self.points
  v=np.stack((-q[:,:,1]*np.sign(q[:,:,0]),np.abs(q[:,:,0])),axis=-1)*(.12+vortex*.05)
  v+=np.stack((np.sin(q[:,:,1]*9+time*.13+self.seed),np.cos(q[:,:,0]*8-time*.11)),axis=-1)*.021*(1-align)
  v-=q*.08;self.points+=v*dt;self.emit+=dt
  if int(time/120)!=self.last_cycle:self.valid=0;self.last_cycle=int(time/120)
  if self.emit>=.15:
   self.emit%=.15;self.points[:,1:]=self.points[:,:-1];self.points[:,0]=self.sources(time);self.valid=min(self.length,self.valid+1)
