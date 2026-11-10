QUAD='''#version 300 es
precision highp float;
out vec2 uv;
void main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));uv=p;gl_Position=vec4(p*2.-1.,0,1);}
'''
HEADER='''#version 300 es
precision highp float;
in vec2 uv;out vec4 color;
uniform vec2 resolution;uniform float time;uniform float dt;uniform float seed;
uniform float intensity;uniform vec3 accent;uniform vec3 secondary;uniform vec3 dark_accent;uniform sampler2D state;
uniform float wave_speed;uniform float reflectivity;
uniform float p1;uniform float p2;uniform float p3;uniform float cycle;
uniform float bg_opacity;
float hash(float n){return fract(sin(n*127.1+seed*311.7)*43758.5453);}
'''
WAVE=HEADER+'''
void main(){
 vec2 d=1./resolution;vec2 h=texture(state,uv).rg;
 float lap=texture(state,uv+vec2(d.x,0)).r+texture(state,uv-vec2(d.x,0)).r
 +texture(state,uv+vec2(0,d.y)).r+texture(state,uv-vec2(0,d.y)).r-4.*h.r;
 float next=(2.*h.r-(1.-.006)*h.g+0.23*wave_speed*wave_speed*lap)/(1.+.006);
 // Short smooth impulses in physical simulation time; no random per-frame sparkle.
 float epoch=floor(time/(3.5/p1));float age=mod(time,3.5/p1);
 for(int i=0;i<4;i++){
  bool sync=mod(epoch,8.)>6.5;
  if(float(i)>=(sync?p3:1.))break;
  float a=6.2831853*float(i)/max(p3,1.)+epoch*.71;
  vec2 center=sync?vec2(.5)+vec2(cos(a),sin(a))*.24:vec2(.16+.68*hash(epoch+3.),.20+.60*hash(epoch+17.));
  if(sync)center.x=.5+(center.x-.5)*resolution.y/resolution.x;
  float r=length((uv-center)*resolution);
  next+=exp(-r*r/26.)*(1.-r*r/26.)*exp(-age*age/0.001)*.10*p2;
 }
 float edge=smoothstep(0.,.12,min(min(uv.x,1.-uv.x),min(uv.y,1.-uv.y)));
 color=vec4(clamp(next,-1.,1.)*edge,h.r,0,1);
}
'''
WAVE_VIEW=HEADER+'''
void main(){vec2 d=1./resolution;
 float h=texture(state,uv).r;
 vec2 n=vec2(texture(state,uv+vec2(d.x,0)).r-texture(state,uv-vec2(d.x,0)).r,
 texture(state,uv+vec2(0,d.y)).r-texture(state,uv-vec2(0,d.y)).r);
 vec3 normal=normalize(vec3(-n*45.,1.));vec3 key=normalize(vec3(-.4,.6,1.));
 float diffuse=max(0.,dot(normal,key)-key.z);
 float spec=max(0.,pow(max(0.,dot(normal,normalize(vec3(-.14,.22,1.)))),32.)-.34);
 float light=clamp(diffuse*.7+spec*.6+abs(h)*.07,0.,.8);
 vec2 q=(uv-.5)*vec2(resolution.x/resolution.y,1.);
 float vignette=1.-smoothstep(.60,1.04,length(q));
 float edge=smoothstep(0.,.17,min(min(uv.x,1.-uv.x),min(uv.y,1.-uv.y)));
 vec3 waterCol=mix(vec3(.08,.09,.11),accent*1.6,0.72);
 vec3 specCol=mix(vec3(1.),secondary*1.5,0.55);
 vec3 litCol=waterCol*diffuse+specCol*spec+abs(h)*.12*secondary;
 vec3 rgb=litCol*vignette*edge*intensity*(.4+.8*reflectivity);
 float fg=clamp((diffuse*1.8+spec*2.5+abs(h)*2.0)*vignette*edge,0.,1.);
 float a=mix(bg_opacity,1.0,fg);
 color=vec4(rgb,a);
}
'''
INK=HEADER+'''
void main(){
 vec2 q=(uv-.5)*vec2(resolution.x/resolution.y,1.);float r=length(q);
 float phase=mod(time,cycle)/cycle;
 float converge=smoothstep(.4,.65,phase)*(1.-smoothstep(.76,.92,phase));
 vec2 v=vec2(-q.y,q.x)*(.025+p2*.055)/(r+.18);
 v+=vec2(sin(q.y*9.+time*.13),cos(q.x*8.-time*.11))*.021;
 v-=q*converge*.22;
 vec2 sampleUV=uv-v*dt/vec2(resolution.x/resolution.y,1.);
 vec3 dye=texture(state,sampleUV).rgb*exp(-dt/(8.+p3*22.));
 float source=0.;
 for(int i=0;i<6;i++){
  if(float(i)>=p1)break;
  float a=float(i)*6.2831853/max(p1,1.)+sin(time*.07)*.3+seed*.31;
  vec2 pt=vec2(cos(a),sin(a))*(.27-.16*converge);
  float dist=length(q-pt);
  source+=exp(-dist*dist/0.000045)*dt*28.*(1.-smoothstep(.77,.95,phase));
 }
 // Semi-Lagrangian density transport through a coherent analytic velocity field.
 vec3 inkCol=mix(vec3(.7,.7,.75),accent*1.6,0.82);
 vec3 outRgb=clamp(dye+source*inkCol,0.,.90);
 float alpha=clamp(max(outRgb.r,max(outRgb.g,outRgb.b))*3.0,0.,1.);
 color=vec4(outRgb,alpha);
}
'''
COMPOSITE=HEADER+'''
void main(){vec4 samp=texture(state,uv);vec3 c=samp.rgb;float fade=smoothstep(0.,2.,time);
 vec3 rgb=clamp(mix(c,c*accent*1.8,0.22)*intensity*fade,vec3(0),vec3(1.0));
 float fg=clamp(max(samp.a,max(c.r,max(c.g,c.b))*2.0),0.,1.);
 float a=mix(bg_opacity,1.0,fg);
 color=vec4(rgb,a);}
'''
GEOM_VERT='''#version 300 es
precision highp float;
layout(location=0) in vec3 pos;layout(location=1) in vec3 rgb;
out vec3 c;uniform vec2 resolution;
void main(){gl_Position=vec4(pos.x*resolution.y/resolution.x,pos.y,pos.z,1);c=rgb;}
'''
GEOM_FRAG='''#version 300 es
precision highp float;
in vec3 c;out vec4 color;void main(){color=vec4(c,1);}
'''
MATERIAL=HEADER+'''
uniform int garden;uniform float droplet_count;uniform float roughness;
float smin(float a,float b,float k){float h=clamp(.5+.5*(b-a)/k,0.,1.);return mix(b,a,h)-k*h*(1.-h);}
vec3 center(int i){float fi=float(i);float a=fi*2.399963+seed*.17;float phase=mod(time,210.)/210.;
 float merge=smoothstep(.10,.58,phase)*(1.-smoothstep(.75,.96,phase));
 if(garden==1)return vec3(cos(a),.16*sin(a*1.3+time*.025),sin(a))*(.60*(1.-merge));
 return vec3(.43*cos(a+time*.055),.24*sin(a*1.7+time*.038),.29*sin(a+time*.055));}
float field(vec3 p){float d=10.;float phase=mod(time,210.)/210.;float merge=smoothstep(.10,.58,phase)*(1.-smoothstep(.75,.96,phase));
 for(int i=0;i<16;i++){if(float(i)>=droplet_count)break;vec3 c=center(i);float r=garden==1?.095*mix(1.,pow(droplet_count,1./3.),merge):.18;
 float q=length(p-c)-r;
 if(garden==0){vec3 c2=center((i+1)%int(droplet_count));vec3 ab=c2-c;float h=clamp(dot(p-c,ab)/dot(ab,ab),0.,1.);q=min(q,length(p-c-ab*h)-.075);}
 d=smin(d,q,garden==1?.055:.17);}
 return d;}
void main(){vec2 q=(uv-.5)*vec2(resolution.x/resolution.y,1.);vec3 ro=vec3(0,.55,2.5),rd=normalize(vec3(q*1.6,-2.2));
 float t=0.;bool hit=false;vec3 p;
 for(int k=0;k<72;k++){p=ro+rd*t;float d=field(p);if(d<.0015){hit=true;break;}t+=max(d*.7,.001);if(t>5.)break;}
 vec3 col=vec3(0);
 if(hit){float e=.002;vec3 n=normalize(vec3(field(p+vec3(e,0,0))-field(p-vec3(e,0,0)),field(p+vec3(0,e,0))-field(p-vec3(0,e,0)),field(p+vec3(0,0,e))-field(p-vec3(0,0,e))));
 vec3 l=normalize(vec3(-.6,1.,1.));float diff=max(0.,dot(n,l));float spec=pow(max(0.,dot(reflect(rd,n),l)),mix(75.,14.,roughness));
 float rim=pow(1.-max(0.,dot(n,-rd)),3.);
 vec3 specTint=mix(vec3(.32,.36,.41),accent*1.8,0.70);
 vec3 rimTint=mix(secondary,accent*1.5,0.55);
 col=(vec3(.03,.035,.04)*diff+specTint*spec+rimTint*rim*0.8);
 }
 float fg=hit?1.0:0.0;
 color=vec4(clamp(col*intensity*smoothstep(0.,3.,time),0.,.85),fg);}
'''
COSMIC=HEADER+'''
uniform float star_density;uniform float lensing;
float hash21(vec2 p){p=fract(p*vec2(123.34,456.21)+seed*17.1);p+=dot(p,p+45.32);return fract(p.x*p.y);}
float cnoise(vec2 p){vec2 i=floor(p);vec2 f=fract(p);f=f*f*(3.-2.*f);
 return mix(mix(hash21(i),hash21(i+vec2(1,0)),f.x),mix(hash21(i+vec2(0,1)),hash21(i+vec2(1,1)),f.x),f.y);}
float cfbm(vec2 p){float v=0.,a=.5;mat2 rot=mat2(.8,-.6,.6,.8);
 for(int i=0;i<4;i++){v+=a*cnoise(p);p=rot*p*2.;a*=.5;}return v;}
float stars(vec2 p,float layer){vec2 id=floor(p);vec2 f=fract(p);float h=fract(sin(dot(id,vec2(127.1,311.7))+layer*43.+seed*17.)*43758.5453);
 if(h>star_density*.85)return 0.;vec2 pt=vec2(fract(h*73.),fract(h*119.));float d=length(f-pt);
 float footprint=clamp(dot(fwidth(p),fwidth(p))*.2,.001,.014);return exp(-d*d/max(.001+.001*h,footprint))*(.3+.7*h);}
void main(){
 vec2 p=(uv-.5)*vec2(resolution.x/resolution.y,1.);p+=vec2(sin(time*.02),cos(time*.015))*.015;
 float r=length(p);float rs=.17;
 float deflection=lensing*(rs*.45)/(r*r+.002);vec2 lensed=p*(1.-deflection*.08);
 float s=stars(lensed*55.,1.)+stars(lensed*110.+3.1,2.)*.5;
 vec3 col=vec3(.5,.55,.6)*s*smoothstep(rs*1.05,rs*1.25,r);
 float tilt=.28;vec2 pDisk=vec2(p.x,p.y/tilt);float rDisk=length(pDisk);float phi=atan(pDisk.y,pDisk.x);
 float angVel=.85/(rDisk*sqrt(rDisk)+.08);float diskTime=time*.6+angVel;
 vec2 plasmaUv=vec2(rDisk*4.-time*.1,phi*3.+diskTime);float plasma=cfbm(plasmaUv);
 float doppler=1.-.45*(p.x/(r+.05));
 float rIn=rs*1.25,rOut=rs*3.4;
 float diskMask=smoothstep(rIn,rIn+.06,rDisk)*(1.-smoothstep(rOut*.6,rOut,rDisk));
 float rLensTop=length(vec2(p.x,(abs(p.y)-rs*.7)/(tilt*.6)));
 float lensedRing=smoothstep(rs*1.1,rs*1.3,rLensTop)*(1.-smoothstep(rs*1.8,rs*2.8,rLensTop));
 float diskDensity=diskMask*(.6+.4*plasma)*doppler;
 float haloDensity=lensedRing*(.4+.3*plasma)*(1.-smoothstep(0.,rs*.4,abs(p.x)))*.8;
 float photonRing=exp(-pow((r-rs*1.12)/.007,2.))*1.8+exp(-pow((r-rs*1.05)/.0035,2.))*1.2;
 vec3 plasmaColor=mix(vec3(1.,.65,.32),vec3(1.,.92,.78),plasma*.7+photonRing*.3);
 plasmaColor=mix(plasmaColor,accent*1.8,0.65);
 col+=plasmaColor*(diskDensity*1.5+haloDensity*1.0)+mix(vec3(1.,.85,.85),secondary*1.6,0.60)*photonRing*doppler;
 float glow=exp(-r*3.8)*.40+exp(-r*8.5)*.55;
 float innerGlow=glow*(1.-smoothstep(rs,rs+.02,r));
 col+=mix(vec3(.6,.1,.1),accent*1.5,0.65)*innerGlow;
 col*=smoothstep(rs*.96,rs*1.02,r)*(1.-smoothstep(.8,1.4,r))*intensity*smoothstep(0.,2.5,time);
 float fg=clamp((diskDensity*1.4+haloDensity+photonRing+innerGlow*1.5)*1.8,0.,1.);
 float a=mix(bg_opacity,1.0,fg);
 color=vec4(clamp(col,0.,1.),a);
}
'''
SAND_STEP=HEADER+'''
uniform float tines;uniform float groove_depth;
vec2 path(float t){float a=clamp(mod(t,190.)/135.,0.,1.)*6.2831853;float family=mod(floor(seed),3.);
 if(family<.5)return vec2(cos(a),sin(a*2.))*.30;
 if(family<1.5)return vec2(cos(a),sin(a))*(.24+.10*cos(a*5.));
 return vec2(cos(a*3.),sin(a*2.))*.29;}
float sdseg(vec2 p,vec2 a,vec2 b){vec2 ab=b-a;return length(p-a-ab*clamp(dot(p-a,ab)/max(dot(ab,ab),.000001),0.,1.));}
void main(){vec2 q=(uv-.5)*vec2(resolution.x/resolution.y,1.);vec2 a=path(time-dt),b=path(time);vec2 tangent=normalize(path(time+.05)-path(time-.05)+.000001);vec2 normal=vec2(-tangent.y,tangent.x);
 float h=texture(state,uv).r;float groove=0.;
 if(mod(time,190.)<135.)for(int i=0;i<14;i++){if(float(i)>=tines)break;vec2 offset=normal*(float(i)-(tines-1.)*.5)*.010;
 float d=sdseg(q,a+offset,b+offset);groove=min(groove,-exp(-d*d/.000004)*.035*groove_depth);}
 h=min(h,groove);h*=exp(-dt*smoothstep(160.,185.,mod(time,190.))*.8);color=vec4(h,0,0,1);}
'''
SAND_VIEW=HEADER+'''
void main(){vec2 d=1./resolution;float h=texture(state,uv).r;vec2 n=vec2(texture(state,uv+vec2(d.x,0)).r-texture(state,uv-vec2(d.x,0)).r,texture(state,uv+vec2(0,d.y)).r-texture(state,uv-vec2(0,d.y)).r);
 vec3 normal=normalize(vec3(n*38.,1.));float lit=max(0.,dot(normal,normalize(vec3(-.5,.7,1.)))-.55);
 float grain=fract(sin(dot(floor(uv*resolution*2.),vec2(127.1,311.7)))*43758.5453);
 float vignette=1.-smoothstep(.35,.65,length(uv-.5));
 vec3 sandBase=vec3(.018,.020,.024)*(grain*.3+.7);
 vec3 sandLit=mix(vec3(.26,.29,.33),accent*1.5,0.65)*lit;
 vec3 col=(sandBase+sandLit)*vignette;
 vec3 rgb=col*intensity*smoothstep(0.,3.,time);
 float fg=clamp(lit*3.0,0.,1.);
 float a=mix(bg_opacity,1.0,fg*vignette);
 color=vec4(rgb,a);}
'''
INK_CHOREOGRAPHY=INK.replace('vec2 v=vec2(-q.y,q.x)*(.025+p2*.055)/(r+.18);','float align=smoothstep(.16,.64,phase);\n vec2 v=vec2(-q.y*sign(q.x),abs(q.x))*(.12+p2*.05);').replace('v+=vec2(sin(q.y*9.+time*.13),cos(q.x*8.-time*.11))*.021;','v+=vec2(sin(q.y*9.+time*.13+seed),cos(q.x*8.-time*.11))*.021*(1.-align);').replace('v-=q*converge*.22;','v-=q*.08;').replace('float a=float(i)*6.2831853/max(p1,1.)+sin(time*.07)*.3+seed*.31;\n  vec2 pt=vec2(cos(a),sin(a))*(.27-.16*converge);','float side=mod(float(i),2.)<.5?-1.:1.;\n  vec2 pt=vec2(side*(.22+.015*floor(float(i)/2.)),-.19+.025*sin(time*.05));')
