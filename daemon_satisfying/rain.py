"""Deterministic fixed-step droplets with volume-conserving collision merges."""
import math
import numpy as np
from .scenes import Geometry
class Rain:
 def __init__(self,seed=1,params=None):
  self.rng=np.random.default_rng(seed);self.p=params or {};self.drops=[];self.clock=0.;self.trails=[]
 def update(self,dt,time):
  self.clock+=dt;interval=.55/float(self.p.get('rain_intensity',1.))
  while self.clock>interval:
   self.clock-=interval
   if len(self.drops)<180:self.drops.append([float(self.rng.uniform(-1.,1.)),float(self.rng.uniform(-.1,.85)),float(self.rng.uniform(.006,.018)),0.])
  for drop in self.drops:
   x,y,r,v=drop;friction=float(self.p.get('surface_friction',.5))
   acceleration=max(0.,r-.010*friction)*1.2;drop[3]=min(.22,v+acceleration*dt)
   drop[1]-=drop[3]*dt
   if drop[3]>.015:self.trails.append([x,y,drop[1],r*.35,0.])
  # Spatially local collision, exact area conservation in the glass-plane model.
  grid={};removed=set()
  for i,drop in enumerate(self.drops):
   x,y,r,v=drop;cell=(math.floor(x/.06),math.floor(y/.06))
   for dx in [-1,0,1]:
    for dy in [-1,0,1]:
     for j in grid.get((cell[0]+dx,cell[1]+dy),[]):
      if j in removed:continue
      other=self.drops[j];dist=math.hypot(x-other[0],y-other[1])
      if dist<r+other[2]:
       area=r*r+other[2]**2;drop[0]=(x*r*r+other[0]*other[2]**2)/area;drop[1]=(y*r*r+other[1]*other[2]**2)/area;drop[2]=math.sqrt(area);drop[3]=max(v,other[3]);removed.add(j)
       x,y,r,v=drop
   grid.setdefault(cell,[]).append(i)
  self.drops=[d for i,d in enumerate(self.drops) if i not in removed and d[1]>-.95]
  for trail in self.trails:trail[-1]+=dt
  self.trails=[v for v in self.trails if v[-1]<8][-1200:]
 def geometry(self,time):
  g=Geometry();fade=min(time/3,1)
  for x,a,b,r,age in self.trails:g.line([[x,a],[x,b]],np.array([.12,.14,.17])*math.exp(-age*.55)*fade,max(.35,r*100))
  for x,y,r,v in self.drops:
   g.disk(x,y,r,(.014,.018,.025));a=np.linspace(.25,2.4,16)
   g.line(np.column_stack((x+r*.75*np.cos(a),y+r*(1+v*2)*np.sin(a))),np.array([.31,.35,.40])*fade,.5)
   g.circle(x,y,r,(.07,.085,.11),.4,24)
  return g
