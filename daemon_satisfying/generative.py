"""Distinct constructive and mathematical state machines; no palette-only aliases."""
import math
import numpy as np
from .scenes import Geometry,smooth
TAU=math.tau

def project(p,angle=.3):
 p=np.asarray(p);x=p[:,0]*math.cos(angle)+p[:,2]*math.sin(angle);z=-p[:,0]*math.sin(angle)+p[:,2]*math.cos(angle)
 y=p[:,1]*.86-z*.42;scale=3/(3-z)
 return np.column_stack((x*scale,y*scale))

def segments(g,a,b,colors,width=1):
 a=np.asarray(a);b=np.asarray(b);d=b-a;nn=np.stack((-d[:,1],d[:,0]),axis=-1);nn*=width*.0012/np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-9)
 q=np.stack((a+nn,a-nn,b+nn,b+nn,a-nn,b-nn),axis=1).reshape(-1,2)
 colors=np.broadcast_to(colors,(len(a),3));g.add(np.column_stack((q,np.zeros(len(q)))),np.repeat(colors,6,axis=0))

def points(g,p,r,colors):
 p=np.asarray(p);r=np.broadcast_to(r,(len(p),));a=np.arange(6)*TAU/6;unit=np.stack((np.cos(a),np.sin(a)),axis=-1)
 ring=p[:,None,:]+r[:,None,None]*unit[None,:,:];nxt=np.roll(ring,-1,axis=1)
 q=np.stack((np.broadcast_to(p[:,None,:],ring.shape),ring,nxt),axis=2).reshape(-1,2)
 g.add(np.column_stack((q,np.zeros(len(q)))),np.repeat(np.broadcast_to(colors,(len(p),3)),18,axis=0))

