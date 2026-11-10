"""GPU render graph: retained drawing, stateful simulation, batched geometry."""
import ctypes as C
import math
import numpy as np
from .gpu import GL, P, AATarget
from . import shaders as S
from .scenes import harmonograph, Geometry, Machine, InkFilaments, Choreography
from .machine_gpu import MachineGPU
from .generative import Generative
from .physical import Physical
from .world import WorldGPU
from .rain import Rain
from .settings import validate

PROFILES = {
    'eco': dict(scale=.5, fps=24, sim=192),
    'balanced': dict(scale=.75, fps=30, sim=320),
    'quality': dict(scale=1., fps=45, sim=448),
}

GENERATIVE_EFFECTS = {
    'zen_geometry', 'fractal_bloom', 'particle_architect',
    'harmonic_sculpture', 'circuit_genesis', 'circuit_weaver',
}

PHYSICAL_EFFECTS = {
    'mechanical_eternity', 'silk_continuum', 'infinite_marble_machine',
    'domino_architect', 'wave_field', 'orbital_synchronization',
    'infinite_origami', 'monolithic_construction',
}

IMPLEMENTED = {
    'harmonograph', 'infinite_ripples', 'the_perfect_machine', 'ink_singularity',
    *GENERATIVE_EFFECTS,
    *PHYSICAL_EFFECTS,
    'midnight_rain',
    'liquid_obsidian', 'mercury_garden',
    'event_horizon',
    'infinite_zen_garden',
    'ink_choreography',
}


