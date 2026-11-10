"""Validated parameter contract; invalid/nonfinite imports never reach shaders."""
import json,math,os,tempfile
from pathlib import Path
COMMON={'brightness':(.03,1.,.65),'speed':(.1,3.,1.)}
SPEC={
'harmonograph':{'frequency_ratio':(1.,7.,3.),'damping':(0.,.04,.006),'line_width':(.4,2.,1.15)},
'infinite_ripples':{'frequency':(.2,2.,1.),'amplitude':(.1,2.,1.),'source_count':(1,4,3),'wave_speed':(.5,1.4,1.),'reflectivity':(.1,1.,.7)},
'ink_singularity':{'density':(2,6,4),'vortex_strength':(.1,2.,.6),'trail_persistence':(.1,1.5,.6)},
'the_perfect_machine':{'finish':(.1,1.,.7),'camera_angle':(-.4,.6,.28)}}

def validate(effect,params=None):
 if effect not in SPEC:raise ValueError('Unknown effect')
 params=params or {}
 if not isinstance(params,dict):raise ValueError('Parameters must be an object')
 allowed={**COMMON,**SPEC[effect]};result={}
 for key,(lo,hi,default) in allowed.items():
  val=params.get(key,default)
  if isinstance(val,bool) or not isinstance(val,(int,float)) or not math.isfinite(val):raise ValueError(f'{key} must be finite numeric')
  if val<lo or val>hi:raise ValueError(f'{key} must be between {lo} and {hi}')
  if isinstance(default,int) and int(val)!=val:raise ValueError(f'{key} must be an integer')
  result[key]=int(val) if isinstance(default,int) else float(val)
 for key,default in [('reduced_motion',False),('monochrome',False)]:
  if not isinstance(params.get(key,default),bool):raise ValueError(f'{key} must be boolean')
  result[key]=params.get(key,default)
 palette=params.get('custom_palette')
 if palette is not None:
  if not isinstance(palette,list) or len(palette)!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in palette):raise ValueError('custom_palette must be three finite channels in [0,1]')
  result['custom_palette']=palette
 unknown=set(params)-set(allowed)-{'reduced_motion','monochrome','custom_palette'}
 if unknown:raise ValueError('Unsupported parameters: '+','.join(sorted(unknown)))
 return result

def atomic_json(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,temp=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
 try:
  with os.fdopen(fd,'w') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(temp,path)
 finally:
  if os.path.exists(temp):os.unlink(temp)

def validate_preset(data):
 if not isinstance(data,dict) or data.get('version')!=1:raise ValueError('Unsupported preset format')
 if data.get('quality','balanced') not in ['eco','balanced','quality']:raise ValueError('Unknown quality')
 effects=data.get('effects',{})
 if not isinstance(effects,dict):raise ValueError('effects must be an object')
 for effect,params in effects.items():validate(effect,params)
 for field in ['favorites','disabled','playlist']:
  values=data.get(field,[])
  if not isinstance(values,list) or any(key not in SPEC for key in values):raise ValueError('Invalid '+field)
 if not isinstance(data.get('seed',1),int) or isinstance(data.get('seed',1),bool) or not 0<=data.get('seed',1)<2**24:raise ValueError('Invalid seed')
 return data

SPEC.update({
'zen_geometry':{'complexity':(3,16,9),'symmetry':(3,12,7),'pattern_family':(0,2,0),'line_width':(.4,2.,.8)},
'liquid_obsidian':{'droplet_count':(3,12,6),'roughness':(.1,1.,.4)},
'mechanical_eternity':{'rotation_speed':(.2,2.,1.),'finish':(.1,1.,.7)},
'fractal_bloom':{'recursion_depth':(3,8,6),'symmetry':(3,10,6),'line_width':(.3,2.,.8)},
'silk_continuum':{'ribbon_count':(1,3,2),'ribbon_width':(.015,.07,.045),'stiffness':(.2,1.,.6)},
'particle_architect':{'particle_count':(400,4000,1800),'formation_speed':(.3,2.,1.)},
'harmonic_sculpture':{'wave_complexity':(1,8,3),'curve_density':(.3,2.,1.)},
'midnight_rain':{'rain_intensity':(.2,3.,1.),'surface_friction':(.1,1.,.5)},
'circuit_genesis':{'density':(80,500,240),'trace_width':(.4,2.,.85)},
'event_horizon':{'star_density':(.02,.25,.10),'lensing':(.2,3.,1.)},
'infinite_marble_machine':{'route':(0,2,1),'marble_speed':(.3,2.,1.)},
'domino_architect':{'branch_count':(3,9,6),'fall_speed':(.2,1.,.5)},
'mercury_garden':{'droplet_count':(4,16,12),'roughness':(.1,1.,.3),'attraction':(.3,2.,1.)},
'ink_choreography':{'density':(2,6,4),'vortex_strength':(.1,2.,.6),'trail_persistence':(.1,1.5,.6)},
'infinite_zen_garden':{'tines':(3,12,7),'groove_depth':(.2,2.,1.)},
'wave_field':{'pin_density':(24,52,36),'wave_amplitude':(.02,.16,.13),'wavelength':(.5,2.,1.)},
'orbital_synchronization':{'ring_count':(4,13,10),'rotation_speed':(.3,2.,1.)},
'infinite_origami':{'fold_count':(4,16,10),'fold_speed':(.3,2.,1.)},
'monolithic_construction':{'assembly_speed':(.3,2.,1.),'block_scale':(.7,1.,1.)},
'circuit_weaver':{'node_count':(6,20,12),'obstacle_density':(0.,.25,.12),'route_speed':(.3,2.,1.)}
})
