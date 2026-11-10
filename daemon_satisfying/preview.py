"""Isolated GTK4 GPU preview. Never writes global PID or ambient state."""
import argparse,fcntl,json,os,signal,sys,time
from pathlib import Path
import gi
gi.require_version('Gtk','4.0');gi.require_version('Gdk','4.0')
from gi.repository import Gtk,Gdk,Gio,GLib
from .engine import Engine,IMPLEMENTED,PROFILES

class Surface(Gtk.GLArea):
 def __init__(self,effect,quality,seed,params,theme=None):
  super().__init__();self.effect=effect;self.quality=quality;self.seed=seed;self.params=params;self.theme=theme
  self.engine=None;self.previous=0.;self.pending=0.;self.next_due=0.;self.durations=[];self.frames=0;self.last_render=0.
  self.set_use_es(True);self.set_required_version(3,0);self.set_has_depth_buffer(False);self.set_auto_render(False)
  self.set_hexpand(True);self.set_vexpand(True)
  self.connect('realize',self.realized);self.connect('unrealize',self.unrealized);self.connect('render',self.rendered)
  self.tick_id=self.add_tick_callback(self.tick)
 def realized(self,area):
  self.make_current()
  if self.get_error():raise RuntimeError(str(self.get_error()))
 def unrealized(self,area):
  self.make_current()
  if self.engine:self.engine.close();self.engine=None
 def tick(self,area,clock):
  now=clock.get_frame_time()/1e6
  if not self.get_mapped():self.previous=now;self.pending=0.;self.next_due=0.;return True
  if self.previous==0:self.previous=now
  if self.next_due==0:self.next_due=now
  elapsed=now-self.previous
  self.previous=now;self.pending+=min(elapsed,.25)
  fps=PROFILES[self.quality]['fps']
  root=self.get_root();app=root.get_application() if root and hasattr(root,'get_application') else None
  config=getattr(app,'config',None)
  if config:
   fps=min(fps,float(config.fps))
   metrics=getattr(app,'metrics',None)
   if metrics and not metrics.ac_online and config.battery_reduce_fps:fps=min(fps,float(config.battery_fps))
   if getattr(app,'is_ambient',False):fps=min(fps,40.)
  interval=1/max(1.,fps)
  if now+1e-6>=self.next_due:
   self.queue_render()
   self.next_due=now+interval if now-self.next_due>interval else self.next_due+interval
  return True
 def rendered(self,area,context):
  import ctypes as C
  from .gpu import I,U,GL
  w=self.get_width()*self.get_scale_factor();h=self.get_height()*self.get_scale_factor()
  if w<1 or h<1:return True
  gl=GL();fn=gl.lib.glGetIntegerv;fn.argtypes=[U,C.POINTER(I)];fb=I();fn(0x8CA6,C.byref(fb))
  if not self.engine or (self.engine.w,self.engine.h)!=(w,h):
   if self.engine:self.engine.close()
   self.engine=Engine(self.effect,w,h,self.quality,self.seed,self.params)
   self.engine.gl.GetIntegerv=self.engine.gl.lib.glGetIntegerv;self.engine.gl.GetIntegerv.argtypes=[U,C.POINTER(I)]

  if self.theme:
   palette=getattr(self.theme,'palette',self.theme)
   self.engine.accent=palette.accent[:3]
  start=time.perf_counter();self.engine.render(self.pending,fb.value,(w,h));self.pending=0.
  self.durations.append((time.perf_counter()-start)*1000);self.frames+=1
  return True

class Preview(Gtk.Application):
 def __init__(self,args):
  super().__init__(application_id='org.daemon.satisfying.preview',flags=Gio.ApplicationFlags.NON_UNIQUE)
  self.args=args;self.connect('activate',self.activate);self.surface=None;self.ids=[];self.theme=None
 def activate(self,app):
  # Existing palette owner, read-only. No second theme parser or active-theme changes.
  try:
   from omarchy_screensaver.theme import ThemeManager
  except ImportError:
   sys.path.insert(0,str(Path.home()/'.local/share/omarchy-screensaver'))
   from omarchy_screensaver.theme import ThemeManager
  self.theme=ThemeManager('auto',str(Path.home()/'.config/omarchy-screensaver/themes'))
  win=Gtk.ApplicationWindow(application=self);win.set_title('DAEMON Satisfying · Development Preview');win.set_default_size(960,540)
  css=Gtk.CssProvider();css.load_from_data(b'window { background: #000; }')
  Gtk.StyleContext.add_provider_for_display(win.get_display(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
  self.surface=Surface(self.args.effect,self.args.quality,self.args.seed,{},self.theme);win.set_child(self.surface)
  key=Gtk.EventControllerKey.new();key.connect('key-pressed',lambda *unused:self.dismiss());win.add_controller(key)
  click=Gtk.GestureClick.new();click.connect('pressed',lambda *unused:self.dismiss());win.add_controller(click)
  if self.args.fullscreen:win.fullscreen()
  win.connect('close-request',lambda *unused:self.dismiss())
  self.win=win;win.present()
  self.ids.append(GLib.timeout_add_seconds(self.args.duration,self.dismiss))
  # Reuse ThemeManager; no additional timer polls. Gio watches authoritative theme directory.
  self.monitors=[]
  for path in [Path.home()/'.local/state/omarchy/current',Path.home()/'.config/caelestia']:
   if path.exists():
    mon=Gio.File.new_for_path(str(path)).monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES,None)
    mon.connect('changed',lambda *unused:self.reload_theme());self.monitors.append(mon)
  for sig in (signal.SIGINT,signal.SIGTERM):self.ids.append(GLib.unix_signal_add(GLib.PRIORITY_HIGH,sig,self.dismiss))
 def reload_theme(self):
  self.theme.reload()
 def dismiss(self,*unused):
  if getattr(self,'closing',False):return True
  self.closing=True
  for mon in getattr(self,'monitors',[]):mon.cancel()
  for source in self.ids:
   try:GLib.source_remove(source)
   except Exception:pass
  self.ids=[]
  if self.surface:
   self.surface.make_current()
   if self.surface.engine:self.surface.engine.close();self.surface.engine=None
  self.win.destroy();self.quit();return True

def main():
 p=argparse.ArgumentParser();p.add_argument('effect',choices=sorted(IMPLEMENTED));p.add_argument('--quality',choices=list(PROFILES),default='balanced');p.add_argument('--seed',type=int,default=1);p.add_argument('--duration',type=int,default=12);p.add_argument('--fullscreen',action='store_true');args=p.parse_args()
 # One preview process; a preview never evicts a different owner's session process.
 lock_path=Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/f'daemon-satisfying-preview-{os.getuid()}.lock'
 with lock_path.open('a') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('A DAEMON Satisfying preview is already running')
  app=Preview(args);raise SystemExit(app.run([]))
if __name__=='__main__':main()
