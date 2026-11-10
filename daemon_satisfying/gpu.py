"""Small GLES 3 binding over the system Mesa libraries. No downloaded runtime."""
import ctypes as C
import time
import numpy as np

U, I, F, P = C.c_uint, C.c_int, C.c_float, C.c_void_p
class GL:
    def __init__(self):
        self.lib = C.CDLL('libGLESv2.so.2')
        specs = {
            'GenRenderbuffers':(None,[I,C.POINTER(U)]),'BindRenderbuffer':(None,[U,U]),'RenderbufferStorage':(None,[U,U,I,I]),'FramebufferRenderbuffer':(None,[U,U,U,U]),'DeleteRenderbuffers':(None,[I,C.POINTER(U)]),
            'GetString': (C.c_char_p,[U]), 'GetError': (U,[]),
            'CreateShader':(U,[U]), 'ShaderSource':(None,[U,I,C.POINTER(C.c_char_p),C.POINTER(I)]),
            'CompileShader':(None,[U]),'GetShaderiv':(None,[U,U,C.POINTER(I)]),
            'GetShaderInfoLog':(None,[U,I,C.POINTER(I),P]),'DeleteShader':(None,[U]),
            'CreateProgram':(U,[]),'AttachShader':(None,[U,U]),'LinkProgram':(None,[U]),
            'GetProgramiv':(None,[U,U,C.POINTER(I)]),'GetProgramInfoLog':(None,[U,I,C.POINTER(I),P]),
            'UseProgram':(None,[U]),'DeleteProgram':(None,[U]),
            'GetUniformLocation':(I,[U,C.c_char_p]),'Uniform1i':(None,[I,I]),
            'Uniform1f':(None,[I,F]),'Uniform2f':(None,[I,F,F]),'Uniform3f':(None,[I,F,F,F]),
            'GenVertexArrays':(None,[I,C.POINTER(U)]),'BindVertexArray':(None,[U]),
            'DeleteVertexArrays':(None,[I,C.POINTER(U)]),'GenBuffers':(None,[I,C.POINTER(U)]),
            'BindBuffer':(None,[U,U]),'BufferData':(None,[U,C.c_ssize_t,P,U]),
            'DeleteBuffers':(None,[I,C.POINTER(U)]),'EnableVertexAttribArray':(None,[U]),
            'VertexAttribPointer':(None,[U,I,U,U,I,P]),'DrawArrays':(None,[U,I,I]),
            'GenTextures':(None,[I,C.POINTER(U)]),'BindTexture':(None,[U,U]),
            'TexImage2D':(None,[U,I,I,I,I,I,U,U,P]),'TexParameteri':(None,[U,U,I]),
            'DeleteTextures':(None,[I,C.POINTER(U)]),'ActiveTexture':(None,[U]),
            'GenFramebuffers':(None,[I,C.POINTER(U)]),'BindFramebuffer':(None,[U,U]),
            'FramebufferTexture2D':(None,[U,U,U,U,I]),'CheckFramebufferStatus':(U,[U]),
            'DeleteFramebuffers':(None,[I,C.POINTER(U)]),'Viewport':(None,[I,I,I,I]),
            'ClearColor':(None,[F,F,F,F]),'Clear':(None,[U]),
            'Enable':(None,[U]),'Disable':(None,[U]),'BlendFunc':(None,[U,U]),
            'ReadPixels':(None,[I,I,I,I,U,U,P]),'Finish':(None,[]),
            'RenderbufferStorageMultisample':(None,[U,I,U,I,I]),
            'BlitFramebuffer':(None,[I,I,I,I,I,I,I,I,U,U]),
            'GetIntegerv':(None,[U,C.POINTER(I)]),
        }
        for name,(ret,args) in specs.items():
            fn=getattr(self.lib,'gl'+name); fn.restype=ret; fn.argtypes=args
            setattr(self,name,fn)
    def gen(self,kind):
        v=U(); getattr(self,'Gen'+kind)(1,C.byref(v)); return v.value
    def delete(self,kind,v):
        v=U(v); getattr(self,'Delete'+kind)(1,C.byref(v))
    def program(self,vert,frag):
        shaders=[]; start=time.perf_counter()
        try:
            for typ,src in [(0x8B31,vert),(0x8B30,frag)]:
                sh=self.CreateShader(typ); shaders.append(sh)
                s=C.c_char_p(src.encode()); self.ShaderSource(sh,1,C.byref(s),None)
                self.CompileShader(sh); ok=I(); self.GetShaderiv(sh,0x8B81,C.byref(ok))
                if not ok.value:
                    log=C.create_string_buffer(16384); self.GetShaderInfoLog(sh,len(log),None,log)
                    raise RuntimeError(log.value.decode())
            pr=self.CreateProgram()
            for sh in shaders:self.AttachShader(pr,sh)
            self.LinkProgram(pr); ok=I(); self.GetProgramiv(pr,0x8B82,C.byref(ok))
            if not ok.value:
                log=C.create_string_buffer(16384); self.GetProgramInfoLog(pr,len(log),None,log)
                self.DeleteProgram(pr); raise RuntimeError(log.value.decode())
            return pr, (time.perf_counter()-start)*1000
        finally:
            for sh in shaders:self.DeleteShader(sh)
    def uniform(self,pr,key,*values):
        loc=self.GetUniformLocation(pr,key.encode())
        if loc<0:return
        if len(values)==1 and isinstance(values[0],int):self.Uniform1i(loc,values[0])
        else:getattr(self,'Uniform'+str(len(values))+'f')(loc,*map(float,values))
    def target(self,w,h,floating=False):
        tex=self.gen('Textures'); self.BindTexture(0x0DE1,tex)
        self.TexImage2D(0x0DE1,0,0x881A if floating else 0x8058,w,h,0,0x1908,0x1406 if floating else 0x1401,None)
        for pname,param in [(0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812F),(0x2803,0x812F)]:
            self.TexParameteri(0x0DE1,pname,param)
        fb=self.gen('Framebuffers'); self.BindFramebuffer(0x8D40,fb)
        self.FramebufferTexture2D(0x8D40,0x8CE0,0x0DE1,tex,0)
        if self.CheckFramebufferStatus(0x8D40)!=0x8CD5:raise RuntimeError('Incomplete framebuffer')
        self.ClearColor(0,0,0,0); self.Clear(0x4000)
        return tex,fb
    def pixels(self,w,h):
        a=np.empty((h,w,4),np.uint8); self.ReadPixels(0,0,w,h,0x1908,0x1401,a.ctypes.data_as(P))
        return np.flipud(a).copy()

