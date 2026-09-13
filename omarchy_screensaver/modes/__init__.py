"""Screensaver visual modes module."""

from .aurora import AuroraMode
from .base import BaseMode
from .clock import ClockMode
from .geometry import GeometryMode
from .matrix import MatrixMode
from .particles import ParticlesMode
from .singularity import SingularityMode
from .system import SystemDashboardMode
from .terminal import TerminalMode
from .visualizer import VisualizerMode
from .warp import WarpMode

MODE_REGISTRY = {
    "clock": ClockMode,
    "matrix": MatrixMode,
    "particles": ParticlesMode,
    "warp": WarpMode,
    "geometry": GeometryMode,
    "singularity": SingularityMode,
    "system": SystemDashboardMode,
    "terminal": TerminalMode,
    "visualizer": VisualizerMode,
    "aurora": AuroraMode,
}

AVAILABLE_MODES = list(MODE_REGISTRY.keys())


def create_mode(name: str, theme, config, monitor_index: int = 0) -> BaseMode:
    """Instantiate a mode by name with fallback to clock."""
    mode_cls = MODE_REGISTRY.get(name.lower(), ClockMode)
    return mode_cls(theme, config, monitor_index)
