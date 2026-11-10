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
    "eclipse": ("eclipse", "EclipseMode"),
    "ink_flow": ("ink_flow", "InkFlowMode"),
    "rain": ("rain", "RainMode"),
    # 24 DAEMON Satisfying GPU modes
    "harmonograph": ("satisfying", "HarmonographMode"),
    "infinite_ripples": ("satisfying", "InfiniteRipplesMode"),
    "the_perfect_machine": ("satisfying", "ThePerfectMachineMode"),
    "ink_singularity": ("satisfying", "InkSingularityMode"),
    "zen_geometry": ("satisfying", "ZenGeometryMode"),
    "fractal_bloom": ("satisfying", "FractalBloomMode"),
    "particle_architect": ("satisfying", "ParticleArchitectMode"),
    "harmonic_sculpture": ("satisfying", "HarmonicSculptureMode"),
    "circuit_genesis": ("satisfying", "CircuitGenesisMode"),
    "circuit_weaver": ("satisfying", "CircuitWeaverMode"),
    "mechanical_eternity": ("satisfying", "MechanicalEternityMode"),
    "silk_continuum": ("satisfying", "SilkContinuumMode"),
    "infinite_marble_machine": ("satisfying", "InfiniteMarbleMachineMode"),
    "domino_architect": ("satisfying", "DominoArchitectMode"),
    "wave_field": ("satisfying", "WaveFieldMode"),
    "orbital_synchronization": ("satisfying", "OrbitalSynchronizationMode"),
    "infinite_origami": ("satisfying", "InfiniteOrigamiMode"),
    "monolithic_construction": ("satisfying", "MonolithicConstructionMode"),
    "midnight_rain": ("satisfying", "MidnightRainMode"),
    "liquid_obsidian": ("satisfying", "LiquidObsidianMode"),
    "mercury_garden": ("satisfying", "MercuryGardenMode"),
    "event_horizon": ("satisfying", "EventHorizonMode"),
    "infinite_zen_garden": ("satisfying", "InfiniteZenGardenMode"),
    "ink_choreography": ("satisfying", "InkChoreographyMode"),
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