class Generative:
 def __init__(self,key,seed,params,palette=None):
  self.key=key;self.seed=seed;self.p=params;self.palette=palette or {};self.cycle=-1;self.build(seed)
 def update_theme(self,palette):
  self.palette=palette or {}
 def build(self,seed):
  self.seed=seed;rng=np.random.default_rng(seed)
  if self.key=='particle_architect':
   n=int(self.p.get('particle_count',1800));self.random=rng.normal(size=(n,3));self.random/=np.maximum(np.linalg.norm(self.random,axis=1,keepdims=True),1e-9);self.random*=rng.uniform(.7,1.2,(n,1))
   u=np.arange(n)/n;v=(np.arange(n)*.61803398875)%1;theta=u*TAU;phi=v*TAU
   torus=np.column_stack(((.48+.17*np.cos(phi))*np.cos(theta),.17*np.sin(phi),(.48+.17*np.cos(phi))*np.sin(theta)))
   cube=rng.uniform(-.48,.48,(n,3));axis=np.arange(n)%3;cube[np.arange(n),axis]=np.where(np.arange(n)%2,.48,-.48)
   sphere=np.column_stack((np.sqrt(1-(2*u-1)**2)*np.cos(phi),2*u-1,np.sqrt(1-(2*u-1)**2)*np.sin(phi)))*.58
   self.targets=[torus,cube,sphere]
  elif self.key=='fractal_bloom':
   starts=[];ends=[];depths=[];sym=int(self.p.get('symmetry',6));depth=int(self.p.get('recursion_depth',6));current=[]
   for i in range(sym):current.append((np.array([0.,0.]),i*TAU/sym,.32,0))
   while current:
    start,angle,length,d=current.pop();end=start+np.array([math.cos(angle),math.sin(angle)])*length
    starts.append(start);ends.append(end);depths.append(d)
    if d<depth-1:
     for offset in [-.55,.55]:current.append((end,angle+offset,length*.63,d+1))
   self.starts=np.array(starts);self.ends=np.array(ends);self.depths=np.array(depths);self.depth=depth
  elif self.key=='zen_geometry':
   a=np.linspace(0,TAU,24001);s=int(self.p.get('symmetry',7));family=int(self.p.get('pattern_family',seed%3))
   if family==0:r=.45+.17*np.cos(s*a)+.055*np.cos(s*3*a)
   elif family==1:r=.69*np.cos(s*a)
   else:r=.24+.40*(.5+.5*np.sin(s*a))
   self.path=np.column_stack((r*np.cos(a),r*np.sin(a)))
   # Multiple ordered concentric passes are a construction, not a time-warped static image.
   self.paths=[self.path*f for f in np.linspace(.28,1.,int(self.p.get('complexity',9)))]
  elif self.key=='circuit_weaver':
   from .routing import plan_routes
   self.routes=plan_routes(seed,int(self.p.get('node_count',12)),float(self.p.get('obstacle_density',.12)),48)
  elif self.key=='circuit_genesis':
   size=44;visited={(size//2,size//2)};fronts=[(size//2,size//2)];paths=[]
   for _ in range(int(self.p.get('density',240))):
    if not fronts:break
    start=fronts[int(rng.integers(len(fronts)))];line=None
    for direction in rng.permutation(4):
     d=[(1,0),(0,1),(-1,0),(0,-1)][int(direction)];candidate=[start];p=start
     for _ in range(int(rng.integers(2,7))):
      q=(p[0]+d[0],p[1]+d[1])
      if q in visited or not (2<q[0]<size-2 and 2<q[1]<size-2):break
      visited.add(q);candidate.append(q);p=q
     if len(candidate)>1:line=candidate;break
    if line is not None:paths.append(np.array(line));fronts.append(line[-1])
    else:fronts.remove(start)
   self.branches=paths
 def geometry(self,time):
  time*=float(self.p.get('formation_speed',self.p.get('route_speed',1.)))
  cycle=int(time/180);t=time%180
  if cycle!=self.cycle:
   if self.cycle>=0:self.build(self.seed+1)
   self.cycle=cycle
  g=Geometry();fade=float(smooth(t/3)*(1-smooth((t-160)/20)))
  accent=np.array(self.palette.get('accent',(.59,.45,.48)))
  secondary=np.array(self.palette.get('secondary',(.79,.61,.61)))
  color=accent*fade
  if self.key=='zen_geometry':
   completion=float(np.clip(t/125,0,1))*len(self.paths)
   for i,path in enumerate(self.paths):
    n=int(float(np.clip(completion-i,0,1))*(len(path)-1))
    path_col=(accent if i%2==0 else (accent*.6+secondary*.4))*fade
    if n>1:g.line(path[:n],path_col,self.p.get('line_width',.8))
   if 0<completion<len(self.paths):
    i=int(completion);n=int((completion-i)*(len(self.path)-1));x,y=self.paths[i][n];g.disk(x,y,.004,secondary*1.35*fade,12)
  elif self.key=='fractal_bloom':
   bloom=float(np.clip(t/28.,0,1)*(1-smooth((t-140)/20)))*self.depth
   u=smooth(bloom-self.depths);mask=u>0
   a=self.starts[mask];b=a+(self.ends[mask]-a)*u[mask,None]
   angle=.05*math.sin(time*.012);r=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
   branch_colors=(accent[None,:]*(1.-.08*self.depths[mask,None])+secondary[None,:]*(.12*self.depths[mask,None]))*fade
   segments(g,a@r.T,b@r.T,branch_colors,self.p.get('line_width',.8))
  elif self.key=='particle_architect':
   stage=int(t/55)%3;u=float(smooth((t%55-4)/36));previous=self.random if stage==0 else self.targets[stage-1]
   target=self.targets[stage];n=len(target);delay=((np.arange(n)*.754877)%1)*.13
   individual=smooth((u-delay)/(1-delay));p=previous*(1-individual[:,None])+target*individual[:,None]
   # Arcing correspondence: no particle teleportation between target sculptures.
   p[:,1]+=np.sin(individual*math.pi)*.18*np.sin(np.arange(n)*.37)
   xy=project(p,.2+time*.012);z_factor=(.50+.50*(p[:,2]+1)/2)[:,None]
   p_color=(accent[None,:]*(1-z_factor)+secondary[None,:]*z_factor)*fade
   points(g,xy,.0018,p_color)
  elif self.key=='harmonic_sculpture':
   a=np.linspace(0,TAU,2400);resolve=float(smooth((t-20)/85));chaos=(1-resolve)*.45
   p=np.column_stack((.65*np.sin(a*3+chaos*math.sin(time*.02)),.55*np.sin(a*4),.40*np.sin(a*5+chaos*2)))
   xy=project(p,.2+time*.009);g.line(xy,accent*fade,self.p.get('curve_density',1.0))
   for shift in np.linspace(-.03,.03,int(self.p.get('wave_complexity',3))):g.line(project(p+np.array([0,shift,0]),.2+time*.009),secondary*.65*fade,.45)
  elif self.key=='circuit_weaver':
   routes=self.routes;size=48.;scale=1.38/size;mappt=lambda p:(np.array(p)-size/2)*scale
   blocked=np.array(routes['blocked'])
   if len(blocked):points(g,mappt(blocked),.005,accent*.12*fade)
   total=routes.get('metadata',{}).get('total_distance',sum(p['distance'] for p in routes['paths']))
   amount=float(np.clip(t/125,0,1))*max(total,1)
   for route in routes['paths']:
    n=int(np.clip(amount-route['reveal_start'],0,route['distance']))+1
    if n>1:g.line(mappt(route['points'][:n]),accent*fade,.95)
    if 1<n<len(route['points']):
     x,y=mappt(route['points'][n-1]);g.disk(x,y,.008,secondary*1.35*fade,12)
   for x,y in mappt(routes['nodes']):g.circle(x,y,.012,secondary*fade,.8,24)
   if routes['connected'] and t>125:
    pulse=secondary*.25*math.exp(-((t-132)/5)**2)
    for route in routes['paths']:g.line(mappt(route['points']),(accent*fade)+pulse,1.1)
  elif self.key=='circuit_genesis':
   amount=t/110*len(self.branches)
   for i,path in enumerate(self.branches):
    u=float(np.clip(amount-i,0,1));n=max(1,int(u*(len(path)-1))+1)
    if n>1:g.line((path[:n]-22)*.032,accent*fade,self.p.get('trace_width',.85))
   if t>110:
    for i,path in enumerate(self.branches):
     if i%7==0:
      x,y=(path[-1]-22)*.032;g.circle(x,y,.008,secondary*(.8+.25*math.sin(t*.1+i))*fade,.7,16)
  return g