class Engine:
    def __init__(self, effect, w, h, quality='balanced', seed=1, params=None, theme=None, config=None):
        if effect not in IMPLEMENTED:
            raise ValueError('Effect not implemented: ' + effect)
        self.gl = GL()
        self.effect = effect
        self.w = w
        self.h = h
        self.quality = quality
        self.profile = PROFILES[quality]
        self.seed = seed
        self.next_seed = seed
        self.params = validate(effect, params)
        self.time = 0.
        self.accum = 0.
        self.last_draw = 0.
        self.index = 0
        self.config = config
        self.bg_opacity = self._resolve_bg_opacity(config)
        self.theme = theme
        self.accent, self.secondary, self.dark_accent, self.foreground = self._extract_theme_colors(theme)
        self.palette_dict = {
            'accent': self.accent,
            'secondary': self.secondary,
            'dark_accent': self.dark_accent,
            'foreground': self.foreground,
        }
        self.intensity = float(np.clip(self.params.get('brightness', .65), .03, 1.))
        self.speed = float(np.clip(self.params.get('speed', 1.), .1, 3.))
        if self.params.get('reduced_motion', False):
            self.speed *= .35
        self.programs = {}
        self.compile_ms = 0.
        self.targets = []
        self.aa_target = None
        self.bg_tex = self._init_bg_texture(w, h)

        g = self.gl
        self.vao = g.gen('VertexArrays')
        g.BindVertexArray(self.vao)
        self.vbo = g.gen('Buffers')
        for key, vert, frag in [('view', S.QUAD, S.COMPOSITE), ('geom', S.GEOM_VERT, S.GEOM_FRAG)]:
            self.compile(key, vert, frag)
        self.sw = int(self.profile['sim'] * w / h)
        self.sh = self.profile['sim']

        if effect == 'infinite_ripples':
            self.compile('step', S.QUAD, S.WAVE)
            self.compile('waveview', S.QUAD, S.WAVE_VIEW)
            self.targets = [g.target(self.sw, self.sh, True) for _ in range(2)]
        elif effect == 'infinite_zen_garden':
            self.compile('sandstep', S.QUAD, S.SAND_STEP)
            self.compile('sandview', S.QUAD, S.SAND_VIEW)
            self.targets = [g.target(self.sw, self.sh, True) for _ in range(2)]
        elif effect == 'ink_singularity':
            self.ink = InkFilaments(seed, self.params.get('density', 4), palette=self.palette_dict)
            self.compile('step', S.QUAD, S.INK)
            self.targets = [g.target(self.sw, self.sh, True) for _ in range(2)]
            self.aa_target = AATarget(g, w, h, samples=4)
        elif effect == 'ink_choreography':
            self.ink = Choreography(seed, self.params.get('density', 4), palette=self.palette_dict)
            self.compile('step', S.QUAD, S.INK_CHOREOGRAPHY)
            self.targets = [g.target(self.sw, self.sh, True) for _ in range(2)]
            self.aa_target = AATarget(g, w, h, samples=4)
        elif effect == 'harmonograph':
            self.aa_target = AATarget(g, w, h, samples=4)
            self.path = harmonograph(
                np.linspace(0, 16, 36001), seed,
                float(np.clip(self.params.get('frequency_ratio', 3), 1, 7)),
                float(np.clip(self.params.get('damping', .006), 0, .1)),
            )
        elif effect == 'the_perfect_machine':
            self.machine = MachineGPU(g, int(w * self.profile['scale']), int(h * self.profile['scale']), seed)
            self.compile_ms += self.machine.compile_ms
        elif effect in ('liquid_obsidian', 'mercury_garden'):
            self.compile('material', S.QUAD, S.MATERIAL)
            caps = {'eco': (854, 480), 'balanced': (1280, 720), 'quality': (1920, 1080)}
            capw, caph = caps[quality]
            factor = min(self.profile['scale'], capw / w, caph / h)
            self.material_size = (max(1, int(w * factor)), max(1, int(h * factor)))
            self.material_target = g.target(*self.material_size)
            self.targets.append(self.material_target)
        elif effect == 'event_horizon':
            self.compile('cosmic', S.QUAD, S.COSMIC)
        elif effect == 'midnight_rain':
            self.rain = Rain(seed, self.params, palette=self.palette_dict)
            self.aa_target = AATarget(g, w, h, samples=4)
        elif effect in GENERATIVE_EFFECTS:
            self.generative = Generative(effect, seed, self.params, palette=self.palette_dict)
            self.aa_target = AATarget(g, w, h, samples=4)
        elif effect in PHYSICAL_EFFECTS:
            self.physical = Physical(effect, seed, self.params, palette=self.palette_dict)
            self.world_gpu = WorldGPU(g, int(w * self.profile['scale']), int(h * self.profile['scale']))
            self.compile_ms += self.world_gpu.compile_ms

        g.BindFramebuffer(0x8D40, 0)

    def _extract_theme_colors(self, theme):
        if theme is not None:
            palette = getattr(theme, 'palette', theme)
            accent = getattr(palette, 'accent', None)
            if accent:
                acc = tuple(accent[:3])
                sec = tuple(getattr(palette, 'secondary', accent)[:3])
                dark_acc = tuple(getattr(palette, 'dark_accent', (acc[0] * 0.4, acc[1] * 0.4, acc[2] * 0.4))[:3])
                fg = tuple(getattr(palette, 'foreground', (0.8, 0.8, 0.8))[:3])
                return acc, sec, dark_acc, fg
        return (.59, .45, .48), (.79, .61, .61), (.24, .18, .19), (.76, .62, .55)

    def update_theme(self, theme):
        self.theme = theme
        self.accent, self.secondary, self.dark_accent, self.foreground = self._extract_theme_colors(theme)
        self.palette_dict = {
            'accent': self.accent,
            'secondary': self.secondary,
            'dark_accent': self.dark_accent,
            'foreground': self.foreground,
        }
        if hasattr(self, 'generative'):
            self.generative.update_theme(self.palette_dict)
        if hasattr(self, 'physical'):
            self.physical.update_theme(self.palette_dict)
        if hasattr(self, 'rain'):
            self.rain.update_theme(self.palette_dict)
        if hasattr(self, 'ink'):
            self.ink.update_theme(self.palette_dict)

    def _init_bg_texture(self, w, h):
        g = self.gl
        tex = g.gen('Textures')
        g.BindTexture(0x0DE1, tex)
        g.TexParameteri(0x0DE1, 0x2801, 0x2601)  # GL_LINEAR
        g.TexParameteri(0x0DE1, 0x2800, 0x2601)  # GL_LINEAR
        g.TexParameteri(0x0DE1, 0x2802, 0x812F)  # GL_CLAMP_TO_EDGE
        g.TexParameteri(0x0DE1, 0x2803, 0x812F)  # GL_CLAMP_TO_EDGE

        raw_bytes = None
        try:
            from omarchy_screensaver.wallpaper import wallpaper_manager
            raw_bytes = wallpaper_manager.get_rgba_bytes(w, h)
        except Exception:
            pass

        if raw_bytes is not None and len(raw_bytes) == w * h * 4:
            data = (C.c_char * len(raw_bytes)).from_buffer_copy(raw_bytes)
            g.TexImage2D(0x0DE1, 0, 0x1908, w, h, 0, 0x1908, 0x1401, C.cast(data, P))
        else:
            black = (C.c_ubyte * 4)(0, 0, 0, 255)
            g.TexImage2D(0x0DE1, 0, 0x1908, 1, 1, 0, 0x1908, 0x1401, C.cast(black, P))
        return tex

    def _resolve_bg_opacity(self, config):
        if config is not None and hasattr(config, 'background_opacity'):
            return max(0.0, min(1.0, float(config.background_opacity)))
        try:
            from omarchy_screensaver.config import Config
            return max(0.0, min(1.0, float(Config.load().background_opacity)))
        except Exception:
            return 0.68

    def update_config(self, config):
        self.config = config
        self.bg_opacity = self._resolve_bg_opacity(config)

    def compile(self, key, vert, frag):
        pr, ms = self.gl.program(vert, frag)
        self.programs[key] = pr
        self.compile_ms += ms

    def quad(self, key, tex, time, dt, w, h):
        g = self.gl
        pr = self.programs[key]
        g.UseProgram(pr)
        g.BindVertexArray(self.vao)
        g.ActiveTexture(0x84C0)
        g.BindTexture(0x0DE1, tex)
        if getattr(self, 'bg_tex', None):
            g.ActiveTexture(0x84C1)
            g.BindTexture(0x0DE1, self.bg_tex)
        p = self.params
        if self.effect == 'infinite_ripples':
            p1 = p.get('frequency', 1.)
            p2 = p.get('amplitude', 1.)
            p3 = p.get('source_count', 3.)
        else:
            p1 = p.get('density', 4.)
            p2 = p.get('vortex_strength', .6)
            p3 = p.get('trail_persistence', .6)
        uniforms = {
            'state': (0,),
            'bg_state': (1,),
            'resolution': (w, h),
            'time': (float(time),),
            'dt': (float(dt),),
            'seed': (float(self.seed),),
            'intensity': (self.intensity,),
            'bg_opacity': (float(self.bg_opacity),),
            'accent': self.palette(),
            'secondary': self.secondary,
            'dark_accent': self.dark_accent,
            'wave_speed': (float(p.get('wave_speed', 1.)),),
            'reflectivity': (float(p.get('reflectivity', .7)),),
            'p1': (float(np.clip(p1, .1, 6)),),
            'p2': (float(np.clip(p2, .1, 2)),),
            'p3': (float(np.clip(p3, 1 if self.effect == 'infinite_ripples' else 0, 4)),),
            'cycle': (120.,),
            'garden': (1 if self.effect == 'mercury_garden' else 0,),
            'droplet_count': (float(p.get('droplet_count', 6. if self.effect == 'liquid_obsidian' else 12.)),),
            'roughness': (float(p.get('roughness', .4 if self.effect == 'liquid_obsidian' else .3)),),
            'star_density': (float(p.get('star_density', .10)),),
            'lensing': (float(p.get('lensing', 1.)),),
            'tines': (float(p.get('tines', 7.)),),
            'groove_depth': (float(p.get('groove_depth', 1.)),),
        }
        for name, values in uniforms.items():
            g.uniform(pr, name, *values)
        g.DrawArrays(4, 0, 3)

    def geometry(self, geometry, w, h):
        data = geometry.array()
        g = self.gl
        pr = self.programs['geom']
        g.UseProgram(pr)
        g.uniform(pr, 'resolution', w, h)
        g.BindVertexArray(self.vao)
        g.BindBuffer(0x8892, self.vbo)
        g.BufferData(0x8892, data.nbytes, data.ctypes.data_as(P), 0x88E0)
        for i in range(2):
            g.EnableVertexAttribArray(i)
            g.VertexAttribPointer(i, 3, 0x1406, 0, 24, P(i * 12))
        g.DrawArrays(4, 0, len(data))

    def render(self, dt, target=0, output_size=None):
        g = self.gl
        ow, oh = output_size or (self.w, self.h)
        dt = max(0., min(float(dt), .25)) * self.speed
        old = self.time
        self.time += dt
        g.Disable(0x0BE2)
        g.Disable(0x0B71)

        if self.effect == 'infinite_ripples':
            self.accum += dt
            fixed = 1 / 60
            steps = min(16, int((self.accum + 1e-9) / fixed))
            for _ in range(steps):
                src = self.targets[self.index]
                dst = self.targets[1 - self.index]
                g.BindFramebuffer(0x8D40, dst[1])
                g.Viewport(0, 0, self.sw, self.sh)
                self.quad('step', src[0], self.time - self.accum, fixed, self.sw, self.sh)
                self.accum -= fixed
                self.index = 1 - self.index
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            self.quad('waveview', self.targets[self.index][0], self.time, dt, self.sw, self.sh)

        elif self.effect == 'infinite_zen_garden':
            self.accum += dt
            fixed = 1 / 60
            steps = min(16, int((self.accum + 1e-9) / fixed))
            for _ in range(steps):
                src = self.targets[self.index]
                dst = self.targets[1 - self.index]
                g.BindFramebuffer(0x8D40, dst[1])
                g.Viewport(0, 0, self.sw, self.sh)
                self.quad('sandstep', src[0], self.time - self.accum, fixed, self.sw, self.sh)
                self.accum -= fixed
                self.index = 1 - self.index
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            self.quad('sandview', self.targets[self.index][0], self.time, dt, self.sw, self.sh)

        elif self.effect in ('ink_singularity', 'ink_choreography'):
            self.accum += dt
            fixed = 1 / 60
            steps = min(16, int((self.accum + 1e-9) / fixed))
            for _ in range(steps):
                src = self.targets[self.index]
                dst = self.targets[1 - self.index]
                g.BindFramebuffer(0x8D40, dst[1])
                g.Viewport(0, 0, self.sw, self.sh)
                self.quad('step', src[0], self.time - self.accum, fixed, self.sw, self.sh)
                self.ink.update(self.time - self.accum, fixed, float(self.params.get('vortex_strength', .6)))
                self.accum -= fixed
                self.index = 1 - self.index
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            self.quad('view', self.targets[self.index][0], self.time, dt, self.sw, self.sh)
            # Antialiased ink filaments overlay via AATarget
            g.BindFramebuffer(0x8D40, self.aa_target.fb)
            g.Viewport(0, 0, self.w, self.h)
            g.ClearColor(0, 0, 0, 0)
            g.Clear(0x4000)
            self.geometry(self.ink.geometry(self.time, 1.), self.w, self.h)
            tex = self.aa_target.resolve()
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            g.Enable(0x0BE2)
            g.BlendFuncSeparate(1, 1, 0, 1)
            self.quad('view', tex, self.time, dt, self.w, self.h)
            g.Disable(0x0BE2)

        elif self.effect == 'harmonograph':
            g.BindFramebuffer(0x8D40, self.aa_target.fb)
            g.Viewport(0, 0, self.w, self.h)
            cycle = 150.
            p = self.time % cycle
            last = old % cycle
            if p < last:
                g.ClearColor(0, 0, 0, 0)
                g.Clear(0x4000)
                self.seed = self.next_seed if self.next_seed != self.seed else self.seed + 1
                self.path = harmonograph(
                    np.linspace(0, 16, 36001), self.seed,
                    self.params.get('frequency_ratio', 3), self.params.get('damping', .006),
                )
                last = 0
            a = int(min(last / 112, 1) * 36000)
            b = int(min(p / 112, 1) * 36000)
            geo = Geometry()
            if b > a:
                geo.line(self.path[a:b + 1], self.palette(), float(np.clip(self.params.get('line_width', 1.15), .2, 2.)))
            self.geometry(geo, self.w, self.h)
            tex = self.aa_target.resolve()
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            brightness = self.intensity
            self.intensity *= 1 - float(np.clip((p - 133) / 17, 0, 1))
            self.quad('view', tex, self.time, dt, self.w, self.h)
            self.intensity = brightness
            if p < 112 and b > 0:
                pen = Geometry()
                x, y = self.path[b]
                pen.disk(x, y, .0045, (self.secondary[0] * brightness, self.secondary[1] * brightness, self.secondary[2] * brightness), 16)
                self.geometry(pen, ow, oh)

        elif self.effect == 'the_perfect_machine':
            tex = self.machine.render(self.time, self.intensity, self.palette(), self.params)
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            intensity = self.intensity
            self.intensity = 1.
            self.quad('view', tex, self.time, dt, self.w, self.h)
            self.intensity = intensity

        elif self.effect in ('liquid_obsidian', 'mercury_garden'):
            tex, fb = self.material_target
            rw, rh = self.material_size
            g.BindFramebuffer(0x8D40, fb)
            g.Viewport(0, 0, rw, rh)
            self.quad('material', 0, self.time, dt, rw, rh)
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            intensity = self.intensity
            self.intensity = 1.
            self.quad('view', tex, self.time, dt, rw, rh)
            self.intensity = intensity

        elif self.effect == 'event_horizon':
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            self.quad('cosmic', 0, self.time, dt, ow, oh)

        elif self.effect == 'midnight_rain':
            self.rain.update(dt, self.time)
            geo = self.rain.geometry(self.time)
            g.BindFramebuffer(0x8D40, self.aa_target.fb)
            g.Viewport(0, 0, self.w, self.h)
            g.ClearColor(0, 0, 0, 0)
            g.Clear(0x4000)
            self.geometry(geo, self.w, self.h)
            tex = self.aa_target.resolve()
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            self.quad('view', tex, self.time, dt, self.w, self.h)

        elif self.effect in GENERATIVE_EFFECTS:
            geo = self.generative.geometry(self.time)
            g.BindFramebuffer(0x8D40, self.aa_target.fb)
            g.Viewport(0, 0, self.w, self.h)
            g.ClearColor(0, 0, 0, 0)
            g.Clear(0x4000)
            self.geometry(geo, self.w, self.h)
            tex = self.aa_target.resolve()
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            self.quad('view', tex, self.time, dt, self.w, self.h)

        elif self.effect in PHYSICAL_EFFECTS:
            world = self.physical.world(self.time)
            tex = self.world_gpu.render(world, self.time, self.intensity, self.palette(), self.secondary)
            g.BindFramebuffer(0x8D40, target)
            g.Viewport(0, 0, ow, oh)
            intensity = self.intensity
            self.intensity = 1.
            self.quad('view', tex, self.time, dt, self.w, self.h)
            self.intensity = intensity

        err = g.GetError()
        if err:
            raise RuntimeError(f'GLES error {err:#x}')

    def palette(self):
        if self.params.get('monochrome'):
            return (.3, .3, .3)
        return tuple(self.params.get('custom_palette', self.accent))

    def set_seed(self, seed):
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**24:
            raise ValueError('Invalid seed')
        self.next_seed = seed
        if self.effect != 'harmonograph':
            self.seed = seed
        if hasattr(self, 'ink'):
            self.ink.seed = seed
            self.ink.last_cycle = -1
            self.ink.valid = 0
        if hasattr(self, 'machine'):
            self.machine.seed = seed
        if hasattr(self, 'generative'):
            self.generative.build(seed)
        if hasattr(self, 'physical'):
            self.physical.build(seed)
        if hasattr(self, 'rain'):
            self.rain = Rain(seed, self.params)

    def set_parameters(self, params):
        new = validate(self.effect, params)
        if hasattr(self, 'ink') and new.get('density') != self.params.get('density'):
            self.ink = type(self.ink)(self.seed, new['density'])
        if hasattr(self, 'generative'):
            self.generative.p = new
            self.generative.build(self.seed)
        if hasattr(self, 'physical'):
            self.physical.p = new
            self.physical.build(self.seed)
        if hasattr(self, 'rain'):
            self.rain.p = new
        self.params = new
        self.intensity = new['brightness']
        self.speed = new['speed'] * (.35 if new['reduced_motion'] else 1.)

    def close(self):
        g = self.gl
        if hasattr(self, 'machine'):
            self.machine.close()
        if hasattr(self, 'world_gpu'):
            self.world_gpu.close()
        if hasattr(self, 'aa_target') and self.aa_target:
            self.aa_target.close()
            self.aa_target = None
        if getattr(self, 'bg_tex', None):
            g.delete('Textures', self.bg_tex)
            self.bg_tex = None
        for tex, fb in self.targets:
            g.delete('Textures', tex)
            g.delete('Framebuffers', fb)
        for pr in self.programs.values():
            g.DeleteProgram(pr)
        g.delete('Buffers', self.vbo)
        g.delete('VertexArrays', self.vao)
        self.targets = []
        self.programs = {}