class AATarget:
    """Multisampled geometry target with an explicit single-sample texture resolve.

    Feedback simulations deliberately keep their own single-sample textures.
    """
    def __init__(self,gl,w,h,samples=4,depth=False):
        self.g=gl;self.w=w;self.h=h;self.closed=False;self.depth=None
        maximum=I();gl.GetIntegerv(0x8D57,C.byref(maximum))
        self.samples=max(1,min(int(samples),maximum.value))
        self.tex,self.resolve_fb=gl.target(w,h)
        self.fb=gl.gen('Framebuffers');self.color=gl.gen('Renderbuffers')
        gl.BindFramebuffer(0x8D40,self.fb);gl.BindRenderbuffer(0x8D41,self.color)
        gl.RenderbufferStorageMultisample(0x8D41,self.samples,0x8058,w,h)
        gl.FramebufferRenderbuffer(0x8D40,0x8CE0,0x8D41,self.color)
        if depth:
            self.depth=gl.gen('Renderbuffers');gl.BindRenderbuffer(0x8D41,self.depth)
            gl.RenderbufferStorageMultisample(0x8D41,self.samples,0x81A6,w,h)
            gl.FramebufferRenderbuffer(0x8D40,0x8D00,0x8D41,self.depth)
        if gl.CheckFramebufferStatus(0x8D40)!=0x8CD5:
            self.close();raise RuntimeError('Multisample geometry target incomplete')
        gl.Viewport(0,0,w,h);gl.ClearColor(0,0,0,1);gl.Clear(0x4000)
    def resolve(self):
        g=self.g;g.BindFramebuffer(0x8CA8,self.fb)
        g.BindFramebuffer(0x8CA9,self.resolve_fb)
        g.BlitFramebuffer(0,0,self.w,self.h,0,0,self.w,self.h,0x4000,0x2600)
        return self.tex
    def close(self):
        if self.closed:return
        self.closed=True;g=self.g
        g.delete('Textures',self.tex);g.delete('Framebuffers',self.resolve_fb)
        g.delete('Framebuffers',self.fb);g.delete('Renderbuffers',self.color)
        if self.depth is not None:g.delete('Renderbuffers',self.depth)

class Headless:
    """EGL surfaceless display + pbuffer. Fails rather than hiding software fallback."""
    def __init__(self,w,h,allow_software=False):
        e=C.CDLL('libEGL.so.1'); self.e=e
        specs={'GetPlatformDisplay':(P,[U,P,C.POINTER(I)]),'Initialize':(U,[P,C.POINTER(I),C.POINTER(I)]),
        'BindAPI':(U,[U]),'ChooseConfig':(U,[P,C.POINTER(I),C.POINTER(P),I,C.POINTER(I)]),
        'CreatePbufferSurface':(P,[P,P,C.POINTER(I)]),'CreateContext':(P,[P,P,P,C.POINTER(I)]),
        'MakeCurrent':(U,[P,P,P,P]),'DestroyContext':(U,[P,P]),'DestroySurface':(U,[P,P]),'Terminate':(U,[P])}
        for name,(ret,args) in specs.items():
            f=getattr(e,'egl'+name);f.restype=ret;f.argtypes=args;setattr(self,name,f)
        def attrs(*v):return (I*len(v))(*v)
        self.display=self.GetPlatformDisplay(0x31DD,None,None)
        major=I();minor=I()
        if not self.Initialize(self.display,C.byref(major),C.byref(minor)):raise RuntimeError('EGL initialization failed')
        self.BindAPI(0x30A0);config=P(); count=I()
        self.ChooseConfig(self.display,attrs(0x3033,1,0x3040,0x40,0x3024,8,0x3023,8,0x3022,8,0x3038),C.byref(config),1,C.byref(count))
        if not count.value:raise RuntimeError('No GLES3 EGL config')
        self.surface=self.CreatePbufferSurface(self.display,config,attrs(0x3057,w,0x3056,h,0x3038))
        self.context=self.CreateContext(self.display,config,None,attrs(0x3098,3,0x3038))
        if not self.MakeCurrent(self.display,self.surface,self.surface,self.context):raise RuntimeError('EGL context failed')
        self.gl=GL(); self.renderer=self.gl.GetString(0x1F01).decode()
        if not allow_software and any(s in self.renderer.lower() for s in ['llvmpipe','softpipe','swrast']):
            self.close();raise RuntimeError('Software renderer refused: '+self.renderer)
    def close(self):
        self.MakeCurrent(self.display,None,None,None)
        self.DestroyContext(self.display,self.context);self.DestroySurface(self.display,self.surface);self.Terminate(self.display)
