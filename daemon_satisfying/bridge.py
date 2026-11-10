"""Studio bridge integrating Satisfying 24 GPU effects with omarchy_screensaver.

Exposes GPU-accelerated BaseMode subclasses that map to engine.Engine and preview.Surface,
maintaining theme synchronisation, input handling, and Preferences configuration.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple, Type
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from .engine import Engine
from .preferences import Preferences
from .preview import Surface
from .settings import SPEC

try:
    from omarchy_screensaver.modes.base import BaseMode
except ImportError:
    class BaseMode:  # type: ignore
        """Fallback mock for headless unit tests without omarchy_screensaver on sys.path."""
        def __init__(self, theme, config, monitor_index: int = 0):
            self.theme = theme
            self.config = config
            self.monitor_index = monitor_index
            self.time: float = 0.0

        def update_theme(self, theme):
            self.theme = theme

        def update(self, dt: float, metrics: Any, media_info: Any):
            self.time += dt

        def on_resize(self, width: int, height: int):
            pass

        def render(self, cr: Any, width: int, height: int, scale: float):
            pass


class SatisfyingMode(BaseMode):
    """Base adapter connecting an Engine effect to the screensaver window."""

    is_gpu: bool = True
    effect_id: str = ""

    def __init__(self, theme: Any, config: Any, monitor_index: int = 0) -> None:
        super().__init__(theme, config, monitor_index)
        self.preferences = Preferences()
        self.quality = self.preferences.data.get("quality", "balanced")
        self.seed = self.preferences.data.get("seed", 1)
        self.params = dict(self.preferences.data.get("effects", {}).get(self.effect_id, {}))
        self.surface: Optional[Surface] = None

    def update_theme(self, theme: Any) -> None:
        """Propagate live palette updates to active GPU engine."""
        super().update_theme(theme)
        if self.surface:
            self.surface.theme = theme
            if self.surface.engine and hasattr(self.surface.engine, "update_theme"):
                self.surface.engine.update_theme(theme)

    def update(self, dt: float, metrics: Any, media_info: Optional[Any]) -> None:
        """Advance time; GPU engine handles internal physics inside render loop."""
        self.time += dt

    def on_resize(self, width: int, height: int) -> None:
        """Window resize notification: GLArea owns FBO reallocation during render."""
        if self.surface:
            if hasattr(self.surface, "queue_render"):
                self.surface.queue_render()
            elif hasattr(self.surface, "queue_draw"):
                self.surface.queue_draw()

    def get_widget(self, window: Any) -> Gtk.Widget:
        """Create or return the Gtk.GLArea surface for this mode."""
        if self.surface is None:
            self.surface = Surface(
                effect=self.effect_id,
                quality=self.quality,
                seed=self.seed,
                params=self.params,
                theme=self.theme,
            )
        return self.surface

    def render(self, cr: Any, width: int, height: int, scale: float) -> None:
        """Cairo fallback representation for headless diagnostics and static previews."""
        if cr is not None and getattr(self, "theme", None):
            palette = getattr(self.theme, "palette", self.theme)
            accent = getattr(palette, "accent", (0.8, 0.8, 0.8, 1.0))
            cr.set_source_rgba(accent[0], accent[1], accent[2], 0.8)
            cr.rectangle(0, 0, width, height)
            cr.fill()

    def close(self) -> None:
        """Release underlying GPU surface and engine context with active GL context."""
        if not self.surface:
            return

        surface = self.surface
        self.surface = None

        if getattr(surface, "tick_id", None):
            try:
                surface.remove_tick_callback(surface.tick_id)
            except Exception:
                pass
            surface.tick_id = None

        engine = getattr(surface, "engine", None)
        if engine:
            surface.engine = None
            if hasattr(surface, "get_realized") and surface.get_realized():
                try:
                    surface.make_current()
                except Exception:
                    pass
            elif hasattr(surface, "make_current"):
                try:
                    surface.make_current()
                except Exception:
                    pass

            try:
                engine.close()
            except Exception:
                pass


def _to_pascal_case(snake_str: str) -> str:
    return "".join(part.capitalize() for part in snake_str.split("_")) + "Mode"


# Construct explicit classes for all 24 SPEC effect IDs
MODE_CLASSES: Dict[str, Type[SatisfyingMode]] = {}

for effect_name in sorted(SPEC.keys()):
    cls_name = _to_pascal_case(effect_name)
    cls = type(
        cls_name,
        (SatisfyingMode,),
        {
            "effect_id": effect_name,
            "__doc__": f"GPU screensaver mode adapter for '{effect_name}'.",
        },
    )
    MODE_CLASSES[effect_name] = cls
    globals()[cls_name] = cls

# Explicit exports for all 24 mode classes
HarmonographMode = MODE_CLASSES["harmonograph"]
InfiniteRipplesMode = MODE_CLASSES["infinite_ripples"]
ThePerfectMachineMode = MODE_CLASSES["the_perfect_machine"]
InkSingularityMode = MODE_CLASSES["ink_singularity"]
ZenGeometryMode = MODE_CLASSES["zen_geometry"]
FractalBloomMode = MODE_CLASSES["fractal_bloom"]
ParticleArchitectMode = MODE_CLASSES["particle_architect"]
HarmonicSculptureMode = MODE_CLASSES["harmonic_sculpture"]
CircuitGenesisMode = MODE_CLASSES["circuit_genesis"]
CircuitWeaverMode = MODE_CLASSES["circuit_weaver"]
MechanicalEternityMode = MODE_CLASSES["mechanical_eternity"]
SilkContinuumMode = MODE_CLASSES["silk_continuum"]
InfiniteMarbleMachineMode = MODE_CLASSES["infinite_marble_machine"]
DominoArchitectMode = MODE_CLASSES["domino_architect"]
WaveFieldMode = MODE_CLASSES["wave_field"]
OrbitalSynchronizationMode = MODE_CLASSES["orbital_synchronization"]
InfiniteOrigamiMode = MODE_CLASSES["infinite_origami"]
MonolithicConstructionMode = MODE_CLASSES["monolithic_construction"]
MidnightRainMode = MODE_CLASSES["midnight_rain"]
LiquidObsidianMode = MODE_CLASSES["liquid_obsidian"]
MercuryGardenMode = MODE_CLASSES["mercury_garden"]
EventHorizonMode = MODE_CLASSES["event_horizon"]
InfiniteZenGardenMode = MODE_CLASSES["infinite_zen_garden"]
InkChoreographyMode = MODE_CLASSES["ink_choreography"]

__all__ = [
    "SatisfyingMode",
    "MODE_CLASSES",
    "HarmonographMode",
    "InfiniteRipplesMode",
    "ThePerfectMachineMode",
    "InkSingularityMode",
    "ZenGeometryMode",
    "FractalBloomMode",
    "ParticleArchitectMode",
    "HarmonicSculptureMode",
    "CircuitGenesisMode",
    "CircuitWeaverMode",
    "MechanicalEternityMode",
    "SilkContinuumMode",
    "InfiniteMarbleMachineMode",
    "DominoArchitectMode",
    "WaveFieldMode",
    "OrbitalSynchronizationMode",
    "InfiniteOrigamiMode",
    "MonolithicConstructionMode",
    "MidnightRainMode",
    "LiquidObsidianMode",
    "MercuryGardenMode",
    "EventHorizonMode",
    "InfiniteZenGardenMode",
    "InkChoreographyMode",
]
