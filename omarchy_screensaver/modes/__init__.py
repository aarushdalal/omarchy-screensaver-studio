"""Screensaver visual modes module with lazy-loading registry."""

import importlib
from typing import Dict, Type

from .base import BaseMode

MODE_MODULE_MAP = {
    "clock": ("clock", "ClockMode"),
    "matrix": ("matrix", "MatrixMode"),
    "particles": ("particles", "ParticlesMode"),
    "warp": ("warp", "WarpMode"),
    "geometry": ("geometry", "GeometryMode"),
    "singularity": ("singularity", "SingularityMode"),
    "system": ("system", "SystemDashboardMode"),
    "terminal": ("terminal", "TerminalMode"),
    "visualizer": ("visualizer", "VisualizerMode"),
    "aurora": ("aurora", "AuroraMode"),
    # 5 New Dark Ambient Modes
    "cyber_nexus": ("cyber_nexus", "CyberNexusMode"),
    "synthwave": ("synthwave", "SynthwaveMode"),
    "quantum_helix": ("quantum_helix", "QuantumHelixMode"),
    "topography": ("topography", "TopographyMode"),
    "celestial_orbit": ("celestial_orbit", "CelestialOrbitMode"),
}

AVAILABLE_MODES = list(MODE_MODULE_MAP.keys())
_LOADED_MODES: Dict[str, Type[BaseMode]] = {}


def get_mode_class(name: str) -> Type[BaseMode]:
    """Dynamically loads and caches mode classes on demand."""
    key = name.lower()
    if key in _LOADED_MODES:
        return _LOADED_MODES[key]

    if key in MODE_MODULE_MAP:
        mod_name, cls_name = MODE_MODULE_MAP[key]
        mod = importlib.import_module(f".{mod_name}", package=__name__)
        cls = getattr(mod, cls_name)
        _LOADED_MODES[key] = cls
        return cls

    # Fallback to clock
    if "clock" not in _LOADED_MODES:
        mod = importlib.import_module(".clock", package=__name__)
        _LOADED_MODES["clock"] = getattr(mod, "ClockMode")
    return _LOADED_MODES["clock"]


def create_mode(name: str, theme, config, monitor_index: int = 0) -> BaseMode:
    """Instantiate a mode by name with lazy loading and fallback to clock."""
    mode_cls = get_mode_class(name)
    return mode_cls(theme, config, monitor_index)
