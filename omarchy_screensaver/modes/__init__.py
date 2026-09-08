"""Screensaver visual modes module."""

from .aurora import AuroraMode
from .base import BaseMode
from .clock import ClockMode
from .particles import ParticlesMode
from .system import SystemDashboardMode
from .terminal import TerminalMode
from .visualizer import VisualizerMode

MODE_REGISTRY = {
    "clock": ClockMode,
    "particles": ParticlesMode,
    "terminal": TerminalMode,
    "system": SystemDashboardMode,
    "visualizer": VisualizerMode,
    "aurora": AuroraMode,
}

AVAILABLE_MODES = list(MODE_REGISTRY.keys())


def create_mode(name: str, theme, config, monitor_index: int = 0) -> BaseMode:
    """Instantiate a mode by name with fallback to clock."""
    mode_cls = MODE_REGISTRY.get(name.lower(), ClockMode)
    return mode_cls(theme, config, monitor_index)
